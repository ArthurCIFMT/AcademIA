import os
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import RLock
from uuid import UUID

from qdrant_client import QdrantClient, models

from app.modules.knowledge.embeddings.encoder import EmbeddingError, validate_vectors
from app.modules.knowledge.vector.contracts import (
    CollectionStatus,
    VectorError,
    VectorErrorCode,
)
from app.modules.knowledge.vector.points import Payload, Point
from app.modules.knowledge.vector.settings import VectorSettings

ClientFactory = Callable[[Path], QdrantClient]


def _new_client(path: Path) -> QdrantClient:
    # Todas as operações são serializadas pelo lock do adaptador. O engine local
    # usa SQLite e a API pode chamar a porta em diferentes threads do mesmo worker.
    return QdrantClient(path=str(path), force_disable_check_same_thread=True)


class QdrantStore:
    def __init__(
        self, settings: VectorSettings, *, client_factory: ClientFactory | None = None
    ) -> None:
        self.settings = settings
        self._factory = client_factory or _new_client
        self._client: QdrantClient | None = None
        self._lock = RLock()
        self._pid = os.getpid()

    def _assert_process(self) -> None:
        if os.getpid() != self._pid:
            raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL)

    def _metadata(self) -> dict[str, object]:
        space = self.settings.space
        return {
            "academia": {
                "schema_version": 1,
                "embedding_space": space.model_dump(mode="json"),
                "space_sha256": space.fingerprint,
            }
        }

    def _describe(self, client: QdrantClient) -> CollectionStatus:
        info = client.get_collection(self.settings.collection)
        vectors = info.config.params.vectors
        space = self.settings.space
        if (
            not isinstance(vectors, models.VectorParams)
            or vectors.size != space.dimension
            or vectors.distance != models.Distance.COSINE
            or vectors.multivector_config is not None
            or info.config.params.sparse_vectors
            or (info.config.metadata or {}).get("academia")
            != self._metadata()["academia"]
        ):
            raise VectorError(VectorErrorCode.CONFIGURACAO_INCOMPATIVEL)
        if info.points_count is None:
            raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL)
        return CollectionStatus(
            collection=self.settings.collection,
            model=space.model,
            model_revision=space.revision,
            dimension=space.dimension,
            metric=space.metric,
            space_sha256=space.fingerprint,
            points=info.points_count,
        )

    def check(self) -> CollectionStatus:
        self._assert_process()
        with self._lock:
            candidate = self._client
            try:
                if candidate is None:
                    candidate = self._factory(self.settings.directory)
                    if not candidate.collection_exists(self.settings.collection):
                        candidate.create_collection(
                            self.settings.collection,
                            vectors_config=models.VectorParams(
                                size=self.settings.space.dimension,
                                distance=models.Distance.COSINE,
                            ),
                            metadata=self._metadata(),
                        )
                status = self._describe(candidate)
                self._client = candidate
                return status
            except Exception as error:
                # Preservar a falha original; não trocar engine, recriar coleção ou
                # converter indisponibilidade em uma lista vazia de evidências.
                if candidate is not None:
                    with suppress(Exception):
                        candidate.close()
                self._client = None
                if isinstance(error, VectorError):
                    raise error from None
                raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL) from None

    def close(self) -> None:
        self._assert_process()
        with self._lock:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL) from None
                self._client = None

    def upsert(self, points: list[Point]) -> None:
        with self._lock:
            self.check()
            if not self.settings.space.revision:
                raise VectorError(VectorErrorCode.CONFIGURACAO_INCOMPATIVEL)
            try:
                for point in points:
                    point.check(
                        self.settings.space.dimension, self.settings.space.fingerprint
                    )
                assert self._client is not None
                self._client.upsert(
                    self.settings.collection,
                    points=[
                        models.PointStruct(
                            id=str(p.id),
                            vector=p.vector,
                            payload={
                                **p.payload.model_dump(mode="json"),
                                "payload_sha256": p.payload.fingerprint,
                            },
                        )
                        for p in points
                    ],
                    wait=True,
                )
            except Exception:
                raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL) from None

    def present(self, expected: dict[UUID, Payload]) -> set[UUID]:
        with self._lock:
            self.check()
            assert self._client is not None
            found: set[UUID] = set()
            try:
                ids = list(expected)
                for start in range(0, len(ids), 128):
                    records = self._client.retrieve(
                        self.settings.collection,
                        ids=[str(x) for x in ids[start : start + 128]],
                        with_payload=True,
                        with_vectors=True,
                    )
                    for record in records:
                        try:
                            id = UUID(str(record.id))
                            payload = dict(record.payload or {})
                            checksum = payload.pop("payload_sha256", None)
                            parsed = Payload.model_validate(payload)
                            parsed.check()
                        except (ValueError, TypeError):
                            continue
                        if (
                            id in expected
                            and parsed == expected[id]
                            and checksum == parsed.fingerprint
                            and isinstance(record.vector, list)
                        ):
                            try:
                                validate_vectors(
                                    [
                                        [
                                            float(x)
                                            for x in record.vector
                                            if isinstance(x, (float, int))
                                        ]
                                    ],
                                    1,
                                    self.settings.space.dimension,
                                )
                            except (ValueError, TypeError, EmbeddingError):
                                continue
                            found.add(id)
                return found
            except Exception:
                raise VectorError(VectorErrorCode.SERVICO_INDISPONIVEL) from None

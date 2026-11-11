import os
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import RLock

from qdrant_client import QdrantClient, models

from app.modules.knowledge.vector.contracts import (
    CollectionStatus,
    VectorError,
    VectorErrorCode,
)
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

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid5

import portalocker
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.identity.roles import effective_roles
from app.modules.knowledge.embeddings.encoder import (
    EmbeddingError,
    Encoder,
    validate_vectors,
)
from app.modules.knowledge.ingestion.chunking import (
    Chunk,
    ChunkingError,
    Selection,
    make_chunks,
    plan_hash,
)
from app.modules.knowledge.ingestion.contracts import ExtractionResult, digest
from app.modules.knowledge.ingestion.index_models import Fragment, Ingestion
from app.modules.knowledge.models import DocumentVersion
from app.modules.knowledge.service import CorpusError, authorize, is_approved
from app.modules.knowledge.vector.contracts import VectorError
from app.modules.knowledge.vector.points import Payload, Point, VectorIndex
from app.policies.access import Actor


class IndexingError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class IndexingResult:
    id: UUID
    estado: str
    total: int
    indexados: int
    erro_codigo: str | None


def available_ingestions(
    session: Session, collection: str, space_hash: str
) -> list[UUID]:
    rows = session.execute(
        select(Ingestion.id, Ingestion.configuracao)
        .join(DocumentVersion, DocumentVersion.id == Ingestion.documento_versao_id)
        .where(
            Ingestion.estado == "CONCLUIDA",
            Ingestion.colecao == collection,
            DocumentVersion.ambiente == "LITERATURA",
            DocumentVersion.estado == "APROVADO",
            DocumentVersion.revision == Ingestion.aprovacao_revisao,
        )
    )
    return [
        id for id, configuration in rows if configuration["space_sha256"] == space_hash
    ]


class Indexer:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        index: VectorIndex,
        encoder: Encoder,
        *,
        lock_root: Path | None = None,
        batch_size: int = 8,
        timeout: float = 60,
        batch_budget: float = 180,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 1 <= batch_size <= 32 or timeout <= 0 or batch_budget <= 0:
            raise ValueError("Limites inválidos.")
        self.sessions, self.index, self.encoder = sessions, index, encoder
        self.root = (
            lock_root
            or Path(os.environ.get("ACADEMIA_INDEX_LOCK_DIR", "data/indexacao"))
        ).resolve()
        self.batch_size, self.timeout, self.batch_budget, self.sleep = (
            batch_size,
            timeout,
            batch_budget,
            sleep,
        )

    def _authorize(
        self, session: Session, actor: Actor, extraction: ExtractionResult
    ) -> None:
        authorize(Actor(actor.user_id, effective_roles(session, actor.user_id)))
        session.get(
            DocumentVersion,
            extraction.documento_versao_id,
            with_for_update=True,
            populate_existing=True,
        )
        if not is_approved(
            session, extraction.documento_versao_id, extraction.aprovacao_revisao
        ):
            raise IndexingError("VERSAO_NAO_APROVADA")
        source = session.get(DocumentVersion, extraction.documento_versao_id)
        assert source
        if (
            source.sha256 != extraction.arquivo_sha256
            or source.metadados != extraction.metadados.model_dump(mode="json")
        ):
            raise IndexingError("ORIGEM_INCONSISTENTE")

    def _result(self, session: Session, id: UUID) -> IndexingResult:
        row = session.get(Ingestion, id, populate_existing=True)
        assert row
        done = len(
            list(
                session.scalars(
                    select(Fragment.id).where(
                        Fragment.ingestao_id == id, Fragment.indexado_em.is_not(None)
                    )
                )
            )
        )
        return IndexingResult(row.id, row.estado, row.total, done, row.erro_codigo)

    def _state(
        self, session: Session, row: Ingestion, state: str, error: str | None
    ) -> None:
        row.estado, row.erro_codigo = state, error
        row.concluida_em = datetime.now(UTC) if state == "CONCLUIDA" else None
        row.revision += 1
        session.flush()

    def _vectors(self, batch: list[Chunk]) -> list[list[float]]:
        deadline = time.monotonic() + self.batch_budget
        for attempt in range(3):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EmbeddingError("ORCAMENTO_EXCEDIDO")
            try:
                vectors = self.encoder.passages(
                    [chunk.embedding_text for chunk in batch],
                    min(self.timeout, remaining),
                )
                validate_vectors(vectors, len(batch), self.encoder.space.dimension)
                if time.monotonic() > deadline:
                    raise EmbeddingError("ORCAMENTO_EXCEDIDO")
                return vectors
            except EmbeddingError as error:
                if not error.transient or attempt == 2:
                    raise
                delay = float(attempt + 1)
                if time.monotonic() + delay >= deadline:
                    raise EmbeddingError("ORCAMENTO_EXCEDIDO") from None
                self.sleep(delay)
        raise AssertionError("Tentativas esgotadas")

    def run(
        self, actor: Actor, extraction: ExtractionResult, selection: Selection
    ) -> IndexingResult:
        with self.sessions.begin() as session:
            self._authorize(session, actor, extraction)
        space = self.encoder.space
        if not space.revision:
            raise IndexingError("REVISAO_DO_MODELO_NAO_FIXADA")
        status = self.index.check()
        if status.space_sha256 != space.fingerprint:
            raise IndexingError("ESPACO_INCOMPATIVEL")
        configuration = {
            "schema_version": 1,
            "extracao_id": str(extraction.id),
            "extracao_config": extraction.config_sha256,
            "arquivo_sha256": extraction.arquivo_sha256,
            "selection": selection.model_dump(mode="json"),
            "space_sha256": space.fingerprint,
            "space": space.model_dump(mode="json"),
            "chunk_tokens": 300,
            "overlap_tokens": 48,
            "collection": status.collection,
        }
        configuration_hash = digest(configuration)
        id = uuid5(extraction.documento_versao_id, configuration_hash)
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            with portalocker.Lock(str(self.root / (id.hex + ".lock")), timeout=10):
                return self._run_locked(
                    actor, extraction, selection, configuration, configuration_hash, id
                )
        except (OSError, portalocker.exceptions.LockException):
            raise IndexingError("INDEXACAO_OCUPADA_OU_INDISPONIVEL") from None

    def _run_locked(
        self,
        actor: Actor,
        extraction: ExtractionResult,
        selection: Selection,
        configuration: dict[str, object],
        configuration_hash: str,
        id: UUID,
    ) -> IndexingResult:
        pending: str | None = None
        try:
            chunks = make_chunks(extraction, selection, self.encoder, id)
        except ChunkingError as error:
            chunks, pending = [], error.code
        collection = self.index.check().collection
        with self.sessions.begin() as session:
            self._authorize(session, actor, extraction)
            row = session.get(Ingestion, id)
            if row is None:
                row = Ingestion(
                    id=id,
                    documento_versao_id=extraction.documento_versao_id,
                    aprovacao_revisao=extraction.aprovacao_revisao,
                    extracao_id=extraction.id,
                    config_hash=configuration_hash,
                    configuracao=configuration,
                    plano_hash=plan_hash(chunks),
                    colecao=collection,
                    estado="PENDENTE_TRATAMENTO" if pending else "PROCESSANDO",
                    total=len(chunks),
                    erro_codigo=pending,
                    criado_por=actor.user_id,
                    iniciada_em=datetime.now(UTC),
                    concluida_em=None,
                    revision=1,
                )
                session.add(row)
                session.flush()
                for chunk in chunks:
                    session.add(
                        Fragment(
                            id=chunk.id,
                            ingestao_id=id,
                            ordem=chunk.ordinal,
                            pagina_inicio=chunk.pagina,
                            pagina_fim=chunk.pagina,
                            linha_inicio=chunk.linha_inicio,
                            linha_fim=chunk.linha_fim,
                            secao=chunk.secao,
                            inicio=chunk.inicio,
                            fim=chunk.fim,
                            texto_hash=chunk.texto_hash,
                            tokens=chunk.tokens,
                            input_tokens=chunk.input_tokens,
                            vetor_id=chunk.id,
                            colecao=collection,
                            indexado_em=None,
                        )
                    )
                record_audit(
                    session,
                    AuditEvent(
                        id=uuid5(id, "prepared"),
                        actor_id=actor.user_id,
                        action="knowledge.indexing.prepared",
                        resource_type="ingestao",
                        resource_id=id,
                        correlation_id=id,
                        occurred_at=datetime.now(UTC),
                    ),
                )
            elif (
                row.plano_hash != plan_hash(chunks) or row.configuracao != configuration
            ):
                raise IndexingError("PLANO_INCONSISTENTE")
            if pending:
                return self._result(session, id)
            was_complete = row.estado == "CONCLUIDA"
            if not was_complete:
                self._state(session, row, "PROCESSANDO", None)
        payloads = {
            chunk.id: Payload(
                ingestao_id=id,
                documento_versao_id=extraction.documento_versao_id,
                fragmento_id=chunk.id,
                aprovacao_revisao=extraction.aprovacao_revisao,
                config_hash=configuration_hash,
                space_sha256=self.encoder.space.fingerprint,
                texto=chunk.texto,
                texto_hash=chunk.texto_hash,
                metadados=extraction.metadados,
                finalidade=selection.finalidade,
                pagina=chunk.pagina,
                linha_inicio=chunk.linha_inicio,
                linha_fim=chunk.linha_fim,
                secao=chunk.secao,
                inicio=chunk.inicio,
                fim=chunk.fim,
                tokens=chunk.tokens,
                input_tokens=chunk.input_tokens,
            )
            for chunk in chunks
        }
        try:
            present = self.index.present(payloads)
            if was_complete and present == set(payloads):
                with self.sessions.begin() as session:
                    self._authorize(session, actor, extraction)
                    return self._result(session, id)
            missing = [chunk for chunk in chunks if chunk.id not in present]
            with self.sessions.begin() as session:
                if was_complete:
                    row = session.get(Ingestion, id)
                    assert row
                    self._state(session, row, "PROCESSANDO", None)
                for fragment in session.scalars(
                    select(Fragment).where(Fragment.ingestao_id == id)
                ):
                    fragment.indexado_em = (
                        datetime.now(UTC) if fragment.id in present else None
                    )
            for start in range(0, len(missing), self.batch_size):
                with self.sessions.begin() as session:
                    self._authorize(session, actor, extraction)
                batch = missing[start : start + self.batch_size]
                vectors = self._vectors(batch)
                with self.sessions.begin() as session:
                    self._authorize(session, actor, extraction)
                self.index.upsert(
                    [
                        Point(id=chunk.id, vector=vector, payload=payloads[chunk.id])
                        for chunk, vector in zip(batch, vectors, strict=True)
                    ]
                )
                confirmed = self.index.present(
                    {chunk.id: payloads[chunk.id] for chunk in batch}
                )
                if confirmed != {chunk.id for chunk in batch}:
                    raise IndexingError("LOTE_NAO_CONFIRMADO")
                with self.sessions.begin() as session:
                    self._authorize(session, actor, extraction)
                    for fragment in session.scalars(
                        select(Fragment).where(Fragment.id.in_(confirmed))
                    ):
                        fragment.indexado_em = datetime.now(UTC)
            if self.index.present(payloads) != set(payloads):
                raise IndexingError("INDICE_INCOMPLETO")
            with self.sessions.begin() as session:
                self._authorize(session, actor, extraction)
                row = session.get(Ingestion, id)
                assert row
                self._state(session, row, "CONCLUIDA", None)
                record_audit(
                    session,
                    AuditEvent(
                        id=uuid5(id, f"completed:{row.revision}"),
                        actor_id=actor.user_id,
                        action="knowledge.indexing.completed",
                        resource_type="ingestao",
                        resource_id=id,
                        correlation_id=id,
                        occurred_at=datetime.now(UTC),
                    ),
                )
                return self._result(session, id)
        except (EmbeddingError, VectorError, IndexingError, CorpusError) as error:
            code = (
                "PERMISSAO_INDISPONIVEL"
                if isinstance(error, CorpusError)
                else error.code.value
                if isinstance(error, VectorError)
                else error.code
            )
            with self.sessions.begin() as session:
                row = session.get(Ingestion, id)
                assert row
                state = (
                    "REVOGADA"
                    if not is_approved(
                        session,
                        extraction.documento_versao_id,
                        extraction.aprovacao_revisao,
                    )
                    else "FALHA"
                )
                self._state(session, row, state, code)
                return self._result(session, id)

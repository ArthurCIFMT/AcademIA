"""Preparação offline e reproduzível das seleções de literatura já revisadas."""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.knowledge.catalog import import_initial
from app.modules.knowledge.embeddings.encoder import Encoder
from app.modules.knowledge.ingestion.chunking import Selection, Span
from app.modules.knowledge.ingestion.contracts import (
    ExtractionPolicy,
    ExtractionResult,
    State,
    StrictModel,
)
from app.modules.knowledge.ingestion.index_models import Ingestion
from app.modules.knowledge.ingestion.indexing import Indexer, IndexingResult
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.schemas import ImportResult, Purpose
from app.modules.knowledge.service import (
    approved_references,
    authorize,
    is_approved,
)
from app.modules.knowledge.storage import CorpusStorage
from app.modules.knowledge.vector.points import VectorIndex
from app.policies.access import Actor

PLAN = "materiais/rag/preparacao-local-v1.json"
REASON = "Preparação local v1: recortes revisados RAG-05/AI-06."
Hash = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class PlanSource(StrictModel):
    fonte_id: str
    selecao: str
    finalidades: Annotated[list[Purpose], Field(min_length=1)]


class PreparationPlan(StrictModel):
    schema_version: Literal[1]
    limites: str
    fontes: Annotated[list[PlanSource], Field(min_length=1)]


class ReviewedSpan(BaseModel):
    pagina: int
    inicio: int
    fim: int
    secao: str
    texto_hash: Hash

    def span(self) -> Span:
        return Span.model_validate(self.model_dump(exclude={"texto_hash"}))


class ReviewedSource(BaseModel):
    fonte_id: str
    arquivo_sha256: Hash
    trechos: Annotated[list[ReviewedSpan], Field(min_length=1)]
    politica_extracao: str | None = None


@dataclass(frozen=True)
class PreparedSelection:
    source: ReviewedSource
    policy: ExtractionPolicy
    selection: Selection


@dataclass(frozen=True)
class SourceResult:
    fonte_id: str
    finalidade: Purpose
    indexacao: IndexingResult


@dataclass(frozen=True)
class PreparationResult:
    importacao: ImportResult
    ingestoes: tuple[SourceResult, ...]

    def public(self) -> dict[str, object]:
        return {
            "status": "OK",
            "importacao": self.importacao.model_dump(mode="json"),
            "ingestoes": [asdict(item) for item in self.ingestoes],
        }


def _json(root: Path, name: str) -> object:
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    with path.open("rb") as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError("CONFIGURACAO_EXCESSIVA")
    return json.loads(raw)


def load_preparation(root: Path) -> list[PreparedSelection]:
    plan = PreparationPlan.model_validate(_json(root, PLAN))
    approved = _json(root, "materiais/rag/corpus-inicial.json")
    if not isinstance(approved, dict) or not isinstance(
        approved.get("documentos"), list
    ):
        raise ValueError("CURADORIA_INVALIDA")
    result: list[PreparedSelection] = []
    for entry in plan.fontes:
        raw = _json(root, entry.selecao)
        if not isinstance(raw, dict):
            raise ValueError("SELECAO_INVALIDA")
        candidates = raw.get("documentos", [raw])
        if not isinstance(candidates, list):
            raise ValueError("SELECAO_INVALIDA")
        source = next(
            (
                ReviewedSource.model_validate(s)
                for s in candidates
                if isinstance(s, dict) and s.get("fonte_id") == entry.fonte_id
            ),
            None,
        )
        if source is None:
            raise ValueError("FONTE_NAO_SELECIONADA")
        permitted = next(
            (
                s
                for s in approved["documentos"]
                if isinstance(s, dict) and s.get("id") == entry.fonte_id
            ),
            None,
        )
        if (
            permitted is None
            or permitted.get("sha256") != source.arquivo_sha256
            or not set(entry.finalidades) <= set(permitted.get("finalidades", []))
            or len(set(entry.finalidades)) != len(entry.finalidades)
        ):
            raise ValueError("SELECAO_FORA_DA_CURADORIA")
        policy = (
            ExtractionPolicy.model_validate(_json(root, source.politica_extracao))
            if source.politica_extracao
            else ExtractionPolicy()
        )
        for purpose in entry.finalidades:
            result.append(
                PreparedSelection(
                    source,
                    policy,
                    Selection(
                        finalidade=purpose,
                        motivo_curadoria=REASON,
                        trechos=[item.span() for item in source.trechos],
                    ),
                )
            )
    return result


def verify_selection(extraction: ExtractionResult, source: ReviewedSource) -> None:
    if extraction.resultado.estado != State.CONCLUIDA:
        raise ValueError("EXTRACAO_NAO_CONCLUIDA")
    pages = {p.numero: p for p in extraction.resultado.paginas}
    for span in source.trechos:
        page = pages.get(span.pagina)
        if page is None or page.situacao != "TEXTO":
            raise ValueError("PAGINA_NAO_VALIDADA")
        text = page.texto[span.inicio : span.fim]
        if hashlib.sha256(text.encode()).hexdigest() != span.texto_hash:
            raise ValueError("RECORTE_DIVERGENTE_DA_CURADORIA")


def _retire_removed(
    sessions: sessionmaker[Session], actor_id: UUID, keep: set[UUID]
) -> None:
    with sessions.begin() as session:
        actor = Actor(actor_id, effective_roles(session, actor_id))
        authorize(actor)
        for row in session.scalars(
            select(Ingestion).where(Ingestion.estado == "CONCLUIDA").with_for_update()
        ):
            selection = row.configuracao.get("selection")
            if (
                row.id in keep
                or not isinstance(selection, dict)
                or selection.get("motivo_curadoria") != REASON
            ):
                continue
            row.estado = "REVOGADA"
            row.concluida_em = None
            row.erro_codigo = "SELECAO_RETIRADA_DO_PREPARO"
            row.revision += 1
            record_audit(
                session,
                AuditEvent(
                    id=uuid4(),
                    actor_id=actor_id,
                    action="corpus.ingestion.retired",
                    resource_type="ingestao",
                    resource_id=row.id,
                    reason_code="preparacao.plano_atualizado",
                    correlation_id=uuid4(),
                    occurred_at=utc_now(),
                ),
            )


def prepare_corpus(
    sessions: sessionmaker[Session],
    actor_id: UUID,
    storage: CorpusStorage,
    index: VectorIndex,
    encoder: Encoder,
    *,
    root: Path,
    artifacts: Path | None = None,
) -> PreparationResult:
    planned = load_preparation(root)
    with sessions.begin() as session:
        actor = Actor(actor_id, effective_roles(session, actor_id))
        authorize(actor)
        imported = import_initial(
            session, actor, storage, uuid4(), materials=root / "materiais/rag"
        )

    def approved(version: UUID, revision: int) -> bool:
        with sessions.begin() as session:
            return is_approved(session, version, revision)

    results: list[SourceResult] = []
    extractions: dict[tuple[UUID, str], ExtractionResult] = {}
    for item in planned:
        with sessions.begin() as session:
            matches = [
                ref
                for ref in approved_references(session)
                if ref.sha256 == item.source.arquivo_sha256
            ]
        if len(matches) != 1:
            raise ValueError("VERSAO_NAO_APROVADA")
        ref = matches[0]
        key = (ref.version_id, item.policy.fingerprint)
        if key not in extractions:
            extractions[key] = Extractor(
                storage,
                policy=item.policy,
                root=artifacts / "extracoes" if artifacts else None,
            ).extract(ref, approval_check=approved)
        extraction = extractions[key]
        verify_selection(extraction, item.source)
        outcome = Indexer(
            sessions,
            index,
            encoder,
            lock_root=artifacts / "indexacao" if artifacts else None,
        ).run(actor, extraction, item.selection)
        if outcome.estado != "CONCLUIDA":
            raise ValueError("INDEXACAO_NAO_CONCLUIDA")
        results.append(
            SourceResult(item.source.fonte_id, item.selection.finalidade, outcome)
        )
    _retire_removed(sessions, actor_id, {item.indexacao.id for item in results})
    return PreparationResult(imported, tuple(results))

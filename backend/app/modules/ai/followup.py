from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.models import EvidenceRecord, Execution
from app.modules.ai.persistence.state import PostgresState
from app.modules.ai.policies.triage import Policy
from app.modules.ai.schemas.execution import RunResult
from app.modules.knowledge.service import is_approved
from app.modules.training.generation_context import (
    TrainingContext,
    generation_training_context,
)
from app.modules.training.workouts import WorkoutError
from app.policies.access import Actor


class Source(BaseModel):
    fragmento_id: UUID
    documento_versao_id: UUID
    titulo: str
    origem_url: str
    idioma: str
    pagina: int | None
    linha_inicio: int | None
    linha_fim: int | None
    secao: str | None


class GenerationContext(BaseModel):
    execucao_id: UUID
    iniciada_em: UtcTimestamp
    modelo: str
    versao_prompts: str
    regra_versao: int | None
    fontes: list[Source]
    contexto: TrainingContext
    politica_alterada: bool
    fontes_alteradas: bool


def version_context(
    session: Session, actor: Actor, client_id: UUID, version_id: UUID
) -> GenerationContext:
    training = generation_training_context(session, actor, client_id, version_id)
    row = session.scalar(
        select(Execution).where(
            Execution.cliente_id == client_id,
            Execution.versao_publicada_id == version_id,
        )
    )
    if row is None:
        raise WorkoutError(404)
    result = RunResult.model_validate(row.resultado)
    triage = result.triagem
    records = list(
        session.scalars(
            select(EvidenceRecord)
            .where(EvidenceRecord.execucao_id == row.id)
            .order_by(EvidenceRecord.fragmento_id)
        )
    )
    sources = [
        Source.model_validate({key: e.metadados[key] for key in Source.model_fields})
        for e in records
    ]
    changed = any(
        not is_approved(
            session,
            source.documento_versao_id,
            int(str(record.metadados["aprovacao_revisao"])),
        )
        for source, record in zip(sources, records, strict=True)
    )
    return GenerationContext(
        execucao_id=row.id,
        iniciada_em=row.iniciada_em,
        modelo=row.modelo,
        versao_prompts=row.prompt_version,
        regra_versao=triage.regra_versao if triage else None,
        fontes=sources,
        fontes_alteradas=changed,
        contexto=training,
        politica_alterada=bool(triage and triage.regra_sha256 != Policy().fingerprint),
    )


class FollowupService:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def own(self, actor: Actor, id: UUID) -> tuple[RunResult, GenerationContext | None]:
        result = GenerationService(self.sessions).status(actor, id)
        if not result.versao_publicada_id:
            return result, None
        with self.sessions.begin() as session:
            row = session.get(Execution, PostgresState.id(actor, id))
            if row is None:
                raise KeyError(id)
            return result, version_context(
                session, actor, row.cliente_id, result.versao_publicada_id
            )

from uuid import UUID, uuid5

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.modules.assignments.service import PostgresAssignmentReader
from app.modules.notifications.review_status import review_notice_status
from app.modules.onboarding.service import get_current_snapshot
from app.modules.training.catalog import CatalogError, require_prescribable
from app.modules.training.generated import lock_generation_client
from app.modules.training.publication import published_workout
from app.modules.training.review_schemas import ReviewDetail
from app.modules.training.workouts import WorkoutError
from app.policies.access import Actor


class NoticeStatus(BaseModel):
    instrutor_designado_id: UUID | None
    interno_registrado: bool
    email_estado: str | None
    email_tentativas: int


class TrainingContext(BaseModel):
    treino: ReviewDetail
    onboarding_usado_id: UUID
    onboarding_atual_id: UUID | None
    pendencias: list[str]
    aviso: NoticeStatus


def generation_training_context(
    session: Session, actor: Actor, client_id: UUID, version_id: UUID
) -> TrainingContext:
    actor = lock_generation_client(session, actor, client_id)
    detail = published_workout(session, actor, client_id, version_id)
    if not detail or detail.ficha.origem != "IA":
        raise WorkoutError(404)
    snapshot = get_current_snapshot(session, client_id)
    issues = []
    if not snapshot or snapshot.id != detail.ficha.onboarding_id:
        issues.append("ONBOARDING_ATUALIZADO")
    if detail.ficha.conteudo_excluido_em:
        issues.append("CONTEUDO_EXPIRADO")
    else:
        selected = {
            (item.exercicio_id, tuple(item.equipamento_ids)): item.exercicio_snapshot
            for day in detail.ficha.dias
            for item in day.itens
        }
        for (exercise, equipment), snapshot_data in sorted(selected.items()):
            try:
                current = require_prescribable(session, exercise, equipment)
                if current != snapshot_data:
                    issues.append("CATALOGO_OU_RECURSOS_ALTERADOS")
            except CatalogError:
                issues.append("CATALOGO_OU_RECURSOS_ALTERADOS")
    recipient = PostgresAssignmentReader(session).review_recipient(client_id)
    notice = (
        review_notice_status(session, uuid5(version_id, "publicacao"), recipient.id)
        if recipient
        else None
    )
    return TrainingContext(
        treino=detail,
        onboarding_usado_id=detail.ficha.onboarding_id,
        onboarding_atual_id=snapshot.id if snapshot else None,
        pendencias=sorted(set(issues)),
        aviso=NoticeStatus(
            instrutor_designado_id=recipient.id if recipient else None,
            interno_registrado=notice.internal_registered if notice else False,
            email_estado=notice.email.state if notice and notice.email else None,
            email_tentativas=notice.email.attempts if notice and notice.email else 0,
        ),
    )

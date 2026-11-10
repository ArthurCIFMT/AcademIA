from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.identity.models import Role
from app.modules.identity.roles import active_admin_ids, effective_roles
from app.modules.notifications.models import NoticeKind, Notification
from app.policies.access import Actor

NOTICE_ROLES = {
    NoticeKind.TREINO_PARA_AVALIAR: Role.INSTRUTOR,
    NoticeKind.ALTERACAO_CRITICA: Role.ADMINISTRADOR,
}


def _add_notice(
    session: Session, event_id: UUID, recipient_id: UUID, kind: NoticeKind
) -> bool:
    now = datetime.now(UTC)
    statement = (
        insert(Notification)
        .values(
            id=uuid4(),
            evento_id=event_id,
            destinatario_id=recipient_id,
            canal="INTERNO",
            tipo=kind,
            estado="PENDENTE",
            tentativas=0,
            criada_em=now,
            atualizada_em=now,
        )
        .on_conflict_do_nothing(constraint="uq_notificacao_dest_evento_canal")
        .returning(Notification.id)
    )
    return session.scalar(statement) is not None


def notify_workout_review(
    session: Session, event_id: UUID, assigned_instructor_id: UUID | None
) -> bool:
    """O módulo dono da designação informa o responsável atual pela revisão."""
    if assigned_instructor_id is None:
        return False
    if Role.INSTRUTOR not in effective_roles(session, assigned_instructor_id):
        return False
    return _add_notice(
        session, event_id, assigned_instructor_id, NoticeKind.TREINO_PARA_AVALIAR
    )


def notify_critical_change(session: Session, event_id: UUID) -> int:
    """Entrega o aviso a cada administrador ativo na transação do produtor."""
    return sum(
        _add_notice(session, event_id, recipient, NoticeKind.ALTERACAO_CRITICA)
        for recipient in active_admin_ids(session)
    )


def pending_notices(session: Session, actor: Actor) -> list[Notification]:
    visible_kinds = [kind for kind, role in NOTICE_ROLES.items() if role in actor.roles]
    return list(
        session.scalars(
            select(Notification)
            .where(
                Notification.destinatario_id == actor.user_id,
                Notification.canal == "INTERNO",
                Notification.tipo.in_(visible_kinds),
                Notification.estado == "PENDENTE",
            )
            .order_by(Notification.criada_em.desc(), Notification.id.desc())
        )
    )

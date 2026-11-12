from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.ai.chat.models import Message
from app.modules.ai.persistence.models import Execution
from app.modules.identity.service import utc_now


def occupied_slots(session: Session, client: UUID, exclude: UUID | None = None) -> int:
    cutoff = utc_now() - timedelta(seconds=60)
    executions = (
        session.scalar(
            select(func.count())
            .select_from(Execution)
            .where(
                Execution.cliente_id == client,
                Execution.iniciada_em > cutoff,
                Execution.finalidade.in_(["DUVIDA", "ADAPTACAO"]),
            )
        )
        or 0
    )
    reserved = (
        select(func.count())
        .select_from(Message)
        .where(
            Message.conversa_id == client,
            Message.criada_em > cutoff,
            ~select(Execution.id).where(Execution.id == Message.id).exists(),
        )
    )
    if exclude:
        reserved = reserved.where(Message.id != exclude)
    return executions + (session.scalar(reserved) or 0)

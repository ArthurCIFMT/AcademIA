from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.events.contracts import AuditEvent
from app.events.models import OutboxRecord


def enqueue(session: Session, event: AuditEvent) -> bool:
    payload = event.model_dump(mode="json")
    statement = (
        insert(OutboxRecord)
        .values(
            id=event.id,
            evento_tipo=event.action,
            schema_version=event.schema_version,
            payload=payload,
            estado="PENDENTE",
        )
        .on_conflict_do_nothing(index_elements=[OutboxRecord.id])
        .returning(OutboxRecord.id)
    )
    if session.scalar(statement) is not None:
        return True

    existing = session.get(OutboxRecord, event.id)
    if existing is None or existing.payload != payload:
        raise ValueError("O identificador do evento já foi usado com outro conteúdo.")
    return False


def consume_next(
    session: Session, handle: Callable[[Session, AuditEvent], None]
) -> bool:
    statement = (
        select(OutboxRecord)
        .where(OutboxRecord.estado == "PENDENTE")
        .order_by(OutboxRecord.criado_em, OutboxRecord.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    record = session.scalar(statement)
    if record is None:
        return False

    handle(session, AuditEvent.model_validate(record.payload))
    record.estado = "ENTREGUE"
    record.entregue_em = datetime.now(UTC)
    return True

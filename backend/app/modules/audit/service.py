from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.events.contracts import AuditEvent
from app.events.outbox import enqueue
from app.modules.audit.models import AuditRecord


def record_audit(session: Session, event: AuditEvent) -> bool:
    """Registra evidência e evento dentro da transação do chamador."""
    enqueue(session, event)
    statement = (
        insert(AuditRecord)
        .values(
            id=event.id,
            ator_id=event.actor_id,
            acao=event.action,
            recurso_tipo=event.resource_type,
            recurso_id=event.resource_id,
            motivo=event.reason_code,
            correlation_id=event.correlation_id,
            ocorrido_em=event.occurred_at,
        )
        .on_conflict_do_nothing(index_elements=[AuditRecord.id])
        .returning(AuditRecord.id)
    )
    return session.scalar(statement) is not None

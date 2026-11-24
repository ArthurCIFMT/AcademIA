from collections.abc import Callable
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events.contracts import AuditEvent
from app.modules.access.authorization.service import AccessError, prepare_decision
from app.modules.access.events.models import AccessEvent
from app.modules.access.integrations.turnstile.contracts import AccessSettings
from app.modules.access.manual.contracts import ManualConfirmation
from app.modules.access.manual.models import ManualIdentification
from app.modules.audit.service import record_audit
from app.modules.people.membership_directory import MembershipDirectory

FAILURE_STATUSES = frozenset(
    {
        "DESCONHECIDO",
        "PONTUACAO_BAIXA",
        "AMBIGUO",
        "CAPTURA_INVALIDA",
        "FALHA_PROVEDOR",
    }
)


def prepare_manual_decision(
    db: Session,
    failure_id: UUID,
    payload: ManualConfirmation,
    *,
    actor_id: UUID,
    correlation_id: UUID,
    settings: AccessSettings,
    clock: Callable[[], datetime],
) -> tuple[UUID, bool]:
    source = db.get(AccessEvent, failure_id, with_for_update=True)
    if source is None or source.tipo != "IDENTIFICACAO":
        raise AccessError(404)
    if source.resultado_identificacao not in FAILURE_STATUSES:
        raise AccessError(409)
    directory = MembershipDirectory(db)
    directory.lock_people(payload.cliente_id, actor_id)
    if not directory.attendant_is_active(actor_id):
        raise AccessError(403)
    previous = db.scalar(
        select(ManualIdentification).where(
            ManualIdentification.evento_falha_id == failure_id
        )
    )
    if previous is not None:
        event = db.get_one(AccessEvent, previous.evento_id)
        if (
            previous.atendente_id != actor_id
            or event.cliente_id != payload.cliente_id
            or previous.motivo != payload.motivo
        ):
            raise AccessError(409)
        return prepare_decision(db, event.id, settings, clock)

    now = clock()
    if (
        not timedelta()
        <= now - source.ocorrido_em
        <= timedelta(seconds=settings.access_identification_max_age_seconds)
    ):
        raise AccessError(410)
    if not directory.client_exists(payload.cliente_id):
        raise AccessError(404)

    event_id = uuid4()
    db.add(
        AccessEvent(
            id=event_id,
            origem="ATENDIMENTO_MANUAL",
            event_id_externo=str(failure_id),
            cliente_id=payload.cliente_id,
            tipo="IDENTIFICACAO_MANUAL",
            ocorrido_em=now,
            direcao=source.direcao,
            resultado_identificacao="IDENTIFICADO",
            payload_hash=sha256(payload.model_dump_json().encode()).hexdigest(),
        )
    )
    db.flush()
    db.add(
        ManualIdentification(
            evento_id=event_id,
            evento_falha_id=failure_id,
            atendente_id=actor_id,
            motivo=payload.motivo,
        )
    )
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action="acesso.identidade_confirmada_manualmente",
            resource_type="identificacao_manual",
            resource_id=event_id,
            reason_code="falha_biometria",
            correlation_id=correlation_id,
            occurred_at=now,
        ),
    )
    return prepare_decision(db, event_id, settings, clock)

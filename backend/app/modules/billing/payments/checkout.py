from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.contracts.time import UtcTimestamp, academy_date
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.billing.charges.schemas import Page
from app.modules.billing.payments.models import Payment
from app.modules.billing.payments.service import PaymentError
from app.modules.identity.models import Role
from app.modules.identity.roles import effective_roles
from app.modules.memberships.service import active_plan_offer
from app.modules.people.assignment_directory import AssignmentDirectory

SimulationState = Literal["CONFIRMADO", "PENDENTE", "RECUSADO"]
_ORIGIN = "SIMULACAO"


class SimulatePurchase(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    solicitacao_id: UUID
    plano_id: UUID
    resultado: SimulationState


class SimulatedReceipt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plano_id: UUID
    plano_nome_snapshot: str
    valor: Decimal
    estado: SimulationState
    simulado_em: UtcTimestamp
    confirmado_em: UtcTimestamp | None
    simulado: Literal[True] = True


def own_purchase(db: Session, client_id: UUID, purchase_id: UUID) -> SimulatedReceipt:
    row = db.scalar(
        select(Payment).where(
            Payment.cliente_id == client_id,
            Payment.origem == _ORIGIN,
            Payment.id == purchase_id,
        )
    )
    if row is None:
        raise PaymentError(404)
    return SimulatedReceipt.model_validate(row)


def purchase_history(
    db: Session, client_id: UUID, *, page: int, limit: int
) -> Page[SimulatedReceipt]:
    own = (Payment.cliente_id == client_id, Payment.origem == _ORIGIN)
    total = db.scalar(select(func.count()).select_from(Payment).where(*own)) or 0
    rows = db.scalars(
        select(Payment)
        .where(*own)
        .order_by(Payment.simulado_em.desc(), Payment.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return Page(
        itens=[SimulatedReceipt.model_validate(row) for row in rows],
        pagina=page,
        limite=limit,
        total=total,
    )


def _replay(
    row: Payment, client_id: UUID, data: SimulatePurchase
) -> tuple[SimulatedReceipt, bool]:
    if (
        row.origem != _ORIGIN
        or row.cliente_id != client_id
        or row.plano_id != data.plano_id
        or row.estado != data.resultado
    ):
        raise PaymentError(409)
    return SimulatedReceipt.model_validate(row), False


def simulate_purchase(
    db: Session,
    client_id: UUID,
    data: SimulatePurchase,
    *,
    correlation: UUID,
    now: datetime,
) -> tuple[SimulatedReceipt, bool]:
    AssignmentDirectory(db).lock_people(client_id)
    if Role.CLIENTE not in effective_roles(db, client_id):
        raise PaymentError(403)
    existing = db.get(Payment, data.solicitacao_id)
    if existing is not None:
        return _replay(existing, client_id, data)
    offer = active_plan_offer(db, data.plano_id)
    if offer is None:
        raise PaymentError(409)
    confirmed = data.resultado == "CONFIRMADO"
    row = db.scalar(
        insert(Payment)
        .values(
            id=data.solicitacao_id,
            origem=_ORIGIN,
            cliente_id=client_id,
            plano_id=data.plano_id,
            plano_nome_snapshot=offer.nome,
            valor=offer.preco,
            estado=data.resultado,
            simulado_em=now,
            confirmado_em=now if confirmed else None,
            pago_em=academy_date(now) if confirmed else None,
        )
        .on_conflict_do_nothing(index_elements=[Payment.id])
        .returning(Payment)
    )
    if row is None:
        return _replay(db.get_one(Payment, data.solicitacao_id), client_id, data)
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=client_id,
            correlation_id=correlation,
            action="pagamento.simulado",
            resource_type="pagamento",
            resource_id=row.id,
            occurred_at=now,
        ),
    )
    return SimulatedReceipt.model_validate(row), True

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.billing.payments.models import Payment
from app.modules.billing.payments.schemas import (
    CorrectPayment,
    PaymentPage,
    PaymentView,
    RegisterPayment,
    VoidPayment,
)
from app.modules.identity.roles import effective_roles
from app.modules.people.assignment_directory import AssignmentDirectory
from app.modules.people.staff import registered_employee_names
from app.policies.access import Actor, Operation, allows


class PaymentError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _manual_for(client_id: UUID) -> tuple[ColumnElement[bool], ...]:
    return (Payment.cliente_id == client_id, Payment.origem == "MANUAL")


def _payment(db: Session, client_id: UUID, payment_id: UUID) -> Payment:
    row = db.scalar(
        select(Payment).where(Payment.id == payment_id, *_manual_for(client_id))
    )
    if row is None:
        raise PaymentError(404)
    return row


def _views(db: Session, rows: Sequence[Payment]) -> list[PaymentView]:
    names = registered_employee_names(
        db,
        {
            actor
            for row in rows
            for actor in (row.registrado_por_id, row.anulado_por_id)
            if actor is not None
        },
    )
    return [
        PaymentView.model_validate(
            {
                "id": row.id,
                "cliente_id": row.cliente_id,
                "valor": row.valor,
                "pago_em": row.pago_em,
                "metodo": row.metodo,
                "referencia_externa": row.referencia_externa,
                "estado": row.estado,
                "confirmado_em": row.confirmado_em,
                "registrado_por_id": row.registrado_por_id,
                "registrado_por_nome": names.get(row.registrado_por_id)
                if row.registrado_por_id
                else None,
                "substitui_id": row.substitui_id,
                "anulado_em": row.anulado_em,
                "anulado_por_id": row.anulado_por_id,
                "anulado_por_nome": names.get(row.anulado_por_id)
                if row.anulado_por_id
                else None,
                "motivo_anulacao": row.motivo_anulacao,
            }
        )
        for row in rows
    ]


def _lock_people(db: Session, client_id: UUID, actor_id: UUID) -> None:
    directory = AssignmentDirectory(db)
    directory.lock_people(client_id, actor_id)
    if not allows(
        Actor(actor_id, effective_roles(db, actor_id)), Operation.MANAGE_MANUAL_PAYMENTS
    ):
        raise PaymentError(403)
    if client_id not in directory.clients([client_id]):
        raise PaymentError(404)


def _audit(
    db: Session,
    actor_id: UUID,
    correlation: UUID,
    *,
    payment_id: UUID,
    action: str,
    at: datetime,
) -> None:
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            correlation_id=correlation,
            action=action,
            resource_type="pagamento",
            resource_id=payment_id,
            occurred_at=at,
        ),
    )


def _void(row: Payment, data: VoidPayment, actor_id: UUID, at: datetime) -> None:
    row.estado = "ANULADO"
    row.anulado_por_id = actor_id
    row.anulado_em = at
    row.motivo_anulacao = data.motivo


def list_payments(
    db: Session, client_id: UUID, *, page: int, limit: int
) -> PaymentPage:
    client = AssignmentDirectory(db).clients([client_id]).get(client_id)
    if client is None:
        raise PaymentError(404)
    base = select(Payment).where(*_manual_for(client_id))
    rows = db.scalars(
        base.order_by(Payment.confirmado_em.desc(), Payment.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    return PaymentPage(
        cliente_nome=client.nome,
        itens=_views(db, rows),
        pagina=page,
        limite=limit,
        total=total,
    )


def record_payment(
    db: Session,
    client_id: UUID,
    data: RegisterPayment,
    *,
    actor_id: UUID,
    correlation: UUID,
    now: datetime,
    replaced_id: UUID | None = None,
) -> tuple[PaymentView, bool]:
    _lock_people(db, client_id, actor_id)
    if data.pago_em > academy_date(now):
        raise PaymentError(422)
    previous = _payment(db, client_id, replaced_id) if replaced_id is not None else None
    values = {
        "origem": "MANUAL",
        "cliente_id": client_id,
        "registrado_por_id": actor_id,
        "substitui_id": replaced_id,
        "valor": Decimal(data.valor),
        "pago_em": data.pago_em,
        "metodo": data.metodo,
        "referencia_externa": data.referencia_externa,
    }
    existing = db.get(Payment, data.solicitacao_id)
    if existing is not None:
        if any(
            getattr(existing, field) != value for field, value in values.items()
        ) or (
            isinstance(data, CorrectPayment)
            and previous
            and previous.motivo_anulacao != data.motivo
        ):
            raise PaymentError(409)
        return _views(db, [existing])[0], False
    if previous is not None:
        if previous.estado != "CONFIRMADO" or not isinstance(data, CorrectPayment):
            raise PaymentError(409)
        _void(previous, data, actor_id, now)
        db.flush()
    row = db.scalar(
        insert(Payment)
        .values(
            id=data.solicitacao_id, estado="CONFIRMADO", confirmado_em=now, **values
        )
        .on_conflict_do_nothing()
        .returning(Payment)
    )
    if row is None:
        raise PaymentError(409)
    action = "pagamento.corrigido" if previous else "pagamento.registrado"
    _audit(db, actor_id, correlation, payment_id=row.id, action=action, at=now)
    return _views(db, [row])[0], True


def void_payment(
    db: Session,
    client_id: UUID,
    payment_id: UUID,
    data: VoidPayment,
    *,
    actor_id: UUID,
    correlation: UUID,
    now: datetime,
) -> PaymentView:
    _lock_people(db, client_id, actor_id)
    row = _payment(db, client_id, payment_id)
    if row.estado == "ANULADO":
        if row.anulado_por_id != actor_id or row.motivo_anulacao != data.motivo:
            raise PaymentError(409)
        return _views(db, [row])[0]
    _void(row, data, actor_id, now)
    _audit(
        db, actor_id, correlation, payment_id=row.id, action="pagamento.anulado", at=now
    )
    return _views(db, [row])[0]

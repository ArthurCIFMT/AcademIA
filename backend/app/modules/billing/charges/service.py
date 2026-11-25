from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.billing.charges.models import Charge, ChargeRevision
from app.modules.billing.charges.schemas import (
    ChargeFields,
    ChargePage,
    ChargeSituation,
    ChargeSnapshot,
    ChargeState,
    ChargeView,
    CreateCharge,
    OverduePolicy,
    Page,
    RevisionView,
    UpdateCharge,
)
from app.modules.billing.payments.models import CONFIRMED_PAYMENT, Payment
from app.modules.identity.roles import effective_roles
from app.modules.memberships.service import membership_belongs_to_client
from app.modules.people.assignment_directory import AssignmentDirectory, ClientReference
from app.modules.people.staff import registered_employee_names
from app.policies.access import Actor, Operation, allows

ZERO = Decimal("0.00")
_total_paid = (
    select(func.sum(Payment.valor))
    .where(Payment.cobranca_id == Charge.id, *CONFIRMED_PAYMENT)
    .correlate(Charge)
    .scalar_subquery()
)


class ChargeError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def charge_situation(
    state: ChargeState,
    due: date,
    *,
    saldo: Decimal,
    today: date,
) -> ChargeSituation:
    if state == "CANCELADA":
        return "CANCELADA"
    if not saldo:
        return "QUITADA"
    return "VENCIDA" if due < today else "ABERTA"


def charge_accepts_payment(db: Session, client_id: UUID, charge_id: UUID) -> bool:
    return bool(
        db.scalar(
            select(
                select(Charge.id)
                .where(
                    Charge.id == charge_id,
                    Charge.cliente_id == client_id,
                    Charge.estado == "ABERTA",
                )
                .exists()
            )
        )
    )


def _view(row: Charge, paid: Decimal | None, today: date) -> ChargeView:
    snapshot = ChargeSnapshot.model_validate(row)
    amount_paid = paid if paid is not None else ZERO
    saldo = (
        max(snapshot.valor - amount_paid, ZERO) if snapshot.estado == "ABERTA" else ZERO
    )
    return ChargeView(
        **snapshot.model_dump(),
        id=row.id,
        revisao=row.revisao,
        valor_pago=amount_paid,
        saldo=saldo,
        situacao=charge_situation(
            snapshot.estado, snapshot.vencimento, saldo=saldo, today=today
        ),
    )


def _client(db: Session, client_id: UUID) -> ClientReference:
    client = AssignmentDirectory(db).clients([client_id]).get(client_id)
    if client is None:
        raise ChargeError(404)
    return client


def list_charges(
    db: Session,
    client_id: UUID,
    *,
    page: int,
    limit: int,
    now: datetime,
    policy: OverduePolicy,
) -> ChargePage:
    client = _client(db, client_id)
    base = select(Charge, _total_paid).where(Charge.cliente_id == client_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Charge)
            .where(Charge.cliente_id == client_id)
        )
        or 0
    )
    rows = db.execute(
        base.order_by(Charge.competencia.desc(), Charge.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    today = academy_date(now)
    return ChargePage(
        cliente_nome=client.nome,
        politica_inadimplencia=policy,
        pagina=page,
        limite=limit,
        total=total,
        itens=[_view(row, paid, today) for row, paid in rows],
    )


def _by_id(db: Session, client_id: UUID, charge_id: UUID) -> Charge:
    row = db.scalar(
        select(Charge).where(Charge.id == charge_id, Charge.cliente_id == client_id)
    )
    if row is None:
        raise ChargeError(404)
    return row


def charge_detail(
    db: Session, client_id: UUID, charge_id: UUID, *, now: datetime
) -> ChargeView:
    row = _by_id(db, client_id, charge_id)
    paid = db.scalar(select(_total_paid).select_from(Charge).where(Charge.id == row.id))
    return _view(row, paid, academy_date(now))


def history(
    db: Session, client_id: UUID, charge_id: UUID, *, page: int, limit: int
) -> Page[RevisionView]:
    row = _by_id(db, client_id, charge_id)
    revisions = db.scalars(
        select(ChargeRevision)
        .where(ChargeRevision.cobranca_id == row.id)
        .order_by(ChargeRevision.revisao.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    names = registered_employee_names(db, {revision.autor_id for revision in revisions})
    return Page[RevisionView](
        itens=[
            RevisionView(
                revisao=item.revisao,
                autor_nome=names.get(item.autor_id),
                registrado_em=item.registrado_em,
                dados=ChargeSnapshot.model_validate(item.dados),
            )
            for item in revisions
        ],
        total=row.revisao,
        pagina=page,
        limite=limit,
    )


def _prepare(
    db: Session, actor_id: UUID, client_id: UUID, fields: ChargeFields
) -> None:
    AssignmentDirectory(db).lock_people(client_id, actor_id)
    actor = Actor(actor_id, effective_roles(db, actor_id))
    if not allows(actor, Operation.MANAGE_CHARGES):
        raise ChargeError(403)
    _client(db, client_id)
    if fields.matricula_id is not None and not membership_belongs_to_client(
        db, fields.matricula_id, client_id
    ):
        raise ChargeError(422)


def _record_revision(
    db: Session,
    row: Charge,
    actor_id: UUID,
    correlation: UUID,
    *,
    now: datetime,
    action: str,
) -> None:
    db.add(
        ChargeRevision(
            id=uuid4(),
            cobranca_id=row.id,
            revisao=row.revisao,
            autor_id=actor_id,
            registrado_em=now,
            dados=ChargeSnapshot.model_validate(row).model_dump(mode="json"),
        )
    )
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            correlation_id=correlation,
            action=action,
            resource_type="cobranca",
            resource_id=row.id,
            occurred_at=now,
        ),
    )


def create_charge(
    db: Session,
    client_id: UUID,
    data: CreateCharge,
    *,
    actor_id: UUID,
    correlation: UUID,
    now: datetime,
) -> tuple[ChargeView, bool]:
    _prepare(db, actor_id, client_id, data)
    snapshot = ChargeSnapshot(
        competencia=data.competencia,
        valor=Decimal(data.valor),
        vencimento=data.vencimento,
        matricula_id=data.matricula_id,
        estado="ABERTA",
    )
    row = db.scalar(
        insert(Charge)
        .values(
            id=data.solicitacao_id,
            cliente_id=client_id,
            revisao=1,
            **snapshot.model_dump(),
        )
        .on_conflict_do_nothing(index_elements=[Charge.id])
        .returning(Charge)
    )
    if row is None:
        existing = db.get(Charge, data.solicitacao_id)
        original = db.scalar(
            select(ChargeRevision).where(
                ChargeRevision.cobranca_id == data.solicitacao_id,
                ChargeRevision.revisao == 1,
            )
        )
        if (
            existing is None
            or existing.cliente_id != client_id
            or original is None
            or original.autor_id != actor_id
            or ChargeSnapshot.model_validate(original.dados) != snapshot
        ):
            raise ChargeError(409)
        return charge_detail(db, client_id, existing.id, now=now), False
    _record_revision(db, row, actor_id, correlation, now=now, action="cobranca.criada")
    return _view(row, None, academy_date(now)), True


def update_charge(
    db: Session,
    client_id: UUID,
    charge_id: UUID,
    data: UpdateCharge,
    *,
    actor_id: UUID,
    correlation: UUID,
    now: datetime,
) -> ChargeView:
    _prepare(db, actor_id, client_id, data)
    row = _by_id(db, client_id, charge_id)
    if row.revisao != data.revisao:
        raise ChargeError(409)
    snapshot = ChargeSnapshot(
        competencia=data.competencia,
        valor=Decimal(data.valor),
        vencimento=data.vencimento,
        matricula_id=data.matricula_id,
        estado=data.estado,
    )
    if snapshot != ChargeSnapshot.model_validate(row):
        for field, value in snapshot.model_dump().items():
            setattr(row, field, value)
        row.revisao += 1
        _record_revision(
            db, row, actor_id, correlation, now=now, action="cobranca.atualizada"
        )
    return charge_detail(db, client_id, charge_id, now=now)

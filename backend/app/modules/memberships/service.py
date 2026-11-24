from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.memberships.models import Membership, Plan
from app.modules.memberships.schemas import (
    AccessLimits,
    CreateMembership,
    CreatePlan,
    MembershipPage,
    MembershipSituation,
    MembershipView,
    PlanFields,
    PlanView,
    UpdatePlan,
)
from app.modules.people.membership_directory import MembershipDirectory


class MembershipError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


@dataclass(frozen=True)
class ValidMembership:
    id: UUID
    modalidade: str
    limites: AccessLimits


def membership_situation(
    *, start: date, end: date, closed: bool, on: date
) -> MembershipSituation:
    if closed:
        return "ENCERRADA"
    if on < start:
        return "FUTURA"
    if on > end:
        return "VENCIDA"
    return "VIGENTE"


def membership_belongs_to_client(
    db: Session, membership_id: UUID, client_id: UUID
) -> bool:
    return bool(
        db.scalar(
            select(
                select(Membership.id)
                .where(
                    Membership.id == membership_id,
                    Membership.cliente_id == client_id,
                )
                .exists()
            )
        )
    )


def has_registered_membership(db: Session, client_id: UUID) -> bool:
    """Consulta o vínculo cadastrado, independentemente da vigência de entrada."""
    return bool(
        db.scalar(
            select(
                select(Membership.id).where(Membership.cliente_id == client_id).exists()
            )
        )
    )


def _valid_period(day: date) -> tuple[ColumnElement[bool], ...]:
    return (
        Membership.estado == "ATIVA",
        Membership.inicio <= day,
        Membership.fim >= day,
    )


def enrolled_client_count(db: Session, *, at: datetime) -> int:
    """Clientes distintos com matrícula vigente no dia civil da academia."""
    return (
        db.scalar(
            select(func.count(Membership.cliente_id.distinct())).where(
                *_valid_period(academy_date(at))
            )
        )
        or 0
    )


def valid_membership(
    db: Session, client_id: UUID, *, at: datetime
) -> ValidMembership | None:
    """Porta de validade do MOD-08 para o acesso; não autoriza a passagem."""
    row = db.scalars(
        select(Membership).where(
            Membership.cliente_id == client_id,
            *_valid_period(academy_date(at)),
        )
    ).one_or_none()
    if row is None:
        return None
    return ValidMembership(
        row.id,
        row.modalidade_contratada,
        AccessLimits.model_validate(row.limites_snapshot),
    )


def _plan_values(data: PlanFields) -> dict[str, str | int | bool | None]:
    return {
        "nome": data.nome,
        "modalidade": data.modalidade,
        "duracao_dias": data.duracao_dias,
        "limite_acessos": data.limite_acessos,
        "janela_limite": "DIA_CIVIL" if data.limite_acessos is not None else None,
        "ativo": data.ativo,
    }


def _page[T](
    db: Session, query: Select[T], page: int, limit: int
) -> tuple[list[T], int]:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    items = db.scalars(query.offset((page - 1) * limit).limit(limit))
    return list(items), total or 0


def list_plans(
    db: Session, *, active_only: bool, page: int, limit: int
) -> MembershipPage[PlanView]:
    query = select(Plan).order_by(Plan.nome, Plan.id)
    if active_only:
        query = query.where(Plan.ativo.is_(True))
    items, total = _page(db, query, page, limit)
    return MembershipPage(
        itens=[PlanView.model_validate(item) for item in items],
        pagina=page,
        limite=limit,
        total=total,
    )


def _audit(
    db: Session,
    actor_id: UUID,
    resource_id: UUID,
    correlation: UUID,
    resource_type: str,
    action: str,
) -> None:
    record_audit(
        db,
        AuditEvent(
            id=uuid4(),
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation,
            occurred_at=datetime.now(UTC),
        ),
    )


def create_plan(
    db: Session, data: CreatePlan, *, actor_id: UUID, correlation: UUID
) -> PlanView:
    values = _plan_values(data)
    row = db.scalar(
        insert(Plan)
        .values(id=data.solicitacao_id, revision=1, **values)
        .on_conflict_do_nothing(index_elements=[Plan.id])
        .returning(Plan)
    )
    if row is None:
        existing = db.get_one(Plan, data.solicitacao_id)
        if any(getattr(existing, key) != value for key, value in values.items()):
            raise MembershipError(409)
        return PlanView.model_validate(existing)
    _audit(db, actor_id, row.id, correlation, "plano", "plano.criado")
    return PlanView.model_validate(row)


def update_plan(
    db: Session, plan_id: UUID, data: UpdatePlan, *, actor_id: UUID, correlation: UUID
) -> PlanView:
    row = db.get(Plan, plan_id, with_for_update=True)
    if row is None:
        raise MembershipError(404)
    if row.revision != data.revisao:
        raise MembershipError(409)
    values = _plan_values(data)
    if any(getattr(row, key) != value for key, value in values.items()):
        for key, value in values.items():
            setattr(row, key, value)
        row.revision += 1
        _audit(db, actor_id, row.id, correlation, "plano", "plano.atualizado")
    return PlanView.model_validate(row)


def _membership_view(row: Membership, today: date) -> MembershipView:
    return MembershipView(
        id=row.id,
        cliente_id=row.cliente_id,
        plano_id=row.plano_id,
        atendente_id=row.atendente_id,
        inicio=row.inicio,
        fim=row.fim,
        estado=row.estado,
        situacao=membership_situation(
            start=row.inicio, end=row.fim, closed=row.estado == "ENCERRADA", on=today
        ),
        modalidade_contratada=row.modalidade_contratada,
        limites_snapshot=AccessLimits.model_validate(row.limites_snapshot),
    )


def list_memberships(
    db: Session, client_id: UUID, *, now: datetime, page: int, limit: int
) -> MembershipPage[MembershipView]:
    if not MembershipDirectory(db).client_exists(client_id):
        raise MembershipError(404)
    query = (
        select(Membership)
        .where(Membership.cliente_id == client_id)
        .order_by(Membership.inicio.desc(), Membership.id)
    )
    items, total = _page(db, query, page, limit)
    today = academy_date(now)
    return MembershipPage(
        itens=[_membership_view(item, today) for item in items],
        pagina=page,
        limite=limit,
        total=total,
    )


def enroll(
    db: Session,
    client_id: UUID,
    data: CreateMembership,
    *,
    attendant_id: UUID,
    correlation: UUID,
    now: datetime,
) -> MembershipView:
    directory = MembershipDirectory(db)
    directory.lock_people(client_id, attendant_id)
    if not directory.attendant_is_active(attendant_id):
        raise MembershipError(403)
    if not directory.client_exists(client_id):
        raise MembershipError(404)

    today = academy_date(now)
    existing = db.get(Membership, data.solicitacao_id)
    if existing is not None:
        if (
            existing.cliente_id != client_id
            or existing.atendente_id != attendant_id
            or existing.plano_id != data.plano_id
            or existing.inicio != data.inicio
        ):
            raise MembershipError(409)
        return _membership_view(existing, today)

    if not directory.client_is_eligible(client_id):
        raise MembershipError(409)
    plan = db.get(Plan, data.plano_id, with_for_update={"read": True})
    if plan is None:
        raise MembershipError(404)
    if not plan.ativo:
        raise MembershipError(409)
    if plan.revision != data.plano_revisao:
        raise MembershipError(409)

    latest_end = db.scalar(
        select(func.max(Membership.fim)).where(Membership.cliente_id == client_id)
    )
    if latest_end is not None and data.inicio <= latest_end:
        raise MembershipError(409)
    try:
        end = data.inicio + timedelta(days=plan.duracao_dias - 1)
    except OverflowError:
        raise MembershipError(422) from None

    row = db.scalar(
        insert(Membership)
        .values(
            id=data.solicitacao_id,
            cliente_id=client_id,
            plano_id=plan.id,
            atendente_id=attendant_id,
            inicio=data.inicio,
            fim=end,
            estado="ATIVA",
            modalidade_contratada=plan.modalidade,
            limites_snapshot={
                "limite_acessos": plan.limite_acessos,
                "janela_limite": plan.janela_limite,
            },
        )
        .on_conflict_do_nothing(index_elements=[Membership.id])
        .returning(Membership)
    )
    if row is None:
        raise MembershipError(409)
    action = "matricula.criada" if latest_end is None else "matricula.renovada"
    _audit(db, attendant_id, row.id, correlation, "matricula", action)
    return _membership_view(row, today)

import logging
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.identity.accounts import EmailAlreadyExists, validate_email
from app.modules.identity.first_access import (
    FIRST_ACCESS,
    ProvisionedAccount,
    invalidate_first_access,
    issue_first_access,
    provision_account,
)
from app.modules.identity.http import EmailInput
from app.modules.identity.models import AccessToken, AccountState, Role, User, UserRole
from app.modules.identity.roles import (
    active_admin_ids,
    effective_roles,
    lock_admin_changes,
)
from app.modules.identity.service import utc_now
from app.modules.notifications.email import (
    EmailRequest,
    email_delivery_state,
    local_email_delivery,
)
from app.modules.notifications.models import DeliveryState, EmailKind
from app.modules.notifications.service import notify_critical_change
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor

StaffRole = Literal[Role.ADMINISTRADOR, Role.ATENDENTE, Role.INSTRUTOR]
STAFF_ROLES = (Role.ADMINISTRADOR, Role.ATENDENTE, Role.INSTRUTOR)
logger = logging.getLogger(__name__)


class StaffError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class StaffFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    cargo: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    data_admissao: date
    papeis: Annotated[set[StaffRole], Field(min_length=1)]


class CreateStaff(StaffFields):
    email: EmailInput
    vincular_existente: StrictBool = False


class StaffRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revisao: Annotated[int, Field(strict=True, ge=1)]


class UpdateStaff(StaffFields, StaffRevision):
    ativo: StrictBool


class StaffSummary(BaseModel):
    id: UUID
    email: str
    nome: str
    cargo: str
    data_admissao: date
    papeis: list[Role]
    ativo: bool
    estado_conta: AccountState
    revisao: int


class StaffPage(BaseModel):
    itens: list[StaffSummary]
    pagina: int
    limite: int
    total: int


class StaffInvite(BaseModel):
    estado: DeliveryState | Literal["SEM_CONFIRMACAO"]
    expira_em: UtcTimestamp


class StaffDetail(StaffSummary):
    convite: StaffInvite | None


def _roles(session: Session, user_ids: list[UUID]) -> dict[UUID, set[Role]]:
    by_user: dict[UUID, set[Role]] = {}
    rows = session.execute(
        select(UserRole.usuario_id, UserRole.papel).where(
            UserRole.usuario_id.in_(user_ids), UserRole.papel.in_(STAFF_ROLES)
        )
    )
    for user_id, role in rows:
        by_user.setdefault(user_id, set()).add(Role(role))
    return by_user


def _summary(profile: EmployeeProfile, user: User, roles: set[Role]) -> StaffSummary:
    return StaffSummary(
        id=user.id,
        email=user.email,
        nome=profile.nome,
        cargo=profile.cargo,
        data_admissao=profile.data_admissao,
        papeis=sorted(roles),
        ativo=profile.ativo,
        estado_conta=AccountState(user.estado),
        revisao=user.revision,
    )


def list_staff(session: Session, page: int, limit: int) -> StaffPage:
    total = session.scalar(select(func.count()).select_from(EmployeeProfile)) or 0
    rows = session.execute(
        select(EmployeeProfile, User)
        .join(User, User.id == EmployeeProfile.usuario_id)
        .order_by(EmployeeProfile.nome, EmployeeProfile.usuario_id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    roles = _roles(session, [user.id for _, user in rows])
    return StaffPage(
        itens=[
            _summary(profile, user, roles.get(user.id, set())) for profile, user in rows
        ],
        pagina=page,
        limite=limit,
        total=total,
    )


def _staff_record(
    session: Session, user_id: UUID, *, lock: bool = False
) -> tuple[EmployeeProfile, User]:
    statement = (
        select(EmployeeProfile, User)
        .join(User, User.id == EmployeeProfile.usuario_id)
        .where(User.id == user_id)
    )
    if lock:
        statement = statement.with_for_update(of=(User, EmployeeProfile))
    row = session.execute(statement).one_or_none()
    if row is None:
        raise StaffError(404)
    return row[0], row[1]


def get_staff(session: Session, user_id: UUID) -> StaffDetail:
    profile, user = _staff_record(session, user_id)
    roles = _roles(session, [user_id]).get(user_id, set())
    latest = session.scalar(
        select(AccessToken)
        .where(
            AccessToken.usuario_id == user_id, AccessToken.finalidade == FIRST_ACCESS
        )
        .order_by(AccessToken.expira_em.desc(), AccessToken.id.desc())
        .limit(1)
    )
    invite = None
    if latest is not None:
        state = email_delivery_state(
            session, user_id, latest.id, EmailKind.PRIMEIRO_ACESSO
        )
        invite = StaffInvite(
            estado=state or "SEM_CONFIRMACAO", expira_em=latest.expira_em
        )
    return StaffDetail(**_summary(profile, user, roles).model_dump(), convite=invite)


def _guard_write(session: Session, actor: Actor) -> None:
    lock_admin_changes(session)
    if Role.ADMINISTRADOR not in effective_roles(session, actor.user_id):
        raise StaffError(403)


def _audit(
    session: Session,
    actor: Actor,
    correlation: UUID,
    user_id: UUID,
    action: str,
    *,
    critical: bool = False,
    reason: str | None = None,
) -> None:
    event = AuditEvent(
        id=uuid4(),
        actor_id=actor.user_id,
        action=action,
        resource_type="funcionario",
        resource_id=user_id,
        reason_code=reason,
        correlation_id=correlation,
        occurred_at=utc_now(),
    )
    record_audit(session, event)
    if critical:
        notify_critical_change(session, event.id)


def _role_change(before: set[Role], after: set[StaffRole]) -> str:
    old = "-".join(role.lower() for role in sorted(before)) or "none"
    new = "-".join(role.lower() for role in sorted(after))
    return f"roles.{old}.to.{new}"


def _invite(session: Session, user: User, now: datetime) -> ProvisionedAccount:
    recent = session.scalar(
        select(func.count())
        .select_from(AccessToken)
        .where(
            AccessToken.usuario_id == user.id,
            AccessToken.finalidade == FIRST_ACCESS,
            AccessToken.expira_em > now,
        )
    )
    if recent is not None and recent >= 3:
        raise StaffError(429)
    return issue_first_access(session, user.id, now=now)


def create_staff(
    session: Session, data: CreateStaff, actor: Actor, correlation: UUID
) -> tuple[UUID, str, ProvisionedAccount | None]:
    try:
        email = validate_email(data.email)
    except ValueError:
        raise StaffError(422) from None
    _guard_write(session, actor)
    now = utc_now()
    invite = None
    if data.vincular_existente:
        user = session.scalar(select(User).where(User.email == email).with_for_update())
        if (
            user is None
            or user.estado not in {AccountState.ATIVO, AccountState.CONVIDADO}
            or session.get(ClientProfile, user.id) is None
            or session.get(EmployeeProfile, user.id) is not None
        ):
            raise StaffError(409)
        user_id = user.id
        if user.estado == AccountState.CONVIDADO:
            invite = _invite(session, user, now)
        user.revision += 1
    else:
        try:
            invite = provision_account(session, email, now=now)
        except EmailAlreadyExists:
            raise StaffError(409) from None
        user_id = invite.user_id

    session.add(
        EmployeeProfile(
            usuario_id=user_id,
            nome=data.nome,
            cargo=data.cargo,
            data_admissao=data.data_admissao,
            ativo=True,
        )
    )
    session.add_all(
        UserRole(id=uuid4(), usuario_id=user_id, papel=role) for role in data.papeis
    )
    _audit(
        session,
        actor,
        correlation,
        user_id,
        "staff.created",
        critical=True,
        reason=_role_change(set(), data.papeis),
    )
    return user_id, email, invite


def update_staff(
    session: Session, user_id: UUID, data: UpdateStaff, actor: Actor, correlation: UUID
) -> StaffDetail:
    _guard_write(session, actor)
    profile, user = _staff_record(session, user_id, lock=True)
    if user.revision != data.revisao:
        raise StaffError(409)

    roles = _roles(session, [user_id]).get(user_id, set())
    if (
        profile.ativo
        and user.estado == AccountState.ATIVO
        and Role.ADMINISTRADOR in roles
        and (not data.ativo or Role.ADMINISTRADOR not in data.papeis)
        and active_admin_ids(session) == [user_id]
    ):
        raise StaffError(409)

    critical = roles != data.papeis or profile.ativo != data.ativo
    details_changed = (profile.nome, profile.cargo, profile.data_admissao) != (
        data.nome,
        data.cargo,
        data.data_admissao,
    )
    if critical or details_changed:
        removed = roles - data.papeis
        if removed:
            session.execute(
                delete(UserRole).where(
                    UserRole.usuario_id == user_id, UserRole.papel.in_(removed)
                )
            )
        session.add_all(
            UserRole(id=uuid4(), usuario_id=user_id, papel=role)
            for role in data.papeis - roles
        )
        if profile.ativo and not data.ativo and user.estado == AccountState.CONVIDADO:
            client = session.get(ClientProfile, user_id)
            if client is None or not client.ativo:
                invalidate_first_access(session, user_id, now=utc_now())
        action = "staff.updated"
        if profile.ativo != data.ativo:
            action = "staff.reactivated" if data.ativo else "staff.deactivated"
        profile.nome, profile.cargo = data.nome, data.cargo
        profile.data_admissao, profile.ativo = data.data_admissao, data.ativo
        user.revision += 1
        reason = _role_change(roles, data.papeis) if roles != data.papeis else None
        _audit(
            session,
            actor,
            correlation,
            user_id,
            action,
            critical=critical,
            reason=reason,
        )
    return get_staff(session, user_id)


def resend_staff_invite(
    session: Session, user_id: UUID, revision: int, actor: Actor, correlation: UUID
) -> tuple[str, ProvisionedAccount]:
    _guard_write(session, actor)
    profile, user = _staff_record(session, user_id, lock=True)
    if (
        not profile.ativo
        or user.estado != AccountState.CONVIDADO
        or user.revision != revision
    ):
        raise StaffError(409)
    invite = _invite(session, user, utc_now())
    user.revision += 1
    _audit(session, actor, correlation, user_id, "staff.invitation_reissued")
    return user.email, invite


def send_staff_invite(
    sessions: sessionmaker[Session],
    email: str,
    invite: ProvisionedAccount,
    origin: str,
    correlation: UUID,
) -> None:
    try:
        local_email_delivery(sessions).send(
            EmailRequest(
                event_id=invite.token_id,
                recipient_id=invite.user_id,
                kind=EmailKind.PRIMEIRO_ACESSO,
                address=email,
                body=(
                    "Defina sua senha para o primeiro acesso ao AcademIA.\n\n"
                    f"{origin}/primeiro-acesso#token={invite.token}\n\n"
                    "O link é de uso único e expira em 24 horas."
                ),
            )
        )
    except Exception:
        logger.error(
            "Falha no envio de primeiro acesso. correlation_id=%s", correlation
        )

from datetime import date
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
)
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.identity.accounts import EmailAlreadyExists, validate_email
from app.modules.identity.first_access import (
    ProvisionedAccount,
    invalidate_first_access,
    provision_account,
)
from app.modules.identity.http import EmailInput
from app.modules.identity.models import AccountState, Role, User, UserRole
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.people.invitations import (
    InviteStatus,
    issue_limited_invite,
    latest_invite,
)
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor, Operation, allows


class ClientError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class ClientFields(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    data_nascimento: date
    telefone: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=25)] | None
    ) = None

    @field_validator("data_nascimento")
    @classmethod
    def birth_must_be_today_or_before(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Informe uma data de nascimento válida.")
        return value

    @field_validator("telefone")
    @classmethod
    def empty_phone_is_absent(cls, value: str | None) -> str | None:
        return value or None


class CreateClient(ClientFields):
    email: EmailInput
    vincular_existente: StrictBool = False


class ClientRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revisao: Annotated[int, Field(strict=True, ge=1)]


class UpdateClient(ClientFields, ClientRevision):
    ativo: StrictBool


class ClientSummary(BaseModel):
    id: UUID
    nome: str
    email: str
    ativo: bool
    estado_conta: AccountState
    revisao: int


class ClientDetail(ClientSummary):
    data_nascimento: date
    telefone: str | None
    convite: InviteStatus | None


class ClientPage(BaseModel):
    itens: list[ClientSummary]
    pagina: int
    limite: int
    total: int


def _summary(profile: ClientProfile, user: User) -> ClientSummary:
    return ClientSummary(
        id=user.id,
        nome=profile.nome,
        email=user.email,
        ativo=profile.ativo,
        estado_conta=AccountState(user.estado),
        revisao=user.revision,
    )


def list_clients(session: Session, search: str, page: int, limit: int) -> ClientPage:
    base = select(ClientProfile, User).join(User, User.id == ClientProfile.usuario_id)
    term = search.strip().lower()
    if term:
        base = base.where(
            or_(
                func.lower(ClientProfile.nome).contains(term, autoescape=True),
                User.email.contains(term, autoescape=True),
            )
        )
    total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = session.execute(
        base.order_by(ClientProfile.nome, ClientProfile.usuario_id)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return ClientPage(
        itens=[_summary(profile, user) for profile, user in rows],
        pagina=page,
        limite=limit,
        total=total,
    )


def _client_record(
    session: Session, user_id: UUID, *, lock: bool = False
) -> tuple[ClientProfile, User]:
    statement = (
        select(ClientProfile, User)
        .join(User, User.id == ClientProfile.usuario_id)
        .where(User.id == user_id)
    )
    if lock:
        statement = statement.with_for_update(of=(User, ClientProfile), key_share=True)
    row = session.execute(statement).one_or_none()
    if row is None:
        raise ClientError(404)
    return row[0], row[1]


def get_client(session: Session, user_id: UUID) -> ClientDetail:
    profile, user = _client_record(session, user_id)
    return ClientDetail(
        **_summary(profile, user).model_dump(),
        data_nascimento=profile.data_nascimento,
        telefone=profile.telefone,
        convite=latest_invite(session, user_id),
    )


def _guard_write(session: Session, actor: Actor) -> None:
    current = Actor(actor.user_id, effective_roles(session, actor.user_id))
    if not allows(current, Operation.MANAGE_CLIENTS):
        raise ClientError(403)


def _audit(
    session: Session, actor: Actor, correlation: UUID, user_id: UUID, action: str
) -> None:
    record_audit(
        session,
        AuditEvent(
            id=uuid4(),
            actor_id=actor.user_id,
            action=action,
            resource_type="cliente",
            resource_id=user_id,
            correlation_id=correlation,
            occurred_at=utc_now(),
        ),
    )


def create_client(
    session: Session, data: CreateClient, actor: Actor, correlation: UUID
) -> tuple[UUID, str, ProvisionedAccount | None]:
    try:
        email = validate_email(data.email)
    except ValueError:
        raise ClientError(422) from None
    _guard_write(session, actor)
    now = utc_now()
    invite = None
    if data.vincular_existente:
        user = session.scalar(
            select(User).where(User.email == email).with_for_update(key_share=True)
        )
        if (
            user is None
            or user.estado not in {AccountState.ATIVO, AccountState.CONVIDADO}
            or session.get(EmployeeProfile, user.id) is None
            or session.get(ClientProfile, user.id) is not None
        ):
            raise ClientError(409)
        user_id = user.id
        if user.estado == AccountState.CONVIDADO:
            invite = issue_limited_invite(session, user_id, now)
        user.revision += 1
    else:
        try:
            invite = provision_account(session, email, now=now)
        except EmailAlreadyExists:
            raise ClientError(409) from None
        user_id = invite.user_id

    session.add(
        ClientProfile(
            usuario_id=user_id,
            nome=data.nome,
            data_nascimento=data.data_nascimento,
            telefone=data.telefone,
            ativo=True,
        )
    )
    session.execute(
        insert(UserRole)
        .values(id=uuid4(), usuario_id=user_id, papel=Role.CLIENTE)
        .on_conflict_do_nothing(constraint="uq_usuario_papel")
    )
    _audit(session, actor, correlation, user_id, "client.created")
    return user_id, email, invite


def update_client(
    session: Session, user_id: UUID, data: UpdateClient, actor: Actor, correlation: UUID
) -> ClientDetail:
    _guard_write(session, actor)
    profile, user = _client_record(session, user_id, lock=True)
    if user.revision != data.revisao:
        raise ClientError(409)

    before = (profile.nome, profile.data_nascimento, profile.telefone, profile.ativo)
    after = (data.nome, data.data_nascimento, data.telefone, data.ativo)
    if before != after:
        if profile.ativo and not data.ativo and user.estado == AccountState.CONVIDADO:
            employee = session.get(EmployeeProfile, user_id)
            if employee is None or not employee.ativo:
                invalidate_first_access(session, user_id, now=utc_now())
        action = "client.updated"
        if profile.ativo != data.ativo:
            action = "client.reactivated" if data.ativo else "client.deactivated"
        profile.nome, profile.data_nascimento, profile.telefone, profile.ativo = after
        user.revision += 1
        _audit(session, actor, correlation, user_id, action)
    return get_client(session, user_id)


def resend_client_invite(
    session: Session, user_id: UUID, revision: int, actor: Actor, correlation: UUID
) -> tuple[str, ProvisionedAccount]:
    _guard_write(session, actor)
    profile, user = _client_record(session, user_id, lock=True)
    if (
        not profile.ativo
        or user.estado != AccountState.CONVIDADO
        or user.revision != revision
    ):
        raise ClientError(409)
    invite = issue_limited_invite(session, user_id, utc_now())
    user.revision += 1
    _audit(session, actor, correlation, user_id, "client.invitation_reissued")
    return user.email, invite

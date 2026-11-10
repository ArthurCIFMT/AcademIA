from dataclasses import dataclass, field
from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Literal
from uuid import UUID, uuid5

from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.orm import InstrumentedAttribute, Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.modules.identity.service import TOKEN_PATTERN, digest, utc_now
from app.modules.notifications.email import (
    EmailRequest,
    email_delivery_state,
    local_email_delivery,
)
from app.modules.notifications.models import DeliveryState, EmailKind
from app.modules.onboarding.models import OnboardingInvitation, OnboardingVersion
from app.modules.onboarding.service import DRAFT, OnboardingError, start_initial_draft
from app.modules.people.clients import get_client
from app.modules.people.onboarding_directory import lock_onboarding_client

INVITATION_AGE = timedelta(hours=48)
INVITATION_PAGE = "/onboarding/convite"


class InvitationStatus(BaseModel):
    id: UUID
    estado: DeliveryState | Literal["SEM_CONFIRMACAO"]
    expira_em: UtcTimestamp


@dataclass(frozen=True)
class InvitationMail:
    address: str = field(repr=False)
    token: str = field(repr=False)


def invitation_status(
    session: Session, client_id: UUID, invitation: OnboardingInvitation
) -> InvitationStatus:
    state = email_delivery_state(
        session, client_id, invitation.id, EmailKind.CONVITE_ONBOARDING
    )
    return InvitationStatus(
        id=invitation.id,
        estado=state or "SEM_CONFIRMACAO",
        expira_em=invitation.expira_em,
    )


def find_invitation(
    session: Session, client_id: UUID, invitation_id: UUID | None = None
) -> OnboardingInvitation | None:
    statement = (
        select(OnboardingInvitation)
        .join(OnboardingVersion)
        .where(OnboardingVersion.cliente_id == client_id)
    )
    if invitation_id is not None:
        return session.scalar(statement.where(OnboardingInvitation.id == invitation_id))
    return session.scalar(
        statement.order_by(
            OnboardingInvitation.expira_em.desc(), OnboardingInvitation.id.desc()
        ).limit(1)
    )


def issue_invitation(
    session: Session, client_id: UUID, actor_id: UUID, request_id: UUID
) -> tuple[UUID, InvitationMail | None]:
    if lock_onboarding_client(session, client_id) is None:
        raise OnboardingError(404)
    invitation_id = uuid5(client_id, str(request_id))
    if find_invitation(session, client_id, invitation_id) is not None:
        return invitation_id, None

    draft = start_initial_draft(session, client_id, actor_id)
    now = utc_now()
    recent_count = session.scalar(
        select(func.count())
        .select_from(OnboardingInvitation)
        .where(
            OnboardingInvitation.onboarding_id == draft.id,
            OnboardingInvitation.expira_em > now,
        )
    )
    if recent_count is not None and recent_count >= 3:
        raise OnboardingError(429)
    session.execute(
        update(OnboardingInvitation)
        .where(
            OnboardingInvitation.onboarding_id == draft.id,
            OnboardingInvitation.revogado_em.is_(None),
        )
        .values(revogado_em=now)
    )
    address = get_client(session, client_id).email
    token = token_urlsafe(32)
    session.add(
        OnboardingInvitation(
            id=invitation_id,
            onboarding_id=draft.id,
            token_hash=digest(token),
            expira_em=now + INVITATION_AGE,
        )
    )
    return invitation_id, InvitationMail(address, token)


def send_invitation(
    sessions: sessionmaker[Session],
    client_id: UUID,
    invitation_id: UUID,
    mail: InvitationMail,
    origin: str,
) -> None:
    local_email_delivery(sessions).send(
        EmailRequest(
            event_id=invitation_id,
            recipient_id=client_id,
            kind=EmailKind.CONVITE_ONBOARDING,
            address=mail.address,
            body=(
                "Preencha o formulário inicial do AcademIA.\n\n"
                f"{origin}{INVITATION_PAGE}#token={mail.token}\n\n"
                "O link é de uso único e expira em 48 horas."
            ),
        )
    )


def _lock_grant(
    session: Session,
    token: str,
    column: InstrumentedAttribute[str] | InstrumentedAttribute[str | None],
) -> tuple[OnboardingInvitation, OnboardingVersion]:
    if TOKEN_PATTERN.fullmatch(token) is None:
        raise OnboardingError(401)

    key = column == digest(token)
    client_id = session.scalar(
        select(OnboardingVersion.cliente_id).join(OnboardingInvitation).where(key)
    )
    if client_id is None or lock_onboarding_client(session, client_id) is None:
        raise OnboardingError(401)

    # Releitura após obter o mesmo bloqueio que protege reemissão e conclusão.
    row = session.execute(
        select(OnboardingInvitation, OnboardingVersion)
        .join(OnboardingVersion)
        .where(
            key,
            OnboardingVersion.cliente_id == client_id,
            OnboardingVersion.estado == DRAFT,
            OnboardingVersion.numero == 1,
            OnboardingInvitation.revogado_em.is_(None),
            OnboardingInvitation.expira_em > utc_now(),
        )
    ).one_or_none()
    if row is None:
        raise OnboardingError(401)
    return row[0], row[1]


def exchange_invitation(session: Session, token: str) -> tuple[str, datetime]:
    invitation, _ = _lock_grant(session, token, OnboardingInvitation.token_hash)
    now = utc_now()
    if invitation.consumido_em is not None or invitation.expira_em <= now:
        raise OnboardingError(401)
    secret = token_urlsafe(32)
    invitation.consumido_em = now
    invitation.sessao_restrita_hash = digest(secret)
    invitation.sessao_expira_em = invitation.expira_em
    return secret, invitation.expira_em


def require_restricted_draft(
    session: Session, secret: str
) -> tuple[OnboardingInvitation, OnboardingVersion]:
    invitation, draft = _lock_grant(
        session, secret, OnboardingInvitation.sessao_restrita_hash
    )
    if invitation.sessao_expira_em is None or invitation.sessao_expira_em <= utc_now():
        raise OnboardingError(401)
    return invitation, draft

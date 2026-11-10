import logging
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.modules.identity.first_access import (
    FIRST_ACCESS,
    ProvisionedAccount,
    issue_first_access,
)
from app.modules.identity.models import AccessToken
from app.modules.notifications.email import (
    EmailRequest,
    email_delivery_state,
    local_email_delivery,
)
from app.modules.notifications.models import DeliveryState, EmailKind

logger = logging.getLogger(__name__)


class InviteLimitReached(Exception):
    pass


class InviteStatus(BaseModel):
    estado: DeliveryState | Literal["SEM_CONFIRMACAO"]
    expira_em: UtcTimestamp


def latest_invite(session: Session, user_id: UUID) -> InviteStatus | None:
    latest = session.scalar(
        select(AccessToken)
        .where(
            AccessToken.usuario_id == user_id, AccessToken.finalidade == FIRST_ACCESS
        )
        .order_by(AccessToken.expira_em.desc(), AccessToken.id.desc())
        .limit(1)
    )
    if latest is None:
        return None
    state = email_delivery_state(session, user_id, latest.id, EmailKind.PRIMEIRO_ACESSO)
    return InviteStatus(estado=state or "SEM_CONFIRMACAO", expira_em=latest.expira_em)


def issue_limited_invite(
    session: Session, user_id: UUID, now: datetime
) -> ProvisionedAccount:
    """O chamador mantém o bloqueio da identidade ao reemitir o convite."""
    count = session.scalar(
        select(func.count())
        .select_from(AccessToken)
        .where(
            AccessToken.usuario_id == user_id,
            AccessToken.finalidade == FIRST_ACCESS,
            AccessToken.expira_em > now,
        )
    )
    if count is not None and count >= 3:
        raise InviteLimitReached
    return issue_first_access(session, user_id, now=now)


def send_first_access_invite(
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

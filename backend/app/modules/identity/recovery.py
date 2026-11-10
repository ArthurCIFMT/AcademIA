import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.modules.identity.models import AccessToken, AccountState, User
from app.modules.identity.passwords import Passwords
from app.modules.identity.repository import PostgresIdentity
from app.modules.identity.service import TOKEN_PATTERN, digest, utc_now
from app.modules.notifications.email import EmailRequest, local_email_delivery
from app.modules.notifications.models import DeliveryState, EmailKind

RECOVERY = "RECUPERACAO"
RECOVERY_AGE = timedelta(minutes=30)
logger = logging.getLogger(__name__)


class InvalidRecovery(Exception):
    pass


@dataclass(frozen=True)
class RecoveryLink:
    event_id: UUID
    user_id: UUID
    token: str = field(repr=False)


def issue_recovery(
    session: Session, email: str, *, now: datetime
) -> RecoveryLink | None:
    user_id = session.scalar(
        select(User.id)
        .where(User.email == email, User.estado == AccountState.ATIVO)
        .with_for_update()
    )
    if user_id is None:
        return None

    link = RecoveryLink(uuid4(), user_id, token_urlsafe(32))
    session.add(
        AccessToken(
            id=link.event_id,
            usuario_id=link.user_id,
            hash=digest(link.token),
            finalidade=RECOVERY,
            expira_em=now + RECOVERY_AGE,
        )
    )
    return link


def complete_recovery(
    session: Session, token: str, password: str, passwords: Passwords, *, now: datetime
) -> None:
    if TOKEN_PATTERN.fullmatch(token) is None:
        raise InvalidRecovery

    token_valid = (
        AccessToken.hash == digest(token),
        AccessToken.finalidade == RECOVERY,
        AccessToken.consumido_em.is_(None),
        AccessToken.expira_em > now,
    )
    user = session.scalar(
        select(User)
        .join(AccessToken, AccessToken.usuario_id == User.id)
        .where(User.estado == AccountState.ATIVO, *token_valid)
        .with_for_update(of=User)
    )
    if user is None:
        raise InvalidRecovery

    consumed = session.scalar(
        update(AccessToken)
        .where(AccessToken.usuario_id == user.id, *token_valid)
        .values(consumido_em=now)
        .returning(AccessToken.id)
    )
    if consumed is None:
        raise InvalidRecovery

    session.execute(
        update(AccessToken)
        .where(
            AccessToken.usuario_id == user.id,
            AccessToken.finalidade == RECOVERY,
            AccessToken.consumido_em.is_(None),
        )
        .values(consumido_em=now)
    )
    user.senha_hash = passwords.hash(password)
    user.revision += 1
    PostgresIdentity(session).revoke_all(user.id, now=now)


def send_recovery(
    sessions: sessionmaker[Session], email: str, origin: str, correlation_id: UUID
) -> None:
    """Executa depois da resposta pública e libera a transação antes de SMTP."""
    try:
        with sessions.begin() as session:
            link = issue_recovery(session, email, now=utc_now())
        if link is None:
            return

        url = f"{origin}/redefinir-senha#token={link.token}"
        result = local_email_delivery(sessions).send(
            EmailRequest(
                event_id=link.event_id,
                recipient_id=link.user_id,
                kind=EmailKind.RECUPERACAO,
                address=email,
                body=(
                    "Use o endereço abaixo para redefinir a senha no AcademIA.\n\n"
                    f"{url}\n\n"
                    "O link é de uso único e expira em 30 minutos. "
                    "Se você não fez este pedido, ignore este e-mail."
                ),
            )
        )
        if result.state != DeliveryState.ENVIADO:
            logger.warning(
                "Recuperação sem envio confirmado. correlation_id=%s estado=%s",
                correlation_id,
                result.state.value,
            )
    except Exception:
        logger.error(
            "Falha na entrega de recuperação. correlation_id=%s", correlation_id
        )

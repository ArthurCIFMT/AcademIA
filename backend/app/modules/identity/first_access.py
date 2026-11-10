from dataclasses import dataclass, field
from datetime import datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccessToken, AccountState, User
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import TOKEN_PATTERN, digest

FIRST_ACCESS = "PRIMEIRO_ACESSO"


class InvalidFirstAccess(Exception):
    pass


@dataclass(frozen=True)
class ProvisionedAccount:
    user_id: UUID
    token: str = field(repr=False)
    expires_at: datetime
    token_id: UUID


def invalidate_first_access(session: Session, user_id: UUID, *, now: datetime) -> None:
    session.execute(
        update(AccessToken)
        .where(
            AccessToken.usuario_id == user_id,
            AccessToken.finalidade == FIRST_ACCESS,
            AccessToken.consumido_em.is_(None),
        )
        .values(consumido_em=now)
    )


def issue_first_access(
    session: Session, user_id: UUID, *, now: datetime
) -> ProvisionedAccount:
    invited = session.scalar(
        select(User.id)
        .where(User.id == user_id, User.estado == AccountState.CONVIDADO)
        .with_for_update()
    )
    if invited is None:
        raise InvalidFirstAccess

    invalidate_first_access(session, user_id, now=now)
    raw = token_urlsafe(32)
    token_id = uuid4()
    expires_at = now + timedelta(hours=24)
    session.add(
        AccessToken(
            id=token_id,
            usuario_id=user_id,
            hash=digest(raw),
            finalidade=FIRST_ACCESS,
            expira_em=expires_at,
        )
    )
    return ProvisionedAccount(user_id, raw, expires_at, token_id)


def provision_account(
    session: Session, email: str, *, now: datetime
) -> ProvisionedAccount:
    user_id = create_account(
        session, email, state=AccountState.CONVIDADO, password_hash="", now=now
    )
    return issue_first_access(session, user_id, now=now)


def complete_first_access(
    session: Session, token: str, password: str, passwords: Passwords, *, now: datetime
) -> None:
    if TOKEN_PATTERN.fullmatch(token) is None:
        raise InvalidFirstAccess

    token_valid = (
        AccessToken.hash == digest(token),
        AccessToken.finalidade == FIRST_ACCESS,
        AccessToken.consumido_em.is_(None),
        AccessToken.expira_em > now,
    )
    user = session.scalar(
        select(User)
        .join(AccessToken, AccessToken.usuario_id == User.id)
        .where(User.estado == AccountState.CONVIDADO, *token_valid)
        .with_for_update(of=User)
    )
    if user is None:
        raise InvalidFirstAccess

    used = session.scalar(
        update(AccessToken)
        .where(AccessToken.usuario_id == user.id, *token_valid)
        .values(consumido_em=now)
        .returning(AccessToken.id)
    )
    if used is None:
        raise InvalidFirstAccess
    user.senha_hash = passwords.hash(password)
    user.estado = AccountState.ATIVO
    user.revision += 1

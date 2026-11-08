from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, User


class EmailAlreadyExists(ValueError):
    pass


def canonical_email(value: str) -> str:
    return value.strip().lower()


def validate_email(value: str) -> str:
    email = canonical_email(value)
    local, separator, domain = email.partition("@")
    if (
        not separator
        or not local
        or not domain
        or "@" in domain
        or len(email) > 254
        or any(char.isspace() for char in email)
    ):
        raise ValueError("Informe um e-mail válido.")
    return email


def create_account(
    session: Session,
    email: str,
    *,
    state: AccountState,
    password_hash: str,
    now: datetime,
) -> UUID:
    user_id = uuid4()
    inserted = session.scalar(
        insert(User)
        .values(
            id=user_id,
            email=validate_email(email),
            senha_hash=password_hash,
            estado=state,
            criado_em=now,
            revision=1,
        )
        .on_conflict_do_nothing(index_elements=[User.email])
        .returning(User.id)
    )
    if inserted is None:
        raise EmailAlreadyExists("O e-mail já pertence a uma conta.")
    return user_id

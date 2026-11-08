from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.identity.models import AccountState, StoredSession, User
from app.modules.identity.ports import Credentials, SessionRecord


class PostgresIdentity:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_for_login(self, normalized_email: str) -> Credentials | None:
        account = self.session.scalar(
            select(User).where(User.email == normalized_email)
        )
        if account is None:
            return None
        return Credentials(
            account.id,
            account.senha_hash,
            account.estado == AccountState.ATIVO,
            account.revision,
        )

    def is_active(self, user_id: UUID) -> bool:
        return (
            self.session.scalar(
                select(User.id).where(
                    User.id == user_id, User.estado == AccountState.ATIVO
                )
            )
            is not None
        )

    def create_if_active(self, session: SessionRecord, *, revision: int) -> bool:
        account_id = self.session.scalar(
            select(User.id)
            .where(
                User.id == session.user_id,
                User.estado == AccountState.ATIVO,
                User.revision == revision,
            )
            .with_for_update()
        )
        if account_id is None:
            return False

        self.session.add(
            StoredSession(
                id=session.id,
                usuario_id=account_id,
                token_hash=session.token_hash,
                csrf_hash=session.csrf_hash,
                criado_em=session.created_at,
                ultimo_uso_em=session.last_used_at,
                expira_em=session.expires_at,
            )
        )
        return True

    def find_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        row = self.session.scalar(
            select(StoredSession).where(StoredSession.token_hash == token_hash)
        )
        if row is None:
            return None
        return SessionRecord(
            id=row.id,
            user_id=row.usuario_id,
            token_hash=row.token_hash,
            csrf_hash=row.csrf_hash,
            created_at=row.criado_em,
            last_used_at=row.ultimo_uso_em,
            expires_at=row.expira_em,
            revoked_at=row.revogada_em,
        )

    def touch_if_valid(
        self, session_id: UUID, *, now: datetime, idle_cutoff: datetime
    ) -> bool:
        active_user = (
            select(User.id)
            .where(
                User.id == StoredSession.usuario_id, User.estado == AccountState.ATIVO
            )
            .exists()
        )
        touched = self.session.scalar(
            update(StoredSession)
            .where(
                StoredSession.id == session_id,
                StoredSession.revogada_em.is_(None),
                StoredSession.expira_em > now,
                StoredSession.ultimo_uso_em > idle_cutoff,
                active_user,
            )
            .values(ultimo_uso_em=func.greatest(StoredSession.ultimo_uso_em, now))
            .returning(StoredSession.id)
        )
        return touched is not None

    def revoke(self, session_id: UUID, *, now: datetime) -> None:
        self.session.execute(
            update(StoredSession)
            .where(StoredSession.id == session_id, StoredSession.revogada_em.is_(None))
            .values(revogada_em=now)
        )

    def revoke_all(self, user_id: UUID, *, now: datetime) -> None:
        self.session.execute(
            update(StoredSession)
            .where(
                StoredSession.usuario_id == user_id, StoredSession.revogada_em.is_(None)
            )
            .values(revogada_em=now)
        )

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class Credentials:
    user_id: UUID
    password_hash: str = field(repr=False)
    active: bool
    revision: int


@dataclass(frozen=True)
class SessionRecord:
    id: UUID
    user_id: UUID
    token_hash: str = field(repr=False)
    csrf_hash: str = field(repr=False)
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


class IdentityRepository(Protocol):
    def find_for_login(self, normalized_email: str) -> Credentials | None: ...

    def is_active(self, user_id: UUID) -> bool: ...


class SessionRepository(Protocol):
    def create_if_active(self, session: SessionRecord, *, revision: int) -> bool:
        """Cria após conferir estado e revisão da conta na mesma transação."""
        ...

    def find_by_token_hash(self, token_hash: str) -> SessionRecord | None: ...

    def touch_if_valid(
        self, session_id: UUID, *, now: datetime, idle_cutoff: datetime
    ) -> bool:
        """Atualiza sem reativar sessão vencida, revogada ou de conta inativa."""
        ...

    def revoke(self, session_id: UUID, *, now: datetime) -> None: ...

    def revoke_all(self, user_id: UUID, *, now: datetime) -> None: ...

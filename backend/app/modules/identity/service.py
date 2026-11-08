import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from uuid import UUID, uuid4

from app.modules.identity.accounts import canonical_email
from app.modules.identity.limiter import LoginLimiter
from app.modules.identity.models import Role
from app.modules.identity.passwords import Passwords
from app.modules.identity.ports import (
    IdentityRepository,
    SessionRecord,
    SessionRepository,
)

ABSOLUTE_AGE = timedelta(hours=12)
IDLE_AGE = timedelta(minutes=30)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")


class Unauthenticated(Exception):
    pass


class Forbidden(Exception):
    pass


@dataclass(frozen=True)
class IssuedSession:
    record: SessionRecord
    token: str = field(repr=False)
    csrf: str = field(repr=False)


def utc_now() -> datetime:
    return datetime.now(UTC)


def digest(token: str) -> str:
    return sha256(token.encode("ascii")).hexdigest()


def csrf_matches(session: SessionRecord, csrf: str | None) -> bool:
    return (
        csrf is not None
        and TOKEN_PATTERN.fullmatch(csrf) is not None
        and compare_digest(session.csrf_hash, digest(csrf))
    )


class AuthService:
    def __init__(
        self,
        identities: IdentityRepository,
        sessions: SessionRepository,
        passwords: Passwords,
        limiter: LoginLimiter,
        *,
        clock: Callable[[], datetime] = utc_now,
        role_reader: Callable[[UUID], frozenset[Role]] | None = None,
    ) -> None:
        self.identities = identities
        self.sessions = sessions
        self.passwords = passwords
        self.limiter = limiter
        self.clock = clock
        self.role_reader = role_reader

    def roles_for(self, user_id: UUID) -> frozenset[Role]:
        if self.role_reader is None:
            return frozenset()
        return self.role_reader(user_id)

    def login(self, email: str, password: str, ip: str) -> IssuedSession:
        normalized = canonical_email(email)
        with self.limiter.attempt(normalized, ip, self.clock()):
            account = self.identities.find_for_login(normalized)
            stored_hash = account.password_hash if account is not None else None
            if not self.passwords.verify(password, stored_hash):
                raise Unauthenticated
            if account is None or not account.active:
                raise Unauthenticated

            now = self.clock()
            token, csrf = token_urlsafe(32), token_urlsafe(32)
            record = SessionRecord(
                id=uuid4(),
                user_id=account.user_id,
                token_hash=digest(token),
                csrf_hash=digest(csrf),
                created_at=now,
                last_used_at=now,
                expires_at=now + ABSOLUTE_AGE,
            )
            if not self.sessions.create_if_active(record, revision=account.revision):
                raise Unauthenticated
        return IssuedSession(record, token, csrf)

    def resolve(
        self, token: str | None, *, csrf: str | None = None, require_csrf: bool = False
    ) -> SessionRecord:
        if token is None or TOKEN_PATTERN.fullmatch(token) is None:
            raise Unauthenticated

        now = self.clock()
        idle_cutoff = now - IDLE_AGE
        session = self.sessions.find_by_token_hash(digest(token))
        if (
            session is None
            or session.revoked_at is not None
            or now >= session.expires_at
            or session.last_used_at <= idle_cutoff
            or not self.identities.is_active(session.user_id)
        ):
            raise Unauthenticated
        if require_csrf and not csrf_matches(session, csrf):
            raise Forbidden
        if not self.sessions.touch_if_valid(
            session.id, now=now, idle_cutoff=idle_cutoff
        ):
            raise Unauthenticated
        return session

    def logout(self, session: SessionRecord) -> None:
        self.sessions.revoke(session.id, now=self.clock())

    def revoke_after_password_change(self, user_id: UUID) -> None:
        self.sessions.revoke_all(user_id, now=self.clock())

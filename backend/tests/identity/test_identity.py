import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from app.core.http import error_schemas, install_http_contract
from app.modules.identity.http import SESSION_COOKIE, BrowserAuth
from app.modules.identity.limiter import LoginLimiter, TooManyAttempts
from app.modules.identity.passwords import Passwords
from app.modules.identity.ports import Credentials, SessionRecord
from app.modules.identity.service import AuthService, Forbidden, Unauthenticated
from app.modules.identity.settings import AuthSettings

EMAIL = "cliente@example.test"
PASSWORD = "senha-sintetica-2026"
ORIGIN = "https://academia.example.test"
AUTH_PATH = "/api/v1/auth"


class MemoryStore:
    def __init__(self, account: Credentials) -> None:
        self.account = account
        self.records: dict[UUID, SessionRecord] = {}
        self.unavailable = False
        self.reject_creation = False

    def find_for_login(self, normalized_email: str) -> Credentials | None:
        return self.account if normalized_email == EMAIL else None

    def is_active(self, user_id: UUID) -> bool:
        return self.account.user_id == user_id and self.account.active

    def create_if_active(self, session: SessionRecord, *, revision: int) -> bool:
        if self.reject_creation or not self.is_active(session.user_id):
            return False
        if self.account.revision != revision:
            return False
        self.records[session.id] = session
        return True

    def find_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        if self.unavailable:
            raise RuntimeError("falha interna sintética")
        return next(
            (item for item in self.records.values() if item.token_hash == token_hash),
            None,
        )

    def touch_if_valid(
        self, session_id: UUID, *, now: datetime, idle_cutoff: datetime
    ) -> bool:
        session = self.records[session_id]
        if (
            not self.is_active(session.user_id)
            or session.revoked_at is not None
            or session.expires_at <= now
            or session.last_used_at <= idle_cutoff
        ):
            return False
        self.records[session_id] = replace(
            session, last_used_at=max(now, session.last_used_at)
        )
        return True

    def revoke(self, session_id: UUID, *, now: datetime) -> None:
        session = self.records[session_id]
        self.records[session_id] = replace(
            session, revoked_at=session.revoked_at or now
        )

    def revoke_all(self, user_id: UUID, *, now: datetime) -> None:
        for session_id, session in self.records.items():
            if session.user_id == user_id:
                self.revoke(session_id, now=now)


@dataclass
class Clock:
    now: datetime

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture(scope="module")
def passwords() -> Passwords:
    return Passwords()


@pytest.fixture(scope="module")
def password_hash(passwords: Passwords) -> str:
    return passwords.hash(PASSWORD)


@pytest.fixture
def fixture_auth(
    passwords: Passwords, password_hash: str
) -> tuple[AuthService, MemoryStore, Clock]:
    store = MemoryStore(Credentials(uuid4(), password_hash, True, 1))
    clock = Clock(datetime(2026, 11, 7, tzinfo=UTC))
    limiter = LoginLimiter(max_failures=5, window=timedelta(minutes=15))
    return AuthService(store, store, passwords, limiter, clock=clock), store, clock


def test_argon2id_and_only_hashes_are_stored(
    fixture_auth: tuple[AuthService, MemoryStore, Clock], password_hash: str
) -> None:
    service, store, _ = fixture_auth
    issued = service.login("  CLIENTE@EXAMPLE.TEST ", PASSWORD, "127.0.0.1")
    assert password_hash.startswith("$argon2id$")
    assert len(issued.token) == len(issued.csrf) == 43
    assert issued.token != issued.csrf
    stored = store.records[issued.record.id]
    assert stored.token_hash != issued.token and len(stored.token_hash) == 64
    assert stored.csrf_hash != issued.csrf and len(stored.csrf_hash) == 64
    assert service.resolve(issued.token).user_id == store.account.user_id


@pytest.mark.parametrize("scenario", ["wrong_password", "unknown", "inactive", "race"])
def test_invalid_credentials_create_no_session(
    fixture_auth: tuple[AuthService, MemoryStore, Clock], scenario: str
) -> None:
    service, store, _ = fixture_auth
    if scenario == "inactive":
        store.account = replace(store.account, active=False)
    if scenario == "race":
        store.reject_creation = True
    email = "unknown@example.test" if scenario == "unknown" else EMAIL
    password = "outra-senha-sintetica" if scenario == "wrong_password" else PASSWORD
    with pytest.raises(Unauthenticated):
        service.login(email, password, "127.0.0.1")
    assert not store.records


@pytest.mark.parametrize(
    "case", ["idle", "absolute", "revoked", "inactive", "tampered"]
)
def test_expired_revoked_or_forged_sessions_are_denied(
    fixture_auth: tuple[AuthService, MemoryStore, Clock], case: str
) -> None:
    service, store, clock = fixture_auth
    issued = service.login(EMAIL, PASSWORD, "127.0.0.1")
    token = issued.token
    if case == "idle":
        clock.now += timedelta(minutes=30)
    elif case == "absolute":
        clock.now = issued.record.expires_at
        store.records[issued.record.id] = replace(
            issued.record, last_used_at=clock.now - timedelta(minutes=1)
        )
    elif case == "revoked":
        service.revoke_after_password_change(store.account.user_id)
    elif case == "inactive":
        store.account = replace(store.account, active=False)
    else:
        token = ("A" if token[0] != "A" else "B") + token[1:]
    with pytest.raises(Unauthenticated):
        service.resolve(token)


def test_csrf_failure_does_not_extend_idle_window(
    fixture_auth: tuple[AuthService, MemoryStore, Clock],
) -> None:
    service, store, clock = fixture_auth
    issued = service.login(EMAIL, PASSWORD, "127.0.0.1")
    clock.now += timedelta(minutes=15)
    with pytest.raises(Forbidden):
        service.resolve(issued.token, csrf="A" * 43, require_csrf=True)
    assert store.records[issued.record.id].last_used_at == issued.record.created_at
    assert service.resolve(issued.token, csrf=issued.csrf, require_csrf=True)
    assert store.records[issued.record.id].last_used_at == clock.now


def test_limiter_reserves_concurrent_attempts_and_expires_failures() -> None:
    limiter = LoginLimiter(max_failures=1, window=timedelta(minutes=15))
    now = datetime(2026, 11, 7, tzinfo=UTC)
    with pytest.raises(Unauthenticated), limiter.attempt(EMAIL, "127.0.0.1", now):
        with pytest.raises(TooManyAttempts), limiter.attempt(EMAIL, "127.0.0.1", now):
            pytest.fail("A tentativa já reservada deve contar para o limite.")
        raise Unauthenticated
    with pytest.raises(TooManyAttempts), limiter.attempt(EMAIL, "127.0.0.1", now):
        pytest.fail("A falha deve permanecer na janela.")
    with limiter.attempt(EMAIL, "127.0.0.1", now + timedelta(minutes=15)):
        pass
    with limiter.attempt(EMAIL, "127.0.0.1", now + timedelta(minutes=15)):
        pass


@pytest.mark.integration
def test_http_login_session_logout_and_repository_failure(
    fixture_auth: tuple[AuthService, MemoryStore, Clock],
) -> None:
    service, store, _ = fixture_auth

    @contextmanager
    def scope() -> Iterator[AuthService]:
        yield service

    app = FastAPI(responses=error_schemas())
    install_http_contract(app)
    app.include_router(BrowserAuth(scope, AuthSettings(origin=ORIGIN)).router())
    credentials = {"email": EMAIL, "senha": PASSWORD}
    origin_headers = {"Origin": ORIGIN}

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=ORIGIN) as client:
            assert (await client.get(f"{AUTH_PATH}/session")).status_code == 401
            assert (await client.post(f"{AUTH_PATH}/logout")).status_code == 401
            rejected = await client.post(f"{AUTH_PATH}/login", json=credentials)
            assert rejected.status_code == 403
            response = await client.post(
                f"{AUTH_PATH}/login", json=credentials, headers=origin_headers
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert response.headers["cache-control"] == "no-store"
            cookies = response.headers.get_list("set-cookie")
            assert len(cookies) == 2
            assert all("HttpOnly" in item and "Secure" in item for item in cookies)
            data = response.json()
            document = (await client.get("/openapi.json")).json()
            login = document["paths"][f"{AUTH_PATH}/login"]["post"]
            schemas = document["components"]["schemas"]
            request_ref = login["requestBody"]["content"]["application/json"]["schema"][
                "$ref"
            ]
            response_ref = login["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["$ref"]
            assert set(credentials) == set(
                schemas[request_ref.rsplit("/", 1)[1]]["required"]
            )
            assert set(data) == set(schemas[response_ref.rsplit("/", 1)[1]]["required"])
            assert data["user_id"] == str(store.account.user_id)
            token = response.cookies[SESSION_COOKIE]
            assert token not in response.text and PASSWORD not in response.text

            session = await client.get(f"{AUTH_PATH}/session")
            assert session.json() == data
            store.unavailable = True
            failure = await client.get(f"{AUTH_PATH}/session")
            assert failure.status_code == 500
            assert "falha interna sintética" not in failure.text
            store.unavailable = False

            no_csrf = await client.post(f"{AUTH_PATH}/logout", headers=origin_headers)
            assert no_csrf.status_code == 403
            valid_headers = {**origin_headers, "X-CSRF-Token": data["csrf_token"]}
            bad_origin = await client.post(
                f"{AUTH_PATH}/logout",
                headers={**valid_headers, "Origin": "https://bad.test"},
            )
            assert bad_origin.status_code == 403
            assert (
                await client.post(f"{AUTH_PATH}/logout", headers=valid_headers)
            ).status_code == 204
            replay = await client.get(
                f"{AUTH_PATH}/session", headers={"Cookie": f"{SESSION_COOKIE}={token}"}
            )
            assert replay.status_code == 401

    asyncio.run(exercise())

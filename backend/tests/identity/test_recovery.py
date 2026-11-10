import asyncio
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from os import environ
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.identity import recovery
from app.modules.identity.accounts import create_account
from app.modules.identity.limiter import RecoveryLimiter
from app.modules.identity.models import AccessToken, AccountState
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import digest, utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.email import EmailDelivery
from app.modules.notifications.models import DeliveryState, Notification

ORIGIN = "https://academia.example.test"
RECOVERY_PATH = "/api/v1/auth/recovery"
AUTH = "/api/v1/auth"
OLD_PASSWORD = "senha-sintetica-antiga"
NEW_PASSWORD = "senha-sintetica-nova"


def test_recovery_limit_is_shared_by_normalized_email_and_by_ip() -> None:
    limiter = RecoveryLimiter()
    now = datetime(2026, 11, 10, tzinfo=UTC)
    email = "cliente@example.test"

    assert all(limiter.allow(email, f"ip-{n}", now) for n in range(3))
    assert not limiter.allow(email, "outro-ip", now)
    assert limiter.allow(email, "outro-ip", now + timedelta(minutes=15))
    for number in range(20):
        assert limiter.allow(f"conta{number}@example.test", "ip-comum", now)
    assert not limiter.allow("nova-conta@example.test", "ip-comum", now)
    assert limiter.allow("nova-conta@example.test", "ip-diferente", now)


@pytest.fixture
def sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                ini = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
                config = Config(str(ini))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "head")
                yield create_session_factory(connection)
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def account(sessions: sessionmaker[Session]) -> tuple[UUID, str]:
    email = f"recovery-{uuid4()}@example.test"
    with sessions.begin() as session:
        user_id = create_account(
            session,
            email,
            password_hash=Passwords().hash(OLD_PASSWORD),
            state=AccountState.ATIVO,
            now=utc_now(),
        )
    return user_id, email


@pytest.fixture
def api(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> httpx.ASGITransport:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    return httpx.ASGITransport(
        app=create_app(
            identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
        )
    )


def test_recovery_routes_are_declared_in_openapi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "202" in paths[RECOVERY_PATH]["post"]["responses"]
    assert "204" in paths[f"{RECOVERY_PATH}/confirm"]["post"]["responses"]


def _mailpit_token(email: str) -> str:
    with httpx.Client(
        base_url="http://127.0.0.1:8025", trust_env=False, timeout=5
    ) as sink:
        result = sink.get("/api/v1/search", params={"query": f"to:{email}"})
        result.raise_for_status()
        messages = result.json()["messages"]
        assert len(messages) == 1
        full = sink.get(f"/api/v1/message/{messages[0]['ID']}")
        full.raise_for_status()
        body = full.json()["Text"]
    match = re.search(
        rf"{re.escape(ORIGIN)}/redefinir-senha#token=([A-Za-z0-9_-]{{43}})",
        body,
    )
    assert match is not None
    return match.group(1)


@pytest.mark.integration
def test_recovery_from_mailpit_revokes_sessions_and_replaces_password(
    sessions: sessionmaker[Session], account: tuple[UUID, str], api: httpx.ASGITransport
) -> None:
    if environ.get("ACADEMIA_TEST_MAILPIT") != "1":
        pytest.skip("Inicie o Mailpit local e configure ACADEMIA_TEST_MAILPIT=1.")

    user_id, email = account

    async def run() -> None:
        headers = {"Origin": ORIGIN}
        async with (
            httpx.AsyncClient(
                transport=api, base_url=ORIGIN, headers=headers
            ) as browser,
            httpx.AsyncClient(transport=api, base_url=ORIGIN, headers=headers) as other,
        ):
            for client in (browser, other):
                login = await client.post(
                    f"{AUTH}/login",
                    json={"email": email, "senha": OLD_PASSWORD},
                )
                assert login.status_code == 200

            accepted = await browser.post(RECOVERY_PATH, json={"email": email.upper()})
            unknown = await browser.post(
                RECOVERY_PATH,
                json={"email": f"unknown-{uuid4()}@example.test"},
            )
            assert accepted.status_code == unknown.status_code == 202
            assert accepted.content == unknown.content == b""
            assert (
                accepted.headers["Cache-Control"]
                == unknown.headers["Cache-Control"]
                == "no-store"
            )

            token = await asyncio.to_thread(_mailpit_token, email)
            with sessions.begin() as session:
                record = session.scalar(
                    select(AccessToken).where(AccessToken.usuario_id == user_id)
                )
                assert record is not None and record.hash == digest(token)
                assert record.expira_em > utc_now()
                extra = recovery.issue_recovery(session, email, now=utc_now())
                assert extra is not None

            payload = {"token": token, "senha": NEW_PASSWORD}
            rejected = await browser.post(
                f"{RECOVERY_PATH}/confirm",
                json=payload,
                headers={"Origin": "https://externo.test"},
            )
            assert rejected.status_code == 403
            reset = await browser.post(f"{RECOVERY_PATH}/confirm", json=payload)
            assert (
                reset.status_code == 204
                and len(reset.headers.get_list("set-cookie")) == 2
            )
            assert (await other.get(f"{AUTH}/session")).status_code == 401
            for revoked in (token, extra.token):
                replay = await browser.post(
                    f"{RECOVERY_PATH}/confirm",
                    json={"token": revoked, "senha": OLD_PASSWORD},
                )
                assert replay.status_code == 401
            assert (
                await browser.post(
                    f"{AUTH}/login", json={"email": email, "senha": OLD_PASSWORD}
                )
            ).status_code == 401
            assert (
                await browser.post(
                    f"{AUTH}/login", json={"email": email, "senha": NEW_PASSWORD}
                )
            ).status_code == 200

    asyncio.run(run())


class RejectEmail:
    def deliver(self, _message: EmailMessage) -> DeliveryState:
        return DeliveryState.FALHOU


@pytest.mark.integration
def test_failed_delivery_is_recorded_without_changing_public_response(
    sessions: sessionmaker[Session],
    account: tuple[UUID, str],
    api: httpx.ASGITransport,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    user_id, email = account
    monkeypatch.setattr(
        recovery,
        "local_email_delivery",
        lambda factory: EmailDelivery(factory, RejectEmail(), "academia@example.test"),
    )

    async def run() -> None:
        async with httpx.AsyncClient(transport=api, base_url=ORIGIN) as browser:
            rejected = await browser.post(RECOVERY_PATH, json={"email": email})
            assert rejected.status_code == 403
            for _ in range(4):
                response = await browser.post(
                    RECOVERY_PATH,
                    json={"email": email},
                    headers={"Origin": ORIGIN},
                )
                assert response.status_code == 202 and response.content == b""

    asyncio.run(run())
    with sessions.begin() as session:
        deliveries = list(
            session.scalars(
                select(Notification).where(Notification.destinatario_id == user_id)
            )
        )
        assert len(deliveries) == 3
        assert all(item.estado == DeliveryState.FALHOU for item in deliveries)
    assert caplog.text.count("estado=FALHOU") == 3
    assert email not in caplog.text and "#token=" not in caplog.text


@pytest.mark.integration
def test_expired_token_and_invited_or_inactive_accounts_are_refused(
    sessions: sessionmaker[Session], account: tuple[UUID, str], api: httpx.ASGITransport
) -> None:
    _, email = account
    passwords = Passwords()
    now = utc_now()
    with sessions.begin() as session:
        expired = recovery.issue_recovery(
            session, email, now=now - timedelta(minutes=31)
        )
        assert expired is not None
        for state in (
            AccountState.CONVIDADO,
            AccountState.INATIVO,
            AccountState.BLOQUEADO,
        ):
            blocked_email = f"{state.lower()}@example.test"
            create_account(
                session, blocked_email, state=state, password_hash="", now=now
            )
            assert recovery.issue_recovery(session, blocked_email, now=now) is None
        with pytest.raises(recovery.InvalidRecovery):
            recovery.complete_recovery(
                session, "a" * 42 + "!", NEW_PASSWORD, passwords, now=now
            )

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=api,
            base_url=ORIGIN,
            headers={"Origin": ORIGIN},
        ) as browser:
            denied = await browser.post(
                f"{RECOVERY_PATH}/confirm",
                json={"token": expired.token, "senha": NEW_PASSWORD},
            )
            assert denied.status_code == 401

    asyncio.run(run())


@pytest.mark.integration
def test_only_one_concurrent_recovery_can_change_the_same_account() -> None:
    engine = create_database_engine("test")
    schema = "iam05_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            passwords = Passwords()
            email = "concorrencia@example.test"
            now = utc_now()
            with factory.begin() as session:
                create_account(
                    session,
                    email,
                    password_hash=passwords.hash(OLD_PASSWORD),
                    state=AccountState.ATIVO,
                    now=now,
                )
                first = recovery.issue_recovery(session, email, now=now)
                second = recovery.issue_recovery(session, email, now=now)
                assert first is not None and second is not None

            barrier = Barrier(2)

            def submit(token: str) -> bool:
                barrier.wait(timeout=5)
                try:
                    with factory.begin() as session:
                        recovery.complete_recovery(
                            session, token, NEW_PASSWORD, passwords, now=utc_now()
                        )
                except recovery.InvalidRecovery:
                    return False
                return True

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(submit, [first.token, second.token])) == [
                    False,
                    True,
                ]
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

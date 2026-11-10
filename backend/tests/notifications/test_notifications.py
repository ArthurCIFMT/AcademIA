import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime
from email.message import EmailMessage
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.email import EmailDelivery, EmailRequest
from app.modules.notifications.models import DeliveryState, EmailKind, Notification
from app.modules.notifications.service import (
    notify_critical_change,
    notify_workout_review,
)
from app.modules.people.profiles import EmployeeProfile

_ORIGIN = "https://academia.example.test"
_ROUTE = "/api/v1/notificacoes/pendentes"
_PASSWORD = "senha-sintetica-ntf01"
_NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection, connection.begin() as transaction:
            check_database(connection, "test")
            config_file = (
                Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
            )
            config = Config(str(config_file))
            config.attributes.update(connection=connection, database_target="test")
            try:
                yield connection, config
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def sessions(migration: tuple[Connection, Config]) -> sessionmaker[Session]:
    connection, config = migration
    command.upgrade(config, "head")
    return create_session_factory(connection)


@pytest.fixture(scope="module")
def password_hash() -> str:
    return Passwords().hash(_PASSWORD)


def _account(
    session: Session, name: str, role: Role, password_hash: str, *, active: bool = True
) -> UUID:
    user_id = create_account(
        session,
        email=f"{name}@example.test",
        password_hash=password_hash,
        state=AccountState.ATIVO,
        now=_NOW,
    )
    session.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
    session.add(
        EmployeeProfile(
            usuario_id=user_id,
            nome=name,
            cargo=role,
            data_admissao=date(2026, 11, 7),
            ativo=active,
        )
    )
    session.flush()
    return user_id


@pytest.mark.database
def test_migration_matches_head_and_reverts_only_notifications(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0003")
    command.upgrade(config, "head")
    command.check(config)
    assert inspect(connection).has_table("notificacao", schema="academia")
    command.downgrade(config, "0003")
    assert not inspect(connection).has_table("notificacao", schema="academia")
    assert inspect(connection).has_table("usuario", schema="academia")


@pytest.mark.integration
def test_only_current_authorized_recipient_reads_minimal_json(
    sessions: sessionmaker[Session], password_hash: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    event_id = uuid4()
    with sessions.begin() as session:
        instructor_id = _account(session, "instrutor", Role.INSTRUTOR, password_hash)
        _account(session, "outro-instrutor", Role.INSTRUTOR, password_hash)
        _account(session, "admin", Role.ADMINISTRADOR, password_hash)
        _account(
            session, "admin-inativo", Role.ADMINISTRADOR, password_hash, active=False
        )
        attendant = _account(session, "atendente", Role.ATENDENTE, password_hash)
        assert not notify_workout_review(session, event_id, None)
        assert not notify_workout_review(session, event_id, attendant)
        assert notify_workout_review(session, event_id, instructor_id)
        assert not notify_workout_review(session, event_id, instructor_id)
        critical = uuid4()
        assert notify_critical_change(session, critical) == 1
        assert notify_critical_change(session, critical) == 0

    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )

    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=_ORIGIN
        ) as client:
            assert (await client.get(_ROUTE)).status_code == 401
            for name, kind, status in [
                ("instrutor", "TREINO_PARA_AVALIAR", 200),
                ("outro-instrutor", None, 200),
                ("admin", "ALTERACAO_CRITICA", 200),
                ("atendente", None, 403),
            ]:
                client.cookies.clear()
                login = await client.post(
                    "/api/v1/auth/login",
                    headers={"Origin": _ORIGIN},
                    json={"email": f"{name}@example.test", "senha": _PASSWORD},
                )
                assert login.status_code == 200
                response = await client.get(_ROUTE)
                assert response.status_code == status
                if status == 200:
                    assert response.headers["Cache-Control"] == "no-store"
                    data = response.json()
                    if kind is None:
                        assert data == []
                    else:
                        assert len(data) == 1
                        assert set(data[0]) == {"id", "tipo", "criada_em"}
                        assert data[0]["tipo"] == kind
                        assert (
                            datetime.fromisoformat(data[0]["criada_em"]).utcoffset()
                            is not None
                        )

    asyncio.run(run())


class RecordingTransport:
    def __init__(self, *states: DeliveryState) -> None:
        self.states = iter(states)
        self.message_ids: list[str] = []

    def deliver(self, message: EmailMessage) -> DeliveryState:
        self.message_ids.append(str(message["Message-ID"]))
        return next(self.states)


@pytest.mark.integration
@pytest.mark.parametrize(
    "final", [DeliveryState.ENVIADO, DeliveryState.FALHOU, DeliveryState.INCERTO]
)
def test_failure_preserves_notice_and_retry_is_bounded_and_idempotent(
    sessions: sessionmaker[Session], password_hash: str, final: DeliveryState
) -> None:
    event_id = uuid4()
    with sessions.begin() as session:
        instructor = _account(session, "instrutor", Role.INSTRUTOR, password_hash)
        assert notify_workout_review(session, event_id, instructor)

    transport = RecordingTransport(DeliveryState.FALHOU, DeliveryState.FALHOU, final)
    delivery = EmailDelivery(sessions, transport, "academia@example.test")
    request = EmailRequest(
        event_id,
        instructor,
        EmailKind.TREINO_PARA_AVALIAR,
        "instrutor@example.test",
        "Corpo sintético que não será salvo no banco.",
    )
    first = delivery.send(request)
    assert first.state == DeliveryState.FALHOU
    assert delivery.send(request) == first
    second = delivery.send(request, retry_after=first.attempts)
    assert second.attempts == 2
    assert delivery.send(request, retry_after=first.attempts) == second
    third = delivery.send(request, retry_after=second.attempts)
    assert third.state == final and third.attempts == 3
    assert delivery.send(request, retry_after=third.attempts) == third
    assert len(transport.message_ids) == 3 and len(set(transport.message_ids)) == 1

    with sessions.begin() as session:
        rows = list(
            session.scalars(
                select(Notification).where(Notification.evento_id == event_id)
            )
        )
        assert {item.canal: item.estado for item in rows} == {
            "INTERNO": "PENDENTE",
            "EMAIL": final,
        }


def test_openapi_declares_notification_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    schema = create_app().openapi()
    assert schema["paths"][_ROUTE]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["items"]["$ref"].endswith("/NoticeResponse")

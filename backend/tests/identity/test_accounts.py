import asyncio
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Table, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.identity.accounts import (
    EmailAlreadyExists,
    create_account,
    validate_email,
)
from app.modules.identity.bootstrap import BootstrapConflict, bootstrap_admin
from app.modules.identity.first_access import (
    complete_first_access,
    issue_first_access,
    provision_account,
)
from app.modules.identity.http import SESSION_COOKIE
from app.modules.identity.models import (
    AccessToken,
    AccountState,
    Role,
    StoredSession,
    User,
    UserRole,
)
from app.modules.identity.passwords import Passwords
from app.modules.identity.roles import effective_roles
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile

ORIGIN = "https://academia.example.test"
PASSWORD = "senha-sintetica-do-ensaio"
HIRE_DATE = date(2026, 11, 7)


def config_for(connection: Connection) -> Config:
    path = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
    config = Config(str(path))
    config.attributes.update(connection=connection, database_target="test")
    return config


@pytest.fixture
def connection() -> Iterator[Connection]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as opened:
            transaction = opened.begin()
            try:
                check_database(opened, "test")
                yield opened
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def sessions(connection: Connection) -> sessionmaker[Session]:
    command.upgrade(config_for(connection), "0003")
    return create_session_factory(connection)


@pytest.fixture(scope="module")
def passwords() -> Passwords:
    return Passwords()


def test_email_preserves_provider_specific_parts() -> None:
    assert validate_email("  Nome.Sobrenome+Academia@Example.TEST ") == (
        "nome.sobrenome+academia@example.test"
    )
    with pytest.raises(ValueError):
        validate_email("nome @example.test")


@pytest.mark.database
def test_migration_preserves_historical_actor_and_enforces_future_fk(
    connection: Connection,
) -> None:
    config = config_for(connection)
    command.upgrade(config, "0002")
    write = text(
        "INSERT INTO academia.auditoria "
        "(id, ator_id, acao, recurso_tipo, correlation_id, ocorrido_em) "
        "VALUES (:id, :actor, 'teste', 'perfil', :correlation, now())"
    )
    old_id = uuid4()
    connection.execute(write, {"id": old_id, "actor": uuid4(), "correlation": uuid4()})
    command.upgrade(config, "0003")
    assert (
        connection.scalar(
            text("SELECT id FROM academia.auditoria WHERE id = :id"), {"id": old_id}
        )
        == old_id
    )
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(
            write, {"id": uuid4(), "actor": uuid4(), "correlation": uuid4()}
        )
    command.downgrade(config, "0002")
    assert not inspect(connection).has_table("usuario", schema="academia")
    assert inspect(connection).has_table("auditoria", schema="academia")


@pytest.mark.integration
def test_same_account_has_independent_roles_and_unique_email(
    sessions: sessionmaker[Session], passwords: Passwords
) -> None:
    now = datetime(2026, 11, 7, 16, tzinfo=UTC)
    with sessions.begin() as session:
        invitation = provision_account(session, " MULTI@EXAMPLE.TEST ", now=now)
        complete_first_access(session, invitation.token, PASSWORD, passwords, now=now)
        user_id = invitation.user_id
        session.add_all(
            [
                ClientProfile(
                    usuario_id=user_id,
                    nome="Pessoa teste",
                    data_nascimento=HIRE_DATE,
                    ativo=True,
                ),
                EmployeeProfile(
                    usuario_id=user_id,
                    nome="Pessoa teste",
                    cargo="Instrutor",
                    data_admissao=HIRE_DATE,
                    ativo=True,
                ),
                UserRole(id=uuid4(), usuario_id=user_id, papel=Role.CLIENTE),
                UserRole(id=uuid4(), usuario_id=user_id, papel=Role.INSTRUTOR),
            ]
        )

    with sessions.begin() as session:
        assert effective_roles(session, user_id) == {Role.CLIENTE, Role.INSTRUTOR}
        profile = session.get(EmployeeProfile, user_id)
        assert profile is not None
        profile.ativo = False
        assert effective_roles(session, user_id) == {Role.CLIENTE}
        account = session.get(User, user_id)
        assert account is not None
        account.estado = AccountState.INATIVO
        assert effective_roles(session, user_id) == set()
        with pytest.raises(EmailAlreadyExists):
            provision_account(session, "Multi@example.test", now=now)

    with sessions.begin() as session:
        assert session.scalar(select(func.count(User.id))) == 1


@pytest.mark.integration
def test_concurrent_normalized_email_has_one_winner() -> None:
    engine = create_database_engine("test")
    scratch = "iam02_" + uuid4().hex
    try:
        with engine.begin() as setup:
            check_database(setup, "test")
            setup.execute(CreateSchema(scratch))
        try:
            isolated = engine.execution_options(
                schema_translate_map={"academia": scratch}
            )
            table = User.__table__
            assert isinstance(table, Table)
            with isolated.begin() as setup:
                table.create(setup)
            sessions = create_session_factory(isolated)
            barrier = Barrier(2, timeout=10)

            def compete(email: str) -> UUID | None:
                try:
                    with sessions.begin() as session:
                        barrier.wait()
                        return create_account(
                            session,
                            email,
                            state=AccountState.CONVIDADO,
                            password_hash="",
                            now=utc_now(),
                        )
                except EmailAlreadyExists:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(compete, " DUP@EXAMPLE.TEST ")
                second = pool.submit(compete, "dup@example.test")
                assert sum(item.result() is not None for item in (first, second)) == 1
            with sessions.begin() as session:
                assert session.scalars(select(User.email)).all() == ["dup@example.test"]
        finally:
            with engine.begin() as cleanup:
                cleanup.execute(DropSchema(scratch, cascade=True))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_bootstrap_authenticates_and_inactivation_denies_old_cookie(
    sessions: sessionmaker[Session],
    passwords: Passwords,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    with sessions.begin() as session:
        user_id = bootstrap_admin(
            session,
            email="admin@example.test",
            name="Admin Teste",
            hired_on=HIRE_DATE,
            password=PASSWORD,
            passwords=passwords,
            now=utc_now(),
        )

    with sessions.begin() as session:
        assert (
            bootstrap_admin(
                session,
                email=" ADMIN@EXAMPLE.TEST ",
                name="Outro nome",
                hired_on=HIRE_DATE,
                password="outra-senha-qualquer",
                passwords=passwords,
                now=utc_now(),
            )
            == user_id
        )
        assert effective_roles(session, user_id) == {Role.ADMINISTRADOR}
        assert session.scalar(select(func.count(User.id))) == 1
        with pytest.raises(BootstrapConflict):
            bootstrap_admin(
                session,
                email="outro@example.test",
                name="Outro admin",
                hired_on=HIRE_DATE,
                password=PASSWORD,
                passwords=passwords,
                now=utc_now(),
            )

    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=ORIGIN) as client:
            login = await client.post(
                "/api/v1/auth/login",
                headers={"Origin": ORIGIN},
                json={"email": "admin@example.test", "senha": PASSWORD},
            )
            assert login.status_code == 200
            assert login.json()["user_id"] == str(user_id)
            assert (await client.get("/api/v1/auth/session")).status_code == 200
            with sessions.begin() as session:
                stored = session.scalar(select(StoredSession))
                assert stored is not None and stored.usuario_id == user_id
                assert len(stored.token_hash) == 64
                assert stored.token_hash != login.cookies[SESSION_COOKIE]
                account = session.get(User, user_id)
                assert account is not None
                account.estado = AccountState.INATIVO
                account.revision += 1
            denied = await client.get("/api/v1/auth/session")
            assert denied.status_code == 401
            assert denied.json()["code"] == "UNAUTHENTICATED"

    asyncio.run(exercise())


@pytest.mark.integration
def test_first_access_expiration_activation_and_one_use(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    with sessions.begin() as session:
        expired = provision_account(
            session, "novo@example.test", now=utc_now() - timedelta(hours=25)
        )

    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=ORIGIN) as client:
            headers = {"Origin": ORIGIN}
            credentials = {"email": "novo@example.test", "senha": PASSWORD}
            login = await client.post(
                "/api/v1/auth/login", headers=headers, json=credentials
            )
            assert login.status_code == 401

            async def activate(token: str) -> httpx.Response:
                return await client.post(
                    "/api/v1/auth/first-access",
                    headers=headers,
                    json={"token": token, "senha": PASSWORD},
                )

            assert (await activate(expired.token)).status_code == 401
            with sessions.begin() as session:
                fresh = issue_first_access(session, expired.user_id, now=utc_now())
                session.flush()
                stored = session.scalar(
                    select(AccessToken).where(AccessToken.consumido_em.is_(None))
                )
                assert stored is not None and len(stored.hash) == 64
                assert fresh.token != stored.hash
            assert (await activate(fresh.token)).status_code == 204
            assert (await activate(fresh.token)).status_code == 401
            login = await client.post(
                "/api/v1/auth/login", headers=headers, json=credentials
            )
            assert login.status_code == 200
            assert login.json()["user_id"] == str(expired.user_id)

    asyncio.run(exercise())

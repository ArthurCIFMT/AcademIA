import asyncio
from collections.abc import Iterator
from contextlib import AsyncExitStack
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import Response
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
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor, Operation, allows
from app.policies.http import AuthenticatedActor, require_permission

ORIGIN = "https://academia.example.test"
PASSWORD = "senha-sintetica-do-ensaio"
BASE = "/api/v1/_policy"


class Assignments:
    def __init__(self) -> None:
        self.active: set[tuple[UUID, UUID]] = set()

    def is_active(self, instructor_id: UUID, client_id: UUID) -> bool:
        return (instructor_id, client_id) in self.active


def test_client_scope_requires_owner_and_blocks_administration() -> None:
    actor = Actor(uuid4(), frozenset({Role.CLIENTE}))
    assert allows(actor, Operation.READ_WORKOUT, client_id=actor.user_id)
    assert not allows(actor, Operation.READ_WORKOUT, client_id=uuid4())
    assert not allows(actor, Operation.READ_WORKOUT)
    assert not allows(actor, Operation.MANAGE_EMPLOYEES)


def test_administration_does_not_confer_health_access() -> None:
    admin = Actor(uuid4(), frozenset({Role.ADMINISTRADOR}))
    attendant = Actor(uuid4(), frozenset({Role.ATENDENTE}))
    assert allows(admin, Operation.MANAGE_EMPLOYEES)
    assert allows(attendant, Operation.MANAGE_CLIENTS)
    assert not allows(attendant, Operation.MANAGE_ASSIGNMENTS)
    assert not allows(admin, Operation.READ_HEALTH, client_id=uuid4())


def test_assignment_is_required_and_does_not_share_ai_context() -> None:
    actor = Actor(uuid4(), frozenset({Role.CLIENTE, Role.INSTRUTOR}))
    client_id = uuid4()
    assignments = Assignments()
    assert not allows(actor, Operation.READ_HEALTH, client_id=client_id)
    assert not allows(
        actor, Operation.READ_HEALTH, client_id=client_id, assignments=assignments
    )
    assignments.active.add((actor.user_id, client_id))
    assert allows(
        actor, Operation.READ_HEALTH, client_id=client_id, assignments=assignments
    )
    assert not allows(
        actor, Operation.USE_AI_CONTEXT, client_id=client_id, assignments=assignments
    )
    assert allows(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)


@pytest.fixture
def authorization_sessions() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                check_database(connection, "test")
                ini = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
                config = Config(str(ini))
                config.attributes.update(connection=connection, database_target="test")
                command.upgrade(config, "0003")
                yield create_session_factory(connection)
            finally:
                outer.rollback()
    finally:
        engine.dispose()


def make_user(session: Session, email: str, password_hash: str, *roles: Role) -> UUID:
    user_id = create_account(
        session,
        email,
        state=AccountState.ATIVO,
        password_hash=password_hash,
        now=utc_now(),
    )
    for role in roles:
        session.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
    if Role.CLIENTE in roles:
        session.add(
            ClientProfile(
                usuario_id=user_id,
                nome="Cliente de teste",
                data_nascimento=date(1990, 1, 1),
                ativo=True,
            )
        )
    if any(role != Role.CLIENTE for role in roles):
        session.add(
            EmployeeProfile(
                usuario_id=user_id,
                nome="Funcionário de teste",
                cargo="Teste",
                data_admissao=date(2026, 11, 7),
                ativo=True,
            )
        )
    return user_id


@pytest.mark.integration
def test_direct_routes_apply_permissions_with_real_sessions(
    authorization_sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    sessions = authorization_sessions
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    password_hash = Passwords().hash(PASSWORD)
    with sessions.begin() as session:
        first = make_user(
            session,
            "primeiro@example.test",
            password_hash,
            Role.CLIENTE,
            Role.INSTRUTOR,
        )
        second = make_user(session, "segundo@example.test", password_hash, Role.CLIENTE)
        make_user(session, "atendente@example.test", password_hash, Role.ATENDENTE)
        make_user(session, "admin@example.test", password_hash, Role.ADMINISTRADOR)

    assignments = Assignments()
    first_workout, second_workout = uuid4(), uuid4()
    owners = {first_workout: first, second_workout: second}
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=ORIGIN)
    )

    @app.get(BASE + "/fichas/{workout_id}")
    @app.get(BASE + "/fichas/{workout_id}/exportar")
    def workout(workout_id: UUID, actor: AuthenticatedActor) -> dict[str, UUID]:
        owner = owners[workout_id]
        require_permission(
            actor, Operation.READ_WORKOUT, client_id=owner, assignments=assignments
        )
        return {"client_id": owner}

    @app.get(BASE + "/saude/{client_id}")
    def health(client_id: UUID, actor: AuthenticatedActor) -> dict[str, UUID]:
        require_permission(
            actor, Operation.READ_HEALTH, client_id=client_id, assignments=assignments
        )
        return {"client_id": client_id}

    @app.get(BASE + "/contexto/{client_id}")
    def context(client_id: UUID, actor: AuthenticatedActor) -> dict[str, UUID]:
        require_permission(
            actor,
            Operation.USE_AI_CONTEXT,
            client_id=client_id,
            assignments=assignments,
        )
        return {"client_id": client_id}

    @app.post(BASE + "/funcionarios", status_code=204, response_class=Response)
    def manage_staff(actor: AuthenticatedActor) -> Response:
        require_permission(actor, Operation.MANAGE_EMPLOYEES)
        return Response(status_code=204)

    async def exercise() -> None:
        transport = httpx.ASGITransport(app=app)
        async with AsyncExitStack() as stack:

            async def login(email: str) -> tuple[httpx.AsyncClient, dict[str, str]]:
                client = await stack.enter_async_context(
                    httpx.AsyncClient(transport=transport, base_url=ORIGIN)
                )
                response = await client.post(
                    "/api/v1/auth/login",
                    headers={"Origin": ORIGIN},
                    json={"email": email, "senha": PASSWORD},
                )
                assert response.status_code == 200
                return client, {
                    "Origin": ORIGIN,
                    "X-CSRF-Token": response.json()["csrf_token"],
                }

            anonymous = await stack.enter_async_context(
                httpx.AsyncClient(transport=transport, base_url=ORIGIN)
            )
            assert (
                await anonymous.get(f"{BASE}/fichas/{first_workout}")
            ).status_code == 401
            client_a, headers_a = await login("primeiro@example.test")
            client_b, _ = await login("segundo@example.test")
            attendant, headers_attendant = await login("atendente@example.test")
            admin, headers_admin = await login("admin@example.test")

            current = await client_a.get("/api/v1/auth/session")
            assert current.json()["roles"] == ["CLIENTE", "INSTRUTOR"]
            denied = await client_a.post(
                BASE + "/funcionarios", headers={**headers_a, "X-Role": "ADMINISTRADOR"}
            )
            assert denied.status_code == 403 and denied.json()["code"] == "FORBIDDEN"
            assert (
                await attendant.post(BASE + "/funcionarios", headers=headers_attendant)
            ).status_code == 403
            assert (
                await admin.post(BASE + "/funcionarios", headers=headers_admin)
            ).status_code == 204
            assert (await admin.get(f"{BASE}/saude/{second}")).status_code == 403
            assert (await attendant.get(f"{BASE}/saude/{second}")).status_code == 403

            own = await client_b.get(f"{BASE}/fichas/{second_workout}")
            assert own.json() == {"client_id": str(second)}
            for ending in ("", "/exportar"):
                assert (
                    await client_b.get(f"{BASE}/fichas/{first_workout}{ending}")
                ).status_code == 403
                assert (
                    await client_a.get(f"{BASE}/fichas/{second_workout}{ending}")
                ).status_code == 403

            assignments.active.add((first, second))
            assert (await client_a.get(f"{BASE}/saude/{second}")).status_code == 200
            assert (
                await client_a.get(f"{BASE}/fichas/{second_workout}/exportar")
            ).status_code == 200
            assert (await client_a.get(f"{BASE}/contexto/{second}")).status_code == 403
            assignments.active.clear()
            assert (await client_a.get(f"{BASE}/saude/{second}")).status_code == 403

            assignments.active.add((first, second))
            with sessions.begin() as session:
                profile = session.get(EmployeeProfile, first)
                assert profile is not None
                profile.ativo = False
            current = await client_a.get("/api/v1/auth/session")
            assert current.json()["roles"] == ["CLIENTE"]
            assert (
                await client_a.get(f"{BASE}/fichas/{second_workout}/exportar")
            ).status_code == 403
            assert (
                await client_a.get(f"{BASE}/fichas/{first_workout}")
            ).status_code == 200
            assert (await client_a.get(f"{BASE}/contexto/{first}")).status_code == 200

    asyncio.run(exercise())

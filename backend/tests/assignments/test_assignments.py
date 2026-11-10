from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import Response
from sqlalchemy import Connection, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.assignments.http import AssignmentAccess
from app.modules.assignments.models import Assignment
from app.modules.assignments.service import (
    AssignmentError,
    ChangeAssignment,
    change_assignment,
)
from app.modules.audit.models import AuditRecord
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission

_ORIGIN = "https://academia.example.test"
_BASE = "/api/v1/designacoes"
_PASSWORD = "senha-sintetica-pes03"
_DATE = date(1990, 1, 1)


@dataclass(frozen=True)
class People:
    admin: UUID
    first: UUID
    second: UUID
    inactive: UUID
    attendant: UUID
    client: UUID


def _seed(factory: sessionmaker[Session]) -> People:
    password = Passwords().hash(_PASSWORD)
    with factory.begin() as session:

        def add(
            name: str, role: Role, *, active: bool = True, invited: bool = False
        ) -> UUID:
            user_id = create_account(
                session,
                f"{name}@example.test",
                state=AccountState.CONVIDADO if invited else AccountState.ATIVO,
                password_hash="" if invited else password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=user_id,
                        nome=name,
                        data_nascimento=_DATE,
                        ativo=active,
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=user_id,
                        nome=name,
                        cargo=role,
                        data_admissao=_DATE,
                        ativo=active,
                    )
                )
            return user_id

        return People(
            add("admin", Role.ADMINISTRADOR),
            add("primeiro", Role.INSTRUTOR),
            add("segundo", Role.INSTRUTOR),
            add("inativo", Role.INSTRUTOR, active=False),
            add("atendente", Role.ATENDENTE),
            add("cliente", Role.CLIENTE, invited=True),
        )


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                ini = Path(__file__).resolve().parents[3] / "database" / "alembic.ini"
                config = Config(str(ini))
                config.attributes.update(connection=connection, database_target="test")
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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_assignment_contract_requires_the_expected_current_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError):
        ChangeAssignment.model_validate({"instrutor_id": str(uuid4())})
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "get" in paths[_BASE + "/minhas"]
    assert "put" in paths[_BASE + "/clientes/{client_id}"]


@pytest.mark.database
def test_revision_0005_matches_metadata_and_enforces_period_and_unique_open_link(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0004")
    assert not inspect(connection).has_table("designacao", schema="academia")
    command.upgrade(config, "0005")
    command.check(config)
    factory = create_session_factory(connection)
    people = _seed(factory)
    now = utc_now()

    def insert(instructor: UUID, *, end: bool = False) -> None:
        with factory.begin() as session:
            session.add(
                Assignment(
                    id=uuid4(),
                    cliente_id=people.client,
                    instrutor_id=instructor,
                    inicio=now,
                    fim=now - timedelta(seconds=1) if end else None,
                    atribuido_por=people.admin,
                )
            )

    insert(people.first)
    with pytest.raises(IntegrityError, match="uq_designacao_cliente_vigente"):
        insert(people.second)
    with pytest.raises(IntegrityError, match="ck_designacao_periodo"):
        insert(people.second, end=True)
    command.downgrade(config, "0004")
    assert not inspect(connection).has_table("designacao", schema="academia")
    with factory.begin() as session:
        assert session.get(ClientProfile, people.client) is not None


@pytest.mark.integration
@pytest.mark.anyio
async def test_replacement_revokes_old_professional_access_and_retains_history(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = _seed(sessions)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )

    @app.get(
        "/api/v1/__test/health-access/{client_id}",
        status_code=204,
        response_class=Response,
    )
    def probe(
        client_id: UUID, actor: AuthenticatedActor, assignments: AssignmentAccess
    ) -> Response:
        require_permission(
            actor, Operation.READ_HEALTH, client_id=client_id, assignments=assignments
        )
        return Response(status_code=204)

    transport = httpx.ASGITransport(app=app)
    async with (
        httpx.AsyncClient(
            transport=transport, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        ) as admin,
        httpx.AsyncClient(
            transport=transport, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        ) as first,
        httpx.AsyncClient(
            transport=transport, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        ) as second,
    ):

        async def sign_in(client: httpx.AsyncClient, name: str) -> None:
            result = await client.post(
                "/api/v1/auth/login",
                json={"email": f"{name}@example.test", "senha": _PASSWORD},
            )
            assert result.status_code == 200
            client.headers["X-CSRF-Token"] = result.json()["csrf_token"]

        address = f"{_BASE}/clientes/{people.client}"
        access = f"/api/v1/__test/health-access/{people.client}"
        assert (await admin.get(address)).status_code == 401
        await sign_in(admin, "admin")
        await sign_in(first, "primeiro")
        await sign_in(second, "segundo")
        assert (await first.get(address)).status_code == 403
        assert (await first.get(access)).status_code == 403
        assert (await admin.get(_BASE + "/minhas")).status_code == 403
        options = await admin.get(_BASE + "/instrutores", params={"busca": "SEGUNDO"})
        assert [item["id"] for item in options.json()["itens"]] == [str(people.second)]

        for invalid in (people.inactive, people.attendant, uuid4()):
            denied = await admin.put(
                address, json={"instrutor_id": str(invalid), "vigente_id": None}
            )
            assert denied.status_code == 409
        data = {"instrutor_id": str(people.first), "vigente_id": None}
        assert (await second.put(address, json=data)).status_code == 403
        created = await admin.put(address, json=data)
        assert created.status_code == 200
        old = created.json()
        assert (await first.get(access)).status_code == 204
        assert (await second.get(access)).status_code == 403
        assigned = (await first.get(_BASE + "/minhas")).json()["itens"]
        assert assigned == [
            {"id": str(people.client), "nome": "cliente", "inicio": old["inicio"]}
        ]

        stale = await admin.put(
            address, json={"instrutor_id": str(people.second), "vigente_id": None}
        )
        assert stale.status_code == 409
        updated = await admin.put(
            address, json={"instrutor_id": str(people.second), "vigente_id": old["id"]}
        )
        assert updated.status_code == 200
        new = updated.json()
        assert (await first.get(access)).status_code == 403
        assert (await first.get(_BASE + "/minhas")).json()["total"] == 0
        assert (await second.get(access)).status_code == 204
        assert (await second.get(_BASE + "/minhas")).json()["total"] == 1

        unchanged = await admin.put(
            address, json={"instrutor_id": str(people.second), "vigente_id": new["id"]}
        )
        assert unchanged.json() == new
        history = (await admin.get(address)).json()
        assert history["vigente"] == new
        assert history["historico"]["itens"] == [{**old, "fim": new["inicio"]}]
        assert old["atribuido_por"] == new["atribuido_por"] == str(people.admin)

        with sessions.begin() as session:
            profile = session.get(EmployeeProfile, people.second)
            assert profile is not None
            profile.ativo = False
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AuditRecord)
                    .where(AuditRecord.recurso_tipo == "designacao")
                )
                == 2
            )
        assert (await second.get(access)).status_code == 403
        assert (await second.get(_BASE + "/minhas")).status_code == 403
        assert (await admin.get(address)).json()["instrutor_ativo"] is False


@pytest.mark.integration
def test_competing_replacements_keep_one_current_instructor() -> None:
    engine = create_database_engine("test")
    schema = "pes03_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            people = _seed(factory)
            actor = Actor(people.admin, frozenset({Role.ADMINISTRADOR}))
            with factory.begin() as session:
                initial = change_assignment(
                    session,
                    people.client,
                    ChangeAssignment(instrutor_id=people.first, vigente_id=None),
                    actor,
                    uuid4(),
                )
                profile = session.get(EmployeeProfile, people.inactive)
                assert profile is not None
                profile.ativo = True

            barrier = Barrier(2)

            def replace(instructor: UUID) -> int:
                barrier.wait(timeout=5)
                try:
                    with factory.begin() as session:
                        change_assignment(
                            session,
                            people.client,
                            ChangeAssignment(
                                instrutor_id=instructor, vigente_id=initial.id
                            ),
                            actor,
                            uuid4(),
                        )
                except AssignmentError as exc:
                    return exc.status
                return 200

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(replace, (people.second, people.inactive))) == [
                    200,
                    409,
                ]
            with factory.begin() as session:
                history = list(session.scalars(select(Assignment)))
                assert len(history) == 2
                assert sum(item.fim is None for item in history) == 1
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

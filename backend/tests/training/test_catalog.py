from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
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
from app.modules.audit.models import AuditRecord
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.modules.training.catalog import (
    CatalogError,
    available_combinations,
    create_exercise,
    require_prescribable,
)
from app.modules.training.models import Exercise, ExerciseResource
from app.modules.training.schemas import ExerciseFields, normalize_name

_ROOT = Path(__file__).resolve().parents[3]
_PATH = "/api/v1/exercicios"
_ORIGIN = "https://academia.example.test"
_PASSWORD = "senha-sintetica-trn01"
_A = UUID("11100000-0000-4000-8000-000000000001")
_B = UUID("11100000-0000-4000-8000-000000000002")
_C = UUID("11100000-0000-4000-8000-000000000003")
_BODYWEIGHT = UUID("11200000-0000-4000-8000-000000000001")
_ALTERNATIVES = UUID("11200000-0000-4000-8000-000000000002")
_GROUP = UUID("11300000-0000-4000-8000-000000000001")
_DATE = date(2026, 1, 1)
_BODY = {
    "nome": "  Movimento   de Teste ",
    "descricao": "Descrição sintética para o catálogo.",
    "grupo_muscular": "Grupo de teste",
    "dispensa_equipamento": False,
    "ativo": True,
    "combinacoes": [],
}


def test_available_combinations_requires_a_full_group_or_exemption() -> None:
    groups = [[_A, _B], [_C]]
    assert available_combinations(False, groups, {_A, _C}) == [[_C]]
    assert available_combinations(False, groups, {_A}) == []
    assert available_combinations(False, groups, {_A, _B, _C}) == groups
    assert available_combinations(False, [[], []], {_A}) == []
    assert available_combinations(False, [], {_A}) == []
    assert available_combinations(True, [], set()) == [[]]
    assert available_combinations(True, [[_A]], {_A}) == []


def test_catalog_contract_and_name_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert normalize_name("  REMADA\t   Articulada  ") == "remada articulada"
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    openapi = create_app().openapi()
    paths = openapi["paths"]
    assert "201" in paths[_PATH]["post"]["responses"]
    assert "200" in paths[_PATH + "/elegiveis"]["get"]["responses"]
    schema = openapi["components"]["schemas"]["ExerciseFields"]
    assert set(schema["required"]) == set(_BODY)
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize(
    "override",
    [
        {"nome": "   "},
        {"grupo_muscular": ""},
        {"combinacoes": [[]]},
        {"combinacoes": [[_A, _A]]},
        {"combinacoes": [[_A, _B], [_B, _A]]},
        {"dispensa_equipamento": True, "combinacoes": [[_A]]},
    ],
)
def test_catalog_rejects_invalid_fields_and_ambiguous_combinations(
    override: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ExerciseFields.model_validate({**_BODY, **override})


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                check_database(connection, "test")
                config = Config(str(_ROOT / "database" / "alembic.ini"))
                config.attributes.update(connection=connection, database_target="test")
                yield connection, config
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def seed_catalog(connection: Connection) -> None:
    seed = _ROOT / "database" / "seeds" / "catalogo_exercicios_sintetico.sql"
    connection.exec_driver_sql(seed.read_text(encoding="utf-8"))


@pytest.fixture
def sessions(migration: tuple[Connection, Config]) -> sessionmaker[Session]:
    connection, config = migration
    command.upgrade(config, "head")
    seed_catalog(connection)
    return create_session_factory(connection)


def seed_people(sessions: sessionmaker[Session]) -> dict[Role, UUID]:
    password = Passwords().hash(_PASSWORD)
    actors = {}
    with sessions.begin() as session:
        for role in (Role.ADMINISTRADOR, Role.INSTRUTOR, Role.CLIENTE):
            actor = create_account(
                session,
                f"{role.value.lower()}@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=actor, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=actor,
                        nome=role.value,
                        ativo=True,
                        data_nascimento=_DATE,
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=actor,
                        nome=role.value,
                        cargo=role.value,
                        ativo=True,
                        data_admissao=_DATE,
                    )
                )
            actors[role] = actor
    return actors


async def login(client: httpx.AsyncClient, role: Role) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{role.value.lower()}@example.test",
            "senha": _PASSWORD,
        },
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
async def test_roles_catalog_history_and_inventory_changes(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    actors = seed_people(sessions)
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    api = httpx.ASGITransport(app=app)

    def browser() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=api, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        )

    async with browser() as admin, browser() as trainer, browser() as client:
        assert (await client.get(_PATH)).status_code == 401
        client_headers = await login(client, Role.CLIENTE)
        assert (await client.get(_PATH)).status_code == 403
        assert (
            await client.post(_PATH, headers=client_headers, json=_BODY)
        ).status_code == 403
        admin_headers = await login(admin, Role.ADMINISTRADOR)
        trainer_headers = await login(trainer, Role.INSTRUTOR)
        assert (await trainer.post(_PATH, json=_BODY)).status_code == 403

        options = (await trainer.get(_PATH + "/recursos")).json()
        assert {UUID(item["id"]) for item in options} == {_A, _C}
        candidates = (await trainer.get(_PATH + "/elegiveis")).json()
        assert {UUID(item["id"]) for item in candidates} == {_BODYWEIGHT, _ALTERNATIVES}
        alternative = next(
            item for item in candidates if UUID(item["id"]) == _ALTERNATIVES
        )
        assert alternative["combinacoes_disponiveis"] == [[str(_C)]]

        with sessions.begin() as session:
            require_prescribable(session, _BODYWEIGHT, [])
            require_prescribable(session, _ALTERNATIVES, [_C])
            for resources in ([_A], [_A, _B]):
                with pytest.raises(CatalogError):
                    require_prescribable(session, _ALTERNATIVES, resources)
        for resource, operational in ((_C, False), (_B, True)):
            resource_path = "/api/v1/admin/equipamentos/" + str(resource)
            equipment = (await admin.get(resource_path)).json()
            fields = {
                key: equipment[key]
                for key in ("nome", "descricao", "categoria", "ativo", "revisao")
            }
            changed = await admin.put(
                resource_path,
                headers=admin_headers,
                json={**fields, "operacional": operational},
            )
            assert changed.status_code == 200
            candidates = (await trainer.get(_PATH + "/elegiveis")).json()
            if not operational:
                assert [UUID(item["id"]) for item in candidates] == [_BODYWEIGHT]
                with sessions.begin() as session, pytest.raises(CatalogError):
                    require_prescribable(session, _ALTERNATIVES, [_C])
            else:
                alternative = next(
                    item for item in candidates if UUID(item["id"]) == _ALTERNATIVES
                )
                assert alternative["combinacoes_disponiveis"] == [[str(_A), str(_B)]]
                with sessions.begin() as session:
                    require_prescribable(session, _ALTERNATIVES, [_A, _B])

        invalid = await admin.post(
            _PATH,
            headers=admin_headers,
            json={**_BODY, "combinacoes": [[str(uuid4())]]},
        )
        assert invalid.status_code == 422
        created = await admin.post(_PATH, headers=admin_headers, json=_BODY)
        assert created.status_code == 201
        original = created.json()
        assert original["ativo"] and not original["elegivel"]
        path = _PATH + "/" + original["id"]
        assert (await trainer.get(path)).json() == original
        inactive = await trainer.put(
            path, headers=trainer_headers, json={**_BODY, "revisao": 1, "ativo": False}
        )
        assert inactive.status_code == 200
        duplicate = await trainer.post(
            _PATH, headers=trainer_headers, json={**_BODY, "nome": "MOVIMENTO DE TESTE"}
        )
        assert duplicate.status_code == 409
        assert (await trainer.get(path)).json()["ativo"] is False
        assert (
            await trainer.put(
                path, headers=trainer_headers, json={**_BODY, "revisao": 1}
            )
        ).status_code == 409
        restored = await trainer.put(
            path,
            headers=trainer_headers,
            json={**_BODY, "revisao": 2, "dispensa_equipamento": True},
        )
        assert restored.status_code == 200
        assert restored.json()["id"] == original["id"] and restored.json()["elegivel"]
        candidates = (await trainer.get(_PATH + "/elegiveis")).json()
        assert original["id"] in {item["id"] for item in candidates}
        withdrawn = await trainer.put(
            path,
            headers=trainer_headers,
            json={**_BODY, "revisao": 3, "dispensa_equipamento": True, "ativo": False},
        )
        assert withdrawn.status_code == 200
        assert (await trainer.get(path)).json()["id"] == original["id"]
        candidates = (await trainer.get(_PATH + "/elegiveis")).json()
        assert original["id"] not in {item["id"] for item in candidates}
        with sessions.begin() as session, pytest.raises(CatalogError):
            require_prescribable(session, UUID(original["id"]), [])

        listing = await admin.get(_PATH)
        assert listing.json()["total"] == 3
        assert listing.headers["cache-control"] == "no-store"

        with sessions.begin() as session:
            records = list(
                session.scalars(
                    select(AuditRecord)
                    .where(AuditRecord.recurso_id == UUID(original["id"]))
                    .order_by(AuditRecord.ocorrido_em)
                )
            )
            assert [(row.acao, row.ator_id) for row in records] == [
                ("exercise.created", actors[Role.ADMINISTRADOR]),
                ("exercise.deactivated", actors[Role.INSTRUTOR]),
                ("exercise.reactivated", actors[Role.INSTRUTOR]),
                ("exercise.deactivated", actors[Role.INSTRUTOR]),
            ]


@pytest.mark.database
def test_migration_and_repeatable_seed(migration: tuple[Connection, Config]) -> None:
    connection, config = migration
    command.upgrade(config, "0008")
    assert not inspect(connection).has_table("exercicio", schema="academia")
    command.upgrade(config, "0009")
    command.check(config)
    seed_catalog(connection)
    seed_catalog(connection)
    factory = create_session_factory(connection)
    with factory.begin() as session:
        assert session.scalar(select(func.count()).select_from(Exercise)) == 2
    with (
        pytest.raises(IntegrityError, match="uq_exercicio_recurso_grupo"),
        factory.begin() as session,
    ):
        session.add(ExerciseResource(id=uuid4(), grupo_id=_GROUP, equipamento_id=_A))
    command.downgrade(config, "0008")
    assert not inspect(connection).has_table("exercicio", schema="academia")
    assert inspect(connection).has_table("equipamento", schema="academia")


@pytest.mark.integration
def test_concurrent_normalized_names_commit_only_once() -> None:
    engine = create_database_engine("test")
    schema = "trn01_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            instructor = seed_people(factory)[Role.INSTRUTOR]
            barrier = Barrier(2)

            def create(name: str) -> int:
                data = ExerciseFields.model_validate({**_BODY, "nome": name})
                barrier.wait(timeout=5)
                try:
                    with factory.begin() as session:
                        create_exercise(session, data, instructor, uuid4())
                except CatalogError as exc:
                    return exc.status
                return 201

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(
                    pool.map(create, [" Movimento     de Teste ", "MOVIMENTO DE TESTE"])
                ) == [201, 409]
            with factory.begin() as session:
                assert session.scalar(select(func.count()).select_from(Exercise)) == 1
                assert (
                    session.scalar(select(func.count()).select_from(AuditRecord)) == 1
                )
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

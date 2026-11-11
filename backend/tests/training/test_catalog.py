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
from sqlalchemy import Connection, delete, func, inspect, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.events.contracts import AuditEvent
from app.main import create_app
from app.modules.assignments.models import Assignment
from app.modules.assignments.service import ChangeAssignment, change_assignment
from app.modules.audit.models import AuditRecord
from app.modules.equipment.models import Equipment
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.service import utc_now
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.models import DeliveryState, Notification
from app.modules.onboarding.schemas import (
    Completion,
    ConfirmUpdate,
    DraftChange,
    DraftData,
)
from app.modules.onboarding.service import (
    complete_draft,
    confirm_update,
    get_current_snapshot,
    save_draft,
)
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from app.modules.training.catalog import (
    CatalogError,
    available_combinations,
    create_exercise,
    require_prescribable,
)
from app.modules.training.models import Exercise, ExerciseResource
from app.modules.training.publication import (
    publish_manual,
    published_workout,
    record_opinion,
    review_detail,
    review_queue,
)
from app.modules.training.review_schemas import (
    PublishWorkout,
    ReviewDetail,
    ReviewWorkout,
)
from app.modules.training.schemas import ExerciseFields, normalize_name
from app.modules.training.workout_models import (
    WorkoutDay,
    WorkoutItem,
    WorkoutOpinion,
    WorkoutValidation,
    WorkoutVersion,
)
from app.modules.training.workout_schemas import (
    CreateWorkout,
    UpdateWorkout,
    WorkoutDayInput,
    WorkoutItemInput,
    WorkoutView,
)
from app.modules.training.workouts import (
    WorkoutError,
    create_draft,
    get_workout,
    retention_candidates,
    update_draft,
)
from app.policies.access import Actor

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
    assert inspect(connection).has_table("exercicio", schema="academia")
    command.upgrade(config, "head")
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


_WORKOUT = "/api/v1/treinos/clientes/{}/"
_MANUAL_ITEM = {
    "exercicio_id": str(_BODYWEIGHT),
    "equipamento_ids": [],
    "series": 3,
    "repeticoes": "8 a 12",
    "carga_kg": "12.50",
    "intervalo_segundos": 60,
    "cadencia": "2-0-2",
    "observacoes": "Registro sintético",
}


def workout_people(
    factory: sessionmaker[Session],
) -> tuple[dict[Role, UUID], Actor, UUID]:
    actors = seed_people(factory)
    with factory.begin() as session:
        client_id = actors[Role.CLIENTE]
        draft = save_draft(
            session,
            client_id,
            client_id,
            DraftChange(
                versao_base=None,
                revisao=None,
                dados=DraftData(
                    altura_cm=170,
                    peso_kg=70,
                    objetivo_principal="FORCA",
                    experiencia="INICIANTE",
                    nivel_atividade="LEVE",
                    dias_semana=3,
                    duracao_sessao_min=60,
                    possui_condicoes_saude="NAO",
                    condicoes_saude=[],
                    usa_medicamentos="NAO",
                    medicamentos=[],
                    possui_dor_lesao_limitacao="NAO",
                    limitacoes=[],
                    restricao_exercicio_declarada="NAO",
                    evento_saude_importante_recente="NAO",
                    observacoes="",
                ),
            ),
        )
        snapshot = complete_draft(
            session,
            client_id,
            client_id,
            Completion(versao_base=None, revisao=draft.revisao),
        )
        admin = Actor(actors[Role.ADMINISTRADOR], frozenset({Role.ADMINISTRADOR}))
        change_assignment(
            session,
            client_id,
            ChangeAssignment(
                instrutor_id=actors[Role.INSTRUTOR],
                vigente_id=None,
            ),
            admin,
            uuid4(),
        )
    return (
        actors,
        Actor(actors[Role.INSTRUTOR], frozenset({Role.INSTRUTOR})),
        snapshot.id,
    )


def manual_payload(snapshot_id: UUID, base_id: UUID | None = None) -> dict[str, object]:
    return {
        "solicitacao_id": str(uuid4()),
        "versao_base_id": str(base_id) if base_id else None,
        "onboarding_id": str(snapshot_id),
        "avaliacao_id": None,
        "dias": [{"titulo": "Dia A", "itens": [_MANUAL_ITEM]}],
    }


def publish_fixture(session: Session, client_id: UUID, version_id: UUID) -> None:
    session.execute(
        update(WorkoutVersion)
        .where(WorkoutVersion.cliente_id == client_id, WorkoutVersion.vigente.is_(True))
        .values(estado_publicacao="SUBSTITUIDO", vigente=False)
    )
    session.execute(
        update(WorkoutVersion)
        .where(WorkoutVersion.id == version_id)
        .values(
            estado_publicacao="PUBLICADO",
            vigente=True,
            publicada_em=utc_now(),
        )
    )


def test_workout_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    root = "/api/v1/treinos/clientes/{client_id}"
    assert "201" in paths[root + "/rascunhos"]["post"]["responses"]
    assert "put" in paths[root + "/rascunhos/{version_id}"]
    assert not any("publicar" in path for path in paths)
    value = WorkoutItemInput.model_validate(_MANUAL_ITEM)
    assert str(value.carga_kg) == "12.50"
    for invalid in (
        {"series": 0},
        {"intervalo_segundos": -1},
        {"carga_kg": "1.234"},
        {"series": True},
    ):
        with pytest.raises(ValueError):
            WorkoutItemInput.model_validate({**_MANUAL_ITEM, **invalid})


@pytest.mark.integration
@pytest.mark.anyio
async def test_manual_draft_replay_snapshots_and_scope(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("ACADEMIA_QDRANT_PATH", "servico-indisponivel-no-teste")
    actors, instructor, snapshot_id = workout_people(sessions)
    client_id = actors[Role.CLIENTE]
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    api = httpx.ASGITransport(app=app)
    root = _WORKOUT.format(client_id)
    body = manual_payload(snapshot_id)
    async with (
        httpx.AsyncClient(
            transport=api, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        ) as trainer,
        httpx.AsyncClient(
            transport=api, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        ) as client,
    ):
        client_headers = await login(client, Role.CLIENTE)
        assert (
            await client.post(root + "rascunhos", json=body, headers=client_headers)
        ).status_code == 403
        headers = await login(trainer, Role.INSTRUTOR)
        context = await trainer.get(root + "contexto")
        assert context.status_code == 200 and context.json()["onboarding"]["id"] == str(
            snapshot_id
        )
        assert (await trainer.post(root + "rascunhos", json=body)).status_code == 403
        invalid_reference = await trainer.post(
            root + "rascunhos",
            json={**body, "avaliacao_id": str(uuid4())},
            headers=headers,
        )
        assert invalid_reference.status_code == 422
        created = await trainer.post(root + "rascunhos", json=body, headers=headers)
        assert (
            created.status_code == 201
            and created.headers["cache-control"] == "no-store"
        )
        original = created.json()
        assert original["origem"] == "MANUAL" and original["autor_id"] == str(
            instructor.user_id
        )
        assert (
            original["estado_publicacao"] == "RASCUNHO" and original["vigente"] is False
        )
        version_id = UUID(original["id"])
        assert (
            await trainer.post(root + "rascunhos", json=body, headers=headers)
        ).json() == original
        with sessions.begin() as session:
            publish_fixture(session, client_id, version_id)
        invalid_edit = {
            key: value
            for key, value in body.items()
            if key not in {"solicitacao_id", "versao_base_id"}
        }
        assert (
            await trainer.put(
                root + "rascunhos/" + str(version_id),
                json={**invalid_edit, "revisao": 1},
                headers=headers,
            )
        ).status_code == 409
        with sessions.begin() as session:
            session.execute(
                update(Exercise)
                .where(Exercise.id == _BODYWEIGHT)
                .values(
                    nome="Nome atual do catálogo",
                    descricao="Descrição atual do catálogo",
                )
            )
        history = (await trainer.get(root + "versoes/" + str(version_id))).json()
        assert history["dias"] == original["dias"]
        assert (
            history["dias"][0]["itens"][0]["exercicio_snapshot"]["nome"]
            != "Nome atual do catálogo"
        )
        next_body = manual_payload(snapshot_id, version_id)
        copied = await trainer.post(root + "rascunhos", json=next_body, headers=headers)
        assert copied.status_code == 201
        next_value = copied.json()
        assert next_value["numero"] == 2 and next_value["versao_base_id"] == str(
            version_id
        )
        assert (
            next_value["dias"][0]["itens"][0]["exercicio_snapshot"]["nome"]
            == "Nome atual do catálogo"
        )
        assert (
            await trainer.get(root + "versoes/" + str(version_id))
        ).json() == history
        version_path = root + "rascunhos/" + next_value["id"]
        update_body = {
            **invalid_edit,
            "revisao": 1,
            "dias": [{"titulo": "Dia B", "itens": [{**_MANUAL_ITEM, "series": 4}]}],
        }
        saved = await trainer.put(version_path, json=update_body, headers=headers)
        assert saved.status_code == 200 and saved.json()["revisao"] == 2
        assert saved.json()["dias"][0]["itens"][0]["series"] == 4
        assert (
            await trainer.put(version_path, json=update_body, headers=headers)
        ).status_code == 409
        assert (
            await trainer.get(_WORKOUT.format(uuid4()) + "versoes/" + next_value["id"])
        ).status_code == 403
        with sessions.begin() as session:
            session.execute(
                update(Exercise).where(Exercise.id == _BODYWEIGHT).values(ativo=False)
            )
        declined = await trainer.put(
            version_path, json={**update_body, "revisao": 2}, headers=headers
        )
        assert declined.status_code == 409
        retained = (await trainer.get(root + "versoes/" + next_value["id"])).json()
        assert retained == saved.json()
        with sessions.begin() as session:
            session.add(
                UserRole(
                    id=uuid4(),
                    usuario_id=actors[Role.ADMINISTRADOR],
                    papel=Role.INSTRUTOR,
                )
            )
        admin_headers = await login(client, Role.ADMINISTRADOR)
        assert (await client.get(root + "contexto")).status_code == 403
        with sessions.begin() as session:
            previous = session.scalar(
                select(Assignment).where(
                    Assignment.cliente_id == client_id,
                    Assignment.fim.is_(None),
                )
            )
            assert previous is not None
            change_assignment(
                session,
                client_id,
                ChangeAssignment(
                    instrutor_id=actors[Role.ADMINISTRADOR], vigente_id=previous.id
                ),
                Actor(actors[Role.ADMINISTRADOR], frozenset({Role.ADMINISTRADOR})),
                uuid4(),
            )
        assert (await trainer.get(root + "contexto")).status_code == 403
        assert (
            await trainer.put(
                version_path, json={**update_body, "revisao": 2}, headers=headers
            )
        ).status_code == 403
        assert (await client.get(root + "contexto")).status_code == 200
        assert (
            await client.put(
                version_path, json={**update_body, "revisao": 2}, headers=admin_headers
            )
        ).status_code == 403


@pytest.mark.database
def test_published_workout_immutability_retention_structure_and_numbering(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot_id = workout_people(sessions)
    client_id = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = create_draft(
            session,
            instructor,
            client_id,
            CreateWorkout.model_validate(manual_payload(snapshot_id)),
            uuid4(),
        )
        publish_fixture(session, client_id, first.id)
        item_id = session.scalar(select(WorkoutItem.id))
    with pytest.raises(DBAPIError, match="imutável"), sessions.begin() as session:
        session.execute(
            update(WorkoutItem).where(WorkoutItem.id == item_id).values(series=9)
        )
    with pytest.raises(DBAPIError, match="imutável"), sessions.begin() as session:
        session.execute(
            update(WorkoutVersion)
            .where(WorkoutVersion.id == first.id)
            .values(autor_id=actors[Role.ADMINISTRADOR])
        )
    with pytest.raises(DBAPIError, match="preservados"), sessions.begin() as session:
        session.execute(delete(WorkoutVersion).where(WorkoutVersion.id == first.id))
    with pytest.raises(DBAPIError, match="imutável"), sessions.begin() as session:
        session.execute(
            update(WorkoutVersion)
            .where(WorkoutVersion.id == first.id)
            .values(
                estado_publicacao="CONTEUDO_EXPIRADO",
                vigente=False,
                conteudo_excluido_em=utc_now(),
                motivo_exclusao="LIMITE_15",
            )
        )
    with (
        pytest.raises(IntegrityError, match="uq_ficha_vigente"),
        sessions.begin() as session,
    ):
        contender = create_draft(
            session,
            instructor,
            client_id,
            CreateWorkout.model_validate(manual_payload(snapshot_id, first.id)),
            uuid4(),
        )
        session.execute(
            update(WorkoutVersion)
            .where(WorkoutVersion.id == contender.id)
            .values(
                estado_publicacao="PUBLICADO",
                vigente=True,
                publicada_em=utc_now(),
            )
        )
    with (
        pytest.raises(IntegrityError, match="fk_ficha_onboarding_cliente"),
        sessions.begin() as session,
    ):
        session.add(
            WorkoutVersion(
                id=uuid4(),
                cliente_id=client_id,
                numero=2,
                origem="MANUAL",
                autor_id=instructor.user_id,
                onboarding_id=uuid4(),
                estado_publicacao="RASCUNHO",
                vigente=False,
                revision=1,
            )
        )
    with sessions.begin() as session:
        previous = first.id
        for _ in range(15):
            version = create_draft(
                session,
                instructor,
                client_id,
                CreateWorkout.model_validate(manual_payload(snapshot_id, previous)),
                uuid4(),
            )
            publish_fixture(session, client_id, version.id)
            previous = version.id
        assert retention_candidates(session, client_id) == [first.id]
        extra = create_draft(
            session,
            instructor,
            client_id,
            CreateWorkout.model_validate(manual_payload(snapshot_id, previous)),
            uuid4(),
        )
        assert extra.numero == 17 and retention_candidates(session, client_id) == [
            first.id
        ]
        session.execute(
            update(WorkoutVersion)
            .where(WorkoutVersion.id == first.id)
            .values(
                estado_publicacao="CONTEUDO_EXPIRADO",
                conteudo_excluido_em=utc_now(),
                motivo_exclusao="LIMITE_15",
            )
        )
        day_ids = select(WorkoutDay.id).where(WorkoutDay.versao_id == first.id)
        session.execute(delete(WorkoutItem).where(WorkoutItem.dia_id.in_(day_ids)))
        session.execute(delete(WorkoutDay).where(WorkoutDay.versao_id == first.id))
        expired = get_workout(session, instructor, client_id, first.id)
        assert expired.dias == [] and expired.numero == 1
        assert retention_candidates(session, client_id) == []
        next_draft = create_draft(
            session,
            instructor,
            client_id,
            CreateWorkout.model_validate(manual_payload(snapshot_id, previous)),
            uuid4(),
        )
        assert next_draft.numero == 18


@pytest.mark.database
def test_workout_migration_keeps_existing_catalog(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0009")
    assert not inspect(connection).has_table("versao_ficha", schema="academia")
    command.upgrade(config, "0010")
    assert inspect(connection).has_table("versao_ficha", schema="academia")
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "0009")
    assert not inspect(connection).has_table("versao_ficha", schema="academia")
    assert inspect(connection).has_table("exercicio", schema="academia")


@pytest.mark.integration
@pytest.mark.parametrize("same_request", [False, True])
def test_draft_creation_is_serialized_and_idempotent(same_request: bool) -> None:
    engine = create_database_engine("test")
    schema = "trn02_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            actors, instructor, snapshot_id = workout_people(factory)
            with factory.begin() as session:
                session.add(
                    Exercise(
                        id=_BODYWEIGHT,
                        nome="Movimento sintético",
                        nome_normalizado="movimento sintético",
                        descricao="Descrição sintética",
                        grupo_muscular="Grupo",
                        ativo=True,
                        dispensa_equipamento=True,
                        revision=1,
                    )
                )
            body = manual_payload(snapshot_id)
            inputs = [
                CreateWorkout.model_validate(body),
                CreateWorkout.model_validate(
                    body if same_request else {**body, "solicitacao_id": str(uuid4())}
                ),
            ]
            barrier = Barrier(2)

            def create(data: CreateWorkout) -> int:
                barrier.wait(timeout=5)
                with factory.begin() as session:
                    result = create_draft(
                        session, instructor, actors[Role.CLIENTE], data, uuid4()
                    )
                return result.numero

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(create, inputs)) == (
                    [1, 1] if same_request else [1, 2]
                )
            with factory.begin() as session:
                count = session.scalar(select(func.count()).select_from(WorkoutVersion))
                assert count == (1 if same_request else 2)
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()


def visible_published(
    session: Session,
    actor: Actor,
    client: UUID,
    version: UUID | None = None,
) -> ReviewDetail:
    value = published_workout(session, actor, client, version)
    assert value is not None
    return value


# TRN-03: mesmos fixtures isolados e dados sintéticos do catálogo/rascunho.
def publication_input(
    workout: object, request_id: UUID | None = None
) -> PublishWorkout:
    assert isinstance(workout, WorkoutView)
    return PublishWorkout(
        solicitacao_id=request_id or uuid4(),
        revisao=workout.revisao,
        onboarding_id=workout.onboarding_id,
        versao_base_id=workout.versao_base_id,
        restricoes_conferidas=True,
    )


def draft_and_publish(
    session: Session,
    actor: Actor,
    client: UUID,
    snapshot: UUID,
    base: UUID | None = None,
) -> ReviewDetail:
    draft = create_draft(
        session,
        actor,
        client,
        CreateWorkout.model_validate(manual_payload(snapshot, base)),
        uuid4(),
    )
    return publish_manual(
        session, actor, client, draft.id, publication_input(draft), uuid4()
    )


def opinion_input(state: str) -> ReviewWorkout:
    return ReviewWorkout.model_validate(
        {
            "solicitacao_id": str(uuid4()),
            "estado": state,
            "motivo": "Parecer sintético." if state == "REJEITADO" else None,
        }
    )


@pytest.mark.parametrize("reason", [None, "", "   ", "\x00"])
def test_rejection_requires_a_nonempty_safe_reason(reason: str | None) -> None:
    with pytest.raises(ValueError):
        ReviewWorkout.model_validate(
            {
                "solicitacao_id": str(uuid4()),
                "estado": "REJEITADO",
                "motivo": reason,
            }
        )


def test_publication_and_review_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    base = "/api/v1/treinos/clientes/{client_id}"
    for suffix in ("/versoes/{version_id}/publicacao", "/versoes/{version_id}/parecer"):
        assert "200" in paths[base + suffix]["post"]["responses"]
    assert "/api/v1/treinos/pendentes" in paths
    with pytest.raises(ValueError):
        PublishWorkout.model_validate(
            {
                "solicitacao_id": str(uuid4()),
                "revisao": 1,
                "onboarding_id": str(uuid4()),
                "versao_base_id": None,
                "restricoes_conferidas": False,
            }
        )


@pytest.mark.integration
def test_publication_pending_review_and_rejection_replacement(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    own = Actor(client, frozenset({Role.CLIENTE}))
    reject_a, reject_b = opinion_input("REJEITADO"), opinion_input("REJEITADO")
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        assert first.parecer.estado == "PENDENTE" and first.validacao
        visible = published_workout(session, own, client)
        assert visible and visible.ficha.id == first.ficha.id and visible.ficha.dias
        queue = review_queue(session, instructor, 1, 20)
        assert [item.versao_id for item in queue.itens] == [first.ficha.id]
        record_opinion(session, instructor, client, first.ficha.id, reject_a, uuid4())
        assert visible_published(session, own, client).parecer.estado == "REJEITADO"
        second = draft_and_publish(
            session, instructor, client, snapshot, first.ficha.id
        )
        assert second.parecer.estado == "PENDENTE"
        assert visible_published(session, own, client, first.ficha.id).ficha.dias
        # Publicar B não apaga A. Aceitar outra versão também não.
        third = draft_and_publish(
            session, instructor, client, snapshot, second.ficha.id
        )
        record_opinion(
            session,
            instructor,
            client,
            third.ficha.id,
            opinion_input("ACEITO"),
            uuid4(),
        )
        assert visible_published(session, own, client, first.ficha.id).ficha.dias
        record_opinion(session, instructor, client, second.ficha.id, reject_b, uuid4())
        old = published_workout(session, own, client, first.ficha.id)
        assert (
            old
            and old.ficha.dias == []
            and old.ficha.motivo_exclusao == "REJEITADA_ANTERIOR"
        )
        assert old.parecer.estado == "REJEITADO" and old.parecer.motivo
        assert visible_published(session, own, client, second.ficha.id).ficha.dias
        assert visible_published(session, own, client).ficha.id == third.ficha.id
        # Replay não recria parecer, não apaga o novo rejeitado nem muda a vigente.
        record_opinion(session, instructor, client, first.ficha.id, reject_a, uuid4())
        record_opinion(session, instructor, client, second.ficha.id, reject_b, uuid4())
        assert session.scalar(select(func.count()).select_from(WorkoutOpinion)) == 3
        assert session.scalar(select(func.count()).select_from(WorkoutValidation)) == 3
        assert (
            session.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.canal == "INTERNO")
            )
            == 3
        )


@pytest.mark.integration
def test_late_rejection_purges_the_older_version_not_the_latest(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        second = draft_and_publish(
            session, instructor, client, snapshot, first.ficha.id
        )
        record_opinion(
            session,
            instructor,
            client,
            second.ficha.id,
            opinion_input("REJEITADO"),
            uuid4(),
        )
        late = record_opinion(
            session,
            instructor,
            client,
            first.ficha.id,
            opinion_input("REJEITADO"),
            uuid4(),
        )
        assert late.ficha.dias == [] and late.parecer.estado == "REJEITADO"
        current = published_workout(session, instructor, client)
        assert current and current.ficha.id == second.ficha.id and current.ficha.dias


@pytest.mark.integration
@pytest.mark.parametrize("first_state", ["ACEITO", "REJEITADO"])
def test_publication_retains_15_and_preserves_metadata(
    sessions: sessionmaker[Session], first_state: str
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        record_opinion(
            session,
            instructor,
            client,
            first.ficha.id,
            opinion_input(first_state),
            uuid4(),
        )
        current = first
        for _ in range(14):
            current = draft_and_publish(
                session, instructor, client, snapshot, current.ficha.id
            )
        assert (
            session.scalar(
                select(func.count())
                .select_from(WorkoutVersion)
                .where(WorkoutVersion.conteudo_excluido_em.is_(None))
            )
            == 15
        )
        last_draft = create_draft(
            session,
            instructor,
            client,
            CreateWorkout.model_validate(manual_payload(snapshot, current.ficha.id)),
            uuid4(),
        )
        data = publication_input(last_draft)
        result = publish_manual(
            session, instructor, client, last_draft.id, data, uuid4()
        )
        assert result.ficha.numero == 16 and result.ficha.vigente
        expired = review_detail(session, instructor, client, first.ficha.id)
        assert expired.ficha.dias == [] and expired.ficha.motivo_exclusao == "LIMITE_15"
        assert expired.parecer.estado == first_state
        assert session.scalar(select(func.count()).select_from(WorkoutDay)) == 15
        assert session.scalar(select(func.count()).select_from(WorkoutItem)) == 15
        assert session.scalar(select(func.count()).select_from(WorkoutVersion)) == 16
        assert session.scalar(select(func.count()).select_from(WorkoutValidation)) == 16
        replay = publish_manual(
            session, instructor, client, last_draft.id, data, uuid4()
        )
        assert replay.ficha.id == result.ficha.id
        assert session.scalar(select(func.count()).select_from(WorkoutVersion)) == 16
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditRecord)
                .where(AuditRecord.acao == "workout.content_expired")
            )
            == 1
        )
        next_draft = create_draft(
            session,
            instructor,
            client,
            CreateWorkout.model_validate(manual_payload(snapshot, last_draft.id)),
            uuid4(),
        )
        assert next_draft.numero == 17


@pytest.mark.integration
def test_publication_revalidates_snapshot_inventory_and_draft(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        empty = create_draft(
            session,
            instructor,
            client,
            CreateWorkout.model_validate(
                {**manual_payload(snapshot, first.ficha.id), "dias": []}
            ),
            uuid4(),
        )
        with pytest.raises(WorkoutError) as failure:
            publish_manual(
                session, instructor, client, empty.id, publication_input(empty), uuid4()
            )
        assert failure.value.status == 422
        data = CreateWorkout.model_validate(manual_payload(snapshot, first.ficha.id))
        data.dias[0].itens[0].exercicio_id = _ALTERNATIVES
        data.dias[0].itens[0].equipamento_ids = [_C]
        draft = create_draft(session, instructor, client, data, uuid4())
        # Inventário deixou de atender a alternativa após salvar.
        session.execute(
            update(Equipment).where(Equipment.id == _C).values(operacional=False)
        )
        with pytest.raises(WorkoutError) as failure:
            publish_manual(
                session, instructor, client, draft.id, publication_input(draft), uuid4()
            )
        assert failure.value.status == 409
        session.execute(
            update(Equipment).where(Equipment.id == _C).values(operacional=True)
        )
        # Revisão obsoleta é rejeitada.
        with pytest.raises(WorkoutError):
            publish_manual(
                session,
                instructor,
                client,
                draft.id,
                publication_input(draft).model_copy(update={"revisao": 2}),
                uuid4(),
            )
        # Novo snapshot não é convertido em autorização implícita da ficha antiga.
        previous = get_current_snapshot(session, client)
        assert previous
        confirm_update(
            session,
            client,
            client,
            ConfirmUpdate(
                versao_base=previous.id, confirmado=True, dados=previous.dados
            ),
        )
        with pytest.raises(WorkoutError) as failure:
            publish_manual(
                session, instructor, client, draft.id, publication_input(draft), uuid4()
            )
        assert failure.value.status == 409
        assert visible_published(session, instructor, client).ficha.id == first.ficha.id


@pytest.mark.integration
def test_publication_and_expiry_roll_back_together(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        current = draft_and_publish(session, instructor, client, snapshot)
        first_id = current.ficha.id
        for _ in range(14):
            current = draft_and_publish(
                session, instructor, client, snapshot, current.ficha.id
            )
        draft = create_draft(
            session,
            instructor,
            client,
            CreateWorkout.model_validate(manual_payload(snapshot, current.ficha.id)),
            uuid4(),
        )

    def fail_notice(*args: object) -> bool:
        raise RuntimeError("Falha transacional sintética")

    monkeypatch.setattr(
        "app.modules.training.publication.notify_workout_review", fail_notice
    )
    with pytest.raises(RuntimeError), sessions.begin() as session:
        publish_manual(
            session, instructor, client, draft.id, publication_input(draft), uuid4()
        )
    with sessions.begin() as session:
        assert (
            visible_published(session, instructor, client).ficha.id == current.ficha.id
        )
        assert review_detail(session, instructor, client, first_id).ficha.dias
        assert (
            get_workout(session, instructor, client, draft.id).estado_publicacao
            == "RASCUNHO"
        )
        assert session.get(WorkoutValidation, draft.id) is None


@pytest.mark.database
def test_publication_migration_and_immutable_reviews(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0010")
    assert not inspect(connection).has_table("validacao_ficha", schema="academia")
    command.upgrade(config, "head")
    command.check(config)
    factory = create_session_factory(connection)
    seed_catalog(connection)
    actors, instructor, snapshot = workout_people(factory)
    with factory.begin() as session:
        first = draft_and_publish(session, instructor, actors[Role.CLIENTE], snapshot)
        opinion = record_opinion(
            session,
            instructor,
            actors[Role.CLIENTE],
            first.ficha.id,
            opinion_input("ACEITO"),
            uuid4(),
        )
    for model in (WorkoutOpinion, WorkoutValidation):
        with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
            session.execute(delete(model))
    assert opinion.parecer.instrutor_id == instructor.user_id
    command.downgrade(config, "0010")
    assert inspect(connection).has_table("parecer", schema="academia")


@pytest.mark.integration
@pytest.mark.anyio
async def test_publication_api_permissions_mail_failure_replay_and_reassignment(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client_id = actors[Role.CLIENTE]
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    transport = httpx.ASGITransport(app=app)
    deliveries: list[object] = []

    def failing_mail(_self: object, message: object) -> DeliveryState:
        deliveries.append(message)
        return DeliveryState.FALHOU

    monkeypatch.setattr(
        "app.modules.notifications.email.LocalSmtp.deliver", failing_mail
    )

    def browser() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=transport, base_url=_ORIGIN, headers={"Origin": _ORIGIN}
        )

    root = f"/api/v1/treinos/clientes/{client_id}"
    async with browser() as trainer, browser() as own, browser() as admin:
        assert (await own.get(root + "/atual")).status_code == 401
        headers = await login(trainer, Role.INSTRUTOR)
        own_headers = await login(own, Role.CLIENTE)
        await login(admin, Role.ADMINISTRADOR)
        assert (await own.get(root + "/atual")).json() is None
        draft_response = await trainer.post(
            root + "/rascunhos", headers=headers, json=manual_payload(snapshot)
        )
        assert draft_response.status_code == 201
        draft = WorkoutView.model_validate(draft_response.json())
        path = root + f"/versoes/{draft.id}"
        data = publication_input(draft).model_dump(mode="json")
        assert (await own.get(root + f"/publicadas/{draft.id}")).status_code == 404
        assert (
            await own.post(path + "/publicacao", headers=own_headers, json=data)
        ).status_code == 403
        assert (await admin.get(path + "/revisao")).status_code == 403
        assert (await trainer.post(path + "/publicacao", json=data)).status_code == 403
        publication = await trainer.post(
            path + "/publicacao", headers=headers, json=data
        )
        assert publication.status_code == 200
        assert publication.headers["cache-control"] == "no-store"
        assert publication.json()["aviso_email"] == {
            "estado": "FALHOU",
            "tentativas": 1,
        }
        assert (
            await trainer.post(path + "/publicacao", headers=headers, json=data)
        ).status_code == 200
        assert len(deliveries) == 1
        visible = (await own.get(root + "/atual")).json()
        assert visible["parecer"]["estado"] == "PENDENTE" and visible["ficha"]["dias"]
        assert (
            await own.get(f"/api/v1/treinos/clientes/{uuid4()}/atual")
        ).status_code == 403
        assert (
            len((await trainer.get("/api/v1/treinos/pendentes")).json()["itens"]) == 1
        )
        assert (await own.get("/api/v1/treinos/pendentes")).status_code == 403
        retry = await trainer.post(
            path + "/aviso", headers=headers, json={"tentativa_anterior": 1}
        )
        assert retry.json() == {"estado": "FALHOU", "tentativas": 2}
        await trainer.post(
            path + "/aviso", headers=headers, json={"tentativa_anterior": 1}
        )
        assert len(deliveries) == 2
        rejected = opinion_input("REJEITADO").model_dump(mode="json")
        assert (
            await trainer.post(
                path + "/parecer", headers=headers, json={**rejected, "motivo": "  "}
            )
        ).status_code == 422
        assert (
            await own.post(path + "/parecer", headers=own_headers, json=rejected)
        ).status_code == 403
        result = await trainer.post(path + "/parecer", headers=headers, json=rejected)
        assert result.status_code == 200 and result.json()["parecer"][
            "instrutor_id"
        ] == str(instructor.user_id)
        assert (
            await trainer.post(path + "/parecer", headers=headers, json=rejected)
        ).json() == result.json()
        assert (
            await trainer.post(
                path + "/parecer",
                headers=headers,
                json=opinion_input("ACEITO").model_dump(mode="json"),
            )
        ).status_code == 409
        assert (await own.get(root + "/atual")).json()["parecer"][
            "estado"
        ] == "REJEITADO"
        assert (await own.get(root + "/atual")).json()["ficha"]["dias"]
        assert (await trainer.get("/api/v1/treinos/pendentes")).json()["total"] == 0
        with sessions.begin() as session:
            notice = session.scalar(
                select(Notification).where(Notification.canal == "EMAIL")
            )
            assert notice and notice.estado == "FALHOU"
            # Trocar o responsável remove a autorização do autor histórico.
            successor = create_account(
                session,
                "sucessor@example.test",
                state=AccountState.ATIVO,
                password_hash=Passwords().hash(_PASSWORD),
                now=utc_now(),
            )
            session.add(
                EmployeeProfile(
                    usuario_id=successor,
                    nome="Sucessor sintético",
                    cargo="Instrutor",
                    ativo=True,
                    data_admissao=_DATE,
                )
            )
            session.add(
                UserRole(id=uuid4(), usuario_id=successor, papel=Role.INSTRUTOR)
            )
            current = session.scalar(
                select(Assignment).where(
                    Assignment.cliente_id == client_id, Assignment.fim.is_(None)
                )
            )
            assert current
            change_assignment(
                session,
                client_id,
                ChangeAssignment(instrutor_id=successor, vigente_id=current.id),
                Actor(actors[Role.ADMINISTRADOR], frozenset({Role.ADMINISTRADOR})),
                uuid4(),
            )
        assert (await trainer.get(path + "/revisao")).status_code == 403
        assert (
            await trainer.post(path + "/parecer", headers=headers, json=rejected)
        ).status_code == 403
        assert (await own.get(root + "/atual")).status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("operation", ["publish", "replay", "reject"])
def test_concurrent_publication_and_rejection(operation: str) -> None:
    engine = create_database_engine("test")
    schema = "trn03_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            actors, instructor, snapshot = workout_people(factory)
            client = actors[Role.CLIENTE]
            with factory.begin() as session:
                session.add(
                    Exercise(
                        id=_BODYWEIGHT,
                        nome="Movimento sintético",
                        nome_normalizado="movimento sintético",
                        descricao="Sintético",
                        grupo_muscular="Grupo",
                        ativo=True,
                        dispensa_equipamento=True,
                        revision=1,
                    )
                )
            with factory.begin() as session:
                previous = None
                # A concorrência também cruza o limiar da 16ª publicação.
                for _ in range(15):
                    previous = draft_and_publish(
                        session, instructor, client, snapshot, previous
                    ).ficha.id
                assert previous
                if operation == "reject":
                    first = draft_and_publish(
                        session, instructor, client, snapshot, previous
                    ).ficha
                    second = draft_and_publish(
                        session, instructor, client, snapshot, first.id
                    ).ficha
                    versions = [first, second]
                else:
                    first = create_draft(
                        session,
                        instructor,
                        client,
                        CreateWorkout.model_validate(
                            manual_payload(snapshot, previous)
                        ),
                        uuid4(),
                    )
                    second = (
                        first
                        if operation == "replay"
                        else create_draft(
                            session,
                            instructor,
                            client,
                            CreateWorkout.model_validate(
                                manual_payload(snapshot, previous)
                            ),
                            uuid4(),
                        )
                    )
                    versions = [first, second]
            request_id = uuid4()
            inputs = [publication_input(version, request_id) for version in versions]
            decisions = [opinion_input("REJEITADO"), opinion_input("REJEITADO")]
            barrier = Barrier(2)

            def perform(index: int) -> int:
                barrier.wait(timeout=10)
                try:
                    with factory.begin() as session:
                        if operation == "reject":
                            record_opinion(
                                session,
                                instructor,
                                client,
                                versions[index].id,
                                decisions[index],
                                uuid4(),
                            )
                        else:
                            publish_manual(
                                session,
                                instructor,
                                client,
                                versions[index].id,
                                inputs[index],
                                uuid4(),
                            )
                    return 200
                except WorkoutError as failure:
                    return failure.status

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(perform, [0, 1])) == (
                    [200, 409] if operation == "publish" else [200, 200]
                )
            with factory.begin() as session:
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(WorkoutVersion)
                        .where(WorkoutVersion.vigente.is_(True))
                    )
                    == 1
                )
                assert session.scalar(
                    select(func.count())
                    .select_from(WorkoutVersion)
                    .where(
                        WorkoutVersion.estado_publicacao.in_(
                            ("PUBLICADO", "SUBSTITUIDO")
                        )
                    )
                ) in range(16)
                if operation == "reject":
                    assert (
                        review_detail(
                            session, instructor, client, versions[0].id
                        ).ficha.dias
                        == []
                    )
                    assert (
                        visible_published(session, instructor, client).ficha.id
                        == versions[1].id
                    )
                    assert visible_published(session, instructor, client).ficha.dias
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_pending_queue_follows_assignment_and_own_read_needs_no_instructor(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        current = session.scalar(
            select(Assignment).where(
                Assignment.cliente_id == client, Assignment.fim.is_(None)
            )
        )
        assert current
        current.fim = utc_now()
        session.flush()
        assert review_queue(session, instructor, 1, 20).total == 0
        own = Actor(client, frozenset({Role.CLIENTE}))
        assert visible_published(session, own, client).parecer.estado == "PENDENTE"
        with pytest.raises(WorkoutError):
            record_opinion(
                session,
                instructor,
                client,
                first.ficha.id,
                opinion_input("ACEITO"),
                uuid4(),
            )
        successor = create_account(
            session,
            "novo-responsavel@example.test",
            state=AccountState.ATIVO,
            password_hash=Passwords().hash(_PASSWORD),
            now=utc_now(),
        )
        session.add(
            EmployeeProfile(
                usuario_id=successor,
                nome="Responsável sintético",
                cargo="Instrutor",
                ativo=True,
                data_admissao=_DATE,
            )
        )
        session.add(UserRole(id=uuid4(), usuario_id=successor, papel=Role.INSTRUTOR))
        change_assignment(
            session,
            client,
            ChangeAssignment(instrutor_id=successor, vigente_id=None),
            Actor(actors[Role.ADMINISTRADOR], frozenset({Role.ADMINISTRADOR})),
            uuid4(),
        )
        next_actor = Actor(successor, frozenset({Role.INSTRUTOR}))
        assert (
            review_queue(session, next_actor, 1, 20).itens[0].versao_id
            == first.ficha.id
        )
        decision = record_opinion(
            session,
            next_actor,
            client,
            first.ficha.id,
            opinion_input("ACEITO"),
            uuid4(),
        )
        assert decision.parecer.instrutor_id == successor


@pytest.mark.integration
def test_catalog_changes_require_resaving_before_publication(
    sessions: sessionmaker[Session],
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        draft = create_draft(
            session,
            instructor,
            client,
            CreateWorkout.model_validate(manual_payload(snapshot)),
            uuid4(),
        )
        session.execute(
            update(Exercise)
            .where(Exercise.id == _BODYWEIGHT)
            .values(revision=2, descricao="Descrição sintética atualizada")
        )
        with pytest.raises(WorkoutError) as error:
            publish_manual(
                session, instructor, client, draft.id, publication_input(draft), uuid4()
            )
        assert error.value.status == 409
        updated = update_draft(
            session,
            instructor,
            client,
            draft.id,
            UpdateWorkout(
                onboarding_id=snapshot,
                revisao=draft.revisao,
                dias=[
                    WorkoutDayInput.model_validate(
                        day.model_dump(
                            exclude={"itens": {"__all__": {"exercicio_snapshot"}}}
                        )
                    )
                    for day in draft.dias
                ],
            ),
            uuid4(),
        )
        published = publish_manual(
            session, instructor, client, draft.id, publication_input(updated), uuid4()
        )
        assert (
            published.ficha.dias[0].itens[0].exercicio_snapshot["catalogo_revisao"] == 2
        )


@pytest.mark.integration
def test_rejection_and_expiry_roll_back_as_one_operation(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actors, instructor, snapshot = workout_people(sessions)
    client = actors[Role.CLIENTE]
    with sessions.begin() as session:
        first = draft_and_publish(session, instructor, client, snapshot)
        record_opinion(
            session,
            instructor,
            client,
            first.ficha.id,
            opinion_input("REJEITADO"),
            uuid4(),
        )
        second = draft_and_publish(
            session, instructor, client, snapshot, first.ficha.id
        )
    from app.modules.audit.service import record_audit as original

    def fail_after_expiry(session: Session, event: AuditEvent) -> bool:
        if event.action == "workout.rejected":
            raise RuntimeError("Falha sintética após expurgo")
        return original(session, event)

    request = opinion_input("REJEITADO")
    with monkeypatch.context() as scoped_patch:
        scoped_patch.setattr(
            "app.modules.training.publication.record_audit", fail_after_expiry
        )
        with pytest.raises(RuntimeError), sessions.begin() as session:
            record_opinion(
                session, instructor, client, second.ficha.id, request, uuid4()
            )
    with sessions.begin() as session:
        assert review_detail(session, instructor, client, first.ficha.id).ficha.dias
        assert (
            review_detail(session, instructor, client, second.ficha.id).parecer.estado
            == "PENDENTE"
        )
        record_opinion(session, instructor, client, second.ficha.id, request, uuid4())
        assert (
            review_detail(session, instructor, client, first.ficha.id).ficha.dias == []
        )
        # Replay da publicação antiga não ressuscita conteúdo ou promove a vigente.
        validation = session.get(WorkoutValidation, first.ficha.id)
        assert validation
        repeated = publish_manual(
            session,
            instructor,
            client,
            first.ficha.id,
            publication_input(first.ficha, validation.solicitacao_id),
            uuid4(),
        )
        assert repeated.ficha.dias == []
        assert (
            visible_published(session, instructor, client).ficha.id == second.ficha.id
        )

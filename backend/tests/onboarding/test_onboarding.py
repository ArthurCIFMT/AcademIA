import json
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, delete, inspect, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
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
from app.modules.onboarding.models import Evaluation, OnboardingVersion
from app.modules.onboarding.schemas import Completion, DraftChange, DraftData
from app.modules.onboarding.service import (
    OnboardingError,
    age_at,
    append_evaluation,
    complete_draft,
    get_snapshot,
    is_current_snapshot,
    save_draft,
)
from app.modules.people.profiles import ClientProfile, EmployeeProfile

_ROOT = Path(__file__).resolve().parents[3]
_FORM: dict[str, object] = json.loads(
    (_ROOT / "docs/testes/contratos-onboarding-v1.json").read_text("utf-8")
)["casos"][0]["entrada"]
_ORIGIN = "https://academia.example.test"
_API = "/api/v1/onboarding/meu"
_PASSWORD = "senha-sintetica-onb02"
_BIRTH = date(1995, 1, 1)


@dataclass(frozen=True)
class People:
    client: UUID
    other: UUID
    instructor: UUID


def _seed(factory: sessionmaker[Session]) -> People:
    password = Passwords().hash(_PASSWORD)
    with factory.begin() as session:

        def add(name: str, role: Role) -> UUID:
            user_id = create_account(
                session,
                f"{name}@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=utc_now(),
            )
            session.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
            if role == Role.CLIENTE:
                session.add(
                    ClientProfile(
                        usuario_id=user_id,
                        nome=name,
                        data_nascimento=_BIRTH,
                        ativo=True,
                    )
                )
            else:
                session.add(
                    EmployeeProfile(
                        usuario_id=user_id,
                        nome=name,
                        cargo=role,
                        data_admissao=date(2026, 1, 1),
                        ativo=True,
                    )
                )
            return user_id

        return People(
            add("cliente", Role.CLIENTE),
            add("outro", Role.CLIENTE),
            add("instrutor", Role.INSTRUTOR),
        )


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


@pytest.fixture
def sessions(migration: tuple[Connection, Config]) -> sessionmaker[Session]:
    connection, config = migration
    command.upgrade(config, "head")
    return create_session_factory(connection)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_age_changes_on_birthday() -> None:
    assert age_at(_BIRTH, date(2025, 12, 31)) == 30
    assert age_at(_BIRTH, date(2026, 1, 1)) == 31


def test_openapi_exposes_own_scope_and_confirm_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert "get" in paths[_API]
    assert "patch" in paths[_API + "/rascunho"]
    assert "201" in paths[_API + "/atualizacoes"]["post"]["responses"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_own_draft_completion_and_version_confirmation(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    people = _seed(sessions)
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as client:

        async def login(email: str) -> str:
            client.cookies.clear()
            result = await client.post(
                "/api/v1/auth/login",
                json={"email": f"{email}@example.test", "senha": _PASSWORD},
            )
            assert result.status_code == 200
            return str(result.json()["csrf_token"])

        assert (await client.get(_API)).status_code == 401
        csrf = await login("cliente")
        assert (await client.get(_API)).json() == {"rascunho": None, "concluido": None}
        body = {
            "versao_base": None,
            "revisao": None,
            "dados": {"altura_cm": 175.2, "usa_medicamentos": None},
        }
        assert (await client.patch(_API + "/rascunho", json=body)).status_code == 403
        headers = {"X-CSRF-Token": csrf}
        partial = await client.patch(_API + "/rascunho", json=body, headers=headers)
        assert partial.status_code == 200
        draft = partial.json()
        assert draft["numero"] == 1 and draft["estado"] == "RASCUNHO"
        assert draft["dados"] == body["dados"]
        assert (await client.get(_API)).json()["rascunho"] == draft
        missing = await client.post(
            _API + "/conclusao",
            json={"versao_base": None, "revisao": draft["revisao"]},
            headers=headers,
        )
        assert missing.status_code == 422
        assert (await client.get(_API)).json()["rascunho"] == draft

        form = {**_FORM, "usa_medicamentos": "NAO_SEI", "altura_cm": 175.2}
        saved = await client.patch(
            _API + "/rascunho",
            json={"versao_base": None, "revisao": draft["revisao"], "dados": form},
            headers=headers,
        )
        assert saved.status_code == 200
        finished = await client.post(
            _API + "/conclusao",
            json={"versao_base": None, "revisao": saved.json()["revisao"]},
            headers=headers,
        )
        assert finished.status_code == 200
        previous = finished.json()
        assert previous["estado"] == "CONCLUIDO" and previous["numero"] == 1
        assert previous["dados"]["usa_medicamentos"] == "NAO_SEI"
        assert previous["concluido_por"] == str(people.client)
        assert previous["concluido_em"].endswith("Z")
        assert finished.headers["Cache-Control"] == "no-store"

        proposed = await client.patch(
            _API + "/rascunho",
            headers=headers,
            json={
                "versao_base": previous["id"],
                "revisao": None,
                "dados": {"peso_kg": 76.1},
            },
        )
        assert proposed.status_code == 200 and proposed.json()["numero"] == 2
        assert proposed.json()["dados"]["usa_medicamentos"] == "NAO_SEI"
        with sessions.begin() as db:
            assert is_current_snapshot(db, people.client, UUID(previous["id"]))

        change = {
            "versao_base": previous["id"],
            "revisao": proposed.json()["revisao"],
            "confirmado": False,
            "dados": proposed.json()["dados"],
        }
        assert (
            await client.post(_API + "/atualizacoes", json=change, headers=headers)
        ).status_code == 422
        confirm = await client.post(
            _API + "/atualizacoes",
            json={**change, "confirmado": True},
            headers=headers,
        )
        assert confirm.status_code == 201
        latest = confirm.json()
        assert latest["id"] != previous["id"] and latest["numero"] == 2
        assert latest["dados"]["peso_kg"] == 76.1
        old_path = _API + "/versoes/" + previous["id"]
        assert (await client.get(old_path)).json() == previous
        assert (await client.get(_API)).json() == {
            "rascunho": None,
            "concluido": latest,
        }
        stale = await client.post(
            _API + "/atualizacoes",
            json={**change, "confirmado": True},
            headers=headers,
        )
        assert stale.status_code == 409
        with sessions.begin() as db:
            assert not is_current_snapshot(db, people.client, UUID(previous["id"]))
            assert is_current_snapshot(db, people.client, UUID(latest["id"]))

        other_csrf = await login("outro")
        assert (await client.get(old_path)).status_code == 404
        assert (await client.get(_API)).json() == {"rascunho": None, "concluido": None}
        forged = await client.patch(
            _API + "/rascunho",
            json={**body, "cliente_id": str(people.client)},
            headers={"X-CSRF-Token": other_csrf},
        )
        assert forged.status_code == 422
        await login("instrutor")
        assert (await client.get(_API)).status_code == 403


@pytest.mark.database
def test_0006_keeps_snapshots_and_evaluations_immutable(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0005")
    command.upgrade(config, "head")
    command.check(config)
    factory = create_session_factory(connection)
    people = _seed(factory)
    with factory.begin() as session:
        draft = save_draft(
            session,
            people.client,
            people.client,
            DraftChange(
                versao_base=None, revisao=None, dados=DraftData.model_validate(_FORM)
            ),
        )
        with pytest.raises(OnboardingError):
            append_evaluation(session, people.client, people.instructor, draft.id, {})
        snapshot = complete_draft(
            session,
            people.client,
            people.client,
            Completion(versao_base=None, revisao=draft.revisao),
        )
        first = append_evaluation(
            session,
            people.client,
            people.instructor,
            snapshot.id,
            {"observacao": "sintética"},
        )
        second = append_evaluation(
            session, people.client, people.instructor, snapshot.id, {}
        )
        assert first.id != second.id and first.registrado_em <= second.registrado_em
        assert get_snapshot(session, people.other, snapshot.id) is None

    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(
            update(OnboardingVersion)
            .where(OnboardingVersion.id == snapshot.id)
            .values(dados={})
        )
    with pytest.raises(DBAPIError, match="imutável"), factory.begin() as session:
        session.execute(delete(Evaluation).where(Evaluation.id == first.id))
    with (
        pytest.raises(IntegrityError, match="fk_avaliacao_onboarding_cliente"),
        factory.begin() as session,
    ):
        session.add(
            Evaluation(
                id=uuid4(),
                cliente_id=people.other,
                instrutor_id=people.instructor,
                onboarding_id=snapshot.id,
                registrado_em=utc_now(),
                dados={},
            )
        )
    command.downgrade(config, "0005")
    assert not inspect(connection).has_table("onboarding_versao", schema="academia")
    assert inspect(connection).has_table("designacao", schema="academia")


@pytest.mark.integration
def test_concurrent_edits_cannot_replace_each_other() -> None:
    engine = create_database_engine("test")
    schema = "onb02_" + uuid4().hex
    try:
        with engine.begin() as connection:
            check_database(connection, "test")
            connection.execute(CreateSchema(schema))
        try:
            scoped = engine.execution_options(schema_translate_map={"academia": schema})
            Base.metadata.create_all(scoped)
            factory = create_session_factory(scoped)
            client = _seed(factory).client
            with factory.begin() as session:
                draft = save_draft(
                    session,
                    client,
                    client,
                    DraftChange(versao_base=None, revisao=None, dados=DraftData()),
                )
            barrier = Barrier(2)

            def edit(weight: float) -> int:
                barrier.wait(timeout=5)
                try:
                    with factory.begin() as session:
                        save_draft(
                            session,
                            client,
                            client,
                            DraftChange(
                                versao_base=None,
                                revisao=draft.revisao,
                                dados=DraftData(peso_kg=weight),
                            ),
                        )
                except OnboardingError as exc:
                    return exc.status
                return 200

            with ThreadPoolExecutor(max_workers=2) as pool:
                assert sorted(pool.map(edit, [75.1, 75.2])) == [200, 409]
            with factory.begin() as session:
                only = session.scalars(select(OnboardingVersion)).one()
                assert only.revision == 2 and only.dados["peso_kg"] in (75.1, 75.2)
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

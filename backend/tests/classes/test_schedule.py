from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.audit.models import AuditRecord
from app.modules.classes.service import ClassFields
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile

_ADMIN = "/api/v1/admin/aulas"
_PUBLIC = "/api/v1/aulas"
_ORIGIN = "https://academia.example.test"
_PASSWORD = "senha-sintetica-aul01"
_NOW = datetime.now(UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def migration() -> Iterator[tuple[Connection, Config]]:
    engine = create_database_engine("test")
    config = Config(
        str(Path(__file__).resolve().parents[3] / "database" / "alembic.ini")
    )
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                check_database(connection, "test")
                config.attributes.update(connection=connection, database_target="test")
                yield connection, config
            finally:
                outer.rollback()
    finally:
        engine.dispose()


def _email(role: Role) -> str:
    return role.value.lower() + "@example.test"


def _class(days: int, name: str = "Aula sintética") -> dict[str, str]:
    start = _NOW + timedelta(days=days)
    return {
        "solicitacao_id": str(uuid4()),
        "nome": name,
        "inicio": start.isoformat(),
        "fim": (start + timedelta(hours=1)).isoformat(),
    }


def test_offset_is_normalized_and_midnight_can_follow_start() -> None:
    data = ClassFields(
        nome="  Aula noturna ",
        inicio=datetime.fromisoformat("2030-02-01T23:30:00-03:00"),
        fim=datetime.fromisoformat("2030-02-02T00:15:00-03:00"),
    )
    assert data.nome == "Aula noturna"
    assert data.inicio == datetime(2030, 2, 2, 2, 30, tzinfo=UTC)
    assert data.fim == datetime(2030, 2, 2, 3, 15, tzinfo=UTC)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2030-02-30T09:00:00-03:00", "2030-03-01T10:00:00-03:00"),
        ("2030-02-01T09:00:00", "2030-02-01T10:00:00-03:00"),
        (1896192000, "2030-02-01T10:00:00-03:00"),
        ("1896192000", "2030-02-01T10:00:00-03:00"),
        ("2030-02-01T09:00:00-03:00", "2030-02-01T12:00:00Z"),
        ("2030-02-01T09:00:00-03:00", "2030-02-01T11:00:00Z"),
        ("0001-01-01T00:00:00+03:00", "2030-02-01T10:00:00-03:00"),
        ("2030-02-01T09:00:00-03:00", "9999-12-31T23:59:59-03:00"),
    ],
)
def test_invalid_dates_and_intervals_are_rejected(start: str | int, end: str) -> None:
    with pytest.raises(ValueError):
        ClassFields.model_validate({"nome": "Aula", "inicio": start, "fim": end})


def test_contract_documents_utc_input_and_admin_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    spec = create_app().openapi()
    schemas = spec["components"]["schemas"]
    assert schemas["CreateClass"]["properties"]["inicio"]["format"] == "date-time"
    assert "revisao" not in schemas["PublicClass"]["properties"]
    assert set(spec["paths"][_PUBLIC]) == {"get"}
    assert "201" in spec["paths"][_ADMIN]["post"]["responses"]
    assert "409" in spec["paths"][_ADMIN + "/{occurrence_id}"]["put"]["responses"]
    assert (
        "403"
        in spec["paths"][_ADMIN + "/{occurrence_id}/cancelamento"]["post"]["responses"]
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_agenda_routes_update_public_list_and_preserve_cancelled_history(
    migration: tuple[Connection, Config],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    connection, config = migration
    command.upgrade(config, "head")
    sessions = create_session_factory(connection)
    password_hash = Passwords().hash(_PASSWORD)
    with sessions.begin() as db:
        for role in Role:
            user_id = create_account(
                db,
                _email(role),
                state=AccountState.ATIVO,
                password_hash=password_hash,
                now=_NOW,
            )
            db.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
            db.add(
                ClientProfile(
                    usuario_id=user_id,
                    nome="Cliente de teste",
                    data_nascimento=date(1990, 1, 1),
                    ativo=True,
                )
                if role == Role.CLIENTE
                else EmployeeProfile(
                    usuario_id=user_id,
                    nome="Funcionário de teste",
                    cargo=role.value,
                    data_admissao=_NOW.date(),
                    ativo=True,
                )
            )

    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as api:
        new = _class(2)
        assert (await api.get(_PUBLIC)).json()["total"] == 0
        assert (await api.get(_ADMIN)).status_code == 401
        assert (await api.post(_ADMIN, json=new)).status_code == 401
        for role in Role:
            api.cookies.clear()
            login = await api.post(
                "/api/v1/auth/login", json={"email": _email(role), "senha": _PASSWORD}
            )
            assert login.status_code == 200
            csrf = {"X-CSRF-Token": login.json()["csrf_token"]}
            if role != Role.ADMINISTRADOR:
                assert (await api.get(_ADMIN)).status_code == 403
                assert (
                    await api.post(_ADMIN, json=new, headers=csrf)
                ).status_code == 403

        api.cookies.clear()
        admin = await api.post(
            "/api/v1/auth/login",
            json={"email": _email(Role.ADMINISTRADOR), "senha": _PASSWORD},
        )
        headers = {"X-CSRF-Token": admin.json()["csrf_token"]}
        assert (await api.post(_ADMIN, json=new)).status_code == 403
        assert (
            await api.post(_ADMIN, json={**new, "fim": new["inicio"]}, headers=headers)
        ).status_code == 422
        created = await api.post(_ADMIN, json=new, headers=headers)
        assert created.status_code == 201
        original = created.json()
        route = _ADMIN + "/" + original["id"]
        assert (await api.post(_ADMIN, json=new, headers=headers)).json() == original
        assert (
            await api.post(_ADMIN, json={**new, "nome": "Outro"}, headers=headers)
        ).status_code == 409
        assert (
            await api.post(_ADMIN, json=_class(-2, "Concluída"), headers=headers)
        ).status_code == 201
        other = await api.post(
            _ADMIN, json=_class(4, "Aula posterior"), headers=headers
        )
        assert other.status_code == 201
        visible = await api.get(_PUBLIC, params={"limite": 1})
        assert visible.headers["Cache-Control"] == "no-store"
        assert visible.json()["total"] == 2
        (card,) = visible.json()["itens"]
        assert (
            card["id"] == original["id"]
            and "revisao" not in card
            and "estado" not in card
        )

        changed = {
            "nome": "Pilates de teste",
            "inicio": (_NOW + timedelta(days=3)).isoformat(),
            "fim": (_NOW + timedelta(days=3, hours=1)).isoformat(),
            "revisao": 1,
        }
        assert (await api.put(route, json=changed, headers=headers)).json()[
            "revisao"
        ] == 2
        assert (await api.put(route, json=changed, headers=headers)).status_code == 409
        assert (await api.get(_PUBLIC)).json()["itens"][0]["nome"] == changed["nome"]
        cancellation = route + "/cancelamento"
        assert (
            await api.post(cancellation, json={"revisao": 1}, headers=headers)
        ).status_code == 409
        cancelled = await api.post(cancellation, json={"revisao": 2}, headers=headers)
        entry = cancelled.json()
        assert cancelled.status_code == 200 and entry["estado"] == "CANCELADA"
        assert (
            await api.post(cancellation, json={"revisao": 3}, headers=headers)
        ).json() == entry
        assert (
            await api.put(route, json={**changed, "revisao": 3}, headers=headers)
        ).status_code == 409
        history = (await api.get(_ADMIN)).json()
        assert history["total"] == 3 and entry in history["itens"]
        api.cookies.clear()
        assert (await api.get(_PUBLIC)).json()["total"] == 1
        assert (await api.get(_PUBLIC)).json()["itens"][0]["nome"] == "Aula posterior"

    with sessions.begin() as db:
        actions = db.scalars(
            select(AuditRecord.acao).where(
                AuditRecord.recurso_id == UUID(original["id"])
            )
        ).all()
        assert sorted(actions) == ["class.cancelled", "class.created", "class.updated"]


@pytest.mark.database
def test_occurrence_migration_and_database_interval_constraint(
    migration: tuple[Connection, Config],
) -> None:
    conn, config = migration
    command.upgrade(config, "0017")
    assert not inspect(conn).has_table("aula_ocorrencia", schema="academia")
    command.upgrade(config, "0018")
    with pytest.raises(IntegrityError, match="ck_aula_intervalo"), conn.begin_nested():
        conn.execute(
            text(
                "INSERT INTO academia.aula_ocorrencia "
                "(id, nome, inicio, fim, estado, revision) "
                "VALUES (:id, 'Aula', :now, :now, 'AGENDADA', 1)"
            ),
            {"id": uuid4(), "now": _NOW},
        )
    command.downgrade(config, "0017")
    assert not inspect(conn).has_table("aula_ocorrencia", schema="academia")
    command.upgrade(config, "0018")
    assert inspect(conn).has_table("aula_ocorrencia", schema="academia")

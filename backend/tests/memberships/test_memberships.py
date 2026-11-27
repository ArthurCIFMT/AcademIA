from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.contracts.time import academy_date
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
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.schemas import CreateMembership
from app.modules.memberships.service import membership_situation, valid_membership
from app.modules.people.profiles import ClientProfile, EmployeeProfile

_PLANS = "/api/v1/admin/planos"
_ACTIVE = "/api/v1/atendimento/planos"
_ORIGIN = "https://academia.example.test"
_PASSWORD = "senha-sintetica-mem01"
_NOW = datetime.now(UTC)


def _history(client_id: UUID) -> str:
    return f"/api/v1/atendimento/clientes/{client_id}/matriculas"


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


@pytest.mark.parametrize(
    ("instant", "closed", "expected"),
    [
        (datetime(2026, 11, 24, 2, 59, tzinfo=UTC), False, "FUTURA"),
        (datetime(2026, 11, 24, 3, 0, tzinfo=UTC), False, "VIGENTE"),
        (datetime(2026, 11, 26, 2, 59, tzinfo=UTC), False, "VIGENTE"),
        (datetime(2026, 11, 26, 3, 0, tzinfo=UTC), False, "VENCIDA"),
        (datetime(2026, 11, 24, 3, 0, tzinfo=UTC), True, "ENCERRADA"),
    ],
)
def test_civil_membership_boundaries(
    instant: datetime, closed: bool, expected: str
) -> None:
    assert (
        membership_situation(
            start=date(2026, 11, 24),
            end=date(2026, 11, 25),
            closed=closed,
            on=academy_date(instant),
        )
        == expected
    )


@pytest.mark.parametrize(
    "value", ["2026-02-30", "2026-01-01T00:00:00Z", "20260101", 1790000000]
)
def test_input_requires_an_iso_civil_date(value: str | int) -> None:
    with pytest.raises(ValueError):
        CreateMembership.model_validate(
            dict(
                solicitacao_id=uuid4(), plano_id=uuid4(), plano_revisao=1, inicio=value
            )
        )


def test_openapi_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    spec = create_app().openapi()
    schemas = spec["components"]["schemas"]
    assert schemas["CreateMembership"]["properties"]["inicio"]["format"] == "date"
    assert set(schemas["CreateMembership"]["properties"]) == {
        "solicitacao_id",
        "plano_id",
        "plano_revisao",
        "inicio",
    }
    assert schemas["CreateMembership"]["additionalProperties"] is False
    assert set(spec["paths"][_ACTIVE]) == {"get"}
    assert "409" in spec["paths"][_PLANS + "/{plan_id}"]["put"]["responses"]
    assert (
        "201"
        in spec["paths"]["/api/v1/atendimento/clientes/{client_id}/matriculas"]["post"][
            "responses"
        ]
    )


def _email(role: Role) -> str:
    return f"mem01-{role.value.lower()}@example.test"


async def _login(api: httpx.AsyncClient, role: Role) -> dict[str, str]:
    api.cookies.clear()
    response = await api.post(
        "/api/v1/auth/login", json={"email": _email(role), "senha": _PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.parametrize("financial_state", [None, "PENDENTE", "RECUSADO"])
async def test_attendant_enrolls_and_renews_without_financial_dependency(
    migration: tuple[Connection, Config],
    monkeypatch: pytest.MonkeyPatch,
    financial_state: str | None,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Teste")
    connection, config = migration
    command.upgrade(config, "head")
    financial_tables = {"pagamento", "cobranca_revisao", "cobranca"}
    if financial_state is None:
        check_database(connection, "test")
        connection.exec_driver_sql("DROP TABLE academia.pagamento RESTRICT")
        connection.exec_driver_sql("DROP TABLE academia.cobranca_revisao RESTRICT")
        connection.exec_driver_sql("DROP TABLE academia.cobranca RESTRICT")
    tables = set(inspect(connection).get_table_names(schema="academia"))
    expected_financial_tables = set() if financial_state is None else financial_tables
    assert tables & financial_tables == expected_financial_tables
    sessions = create_session_factory(connection)
    password = Passwords().hash(_PASSWORD)
    ids = {}
    today = academy_date(_NOW)
    with sessions.begin() as db:
        for role in Role:
            user_id = create_account(
                db,
                _email(role),
                state=AccountState.ATIVO,
                password_hash=password,
                now=_NOW,
            )
            ids[role] = user_id
            db.add(UserRole(id=uuid4(), usuario_id=user_id, papel=role))
            if role == Role.CLIENTE:
                db.add(
                    ClientProfile(
                        usuario_id=user_id,
                        nome="Cliente sintético",
                        data_nascimento=date(1990, 1, 1),
                        ativo=True,
                    )
                )
            else:
                db.add(
                    EmployeeProfile(
                        usuario_id=user_id,
                        nome="Funcionário sintético",
                        cargo=role.value,
                        data_admissao=today,
                        ativo=True,
                    )
                )
    client_id = ids[Role.CLIENTE]
    path = _history(client_id)
    plan_fields = {
        "nome": "Plano sintético",
        "modalidade": "Musculação",
        "duracao_dias": 2,
        "limite_acessos": 2,
        "ativo": True,
    }
    plan_data = {"solicitacao_id": str(uuid4()), **plan_fields}
    first_request = {
        "solicitacao_id": str(uuid4()),
        "plano_id": plan_data["solicitacao_id"],
        "plano_revisao": 1,
        "inicio": today.isoformat(),
    }
    app = create_app(
        identity_sessions=sessions, auth_settings=AuthSettings(origin=_ORIGIN)
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as api:
        assert (await api.get(path)).status_code == 401
        assert (await api.post(path, json=first_request)).status_code == 401
        for role in (Role.ADMINISTRADOR, Role.CLIENTE, Role.INSTRUTOR):
            headers = await _login(api, role)
            assert (await api.get(path)).status_code == 403
            assert (
                await api.post(path, json=first_request, headers=headers)
            ).status_code == 403
            if role != Role.ADMINISTRADOR:
                assert (
                    await api.post(_PLANS, json=plan_data, headers=headers)
                ).status_code == 403

        admin = await _login(api, Role.ADMINISTRADOR)
        assert (await api.post(_PLANS, json=plan_data)).status_code == 403
        plan = await api.post(_PLANS, json=plan_data, headers=admin)
        assert plan.status_code == 201, plan.text
        plan_url = _PLANS + "/" + plan.json()["id"]
        if financial_state is not None:
            charge_id = uuid4()
            connection.execute(
                text("""
                    INSERT INTO academia.cobranca (
                        id, cliente_id, competencia, vencimento, valor, estado, revisao
                    ) VALUES (:id, :client, :month, :due, 10.00, 'ABERTA', 1)
                """),
                {
                    "id": charge_id,
                    "client": client_id,
                    "month": today.replace(day=1),
                    "due": today - timedelta(days=1),
                },
            )
            connection.execute(
                text("""
                    INSERT INTO academia.pagamento
                        (id, cliente_id, plano_id, cobranca_id, origem, estado, valor)
                    VALUES (:id, :client, :plan, :charge, 'ENSAIO', :state, 10.00)
                """),
                {
                    "id": uuid4(),
                    "client": client_id,
                    "plan": UUID(plan.json()["id"]),
                    "charge": charge_id,
                    "state": financial_state,
                },
            )
        attendant = await _login(api, Role.ATENDENTE)
        assert (await api.get(_PLANS)).status_code == 403
        assert (await api.get(_ACTIVE)).json()["itens"] == [plan.json()]
        assert (await api.get(path)).json()["total"] == 0
        assert (
            await api.post(
                _history(ids[Role.INSTRUTOR]), json=first_request, headers=attendant
            )
        ).status_code == 404
        assert (await api.post(path, json=first_request)).status_code == 403
        for unwanted in ("PENDENTE", "RECUSADO", "INDISPONIVEL"):
            injected = {**first_request, "situacao_pagamento": unwanted}
            assert (
                await api.post(path, json=injected, headers=attendant)
            ).status_code == 422
        created = await api.post(path, json=first_request, headers=attendant)
        assert created.status_code == 201, created.text
        original = created.json()
        assert original["fim"] == (today + timedelta(days=1)).isoformat()
        assert original["atendente_id"] == str(ids[Role.ATENDENTE])
        assert original["situacao"] == "VIGENTE"
        assert original["limites_snapshot"] == {
            "limite_acessos": 2,
            "janela_limite": "DIA_CIVIL",
        }
        assert (
            await api.post(path, json=first_request, headers=attendant)
        ).json() == original

        admin = await _login(api, Role.ADMINISTRADOR)
        later_fields = {**plan_fields, "modalidade": "Aulas", "limite_acessos": None}
        edited = await api.put(
            plan_url, json={**later_fields, "revisao": 1}, headers=admin
        )
        assert edited.json()["revisao"] == 2
        assert (
            await api.put(plan_url, json={**plan_fields, "revisao": 1}, headers=admin)
        ).status_code == 409
        attendant = await _login(api, Role.ATENDENTE)
        renewal = {
            **first_request,
            "solicitacao_id": str(uuid4()),
            "plano_revisao": 2,
            "inicio": original["fim"],
        }
        overlap = await api.post(path, json=renewal, headers=attendant)
        assert overlap.status_code == 409 and overlap.json()["code"] == "CONFLICT"
        renewal["inicio"] = (today + timedelta(days=2)).isoformat()
        stale = await api.post(
            path, json={**renewal, "plano_revisao": 1}, headers=attendant
        )
        assert stale.status_code == 409 and stale.json()["code"] == "CONFLICT"
        renewed = await api.post(path, json=renewal, headers=attendant)
        assert renewed.status_code == 201, renewed.text
        new = renewed.json()
        assert new["situacao"] == "FUTURA"
        assert new["limites_snapshot"] == {
            "limite_acessos": None,
            "janela_limite": None,
        }

        admin = await _login(api, Role.ADMINISTRADOR)
        assert (
            await api.put(
                plan_url,
                json={**later_fields, "revisao": 2, "ativo": False},
                headers=admin,
            )
        ).status_code == 200
        attendant = await _login(api, Role.ATENDENTE)
        assert (await api.get(_ACTIVE)).json()["total"] == 0
        new_request = {
            **renewal,
            "solicitacao_id": str(uuid4()),
            "plano_revisao": 3,
            "inicio": (today + timedelta(days=4)).isoformat(),
        }
        denied = await api.post(path, json=new_request, headers=attendant)
        assert denied.status_code == 409 and denied.json()["code"] == "CONFLICT"
        assert (
            await api.post(path, json=first_request, headers=attendant)
        ).json() == original
        assert (await api.get(path)).json()["itens"] == [new, original]

    with sessions.begin() as db:
        active = valid_membership(db, client_id, at=_NOW)
        assert (
            active
            and str(active.id) == original["id"]
            and active.modalidade == "Musculação"
        )
        assert active.limites.limite_acessos == 2
        next_period = datetime.combine(today + timedelta(days=2), time(15), UTC)
        active_next = valid_membership(db, client_id, at=next_period)
        assert (
            active_next
            and active_next.modalidade == "Aulas"
            and active_next.limites.limite_acessos is None
        )
        for instant in (_NOW - timedelta(days=1), _NOW + timedelta(days=5)):
            assert valid_membership(db, client_id, at=instant) is None
        assert valid_membership(db, uuid4(), at=_NOW) is None
        audit = db.scalars(
            select(AuditRecord).where(AuditRecord.recurso_tipo == "matricula")
        ).all()
        assert len(audit) == 2
        assert {event.acao for event in audit} == {
            "matricula.criada",
            "matricula.renovada",
        }
        assert {event.ator_id for event in audit} == {ids[Role.ATENDENTE]}


@pytest.mark.database
def test_migration_roundtrip_and_database_constraints(
    migration: tuple[Connection, Config],
) -> None:
    connection, config = migration
    command.upgrade(config, "0019")
    assert {
        fk["referred_table"]
        for fk in inspect(connection).get_foreign_keys("matricula", schema="academia")
    } == {"cliente", "plano", "funcionario"}
    insert = text("""
        INSERT INTO academia.plano
            (id, nome, modalidade, duracao_dias, limite_acessos,
             janela_limite, ativo, revision)
        VALUES (:id, 'Plano', 'Musculação', :days, :limit, :window, true, 1)
    """)
    for days, limit, window in (
        (0, None, None),
        (1, 0, "DIA_CIVIL"),
        (1, 2, None),
        (1, None, "DIA_CIVIL"),
    ):
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert, {"id": uuid4(), "days": days, "limit": limit, "window": window}
            )
    command.downgrade(config, "0018")
    schema = inspect(connection)
    assert not schema.has_table("matricula", schema="academia")
    assert not schema.has_table("plano", schema="academia")
    assert schema.has_table("aula_ocorrencia", schema="academia")
    command.upgrade(config, "0019")
    assert inspect(connection).has_table("matricula", schema="academia")

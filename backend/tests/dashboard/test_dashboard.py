from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from app.core.http import install_http_contract
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.access.attendance.models import Presence
from app.modules.access.attendance.service import AttendanceHour
from app.modules.access.events.models import AccessEvent
from app.modules.dashboard import service
from app.modules.dashboard.http import dashboard_router
from app.modules.identity.accounts import create_account
from app.modules.identity.composition import install_identity
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.models import Membership, Plan
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from tests.access.conftest import migration as migration

AT = datetime(2026, 11, 24, 2, 30, tzinfo=UTC)
ORIGIN = "https://academia.example.test"
ROUTE = "/api/v1/admin/dashboard"
PASSWORD = "senha-sintetica-dashboard"


def test_frequency_uses_four_weeks_and_seven_civil_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def visits(
        _db: Session, start: date, *, through: datetime
    ) -> tuple[AttendanceHour, ...]:
        assert start == date(2026, 11, 2)
        assert through == AT
        return (
            AttendanceHour(date(2026, 11, 2), 0, 1),
            AttendanceHour(date(2026, 11, 22), 23, 2),
            AttendanceHour(date(2026, 11, 23), 0, 3),
            AttendanceHour(date(2026, 11, 23), 23, 4),
        )

    monkeypatch.setattr(service, "confirmed_visits_by_hour", visits)
    with Session() as db:
        result = service.frequency(db, AT)
    assert [week.visitas for week in result.semanas] == [1, 0, 2, 7]
    assert [day.visitas for day in result.dias] == [0, 0, 0, 0, 0, 2, 7]
    assert result.dias[-1].data == date(2026, 11, 23)
    assert [(h.hora, h.visitas) for h in result.dias[-1].por_hora] == [(0, 3), (23, 4)]


def test_dashboard_openapi_is_wired_to_the_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    spec = create_app().openapi()
    operation = spec["paths"][ROUTE]["get"]
    assert {"200", "401", "403"} <= operation["responses"].keys()
    assert set(spec["components"]["schemas"]["DashboardOverview"]["properties"]) == {
        "consultado_em",
        "clientes_ativos",
        "clientes_matriculados",
        "funcionarios",
        "lotacao",
        "frequencia",
        "financeiro",
    }


def seed_people(db: Session) -> dict[str, UUID]:
    password_hash = Passwords().hash(PASSWORD)
    cases = [
        ("admin", Role.ADMINISTRADOR, AccountState.ATIVO, True),
        ("atendente", Role.ATENDENTE, AccountState.ATIVO, True),
        ("instrutor", Role.INSTRUTOR, AccountState.ATIVO, True),
        ("ex-funcionario", Role.INSTRUTOR, AccountState.INATIVO, False),
        ("cliente", Role.CLIENTE, AccountState.ATIVO, True),
        ("convidado", Role.CLIENTE, AccountState.CONVIDADO, True),
        ("perfil-inativo", Role.CLIENTE, AccountState.ATIVO, False),
        ("conta-inativa", Role.CLIENTE, AccountState.INATIVO, True),
    ]
    ids = {}
    for name, role, account_state, active in cases:
        key = create_account(
            db,
            f"{name}@example.test",
            state=account_state,
            password_hash=password_hash,
            now=AT,
        )
        db.add(UserRole(id=uuid4(), usuario_id=key, papel=role))
        if role == Role.CLIENTE:
            db.add(
                ClientProfile(
                    usuario_id=key,
                    ativo=active,
                    nome=name,
                    data_nascimento=date(1995, 2, 1),
                )
            )
        else:
            db.add(
                EmployeeProfile(
                    usuario_id=key,
                    ativo=active,
                    nome=name,
                    cargo=role.value,
                    data_admissao=date(2026, 1, 1),
                )
            )
        ids[name] = key
    db.flush()
    return ids


def seed_memberships(db: Session, ids: dict[str, UUID]) -> None:
    # Um contrato vigente continua válido mesmo que o plano tenha sido desativado.
    plan_id = uuid4()
    db.add(
        Plan(
            id=plan_id,
            nome="Musculação",
            duracao_dias=1,
            modalidade="Musculação",
            ativo=False,
            revision=1,
        )
    )
    db.flush()
    for name, day, state in [
        ("cliente", 23, "ATIVA"),
        ("convidado", 23, "ATIVA"),
        ("perfil-inativo", 22, "ATIVA"),
        ("conta-inativa", 24, "ATIVA"),
        ("perfil-inativo", 23, "ENCERRADA"),
    ]:
        db.add(
            Membership(
                id=uuid4(),
                cliente_id=ids[name],
                plano_id=plan_id,
                atendente_id=ids["atendente"],
                inicio=date(2026, 11, day),
                fim=date(2026, 11, day),
                estado=state,
                modalidade_contratada="Musculação",
                limites_snapshot={"limite_acessos": None, "janela_limite": None},
            )
        )


def seed_event(db: Session, client: UUID, instant: datetime, *, entry: bool) -> UUID:
    event_id = uuid4()
    db.add(
        AccessEvent(
            id=event_id,
            origem="CATRACA_SIMULADA",
            event_id_externo=str(event_id),
            cliente_id=client,
            tipo="PASSAGEM_SIMULADA",
            ocorrido_em=instant,
            payload_hash="a" * 64,
            direcao="ENTRADA" if entry else "SAIDA",
        )
    )
    return event_id


def seed_visits(db: Session, client: UUID) -> None:
    for iso, closed in [
        ("2026-11-02T02:59:00+00:00", True),
        ("2026-11-02T03:00:00+00:00", True),
        ("2026-11-23T02:50:00+00:00", True),
        (AT.isoformat(), False),
        ("2026-11-24T02:31:00+00:00", True),
    ]:
        at = datetime.fromisoformat(iso)
        entry = seed_event(db, client, at, entry=True)
        exit_ = (
            seed_event(db, client, at + timedelta(minutes=1), entry=False)
            if closed
            else None
        )
        db.flush()
        db.add(
            Presence(
                id=entry,
                entrada_evento_id=entry,
                cliente_id=client,
                saida_evento_id=exit_,
            )
        )
    # Evento técnico sem projeção de presença fica fora dos indicadores.
    seed_event(db, client, AT - timedelta(seconds=1), entry=True)


@pytest.mark.integration
def test_dashboard_counts_and_recovers_from_failed_indicator(
    migration: Connection,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sessions = create_session_factory(migration)
    empty = service.overview(sessions, at=AT).model_dump(mode="json")
    for key in ("clientes_ativos", "clientes_matriculados", "funcionarios", "lotacao"):
        assert empty[key] == {"estado": "DISPONIVEL", "valor": 0}
    assert empty["financeiro"]["valor"]["mes"] == {
        "cobrado": "0.00",
        "recebido": "0.00",
        "pendente": "0.00",
        "vencido": "0.00",
    }

    with sessions.begin() as db:
        ids = seed_people(db)
        seed_memberships(db, ids)
        seed_visits(db, ids["cliente"])

    app = FastAPI()
    install_http_contract(app)
    factory = install_identity(
        app, settings=AuthSettings(origin=ORIGIN), sessions=sessions
    )
    app.include_router(dashboard_router(factory, clock=lambda: AT))

    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as http:

        def login(name: str) -> None:
            http.cookies.clear()
            assert (
                http.post(
                    "/api/v1/auth/login",
                    json={
                        "email": f"{name}@example.test",
                        "senha": PASSWORD,
                    },
                ).status_code
                == 200
            )

        assert http.get(ROUTE).status_code == 401
        for role in ("cliente", "atendente", "instrutor"):
            login(role)
            assert http.get(ROUTE).status_code == 403
        login("admin")
        response = http.get(ROUTE)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        result = response.json()
        assert result["consultado_em"] == "2026-11-24T02:30:00Z"
        for key, expected in (
            ("clientes_ativos", 1),
            ("clientes_matriculados", 2),
            ("funcionarios", 4),
            ("lotacao", 1),
        ):
            assert result[key] == {"estado": "DISPONIVEL", "valor": expected}
        frequency = result["frequencia"]["valor"]
        assert [row["visitas"] for row in frequency["semanas"]] == [1, 0, 1, 1]
        assert [row["visitas"] for row in frequency["dias"]] == [0, 0, 0, 0, 0, 1, 1]
        assert frequency["dias"][-1] == {
            "data": "2026-11-23",
            "visitas": 1,
            "por_hora": [{"hora": 23, "visitas": 1}],
        }
        assert "example.test" not in response.text
        assert str(ids["cliente"]) not in response.text

        def failed_read(db: Session) -> int:
            db.execute(text("SELECT 1 / 0 /* detalhe-sintetico-privado */"))
            raise AssertionError("A consulta deve falhar")

        monkeypatch.setattr(service, "active_client_count", failed_read)
        partial = http.get(ROUTE)
        assert partial.status_code == 200
        assert partial.json() == {
            **result,
            "clientes_ativos": {"estado": "INDISPONIVEL"},
        }
        assert "detalhe-sintetico-privado" not in partial.text + caplog.text

        monkeypatch.setattr(
            service, "financial_overview", lambda db, *, at: failed_read(db)
        )
        finance_failure = http.get(ROUTE)
        assert finance_failure.status_code == 200
        assert finance_failure.json() == {
            **partial.json(),
            "financeiro": {"estado": "INDISPONIVEL"},
        }
        assert "detalhe-sintetico-privado" not in finance_failure.text + caplog.text

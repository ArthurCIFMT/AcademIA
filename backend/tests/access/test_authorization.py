from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from socket import socket
from threading import Barrier, Thread
from time import monotonic, sleep
from uuid import UUID, uuid4

import httpx
import pytest
import uvicorn
from fastapi import FastAPI
from simulators.turnstile.contracts import Settings
from simulators.turnstile.http import create_app as create_simulator
from simulators.turnstile.store import Store
from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.contracts.time import academy_date
from app.core.http import install_http_contract
from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.access.authorization.http import authorization_router
from app.modules.access.authorization.service import (
    academy_window,
    evaluate,
    prepare_decision,
    view_decision,
)
from app.modules.access.events.models import AccessEvent
from app.modules.access.integrations.turnstile.contracts import AccessSettings
from app.modules.identity.accounts import create_account
from app.modules.identity.composition import install_identity
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.schemas import AccessLimits, CreateMembership, CreatePlan
from app.modules.memberships.service import ValidMembership, create_plan, enroll
from app.modules.people.profiles import ClientProfile, EmployeeProfile

NOW = datetime(2026, 11, 24, 15, tzinfo=UTC)
COMMAND = "token_sintetico_de_comando_acs03"
CALLBACK = "token_sintetico_de_retorno_acs03"
PASSWORD = "senha-sintetica-acs03"
ATTENDANT = "atendimento-acs03@example.test"
RETURN_URL = "/api/v1/acesso/catraca/passagens"


@pytest.fixture
def settings() -> AccessSettings:
    return AccessSettings.model_validate(
        {
            "turnstile_command_token": COMMAND + "_local",
            "turnstile_callback_token": CALLBACK + "_local",
            "access_turnstile_timeout_seconds": 0.25,
        }
    )


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, "ENTRADA_PERMITIDA"),
        ({"recognized": False}, "IDENTIDADE_NAO_CONFIRMADA"),
        ({"recent": False}, "IDENTIFICACAO_FORA_DA_JANELA"),
        ({"enabled": False}, "CLIENTE_INABILITADO"),
        ({"membership": None}, "SEM_MATRICULA_VIGENTE"),
        ({"point": "Natação"}, "MODALIDADE_INCOMPATIVEL"),
        ({"used": 1}, "LIMITE_DIARIO"),
        ({"is_exit": True, "enabled": False, "membership": None}, "SAIDA_PERMITIDA"),
    ],
)
def test_decision_table(changes: dict[str, object], expected: str) -> None:
    case = {
        "recognized": True,
        "recent": True,
        "is_exit": False,
        "enabled": True,
        "membership": ValidMembership(
            uuid4(),
            "musculação",
            AccessLimits(limite_acessos=1, janela_limite="DIA_CIVIL"),
        ),
        "point": "Musculação",
        "used": 0,
    }
    from typing import Any

    inputs: Any = case | changes
    assert evaluate(**inputs) == expected


def test_academy_window_links_the_last_minute_to_the_earlier_civil_day() -> None:
    before = datetime(2026, 11, 25, 2, 59, 59, tzinfo=UTC)
    midnight = datetime(2026, 11, 25, 3, tzinfo=UTC)
    assert academy_window(before)[1] == midnight
    assert academy_window(midnight)[0] == midnight


def test_openapi_exposes_distinct_routes_and_callback_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    spec = create_app().openapi()
    operation = spec["paths"][RETURN_URL]["post"]
    assert operation["security"] == [{"RetornoCatraca": []}]
    assert {"200", "201", "401", "409", "410"} <= set(operation["responses"])
    assert "cliente_id" not in spec["components"]["schemas"]["Passage"]["properties"]


def people(db: Session) -> tuple[UUID, UUID]:
    attendee = create_account(
        db,
        ATTENDANT,
        state=AccountState.ATIVO,
        password_hash=Passwords().hash(PASSWORD),
        now=NOW,
    )
    client = create_account(
        db,
        "cliente-acs03@example.test",
        state=AccountState.ATIVO,
        password_hash=Passwords().hash(PASSWORD),
        now=NOW,
    )
    db.add_all(
        [
            UserRole(id=uuid4(), usuario_id=attendee, papel=Role.ATENDENTE),
            UserRole(id=uuid4(), usuario_id=client, papel=Role.CLIENTE),
            EmployeeProfile(
                usuario_id=attendee,
                nome="Atendente",
                cargo="Atendente",
                data_admissao=date(2026, 1, 1),
                ativo=True,
            ),
            ClientProfile(
                usuario_id=client,
                nome="Cliente",
                data_nascimento=date(1999, 1, 1),
                ativo=True,
            ),
        ]
    )
    db.flush()
    return attendee, client


def membership(
    db: Session,
    attendee: UUID,
    client: UUID,
    start: date,
    *,
    modality: str = "Musculação",
    days: int = 2,
) -> UUID:
    plan = create_plan(
        db,
        CreatePlan(
            solicitacao_id=uuid4(),
            nome="Plano",
            modalidade=modality,
            duracao_dias=days,
            limite_acessos=1,
            ativo=True,
        ),
        actor_id=attendee,
        correlation=uuid4(),
    )
    result = enroll(
        db,
        client,
        CreateMembership(
            solicitacao_id=uuid4(),
            plano_id=plan.id,
            plano_revisao=1,
            inicio=start,
        ),
        attendant_id=attendee,
        correlation=uuid4(),
        now=NOW,
    )
    return result.id


def identified(
    db: Session, client: UUID | None, now: datetime, *, direction: str = "ENTRADA"
) -> UUID:
    event_id = uuid4()
    db.add(
        AccessEvent(
            id=event_id,
            origem="ACADEMIA",
            event_id_externo=str(uuid4()),
            cliente_id=client,
            tipo="IDENTIFICACAO",
            ocorrido_em=now,
            payload_hash="a" * 64,
            direcao=direction,
            resultado_identificacao="IDENTIFICADO" if client else "DESCONHECIDO",
            similaridade=0.98 if client else None,
        )
    )
    db.flush()
    return event_id


@pytest.mark.integration
def test_only_active_compatible_memberships_can_authorize(
    migration: Connection,
    settings: AccessSettings,
) -> None:
    sessions = create_session_factory(migration)
    today = academy_date(NOW)
    with sessions.begin() as db:
        attendee, client = people(db)

        def decision(
            client_id: UUID | None, at: datetime = NOW, direction: str = "ENTRADA"
        ) -> str:
            key = identified(db, client_id, at, direction=direction)
            result, _ = prepare_decision(db, key, settings, lambda: at)
            return view_decision(db, result, at).motivo

        assert decision(None) == "IDENTIDADE_NAO_CONFIRMADA"
        assert decision(client) == "SEM_MATRICULA_VIGENTE"
        # Registro financeiro sintético, isolado na transação do teste.
        db.execute(
            text("""
            CREATE TABLE academia.pagamento (cliente_id uuid, estado text)
        """)
        )
        db.execute(
            text("INSERT INTO academia.pagamento VALUES (:id, 'CONFIRMADO')"),
            {"id": client},
        )
        assert decision(client) == "SEM_MATRICULA_VIGENTE"
        membership(db, attendee, client, today - timedelta(days=10))
        assert decision(client) == "SEM_MATRICULA_VIGENTE"
        membership(db, attendee, client, today + timedelta(days=1), modality="Natação")
        assert decision(client) == "SEM_MATRICULA_VIGENTE"
        assert decision(client, NOW + timedelta(days=1)) == "MODALIDADE_INCOMPATIVEL"
        db.get_one(ClientProfile, client).ativo = False
        assert decision(client) == "CLIENTE_INABILITADO"
        assert decision(client, direction="SAIDA") == "SAIDA_PERMITIDA"


@pytest.mark.integration
def test_concurrent_reservations_keep_daily_limit(settings: AccessSettings) -> None:
    engine = create_database_engine("test")
    schema = "acs03_" + uuid4().hex
    with engine.begin() as conn:
        check_database(conn, "test")
        conn.execute(CreateSchema(schema))
    try:
        scoped = engine.execution_options(schema_translate_map={"academia": schema})
        with scoped.begin() as conn:
            Base.metadata.create_all(conn)
        sessions = create_session_factory(scoped)
        with sessions.begin() as db:
            attendee, client = people(db)
            membership(db, attendee, client, academy_date(NOW))
            ids = [identified(db, client, NOW), identified(db, client, NOW)]
        barrier = Barrier(2)

        def solve(event_id: UUID) -> str:
            with sessions.begin() as db:
                barrier.wait(timeout=10)
                key, _ = prepare_decision(db, event_id, settings, lambda: NOW)
                return view_decision(db, key, NOW).motivo

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(solve, ids)) == [
                "ENTRADA_PERMITIDA",
                "LIMITE_DIARIO",
            ]
        after = NOW + timedelta(seconds=settings.access_command_ttl_seconds)
        with sessions.begin() as db:
            result, _ = prepare_decision(
                db,
                identified(db, client, after),
                settings,
                lambda: after,
            )
            assert view_decision(db, result, after).resultado == "ALLOW"
    finally:
        try:
            with engine.begin() as conn:
                conn.execute(DropSchema(schema, cascade=True))
        finally:
            engine.dispose()


@contextmanager
def serve(factory: Callable[[str], FastAPI]) -> Iterator[str]:
    with socket() as listener:
        listener.bind(("127.0.0.1", 0))
        host, port = listener.getsockname()
        url = f"http://{host}:{port}"
        config = uvicorn.Config(
            factory(url), access_log=False, lifespan="off", log_level="warning"
        )
        server = uvicorn.Server(config)
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = monotonic() + 10
            while not server.started and thread.is_alive() and monotonic() < deadline:
                sleep(0.02)
            assert server.started
            yield url
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive()


@pytest.mark.integration
def test_live_authorization_and_confirmed_passage(
    migration: Connection,
    settings: AccessSettings,
    tmp_path: Path,
) -> None:
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        attendee, client = people(db)
        membership(db, attendee, client, academy_date(NOW))
        event_id = identified(db, client, NOW)
        denied_id = identified(db, None, NOW)
        exit_id = identified(db, client, NOW, direction="SAIDA")
    current = NOW
    token, callback_token = COMMAND + "_local", CALLBACK + "_local"

    def backend(url: str) -> FastAPI:
        app = FastAPI()
        install_http_contract(app)
        factory = install_identity(
            app, settings=AuthSettings(origin=url), sessions=sessions
        )
        app.include_router(
            authorization_router(factory, settings, clock=lambda: current)
        )
        return app

    def passages() -> int:
        with sessions.begin() as db:
            return (
                db.scalar(
                    select(func.count())
                    .select_from(AccessEvent)
                    .where(
                        AccessEvent.tipo == "PASSAGEM_SIMULADA",
                    )
                )
                or 0
            )

    def auth_path(event: UUID) -> str:
        return f"/api/v1/atendimento/acessos/{event}/autorizacao"

    with (
        serve(backend) as api_url,
        httpx.Client(
            base_url=api_url,
            headers={"Origin": api_url},
            timeout=5,
            trust_env=False,
        ) as api,
    ):
        cfg = Settings.model_validate(
            {
                "store_path": tmp_path / "sim.sqlite3",
                "command_token": token,
                "callback_token": callback_token,
                "callback_url": api_url + RETURN_URL,
            }
        )
        Store(cfg.store_path).prepare()
        assert api.post(auth_path(event_id)).status_code == 401
        login = api.post(
            "/api/v1/auth/login", json={"email": ATTENDANT, "senha": PASSWORD}
        )
        assert login.status_code == 200, login.text
        staff = {"X-CSRF-Token": login.json()["csrf_token"]}
        with serve(
            lambda _: create_simulator(
                cfg.model_copy(update={"fault": "TIMEOUT"}), clock=lambda: current
            )
        ) as fault:
            settings.turnstile_url = fault
            first = api.post(auth_path(event_id), headers=staff)
            assert first.status_code == 201, first.text
            assert first.json()["resultado"] == "ALLOW"
            command = first.json()["comando"]
            assert command["estado"] == "FALHOU" and command["falha_envio"] == "TIMEOUT"
            assert passages() == 0

        with serve(lambda _: create_simulator(cfg, clock=lambda: current)) as simulator:
            settings.turnstile_url = simulator
            retried = api.post(auth_path(event_id), headers=staff)
            assert retried.status_code == 200
            assert retried.json()["comando"]["request_id"] == command["request_id"]
            assert retried.json()["comando"]["estado"] == "ACEITO"
            denied = api.post(auth_path(denied_id), headers=staff).json()
            assert (
                denied["resultado"] == "DENY"
                and denied["comando"]["estado"] == "ACEITO"
            )
            exit_command = api.post(auth_path(exit_id), headers=staff).json()["comando"]
            assert passages() == 0
            event = {"schema_version": 1, "event_id": str(uuid4())}
            returned = event | {
                "request_id": command["request_id"],
                "occurred_at": NOW.isoformat(),
                "direction": "ENTRY",
                "simulated": True,
            }
            assert api.post(RETURN_URL, json=returned).status_code == 401
            callback = {"Authorization": "Bearer " + callback_token}
            assert (
                api.post(
                    RETURN_URL, json=returned | {"direction": "EXIT"}, headers=callback
                ).status_code
                == 409
            )
            with httpx.Client(
                base_url=simulator,
                headers={"Authorization": "Bearer " + token},
                timeout=5,
                trust_env=False,
            ) as turnstile:

                def trigger(
                    request_id: str, payload: dict[str, object]
                ) -> httpx.Response:
                    return turnstile.post(
                        f"/commands/{request_id}/passages", json=payload
                    )

                assert (
                    trigger(denied["comando"]["request_id"], event).status_code == 409
                )
                assert trigger(command["request_id"], event).status_code == 201
                assert trigger(command["request_id"], event).status_code == 200
                assert passages() == 1
                assert (
                    api.post(RETURN_URL, json=returned, headers=callback).status_code
                    == 200
                )
                assert (
                    api.post(
                        RETURN_URL,
                        json=returned | {"direction": "EXIT"},
                        headers=callback,
                    ).status_code
                    == 409
                )
                current += timedelta(seconds=31)
                assert (
                    trigger(
                        exit_command["request_id"], event | {"event_id": str(uuid4())}
                    ).status_code
                    == 410
                )
                expired = returned | {
                    "event_id": str(uuid4()),
                    "request_id": exit_command["request_id"],
                    "direction": "EXIT",
                }
                assert (
                    api.post(RETURN_URL, json=expired, headers=callback).status_code
                    == 410
                )
            viewed = api.post(auth_path(event_id), headers=staff).json()
            assert viewed["comando"]["estado"] == "CONFIRMADO" and passages() == 1
            with sessions.begin() as db:
                same_day = identified(db, client, current)
            limited = api.post(auth_path(same_day), headers=staff).json()
            assert limited["motivo"] == "LIMITE_DIARIO"
            current = academy_window(current)[1]
            with sessions.begin() as db:
                next_day = identified(db, client, current)
            allowed = api.post(auth_path(next_day), headers=staff).json()
            assert allowed["motivo"] == "ENTRADA_PERMITIDA"
            assert passages() == 1

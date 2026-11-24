from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI
from simulators.turnstile.contracts import Settings
from simulators.turnstile.http import create_app as create_simulator
from simulators.turnstile.store import Store
from sqlalchemy import Connection, func, select

from app.contracts.time import academy_date
from app.core.http import install_http_contract
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.access.authorization.http import authorization_router
from app.modules.access.events.models import AccessEvent
from app.modules.access.integrations.turnstile.contracts import AccessSettings
from app.modules.access.manual.contracts import ManualConfirmation
from app.modules.access.manual.http import manual_access_router
from app.modules.access.manual.models import ManualIdentification
from app.modules.audit.models import AuditRecord
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings
from tests.access.test_authorization import (
    ATTENDANT,
    CALLBACK,
    COMMAND,
    NOW,
    PASSWORD,
    RETURN_URL,
    identified,
    membership,
    people,
    serve,
)

_PATH = "/api/v1/atendimento/acessos/{event_id}/confirmacao-manual"


@pytest.mark.parametrize(
    "changes",
    [
        {"motivo": " \t "},
        {"motivo": "x" * 241},
        {"identidade_confirmada": False},
        {"identidade_confirmada": 1},
        {"direcao": "ENTRADA"},
        {"similaridade": 1.0},
    ],
)
def test_manual_confirmation_requires_explicit_identity_and_reason(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ManualConfirmation.model_validate(
            {
                "cliente_id": uuid4(),
                "motivo": "Documento conferido",
                "identidade_confirmada": True,
                **changes,
            }
        )


def test_manual_openapi_has_protected_confirmation_and_no_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    spec = create_app().openapi()
    assert set(spec["paths"][_PATH]) == {"post"}
    assert {"200", "201", "403", "409", "410", "422"} <= set(
        spec["paths"][_PATH]["post"]["responses"]
    )
    assert set(spec["components"]["schemas"]["ManualConfirmation"]["required"]) == {
        "cliente_id",
        "motivo",
        "identidade_confirmada",
    }


def path(event_id: UUID) -> str:
    return _PATH.format(event_id=event_id)


@pytest.mark.integration
def test_manual_confirmation_preserves_motor_rules_and_audit(
    migration: Connection,
    tmp_path: Path,
) -> None:
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        attendant, client = people(db)
        without_membership = identified(db, None, NOW)
        failure = identified(db, None, NOW)
        after_access = identified(db, None, NOW)
        already_identified = identified(db, client, NOW)
        stale = identified(db, None, NOW - timedelta(seconds=61))

    command_token, callback_token = COMMAND + "_local", CALLBACK + "_local"
    settings = AccessSettings.model_validate(
        {
            "turnstile_command_token": command_token,
            "turnstile_callback_token": callback_token,
            "access_turnstile_timeout_seconds": 2,
            "access_identification_max_age_seconds": 60,
        }
    )

    def backend(url: str) -> FastAPI:
        app = FastAPI()
        install_http_contract(app)
        factory = install_identity(
            app, settings=AuthSettings(origin=url), sessions=sessions
        )
        app.include_router(authorization_router(factory, settings, clock=lambda: NOW))
        app.include_router(manual_access_router(factory, settings, clock=lambda: NOW))
        return app

    payload = {
        "cliente_id": str(client),
        "motivo": "  Documento conferido no balcão  ",
        "identidade_confirmada": True,
    }
    with (
        serve(backend) as origin,
        httpx.Client(
            base_url=origin, headers={"Origin": origin}, trust_env=False, timeout=5
        ) as api,
    ):
        cfg = Settings.model_validate(
            {
                "command_token": command_token,
                "callback_token": callback_token,
                "callback_url": origin + RETURN_URL,
                "store_path": tmp_path / "manual.sqlite3",
            }
        )
        Store(cfg.store_path).prepare()
        assert api.post(path(failure), json=payload).status_code == 401
        login = api.post(
            "/api/v1/auth/login",
            json={
                "email": "cliente-acs03@example.test",
                "senha": PASSWORD,
            },
        )
        assert login.status_code == 200
        assert (
            api.post(
                path(failure),
                json=payload,
                headers={
                    "X-CSRF-Token": login.json()["csrf_token"],
                },
            ).status_code
            == 403
        )
        api.cookies.clear()
        login = api.post(
            "/api/v1/auth/login", json={"email": ATTENDANT, "senha": PASSWORD}
        )
        staff = {"X-CSRF-Token": login.json()["csrf_token"]}
        assert api.post(path(failure), json=payload).status_code == 403
        assert (
            api.post(path(already_identified), json=payload, headers=staff).status_code
            == 409
        )
        assert api.post(path(stale), json=payload, headers=staff).status_code == 410
        assert (
            api.post(
                path(failure), json=payload | {"motivo": ""}, headers=staff
            ).status_code
            == 422
        )
        assert (
            api.post(
                path(failure),
                json=payload | {"cliente_id": str(uuid4())},
                headers=staff,
            ).status_code
            == 404
        )

        with serve(lambda _: create_simulator(cfg, clock=lambda: NOW)) as simulator:
            settings.turnstile_url = simulator
            denied = api.post(path(without_membership), json=payload, headers=staff)
            assert denied.status_code == 201, denied.text
            assert denied.json()["decisao"]["motivo"] == "SEM_MATRICULA_VIGENTE"
            with sessions.begin() as db:
                membership(db, attendant, client, academy_date(NOW))

            allowed = api.post(path(failure), json=payload, headers=staff)
            assert allowed.status_code == 201, allowed.text
            data = allowed.json()
            assert data["origem"] == "ATENDIMENTO_MANUAL"
            assert data["evento_falha_id"] == str(failure)
            decision = data["decisao"]
            assert decision["motivo"] == "ENTRADA_PERMITIDA"
            assert decision["comando"]["estado"] == "ACEITO"
            replay = api.post(path(failure), json=payload, headers=staff)
            assert replay.status_code == 200 and replay.json() == data
            assert (
                api.post(
                    path(failure), json=payload | {"motivo": "Reescrito"}, headers=staff
                ).status_code
                == 409
            )
            assert api.delete(path(failure), headers=staff).status_code == 405

            with httpx.Client(
                base_url=simulator,
                headers={"Authorization": "Bearer " + command_token},
                trust_env=False,
                timeout=5,
            ) as catraca:
                request_id = decision["comando"]["request_id"]
                route = f"/commands/{request_id}/passages"
                passage = {"schema_version": 1, "event_id": str(uuid4())}
                assert catraca.post(route, json=passage).status_code == 201
                assert catraca.post(route, json=passage).status_code == 200

            repeated = api.post(path(failure), json=payload, headers=staff)
            assert repeated.json()["decisao"]["comando"]["estado"] == "CONFIRMADO"
            limited = api.post(path(after_access), json=payload, headers=staff)
            assert limited.json()["decisao"]["motivo"] == "LIMITE_DIARIO"

    with sessions.begin() as db:
        original = db.get_one(AccessEvent, failure)
        assert original.resultado_identificacao == "DESCONHECIDO"
        event_id = UUID(decision["evento_id"])
        manual = db.get_one(ManualIdentification, event_id)
        assert (
            manual.atendente_id == attendant
            and manual.motivo == "Documento conferido no balcão"
        )
        entry = db.scalars(
            select(AuditRecord).where(AuditRecord.recurso_id == event_id)
        ).one()
        assert entry.ator_id == attendant and entry.motivo == "falha_biometria"
        assert (
            db.scalar(
                select(func.count())
                .select_from(AccessEvent)
                .where(
                    AccessEvent.tipo == "PASSAGEM_SIMULADA",
                )
            )
            == 1
        )

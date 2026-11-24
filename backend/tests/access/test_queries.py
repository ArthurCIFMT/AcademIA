from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection

from app.core.http import install_http_contract
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.access.authorization.service import record_passage
from app.modules.access.queries.http import access_queries_router
from app.modules.identity.accounts import create_account
from app.modules.identity.composition import install_identity
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from tests.access.test_attendance import create_passage
from tests.access.test_authorization import ATTENDANT, NOW, PASSWORD, people

ORIGIN = "https://academia.example.test"
OCCUPANCY = "/api/v1/acesso/lotacao"
OWN = "/api/v1/cliente/frequencia"
CLIENTS = "/api/v1/clientes"


def test_openapi_uses_separate_occupancy_and_history_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    spec = create_app().openapi()
    assert set(spec["components"]["schemas"]["OccupancyView"]["properties"]) == {
        "total_presentes"
    }
    assert "422" in spec["paths"][OWN]["get"]["responses"]
    assert CLIENTS + "/{client_id}/frequencia" in spec["paths"]


@pytest.mark.integration
def test_occupancy_and_history_respect_permissions_and_confirmed_passages(
    migration: Connection,
) -> None:
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        attendant, client = people(db)
        profile = db.get_one(ClientProfile, client)
        hire_date = db.get_one(EmployeeProfile, attendant).data_admissao
        for role in (Role.ADMINISTRADOR, Role.INSTRUTOR):
            user_id = create_account(
                db,
                f"{role.value.lower()}@example.test",
                state=AccountState.ATIVO,
                password_hash=Passwords().hash(PASSWORD),
                now=NOW,
            )
            db.add_all(
                [
                    UserRole(id=uuid4(), usuario_id=user_id, papel=role),
                    EmployeeProfile(
                        usuario_id=user_id,
                        nome=role.value,
                        cargo=role.value,
                        data_admissao=hire_date,
                        ativo=True,
                    ),
                ]
            )
        other = create_account(
            db,
            "outro@example.test",
            state=AccountState.ATIVO,
            password_hash=Passwords().hash(PASSWORD),
            now=NOW,
        )
        db.add_all(
            [
                UserRole(id=uuid4(), usuario_id=other, papel=Role.CLIENTE),
                ClientProfile(
                    usuario_id=other,
                    nome="Outro cliente",
                    data_nascimento=profile.data_nascimento,
                    ativo=True,
                ),
            ]
        )
        entry = create_passage(db, client, NOW, entering=True)
        exit_ = create_passage(db, client, NOW + timedelta(seconds=10), entering=False)

    app = FastAPI()
    install_http_contract(app)
    factory = install_identity(
        app, settings=AuthSettings(origin=ORIGIN), sessions=sessions
    )
    app.include_router(access_queries_router(factory, clock=lambda: NOW))
    target = f"{CLIENTS}/{client}/frequencia"

    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as http:

        def login(email: str) -> None:
            http.cookies.clear()
            signed_in = http.post(
                "/api/v1/auth/login", json={"email": email, "senha": PASSWORD}
            )
            assert signed_in.status_code == 200

        assert http.get(OCCUPANCY).status_code == 401
        assert http.get(OWN).status_code == 401
        assert http.get(target).status_code == 401
        login("cliente-acs03@example.test")
        assert http.get(target).status_code == 403
        assert http.get(f"{CLIENTS}/{other}/frequencia").status_code == 403
        assert http.get(OCCUPANCY).json() == {"total_presentes": 0}
        assert http.get(OWN).json()["itens"] == []
        assert http.get(OWN, params={"de": "2026-11-23"}).status_code == 422
        with sessions.begin() as db:
            assert record_passage(db, entry, lambda: NOW)
        occupancy = http.get(OCCUPANCY)
        assert occupancy.json() == {"total_presentes": 1}
        assert occupancy.headers["cache-control"] == "no-store"
        visits = http.get(OWN, params={"de": "2026-11-24", "ate": "2026-11-24"})
        assert visits.headers["cache-control"] == "no-store"
        assert visits.json()["total"] == 1
        assert visits.json()["itens"][0]["entrada_em"].endswith("Z")
        assert visits.json()["itens"][0]["saida_em"] is None
        assert (
            http.get(OWN, params={"de": "2026-11-23", "ate": "2026-11-23"}).json()[
                "total"
            ]
            == 0
        )
        login("outro@example.test")
        assert http.get(OWN, params={"client_id": str(client)}).json()["total"] == 0
        login("instrutor@example.test")
        assert http.get(target).status_code == 403
        assert http.get(OCCUPANCY).json() == {"total_presentes": 1}

        for email in (ATTENDANT, "administrador@example.test"):
            login(email)
            assert http.get(OWN).status_code == 403
            assert http.get(target).json()["itens"] == visits.json()["itens"]
            assert http.get(f"{CLIENTS}/{uuid4()}/frequencia").status_code == 404

        with sessions.begin() as db:
            assert record_passage(db, exit_, lambda: NOW + timedelta(seconds=10))
            assert not record_passage(db, exit_, lambda: NOW + timedelta(seconds=10))
        assert http.get(OCCUPANCY).json() == {"total_presentes": 0}
        items = http.get(target).json()["itens"]
        assert len(items) == 1
        assert items[0]["saida_em"].endswith("Z")

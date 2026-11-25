from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Connection, func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.audit.models import AuditRecord
from app.modules.billing.payments.models import Payment
from app.modules.identity.models import AccountState, User
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.models import Membership
from tests.access.conftest import migration as migration
from tests.dashboard.test_dashboard import ORIGIN, PASSWORD, seed_people

ROUTE = "/api/v1/cliente/compra-simulada"
PLANS = "/api/v1/admin/planos"
PLAN_FIELDS = {
    "nome": "Mensal",
    "duracao_dias": 30,
    "modalidade": "Musculação",
    "ativo": True,
}


def test_checkout_openapi_registers_canonical_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    contract = create_app().openapi()
    paths = contract["paths"]
    assert set(paths[ROUTE]) == {"get", "post"}
    assert "get" in paths[ROUTE + "/planos"]
    assert "get" in paths[ROUTE + "/{purchase_id}"]
    assert set(contract["components"]["schemas"]["SimulatePurchase"]["required"]) == {
        "solicitacao_id",
        "plano_id",
        "resultado",
    }


@pytest.mark.integration
def test_checkout_uses_own_history_server_price_and_idempotency(
    migration: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        people = seed_people(db)
        db.get_one(User, people["convidado"]).estado = AccountState.ATIVO
    app = create_app(
        identity_sessions=sessions,
        auth_settings=AuthSettings(origin=ORIGIN),
    )
    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as http:

        def login(name: str) -> dict[str, str]:
            http.cookies.clear()
            signed = http.post(
                "/api/v1/auth/login",
                json={"email": f"{name}@example.test", "senha": PASSWORD},
            )
            assert signed.status_code == 200
            return {"X-CSRF-Token": signed.json()["csrf_token"]}

        assert http.get(ROUTE).status_code == 401
        admin = login("admin")
        assert http.get(ROUTE + "/planos").status_code == 403
        plans = [
            http.post(
                PLANS,
                headers=admin,
                json={
                    **PLAN_FIELDS,
                    "solicitacao_id": str(uuid4()),
                    "preco_base": price,
                    "ativo": active,
                },
            )
            for price, active in (("129.90", True), (None, True), ("70", False))
        ]
        assert all(plan.status_code == 201 for plan in plans)
        plan_id, unpriced, inactive = (plan.json()["id"] for plan in plans)
        # Clientes anteriores do contrato de planos podem omitir o preço ao editar.
        legacy = http.put(
            f"{PLANS}/{plan_id}", headers=admin, json={**PLAN_FIELDS, "revisao": 1}
        )
        assert legacy.status_code == 200 and legacy.json()["preco_base"] == "129.90"

        own = login("cliente")
        catalog = http.get(ROUTE + "/planos")
        assert catalog.headers["cache-control"] == "no-store"
        assert [item["id"] for item in catalog.json()["itens"]] == [plan_id]
        data = {
            "solicitacao_id": str(uuid4()),
            "plano_id": plan_id,
            "resultado": "CONFIRMADO",
        }
        assert http.post(ROUTE, json=data).status_code == 403
        assert (
            http.post(ROUTE, headers=own, json={**data, "valor": "0"}).status_code
            == 422
        )
        for unavailable in (unpriced, inactive):
            blocked = http.post(
                ROUTE, headers=own, json={**data, "plano_id": unavailable}
            )
            assert blocked.status_code == 409
        confirmed = http.post(ROUTE, headers=own, json=data)
        assert confirmed.status_code == 201
        receipt = confirmed.json()
        assert receipt["valor"] == "129.90" and receipt["simulado"] is True
        assert receipt["confirmado_em"] == receipt["simulado_em"]
        for state in ("PENDENTE", "RECUSADO"):
            outcome = http.post(
                ROUTE,
                headers=own,
                json={**data, "solicitacao_id": str(uuid4()), "resultado": state},
            )
            assert outcome.status_code == 201
            assert outcome.json()["estado"] == state
            assert outcome.json()["confirmado_em"] is None
        assert http.get(ROUTE + "?limite=1").json()["total"] == 3
        assert http.get(ROUTE + "/" + receipt["id"]).json() == receipt
        assert http.get("/api/v1/cliente/cobrancas").json()["total"] == 0
        assert (
            http.post(
                ROUTE, headers=own, json={**data, "resultado": "RECUSADO"}
            ).status_code
            == 409
        )

        someone = login("convidado")
        assert http.get(ROUTE).json()["itens"] == []
        assert http.get(ROUTE + "/" + receipt["id"]).status_code == 404
        assert http.post(ROUTE, headers=someone, json=data).status_code == 409
        admin = login("admin")
        changed = http.put(
            f"{PLANS}/{plan_id}",
            headers=admin,
            json={
                **PLAN_FIELDS,
                "nome": "Novo nome",
                "preco_base": "180",
                "ativo": False,
                "revisao": 1,
            },
        )
        assert changed.status_code == 200
        own = login("cliente")
        replay = http.post(ROUTE, headers=own, json=data)
        assert replay.status_code == 200 and replay.json() == receipt
        assert http.get(ROUTE + "/planos").json()["itens"] == []

    with sessions.begin() as db:
        assert db.scalar(select(func.count()).select_from(Membership)) == 0
        recorded = db.scalars(
            select(Payment).where(Payment.origem == "SIMULACAO")
        ).all()
        assert len(recorded) == 3
        assert sum(item.valor for item in recorded if item.confirmado_em) == Decimal(
            "129.90"
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuditRecord)
                .where(AuditRecord.acao == "pagamento.simulado")
            )
            == 3
        )
        with pytest.raises(IntegrityError), db.begin_nested():
            row = next(item for item in recorded if item.estado == "PENDENTE")
            row.confirmado_em = row.simulado_em
            db.flush()


@pytest.mark.database
def test_checkout_schema_roundtrip_with_no_simulations(migration: Connection) -> None:
    root = Path(__file__).resolve().parents[3]
    cfg = Config(str(root / "database/alembic.ini"))
    cfg.attributes.update(connection=migration, database_target="test")
    command.downgrade(cfg, "0026")
    before = inspect(migration).get_columns("pagamento", schema="academia")
    assert "simulado_em" not in {column["name"] for column in before}
    command.upgrade(cfg, "0027")
    after = inspect(migration).get_columns("pagamento", schema="academia")
    assert {"simulado_em", "plano_nome_snapshot"} <= {
        column["name"] for column in after
    }

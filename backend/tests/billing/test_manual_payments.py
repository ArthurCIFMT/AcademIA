from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import Connection, func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.contracts.time import academy_date
from app.core.http import install_http_contract
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.audit.models import AuditRecord
from app.modules.billing.payments.http import manual_payments_router
from app.modules.billing.payments.models import Payment
from app.modules.billing.payments.schemas import RegisterPayment
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.models import Membership
from app.modules.people.profiles import ClientProfile
from tests.access.conftest import migration as migration
from tests.dashboard.test_dashboard import AT, ORIGIN, PASSWORD, seed_people

PATH = "/api/v1/admin/clientes/{client_id}/pagamentos"


def fields(*, now: datetime = AT) -> dict[str, str]:
    return {
        "solicitacao_id": str(uuid4()),
        "valor": "149.90",
        "metodo": "PIX",
        "pago_em": academy_date(now).isoformat(),
        "referencia_externa": "REF-EXEMPLO-01",
    }


@pytest.mark.parametrize(
    "value", [0.01, "0", "0.00", "-1", "1.999", "10000000000.00", "NaN", "1e2"]
)
def test_payment_amount_requires_a_positive_decimal_string(value: float | str) -> None:
    with pytest.raises(ValidationError):
        RegisterPayment.model_validate({**fields(), "valor": value})


def test_payment_openapi_route_is_connected_to_the_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    paths = create_app().openapi()["paths"]
    assert set(paths[PATH]) == {"get", "post"}
    assert {"200", "201", "403", "409", "422"} <= paths[PATH]["post"][
        "responses"
    ].keys()
    assert PATH + "/{payment_id}/correcao" in paths
    assert PATH + "/{payment_id}/anulacao" in paths


@pytest.mark.integration
def test_manual_payment_lifecycle_is_scoped_idempotent_and_auditable(
    migration: Connection,
) -> None:
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        ids = seed_people(db)

    app = FastAPI()
    install_http_contract(app)
    factory = install_identity(
        app, settings=AuthSettings(origin=ORIGIN), sessions=sessions
    )
    app.include_router(manual_payments_router(factory, clock=lambda: AT))
    path, other = (
        PATH.format(client_id=ids[name]) for name in ("cliente", "convidado")
    )
    data = fields()
    payment_id = data["solicitacao_id"]
    correction_path = path + f"/{payment_id}/correcao"

    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as http:

        def login(name: str) -> dict[str, str]:
            http.cookies.clear()
            result = http.post(
                "/api/v1/auth/login",
                json={
                    "email": name + "@example.test",
                    "senha": PASSWORD,
                },
            )
            assert result.status_code == 200
            return {"X-CSRF-Token": result.json()["csrf_token"]}

        assert http.get(path).status_code == 401
        for role in ("cliente", "atendente", "instrutor"):
            headers = login(role)
            assert http.get(path).status_code == 403
            assert http.post(path, headers=headers, json=data).status_code == 403
        headers = login("admin")
        assert http.get(path).json()["itens"] == []
        assert http.post(path, json=data).status_code == 403
        future = (academy_date(AT) + timedelta(days=1)).isoformat()
        assert (
            http.post(
                path, headers=headers, json=data | {"pago_em": future}
            ).status_code
            == 422
        )
        assert (
            http.post(
                path, headers=headers, json=data | {"cliente_id": str(ids["convidado"])}
            ).status_code
            == 422
        )
        assert http.get(path).json()["total"] == 0

        registered = http.post(path, headers=headers, json=data)
        assert registered.status_code == 201, registered.text
        assert registered.headers["cache-control"] == "no-store"
        original = registered.json()
        assert original["registrado_por_id"] == str(ids["admin"])
        assert original["registrado_por_nome"] == "admin"
        assert original["cliente_id"] == str(ids["cliente"])
        assert original["valor"] == "149.90"
        assert original["estado"] == "CONFIRMADO"
        replay = http.post(path, headers=headers, json=data)
        assert (replay.status_code, replay.json()) == (200, original)
        assert (
            http.post(path, headers=headers, json=data | {"valor": "100"}).status_code
            == 409
        )
        assert http.post(other, headers=headers, json=data).status_code == 409
        assert (
            http.post(
                other,
                headers=headers,
                json={
                    **data,
                    "solicitacao_id": str(uuid4()),
                    "referencia_externa": data["referencia_externa"].lower(),
                },
            ).status_code
            == 409
        )
        assert (
            http.post(
                other + f"/{payment_id}/anulacao",
                headers=headers,
                json={"motivo": "sem vínculo"},
            ).status_code
            == 404
        )

        prior = fields() | {"referencia_externa": "REF-EXEMPLO-02"}
        assert http.post(other, headers=headers, json=prior).status_code == 201
        assert http.get(other).json()["total"] == 1
        replacement = fields() | {
            "valor": "125.35",
            "motivo": "Corrigir o valor anotado.",
        }
        conflict = http.post(
            correction_path,
            headers=headers,
            json={
                **replacement,
                "referencia_externa": prior["referencia_externa"],
            },
        )
        assert conflict.status_code == 409
        assert http.get(path).json()["itens"] == [original]
        assert (
            http.post(
                other + f"/{payment_id}/correcao", headers=headers, json=replacement
            ).status_code
            == 404
        )
        corrected = http.post(correction_path, headers=headers, json=replacement)
        assert corrected.status_code == 201, corrected.text
        new = corrected.json()
        assert new["valor"] == "125.35"
        assert new["substitui_id"] == payment_id
        assert new["estado"] == "CONFIRMADO"
        replay = http.post(correction_path, headers=headers, json=replacement)
        assert (replay.status_code, replay.json()) == (200, new)
        different = {**replacement, "motivo": "Motivo alterado"}
        assert (
            http.post(correction_path, headers=headers, json=different).status_code
            == 409
        )

        headers = login("admin")
        history = http.get(path, params={"limite": 1}).json()
        assert len(history["itens"]) == 1 and history["total"] == 2
        history = http.get(path).json()["itens"]
        by_id = {row["id"]: row for row in history}
        assert by_id[payment_id]["valor"] == "149.90"
        assert by_id[payment_id]["estado"] == "ANULADO"
        assert by_id[payment_id]["motivo_anulacao"] == replacement["motivo"]
        assert by_id[payment_id]["anulado_por_nome"] == "admin"
        void_path = path + "/" + new["id"] + "/anulacao"
        reason = {"motivo": "Lançamento duplicado fora da aplicação."}
        result = http.post(void_path, headers=headers, json=reason)
        assert result.status_code == 200
        assert result.json()["estado"] == "ANULADO"
        assert (
            http.post(void_path, headers=headers, json=reason).json() == result.json()
        )
        assert (
            http.post(void_path, headers=headers, json={"motivo": "Outro"}).status_code
            == 409
        )

    with sessions.begin() as db:
        assert db.scalar(select(func.count()).select_from(Membership)) == 0
        actions = db.scalars(
            select(AuditRecord.acao).where(
                AuditRecord.recurso_id.in_((UUID(payment_id), UUID(new["id"]))),
            )
        ).all()
        assert sorted(actions) == [
            "pagamento.anulado",
            "pagamento.corrigido",
            "pagamento.registrado",
        ]
        assert (
            db.scalar(
                select(func.count())
                .select_from(Payment)
                .where(
                    Payment.cliente_id == ids["cliente"],
                    Payment.estado == "CONFIRMADO",
                )
            )
            == 0
        )


@pytest.mark.database
def test_payment_migration_roundtrip_and_invalid_manual_data(
    migration: Connection,
) -> None:
    config = Config(str(Path(__file__).resolve().parents[3] / "database/alembic.ini"))
    config.attributes.update(connection=migration, database_target="test")
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        ids = seed_people(db)
    command.downgrade(config, "0024")
    assert not inspect(migration).has_table("pagamento", schema="academia")
    command.upgrade(config, "0025")
    assert inspect(migration).has_table("pagamento", schema="academia")
    command.upgrade(config, "head")
    with sessions.begin() as db:
        assert db.get(ClientProfile, ids["cliente"]) is not None
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(
                Payment(
                    id=uuid4(),
                    cliente_id=ids["cliente"],
                    origem="MANUAL",
                    estado="CONFIRMADO",
                    valor=1,
                )
            )
            db.flush()

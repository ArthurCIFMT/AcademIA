from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.core.http import install_http_contract
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.billing.charges.http import charges_router
from app.modules.billing.charges.models import Charge
from app.modules.billing.payments.http import manual_payments_router
from app.modules.billing.payments.models import Payment
from app.modules.identity.composition import install_identity
from app.modules.identity.models import AccountState, User
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.models import Membership, Plan
from tests.access.conftest import migration as migration
from tests.billing.test_manual_payments import fields as payment_fields
from tests.dashboard.test_dashboard import AT, ORIGIN, PASSWORD, seed_people

CHARGES = "/api/v1/admin/clientes/{client_id}/cobrancas"
OWN = "/api/v1/cliente/cobrancas"
TODAY = academy_date(AT)


def profile_rows(db: Session, ids: dict[str, UUID]) -> tuple[UUID, UUID]:
    db.get_one(User, ids["conta-inativa"]).estado = AccountState.ATIVO
    plan_id = uuid4()
    db.add(
        Plan(
            id=plan_id,
            nome="Musculação",
            modalidade="Musculação",
            ativo=True,
            revision=1,
            duracao_dias=30,
        )
    )
    db.flush()
    own, other = uuid4(), uuid4()
    for id_, name in ((own, "cliente"), (other, "conta-inativa")):
        db.add(
            Membership(
                id=id_,
                cliente_id=ids[name],
                plano_id=plan_id,
                atendente_id=ids["atendente"],
                inicio=TODAY,
                fim=TODAY + timedelta(days=29),
                estado="ATIVA",
                modalidade_contratada="Musculação",
                limites_snapshot={"limite_acessos": None, "janela_limite": None},
            )
        )
    return own, other


def fields() -> dict[str, str]:
    return {
        "solicitacao_id": str(uuid4()),
        "valor": "150.00",
        "competencia": TODAY.replace(day=1).isoformat(),
        "vencimento": (TODAY - timedelta(days=1)).isoformat(),
    }


def test_charges_use_distinct_contracts_and_informative_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA")
    monkeypatch.setenv("ACADEMIA_INADIMPLENCIA", "SOMENTE_INFORMATIVA")
    paths = create_app().openapi()["paths"]
    assert set(paths[OWN]) == {"get"}
    assert set(paths[CHARGES]) == {"get", "post"}
    assert set(paths[CHARGES + "/{charge_id}"]) == {"get", "put"}
    assert "get" in paths[CHARGES + "/{charge_id}/historico"]


@pytest.mark.integration
def test_charge_lifecycle_visibility_and_confirmed_payments(
    migration: Connection,
) -> None:
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        ids = seed_people(db)
        own_membership, other_membership = profile_rows(db, ids)

    app = FastAPI()
    install_http_contract(app)
    factory = install_identity(
        app, settings=AuthSettings(origin=ORIGIN), sessions=sessions
    )
    app.include_router(
        charges_router(factory, policy="SOMENTE_INFORMATIVA", clock=lambda: AT)
    )
    app.include_router(manual_payments_router(factory, clock=lambda: AT))
    path = CHARGES.format(client_id=ids["cliente"])
    other_path = CHARGES.format(client_id=ids["conta-inativa"])
    payments = path.removesuffix("/cobrancas") + "/pagamentos"
    data = {**fields(), "matricula_id": str(own_membership)}
    charge_id = data["solicitacao_id"]
    url = path + "/" + charge_id

    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as http:

        def login(who: str) -> dict[str, str]:
            http.cookies.clear()
            signed = http.post(
                "/api/v1/auth/login",
                json={
                    "email": who + "@example.test",
                    "senha": PASSWORD,
                },
            )
            assert signed.status_code == 200
            return {"X-CSRF-Token": signed.json()["csrf_token"]}

        assert http.get(path).status_code == 401
        assert http.get(OWN).status_code == 401
        for who in ("atendente", "instrutor"):
            headers = login(who)
            assert http.post(path, headers=headers, json=data).status_code == 403
            assert http.get(path).status_code == 403
            assert http.get(OWN).status_code == 403
        login("cliente")
        assert http.get(OWN).json()["itens"] == []
        assert http.get(path).status_code == 403

        headers = login("admin")
        assert http.get(OWN).status_code == 403
        assert http.post(path, json=data).status_code == 403
        for invalid in (
            {"matricula_id": str(other_membership)},
            {"valor": "1.234"},
            {"valor": "-1"},
            {"competencia": "2026-11-02"},
            {"vencimento": "2026-11-31"},
            {"valor": 1.23},
        ):
            assert (
                http.post(path, headers=headers, json={**data, **invalid}).status_code
                == 422
            )
        assert http.get(path).json()["total"] == 0
        assert http.get(path + "/matriculas").json()["itens"][0]["id"] == str(
            own_membership
        )

        created = http.post(path, headers=headers, json=data)
        assert created.status_code == 201, created.text
        assert created.json()["saldo"] == "150.00"
        assert created.json()["situacao"] == "VENCIDA"
        assert created.headers["cache-control"] == "no-store"
        assert http.post(path, headers=headers, json=data).status_code == 200
        assert (
            http.post(path, headers=headers, json={**data, "valor": "200"}).status_code
            == 409
        )
        assert http.get(other_path + "/" + charge_id).status_code == 404
        login("conta-inativa")
        response = http.get(OWN, params={"cliente_id": str(ids["cliente"])})
        assert response.json()["itens"] == []
        assert http.get(url).status_code == 403

        login("cliente")
        own = http.get(OWN).json()
        assert own["politica_inadimplencia"] == "SOMENTE_INFORMATIVA"
        assert own["itens"][0]["id"] == charge_id
        assert str(ids["admin"]) not in str(own)
        headers = login("admin")

        update = {key: value for key, value in data.items() if key != "solicitacao_id"}
        change = {**update, "revisao": 1, "estado": "CANCELADA", "valor": "160.00"}
        assert (
            http.put(url, headers=headers, json=change).json()["situacao"]
            == "CANCELADA"
        )
        assert http.put(url, headers=headers, json=change).status_code == 409
        assert (
            http.post(
                payments,
                headers=headers,
                json={
                    **payment_fields(),
                    "cobranca_id": charge_id,
                },
            ).status_code
            == 422
        )
        updated = http.put(
            url,
            headers=headers,
            json={**change, "revisao": 2, "estado": "ABERTA", "valor": "150.00"},
        )
        assert updated.status_code == 200 and updated.json()["revisao"] == 3
        revisions = http.get(url + "/historico", params={"limite": 2}).json()
        assert revisions["total"] == 3
        assert [row["dados"]["estado"] for row in revisions["itens"]] == [
            "ABERTA",
            "CANCELADA",
        ]
        assert revisions["itens"][0]["autor_nome"] == "admin"
        assert revisions["itens"][1]["dados"]["valor"] == "160.00"

        with sessions.begin() as db:
            for attempt in ("PENDENTE", "RECUSADO", "CONFIRMADO"):
                db.add(
                    Payment(
                        id=uuid4(),
                        cliente_id=ids["cliente"],
                        cobranca_id=UUID(charge_id),
                        origem="ENSAIO",
                        estado=attempt,
                        valor=Decimal("150.00"),
                    )
                )
        assert http.get(url).json()["valor_pago"] == "0.00"
        assert (
            http.post(
                other_path.removesuffix("/cobrancas") + "/pagamentos",
                headers=headers,
                json={**payment_fields(), "cobranca_id": charge_id},
            ).status_code
            == 422
        )

        pay = {**payment_fields(), "valor": "70.00", "cobranca_id": charge_id}
        first = http.post(payments, headers=headers, json=pay)
        assert first.status_code == 201, first.text
        assert http.get(url).json()["saldo"] == "80.00"
        second = {
            **payment_fields(),
            "valor": "80.00",
            "cobranca_id": charge_id,
            "referencia_externa": "REF-PARCELA-02",
        }
        assert http.post(payments, headers=headers, json=second).status_code == 201
        assert http.get(url).json()["situacao"] == "QUITADA"
        void = payments + "/" + second["solicitacao_id"] + "/anulacao"
        assert (
            http.post(
                void, headers=headers, json={"motivo": "Duplicidade no recibo"}
            ).status_code
            == 200
        )
        assert http.get(url).json()["saldo"] == "80.00"
        new = {**payment_fields(), "valor": "60.00", "motivo": "Corrigir parcial"}
        corrected = http.post(
            payments + "/" + pay["solicitacao_id"] + "/correcao",
            headers=headers,
            json=new,
        )
        assert corrected.status_code == 201, corrected.text
        assert corrected.json()["cobranca_id"] == charge_id
        assert http.get(url).json()["saldo"] == "90.00"

        login("cliente")
        assert http.get(OWN).json()["itens"][0]["valor_pago"] == "60.00"
        assert http.get(url + "/historico").status_code == 403


@pytest.mark.database
def test_charge_migration_keeps_manual_history_and_enforces_ownership(
    migration: Connection,
) -> None:
    cfg = Config(str(Path(__file__).resolve().parents[3] / "database/alembic.ini"))
    cfg.attributes.update(connection=migration, database_target="test")
    sessions = create_session_factory(migration)
    with sessions.begin() as db:
        ids = seed_people(db)
        own_membership, _ = profile_rows(db, ids)
    command.downgrade(cfg, "0025")
    assert not inspect(migration).has_table("cobranca", schema="academia")
    legacy_id = uuid4()
    migration.execute(
        text("""
        INSERT INTO academia.pagamento
            (id, cliente_id, origem, estado, valor)
        VALUES (:id, :client, 'ENSAIO', 'RECUSADO', 25.00)
    """),
        {"id": legacy_id, "client": ids["cliente"]},
    )
    command.upgrade(cfg, "0026")

    with sessions.begin() as db:
        legacy = db.execute(
            select(Payment.valor, Payment.estado, Payment.cobranca_id).where(
                Payment.id == legacy_id
            )
        ).one()
        assert tuple(legacy) == (
            Decimal("25"),
            "RECUSADO",
            None,
        )
        with pytest.raises(IntegrityError), db.begin_nested():
            db.add(
                Charge(
                    id=uuid4(),
                    cliente_id=ids["conta-inativa"],
                    matricula_id=own_membership,
                    competencia=TODAY.replace(day=1),
                    vencimento=TODAY,
                    valor=Decimal("1.00"),
                    estado="ABERTA",
                    revisao=1,
                )
            )
            db.flush()
        assert db.scalars(select(Charge)).all() == []

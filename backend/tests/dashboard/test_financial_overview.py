from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection

from app.contracts.time import academy_date
from app.database.connection import create_session_factory
from app.modules.billing.charges.models import Charge
from app.modules.billing.payments.checkout import SimulatePurchase, simulate_purchase
from app.modules.billing.payments.schemas import CorrectPayment, RegisterPayment
from app.modules.billing.payments.service import record_payment
from app.modules.billing.reporting import (
    FinancialTotals,
    financial_overview,
    summarize_months,
)
from app.modules.memberships.models import Plan
from tests.access.conftest import migration as migration
from tests.dashboard.test_dashboard import seed_people


def test_month_rollup_preserves_cents_and_fills_empty_month() -> None:
    def totals(billed: str) -> FinancialTotals:
        return FinancialTotals(
            cobrado=Decimal(billed),
            recebido=Decimal("0.00"),
            pendente=Decimal("0.00"),
            vencido=Decimal("0.00"),
        )

    summary = summarize_months(
        (
            (date(2025, 12, 1), totals("28.13")),
            (date(2026, 1, 1), totals("0.10")),
            (date(2026, 2, 1), totals("0.20")),
        ),
        current_month=date(2026, 3, 1),
    )
    assert summary.mes == totals("0.00")
    assert summary.ano == totals("0.30")
    assert summary.total == totals("28.43")


@pytest.mark.integration
def test_finance_uses_civil_periods_and_only_valid_confirmations(
    migration: Connection,
) -> None:
    sessions = create_session_factory(migration)
    at = datetime(2026, 11, 1, 3, tzinfo=UTC)
    prior_month = at - timedelta(seconds=1)
    with sessions.begin() as db:
        people = seed_people(db)
        client, admin = people["cliente"], people["admin"]
        month = date(2026, 11, 1)

        def charge(value: str, competence: date, due: date) -> Charge:
            row = Charge(
                id=uuid4(),
                cliente_id=client,
                competencia=competence,
                vencimento=due,
                valor=Decimal(value),
                estado="ABERTA",
                revisao=1,
            )
            db.add(row)
            return row

        charge("100.00", date(2025, 12, 1), date(2025, 12, 31))
        charge("100.00", month, date(2026, 10, 31))
        due_today = charge("150.00", month, month)
        overpaid = charge("20.00", month, date(2026, 11, 2))
        canceled = charge("99.00", month, date(2026, 11, 2))
        charge("88.00", date(2027, 1, 1), date(2027, 1, 31))
        db.flush()

        def payment_fields(
            value: str, now: datetime, charge_id: UUID | None = None
        ) -> RegisterPayment:
            return RegisterPayment(
                solicitacao_id=uuid4(),
                valor=value,
                pago_em=academy_date(now),
                metodo="OUTRO",
                referencia_externa=str(uuid4()),
                cobranca_id=charge_id,
            )

        def record(
            data: RegisterPayment, now: datetime, old: UUID | None = None
        ) -> None:
            record_payment(
                db,
                client,
                data,
                actor_id=admin,
                correlation=uuid4(),
                now=now,
                replaced_id=old,
            )

        record(
            payment_fields("7.50", datetime(2026, 1, 1, 2, 59, 59, tzinfo=UTC)),
            datetime(2026, 1, 1, 2, 59, 59, tzinfo=UTC),
        )
        record(payment_fields("30.00", prior_month, overpaid.id), prior_month)
        original = payment_fields("40.00", at, due_today.id)
        record(original, at)
        corrected = CorrectPayment(
            **payment_fields("60.00", at, due_today.id).model_dump(),
            motivo="Correção de teste",
        )
        record(corrected, at, original.solicitacao_id)
        record(payment_fields("9.00", at, canceled.id), at)
        canceled.estado = "CANCELADA"

        plan_id = uuid4()
        db.add(
            Plan(
                id=plan_id,
                nome="Plano demonstrativo",
                duracao_dias=30,
                modalidade="Musculação",
                ativo=True,
                revision=1,
                preco_base=Decimal("120.00"),
            )
        )
        db.flush()
        confirmed = SimulatePurchase(
            solicitacao_id=uuid4(), plano_id=plan_id, resultado="CONFIRMADO"
        )
        _, created = simulate_purchase(
            db, client, confirmed, correlation=uuid4(), now=at
        )
        assert created
        _, replay_created = simulate_purchase(
            db, client, confirmed, correlation=uuid4(), now=at
        )
        assert not replay_created
        for outcome in ("PENDENTE", "RECUSADO"):
            simulate_purchase(
                db,
                client,
                SimulatePurchase(
                    solicitacao_id=uuid4(), plano_id=plan_id, resultado=outcome
                ),
                correlation=uuid4(),
                now=at,
            )
        simulate_purchase(
            db,
            client,
            confirmed.model_copy(update={"solicitacao_id": uuid4()}),
            correlation=uuid4(),
            now=at + timedelta(seconds=1),
        )

        summary = financial_overview(db, at=at).model_dump(mode="json")
        assert summary == {
            "competencia_atual": "2026-11-01",
            "mes": {
                "cobrado": "270.00",
                "recebido": "189.00",
                "pendente": "90.00",
                "vencido": "100.00",
            },
            "ano": {
                "cobrado": "270.00",
                "recebido": "219.00",
                "pendente": "90.00",
                "vencido": "100.00",
            },
            "total": {
                "cobrado": "458.00",
                "recebido": "226.50",
                "pendente": "178.00",
                "vencido": "200.00",
            },
        }

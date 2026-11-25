from collections.abc import Collection, Iterable
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import Date, case, cast, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.contracts.time import academy_date
from app.modules.billing.charges.models import Charge
from app.modules.billing.payments.models import CONFIRMED_PAYMENT, Payment

_ZERO = Decimal("0.00")


class FinancialTotals(BaseModel):
    cobrado: Decimal
    recebido: Decimal
    pendente: Decimal
    vencido: Decimal


class FinancialOverview(BaseModel):
    competencia_atual: date
    mes: FinancialTotals
    ano: FinancialTotals
    total: FinancialTotals


def summarize_months(
    months: Iterable[tuple[date, FinancialTotals]], *, current_month: date
) -> FinancialOverview:
    by_month = dict(months)
    month = by_month.get(
        current_month,
        FinancialTotals(cobrado=_ZERO, recebido=_ZERO, pendente=_ZERO, vencido=_ZERO),
    )
    year = [
        totals for day, totals in by_month.items() if day.year == current_month.year
    ]

    def sum_totals(rows: Collection[FinancialTotals]) -> FinancialTotals:
        return FinancialTotals(
            cobrado=sum((row.cobrado for row in rows), _ZERO),
            recebido=sum((row.recebido for row in rows), _ZERO),
            pendente=sum((row.pendente for row in rows), _ZERO),
            vencido=sum((row.vencido for row in rows), _ZERO),
        )

    return FinancialOverview(
        competencia_atual=current_month,
        mes=month,
        ano=sum_totals(year),
        total=sum_totals(by_month.values()),
    )


def financial_overview(db: Session, *, at: datetime) -> FinancialOverview:
    today = academy_date(at)
    # Uma instrução SQL mantém recebimentos e saldos no mesmo snapshot.
    confirmed = (
        select(Payment.cobranca_id, Payment.pago_em, Payment.valor)
        .where(
            *CONFIRMED_PAYMENT,
            Payment.origem.in_(("MANUAL", "SIMULACAO")),
            Payment.confirmado_em <= at,
            Payment.pago_em <= today,
        )
        .cte()
    )
    settled = (
        select(confirmed.c.cobranca_id, func.sum(confirmed.c.valor).label("pago"))
        .where(confirmed.c.cobranca_id.is_not(None))
        .group_by(confirmed.c.cobranca_id)
        .subquery()
    )
    zero = literal(_ZERO)
    balance = func.greatest(Charge.valor - func.coalesce(settled.c.pago, zero), zero)
    charges = (
        select(
            Charge.competencia.label("mes"),
            Charge.valor.label("cobrado"),
            zero.label("recebido"),
            case((Charge.vencimento >= today, balance), else_=zero).label("pendente"),
            case((Charge.vencimento < today, balance), else_=zero).label("vencido"),
        )
        .outerjoin(settled, settled.c.cobranca_id == Charge.id)
        .where(Charge.estado == "ABERTA")
    )
    receipts = select(
        cast(func.date_trunc("month", confirmed.c.pago_em), Date),
        zero,
        confirmed.c.valor,
        zero,
        zero,
    )
    entries = union_all(charges, receipts).subquery()
    rows = db.execute(
        select(
            entries.c.mes,
            func.sum(entries.c.cobrado),
            func.sum(entries.c.recebido),
            func.sum(entries.c.pendente),
            func.sum(entries.c.vencido),
        ).group_by(entries.c.mes)
    )
    return summarize_months(
        (
            (
                month,
                FinancialTotals(
                    cobrado=billed, recebido=paid, pendente=open_, vencido=overdue
                ),
            )
            for month, billed, paid, open_, overdue in rows
        ),
        current_month=today.replace(day=1),
    )

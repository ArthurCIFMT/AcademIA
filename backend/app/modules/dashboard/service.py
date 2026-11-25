import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import academy_date
from app.modules.access.attendance.service import (
    confirmed_visits_by_hour,
    current_occupancy,
)
from app.modules.billing.reporting import financial_overview
from app.modules.dashboard.contracts import (
    Available,
    DashboardOverview,
    DayCount,
    Frequency,
    HourCount,
    Indicator,
    Unavailable,
    WeekCount,
)
from app.modules.identity.roles import active_client_count
from app.modules.memberships.service import enrolled_client_count
from app.modules.people.staff import registered_employee_count

logger = logging.getLogger(__name__)


def frequency(db: Session, at: datetime) -> Frequency:
    today = academy_date(at)
    monday = today - timedelta(days=today.weekday())
    first_week = monday - timedelta(weeks=3)
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    day_hours: dict[date, list[HourCount]] = {day: [] for day in days}
    week_counts = {first_week + timedelta(weeks=offset): 0 for offset in range(4)}
    for entry in confirmed_visits_by_hour(db, first_week, through=at):
        start = entry.date - timedelta(days=entry.date.weekday())
        week_counts[start] += entry.visits
        if entry.date in day_hours:
            day_hours[entry.date].append(
                HourCount(hora=entry.hour, visitas=entry.visits)
            )

    return Frequency(
        semanas=[
            WeekCount(inicio=day, visitas=total) for day, total in week_counts.items()
        ],
        dias=[
            DayCount(
                data=day, visitas=sum(row.visitas for row in hours), por_hora=hours
            )
            for day, hours in day_hours.items()
        ],
    )


def overview(sessions: sessionmaker[Session], *, at: datetime) -> DashboardOverview:
    def read[T](name: str, query: Callable[[Session], T]) -> Indicator[T]:
        try:
            with sessions.begin() as db:
                return Available(valor=query(db))
        except Exception:
            # O resultado de falha e os logs só identificam o tipo de indicador.
            logger.warning("Indicador do painel indisponível: %s", name)
            return Unavailable()

    return DashboardOverview(
        consultado_em=at,
        clientes_ativos=read("clientes_ativos", active_client_count),
        clientes_matriculados=read(
            "clientes_matriculados", lambda db: enrolled_client_count(db, at=at)
        ),
        funcionarios=read("funcionarios", registered_employee_count),
        lotacao=read("lotacao", current_occupancy),
        frequencia=read("frequencia", lambda db: frequency(db, at)),
        financeiro=read("financeiro", lambda db: financial_overview(db, at=at)),
    )

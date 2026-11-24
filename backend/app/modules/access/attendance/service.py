from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Date, Integer, cast, func, select, true
from sqlalchemy.orm import Session, aliased

from app.modules.access.attendance.models import Presence
from app.modules.access.attendance.projection import PassageRecord, project
from app.modules.access.authorization.models import TurnstileCommand
from app.modules.access.events.models import AccessEvent
from app.modules.people.assignment_directory import AssignmentDirectory


@dataclass(frozen=True)
class AttendanceVisit:
    id: UUID
    entered_at: datetime
    exited_at: datetime | None


@dataclass(frozen=True)
class AttendancePage:
    visits: tuple[AttendanceVisit, ...]
    total: int


@dataclass(frozen=True)
class AttendanceHour:
    date: date
    hour: int
    visits: int


def reconcile_client(db: Session, client_id: UUID) -> None:
    AssignmentDirectory(db).lock_people(client_id)
    db.flush()
    passages = db.scalars(
        select(AccessEvent)
        .join(TurnstileCommand, TurnstileCommand.passagem_evento_id == AccessEvent.id)
        .where(
            AccessEvent.cliente_id == client_id,
            AccessEvent.tipo == "PASSAGEM_SIMULADA",
            AccessEvent.origem == "CATRACA_SIMULADA",
            TurnstileCommand.estado == "CONFIRMADO",
        )
    ).all()
    projection = project(
        PassageRecord(row.id, row.direcao, row.ocorrido_em) for row in passages
    )
    for row in passages:
        outcome = projection.outcomes[row.id]
        if row.resultado_presenca != outcome:
            row.resultado_presenca = outcome

    current = {
        row.entrada_evento_id: row
        for row in db.scalars(select(Presence).where(Presence.cliente_id == client_id))
    }
    desired = {visit.entry_id: visit.exit_id for visit in projection.visits}
    for entry_id, presence in list(current.items()):
        if entry_id not in desired or presence.saida_evento_id != desired[entry_id]:
            db.delete(presence)
            del current[entry_id]
    db.flush()
    db.add_all(
        Presence(
            id=entry_id,
            cliente_id=client_id,
            entrada_evento_id=entry_id,
            saida_evento_id=exit_id,
        )
        for entry_id, exit_id in desired.items()
        if entry_id not in current
    )
    db.flush()


def current_occupancy(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Presence)
            .where(Presence.saida_evento_id.is_(None))
        )
        or 0
    )


def confirmed_visits_by_hour(
    db: Session, first_day: date, *, through: datetime
) -> tuple[AttendanceHour, ...]:
    """Conta entradas de visitas confirmadas por data e hora da academia."""
    zone = ZoneInfo("America/Sao_Paulo")
    start = datetime.combine(first_day, time.min, tzinfo=zone).astimezone(UTC)
    local_time = func.timezone(zone.key, AccessEvent.ocorrido_em)
    day = cast(local_time, Date)
    hour = cast(func.extract("hour", local_time), Integer)
    rows = db.execute(
        select(day, hour, func.count())
        .select_from(Presence)
        .join(AccessEvent, AccessEvent.id == Presence.entrada_evento_id)
        .where(AccessEvent.ocorrido_em >= start, AccessEvent.ocorrido_em <= through)
        .group_by(day, hour)
        .order_by(day, hour)
    )
    return tuple(AttendanceHour(day, hour, visits) for day, hour, visits in rows)


def attendance_history(
    db: Session,
    client_id: UUID,
    start: datetime,
    end: datetime,
    *,
    page: int = 1,
    limit: int = 20,
) -> AttendancePage:
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError("O período deve incluir o fuso horário")
    start, end = start.astimezone(UTC), end.astimezone(UTC)
    if start >= end or page < 1 or limit < 1:
        raise ValueError("Período ou paginação inválida")
    entry = aliased(AccessEvent)
    exit_ = aliased(AccessEvent)
    visits = (
        select(
            Presence.id,
            entry.ocorrido_em.label("entered_at"),
            exit_.ocorrido_em.label("exited_at"),
        )
        .join(entry, entry.id == Presence.entrada_evento_id)
        .outerjoin(exit_, exit_.id == Presence.saida_evento_id)
        .where(
            Presence.cliente_id == client_id,
            entry.ocorrido_em >= start,
            entry.ocorrido_em < end,
        )
    )
    total = (
        select(func.count().label("total_count"))
        .select_from(visits.subquery())
        .subquery()
    )
    page_rows = (
        visits.order_by(entry.ocorrido_em.desc(), Presence.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .subquery()
    )
    rows = db.execute(
        select(total.c.total_count, page_rows)
        .select_from(total.outerjoin(page_rows, true()))
        .order_by(page_rows.c.entered_at.desc(), page_rows.c.id.desc())
    ).all()
    return AttendancePage(
        tuple(
            AttendanceVisit(
                visit_id,
                entered.astimezone(UTC),
                exited.astimezone(UTC) if exited is not None else None,
            )
            for _, visit_id, entered, exited in rows
            if visit_id is not None
        ),
        rows[0].total_count,
    )

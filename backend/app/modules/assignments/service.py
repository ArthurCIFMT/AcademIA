from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contracts.time import UtcTimestamp
from app.events.contracts import AuditEvent
from app.modules.assignments.models import Assignment
from app.modules.audit.service import record_audit
from app.modules.identity.service import utc_now
from app.modules.people.assignment_directory import (
    AssignmentDirectory,
    InstructorReference,
)
from app.policies.access import Actor


class AssignmentError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class ChangeAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrutor_id: UUID
    vigente_id: UUID | None


class AssignmentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cliente_id: UUID
    instrutor_id: UUID
    instrutor_nome: str
    inicio: UtcTimestamp
    fim: UtcTimestamp | None
    atribuido_por: UUID


class PersonName(BaseModel):
    id: UUID
    nome: str


class InstructorOption(PersonName):
    email: str


class ClientAssignment(PersonName):
    inicio: UtcTimestamp


class Page[Item](BaseModel):
    itens: list[Item]
    pagina: Annotated[int, Field(ge=1)]
    limite: Annotated[int, Field(ge=1)]
    total: Annotated[int, Field(ge=0)]


class ClientAssignments(BaseModel):
    cliente: PersonName
    cliente_elegivel: bool
    vigente: AssignmentRecord | None
    instrutor_ativo: bool
    historico: Page[AssignmentRecord]


def _current(session: Session, client_id: UUID) -> Assignment | None:
    return session.scalar(
        select(Assignment).where(
            Assignment.cliente_id == client_id, Assignment.fim.is_(None)
        )
    )


def _record(row: Assignment, name: str) -> AssignmentRecord:
    return AssignmentRecord(
        id=row.id,
        cliente_id=row.cliente_id,
        instrutor_id=row.instrutor_id,
        instrutor_nome=name,
        inicio=row.inicio,
        fim=row.fim,
        atribuido_por=row.atribuido_por,
    )


class PostgresAssignmentReader:
    """Adaptador do contrato AssignmentReader usado pela política profissional."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.directory = AssignmentDirectory(session)

    def review_recipient(self, client_id: UUID) -> InstructorReference | None:
        current = _current(self.session, client_id)
        if current is None or not self.is_active(current.instrutor_id, client_id):
            return None
        return self.directory.instructor_reference(current.instrutor_id)

    def is_active(self, instructor_id: UUID, client_id: UUID) -> bool:
        current = _current(self.session, client_id)
        if current is None or current.instrutor_id != instructor_id:
            return False
        client = self.directory.clients([client_id]).get(client_id)
        return bool(
            client
            and client.elegivel
            and self.directory.instructor_is_active(instructor_id)
        )


def history(
    session: Session, client_id: UUID, page: int, limit: int
) -> ClientAssignments:
    directory = AssignmentDirectory(session)
    directory.lock_people(client_id)
    client = directory.clients([client_id]).get(client_id)
    if client is None:
        raise AssignmentError(404)
    current = _current(session, client_id)
    closed = select(Assignment).where(
        Assignment.cliente_id == client_id, Assignment.fim.is_not(None)
    )
    total = session.scalar(select(func.count()).select_from(closed.subquery())) or 0
    rows = list(
        session.scalars(
            closed.order_by(Assignment.inicio.desc(), Assignment.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    ids = [row.instrutor_id for row in rows]
    if current is not None:
        ids.append(current.instrutor_id)
    names = directory.instructor_names(ids)
    return ClientAssignments(
        cliente=PersonName(id=client.id, nome=client.nome),
        cliente_elegivel=client.elegivel,
        vigente=_record(current, names[current.instrutor_id]) if current else None,
        instrutor_ativo=bool(
            current and directory.instructor_is_active(current.instrutor_id)
        ),
        historico=Page[AssignmentRecord](
            itens=[_record(row, names[row.instrutor_id]) for row in rows],
            pagina=page,
            limite=limit,
            total=total,
        ),
    )


def candidates(
    session: Session, search: str, page: int, limit: int
) -> Page[InstructorOption]:
    rows, total = AssignmentDirectory(session).list_instructors(search, page, limit)
    return Page[InstructorOption](
        itens=[
            InstructorOption(id=row.id, nome=row.nome, email=row.email) for row in rows
        ],
        pagina=page,
        limite=limit,
        total=total,
    )


def my_clients(
    session: Session, instructor_id: UUID, page: int, limit: int
) -> Page[ClientAssignment]:
    directory = AssignmentDirectory(session)
    rows = list(
        session.scalars(
            select(Assignment)
            .where(Assignment.instrutor_id == instructor_id, Assignment.fim.is_(None))
            .order_by(Assignment.inicio.desc(), Assignment.id.desc())
        )
    )
    clients = directory.clients([row.cliente_id for row in rows])
    visible = [
        row
        for row in rows
        if row.cliente_id in clients and clients[row.cliente_id].elegivel
    ]
    start = (page - 1) * limit
    return Page[ClientAssignment](
        itens=[
            ClientAssignment(
                id=row.cliente_id, nome=clients[row.cliente_id].nome, inicio=row.inicio
            )
            for row in visible[start : start + limit]
        ],
        pagina=page,
        limite=limit,
        total=len(visible),
    )


def change_assignment(
    session: Session,
    client_id: UUID,
    data: ChangeAssignment,
    actor: Actor,
    correlation: UUID,
) -> AssignmentRecord:
    directory = AssignmentDirectory(session)
    directory.lock_people(client_id, data.instrutor_id)
    client = directory.clients([client_id]).get(client_id)
    if client is None:
        raise AssignmentError(404)
    if not client.elegivel or not directory.instructor_is_active(data.instrutor_id):
        raise AssignmentError(409)

    current = _current(session, client_id)
    if (current.id if current else None) != data.vigente_id:
        raise AssignmentError(409)
    names = directory.instructor_names([data.instrutor_id])
    name = names[data.instrutor_id]
    if current is not None and current.instrutor_id == data.instrutor_id:
        return _record(current, name)

    now = utc_now()
    if current is not None:
        now = max(now, current.inicio)
        current.fim = now
        session.flush()

    row = Assignment(
        id=uuid4(),
        cliente_id=client_id,
        instrutor_id=data.instrutor_id,
        inicio=now,
        fim=None,
        atribuido_por=actor.user_id,
    )
    session.add(row)
    record_audit(
        session,
        AuditEvent(
            id=uuid4(),
            actor_id=actor.user_id,
            action="assignment.replaced" if current else "assignment.created",
            resource_type="designacao",
            resource_id=row.id,
            correlation_id=correlation,
            occurred_at=now,
        ),
    )
    return _record(row, name)

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.assignments.service import (
    AssignmentError,
    AssignmentRecord,
    ChangeAssignment,
    ClientAssignment,
    ClientAssignments,
    InstructorOption,
    Page,
    PostgresAssignmentReader,
    candidates,
    change_assignment,
    history,
    my_clients,
)
from app.modules.identity.models import Role
from app.policies.access import Actor, AssignmentReader, Operation
from app.policies.http import AuthenticatedActor, require_permission

type SessionFactory = Callable[[], sessionmaker[Session]]


def get_assignment_reader(request: Request) -> Iterator[AssignmentReader]:
    get_sessions: SessionFactory = request.app.state.assignment_sessions
    with get_sessions().begin() as session:
        yield PostgresAssignmentReader(session)


AssignmentAccess = Annotated[AssignmentReader, Depends(get_assignment_reader)]


def assignment_admin(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_ASSIGNMENTS)
    response.headers["Cache-Control"] = "no-store"
    return actor


AssignmentAdmin = Annotated[Actor, Depends(assignment_admin)]


def install_assignments(app: FastAPI, get_sessions: SessionFactory) -> None:
    app.state.assignment_sessions = get_sessions
    router = APIRouter(prefix="/api/v1/designacoes", tags=["Designações"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except AssignmentError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/instrutores")
    def list_candidates(
        _actor: AssignmentAdmin,
        busca: Annotated[str, Query(max_length=254)] = "",
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> Page[InstructorOption]:
        with transaction() as session:
            return candidates(session, busca, pagina, limite)

    @router.get("/clientes/{client_id}")
    def client_history(
        client_id: UUID,
        _actor: AssignmentAdmin,
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ClientAssignments:
        with transaction() as session:
            return history(session, client_id, pagina, limite)

    @router.put("/clientes/{client_id}")
    def assign(
        client_id: UUID,
        data: ChangeAssignment,
        request: Request,
        actor: AssignmentAdmin,
    ) -> AssignmentRecord:
        with transaction() as session:
            return change_assignment(
                session, client_id, data, actor, request.state.correlation_id
            )

    @router.get("/minhas")
    def instructor_clients(
        actor: AuthenticatedActor,
        response: Response,
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> Page[ClientAssignment]:
        if Role.INSTRUTOR not in actor.roles:
            raise HTTPException(403)
        response.headers["Cache-Control"] = "no-store"
        with transaction() as session:
            return my_clients(session, actor.user_id, pagina, limite)

    app.include_router(router)

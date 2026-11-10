from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.errors import ErrorResponse
from app.modules.people.invitations import send_first_access_invite
from app.modules.people.staff import (
    CreateStaff,
    StaffDetail,
    StaffError,
    StaffPage,
    StaffRevision,
    UpdateStaff,
    create_staff,
    get_staff,
    list_staff,
    resend_staff_invite,
    update_staff,
)
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def staff_actor(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_EMPLOYEES)
    response.headers["Cache-Control"] = "no-store"
    return actor


StaffActor = Annotated[Actor, Depends(staff_actor)]
THROTTLED: dict[int | str, dict[str, object]] = {
    429: {"model": ErrorResponse, "description": "Limite de convites"}
}


def staff_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/funcionarios", tags=["Funcionários"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except StaffError as exc:
            raise HTTPException(exc.status) from None

    @router.get("")
    def index(
        _actor: StaffActor,
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> StaffPage:
        with transaction() as session:
            return list_staff(session, pagina, limite)

    @router.get("/{user_id}")
    def detail(user_id: UUID, _actor: StaffActor) -> StaffDetail:
        with transaction() as session:
            return get_staff(session, user_id)

    @router.post("", status_code=201, responses=THROTTLED)
    def create(data: CreateStaff, request: Request, actor: StaffActor) -> StaffDetail:
        correlation = request.state.correlation_id
        with transaction() as session:
            user_id, email, invite = create_staff(session, data, actor, correlation)
        if invite is not None:
            send_first_access_invite(
                get_sessions(),
                email,
                invite,
                request.app.state.browser_auth.settings.origin,
                correlation,
            )
        with transaction() as session:
            return get_staff(session, user_id)

    @router.put("/{user_id}")
    def edit(
        user_id: UUID, data: UpdateStaff, request: Request, actor: StaffActor
    ) -> StaffDetail:
        with transaction() as session:
            return update_staff(
                session, user_id, data, actor, request.state.correlation_id
            )

    @router.post("/{user_id}/convite", responses=THROTTLED)
    def reissue(
        user_id: UUID, data: StaffRevision, request: Request, actor: StaffActor
    ) -> StaffDetail:
        correlation = request.state.correlation_id
        with transaction() as session:
            email, invite = resend_staff_invite(
                session, user_id, data.revisao, actor, correlation
            )
        send_first_access_invite(
            get_sessions(),
            email,
            invite,
            request.app.state.browser_auth.settings.origin,
            correlation,
        )
        with transaction() as session:
            return get_staff(session, user_id)

    return router

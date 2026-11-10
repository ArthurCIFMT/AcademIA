from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.errors import ErrorResponse
from app.modules.people.clients import (
    ClientDetail,
    ClientError,
    ClientPage,
    ClientRevision,
    CreateClient,
    UpdateClient,
    create_client,
    get_client,
    list_clients,
    resend_client_invite,
    update_client,
)
from app.modules.people.invitations import InviteLimitReached, send_first_access_invite
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def client_actor(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_CLIENTS)
    response.headers["Cache-Control"] = "no-store"
    return actor


ClientActor = Annotated[Actor, Depends(client_actor)]
THROTTLED: dict[int | str, dict[str, object]] = {
    429: {"model": ErrorResponse, "description": "Limite de convites"}
}


def client_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/clientes", tags=["Clientes"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except ClientError as exc:
            raise HTTPException(exc.status) from None
        except InviteLimitReached:
            raise HTTPException(429) from None

    @router.get("")
    def index(
        _actor: ClientActor,
        busca: Annotated[str, Query(max_length=254)] = "",
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ClientPage:
        with transaction() as session:
            return list_clients(session, busca, pagina, limite)

    @router.get("/{user_id}")
    def detail(user_id: UUID, _actor: ClientActor) -> ClientDetail:
        with transaction() as session:
            return get_client(session, user_id)

    @router.post("", status_code=201, responses=THROTTLED)
    def create(
        data: CreateClient, request: Request, actor: ClientActor
    ) -> ClientDetail:
        correlation = request.state.correlation_id
        with transaction() as session:
            user_id, email, invite = create_client(session, data, actor, correlation)
        if invite is not None:
            send_first_access_invite(
                get_sessions(),
                email,
                invite,
                request.app.state.browser_auth.settings.origin,
                correlation,
            )
        with transaction() as session:
            return get_client(session, user_id)

    @router.put("/{user_id}")
    def edit(
        user_id: UUID, data: UpdateClient, request: Request, actor: ClientActor
    ) -> ClientDetail:
        with transaction() as session:
            return update_client(
                session, user_id, data, actor, request.state.correlation_id
            )

    @router.post("/{user_id}/convite", responses=THROTTLED)
    def reissue(
        user_id: UUID, data: ClientRevision, request: Request, actor: ClientActor
    ) -> ClientDetail:
        correlation = request.state.correlation_id
        with transaction() as session:
            email, invite = resend_client_invite(
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
            return get_client(session, user_id)

    return router

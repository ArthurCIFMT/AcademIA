from collections.abc import Callable, Coroutine
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session, sessionmaker
from starlette.types import Message

from app.contracts.errors import ErrorResponse
from app.modules.access.biometrics.images import (
    MAX_IMAGE_BASE64,
    InvalidFaceImage,
    PhotoUpload,
)
from app.modules.access.biometrics.provider import FacialProvider, RejectedFace
from app.modules.access.biometrics.service import (
    BiometricsError,
    ReferenceService,
    ReferenceStatus,
    status,
)
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission

_MAX_BODY = MAX_IMAGE_BASE64 + 1024


class BoundPhotoRoute(APIRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[object, object, Response]]:
        handler = super().get_route_handler()

        async def run(request: Request) -> Response:
            received = 0

            async def receive() -> Message:
                nonlocal received
                message = await request.receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > _MAX_BODY:
                        raise HTTPException(413)
                return message

            if request.method == "POST":
                return await handler(Request(request.scope, receive=receive))
            return await handler(request)

        return run


def operator(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_BIOMETRICS)
    response.headers["Cache-Control"] = "no-store"
    return actor


Operator = Annotated[Actor, Depends(operator)]
_WRITE: dict[int | str, dict[str, object]] = {
    413: {"model": ErrorResponse, "description": "Foto acima do limite"},
    503: {"model": ErrorResponse, "description": "Provedor facial indisponível"},
}


def biometrics_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    provider: FacialProvider | None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/atendimento/clientes/{client_id}/biometria",
        tags=["Referência facial"],
        route_class=BoundPhotoRoute,
    )

    @router.get("")
    def reference_status(client_id: UUID, _actor: Operator) -> ReferenceStatus:
        try:
            with get_sessions().begin() as db:
                return status(db, client_id, available=provider is not None)
        except BiometricsError as exc:
            raise HTTPException(exc.status) from None

    @router.post("", responses=_WRITE)
    def upload(
        client_id: UUID, data: PhotoUpload, request: Request, actor: Operator
    ) -> ReferenceStatus:
        if provider is None:
            raise HTTPException(503)
        try:
            return ReferenceService(get_sessions(), provider).register(
                client_id,
                actor.user_id,
                request.state.correlation_id,
                data.imagem_base64,
            )
        except (InvalidFaceImage, RejectedFace):
            raise HTTPException(422) from None
        except BiometricsError as exc:
            raise HTTPException(exc.status) from None

    @router.post("/pendencia", responses=_WRITE)
    def resume(client_id: UUID, request: Request, actor: Operator) -> ReferenceStatus:
        if provider is None:
            raise HTTPException(503)
        try:
            return ReferenceService(get_sessions(), provider).resume(
                client_id, actor.user_id, request.state.correlation_id
            )
        except BiometricsError as exc:
            raise HTTPException(exc.status) from None

    return router

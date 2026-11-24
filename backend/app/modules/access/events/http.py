from collections.abc import Callable
from secrets import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.errors import ErrorResponse
from app.modules.access.biometrics.http import BoundPhotoRoute, Operator
from app.modules.access.biometrics.images import InvalidFaceImage
from app.modules.access.biometrics.provider import FacialProvider
from app.modules.access.events.contracts import (
    AccessEventsSettings,
    CaptureRequest,
    ExternalIdentification,
    IdentificationReceipt,
    StaffIdentification,
)
from app.modules.access.events.service import (
    EventRequest,
    IdentificationConflict,
    from_capture,
    from_source,
    receive,
)
from app.modules.people.assignment_directory import AssignmentDirectory

token_scheme = HTTPBearer(auto_error=False, scheme_name="IdentificacaoFacial")
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(token_scheme)]
_RESPONSES: dict[int | str, dict[str, object]] = {
    413: {"model": ErrorResponse, "description": "Corpo acima do limite"},
    503: {"model": ErrorResponse, "description": "Identificação sem configuração"},
}


def identification_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    provider: FacialProvider | None,
    settings: AccessEventsSettings | None,
) -> APIRouter:
    router = APIRouter(tags=["Identificação facial"], route_class=BoundPhotoRoute)

    def configuration() -> AccessEventsSettings:
        if settings is None:
            raise HTTPException(503)
        return settings

    @router.post(
        "/api/v1/atendimento/reconhecimento",
        status_code=201,
        responses={**_RESPONSES, 200: {"model": StaffIdentification}},
    )
    def capture(
        data: CaptureRequest, actor: Operator, response: Response
    ) -> StaffIdentification:
        threshold = configuration().similarity_threshold
        try:
            with get_sessions().begin() as db:
                receipt, created = receive(
                    db,
                    EventRequest.capture(data, actor.user_id),
                    lambda: from_capture(db, data, provider, threshold),
                )
                reference = (
                    AssignmentDirectory(db)
                    .clients([receipt.cliente_id])
                    .get(receipt.cliente_id)
                    if receipt.cliente_id is not None
                    else None
                )
                result = StaffIdentification(
                    **receipt.model_dump(),
                    cliente_nome=reference.nome if reference else None,
                )
        except InvalidFaceImage:
            raise HTTPException(422) from None
        except IdentificationConflict:
            raise HTTPException(409) from None
        response.status_code = 201 if created else 200
        return result

    def external_source(
        request: Request, credentials: Credentials
    ) -> AccessEventsSettings:
        configured = configuration()
        token = configured.identification_token
        if token is None:
            raise HTTPException(503)
        if (
            credentials is None
            or len(request.headers.getlist("authorization")) != 1
            or not compare_digest(
                credentials.credentials.encode(), token.get_secret_value().encode()
            )
        ):
            raise HTTPException(401, headers={"WWW-Authenticate": "Bearer"})
        return configured

    @router.post(
        "/api/v1/acesso/identificacoes",
        status_code=201,
        responses={**_RESPONSES, 200: {"model": IdentificationReceipt}},
    )
    def external(
        data: ExternalIdentification,
        response: Response,
        configured: Annotated[AccessEventsSettings, Depends(external_source)],
    ) -> IdentificationReceipt:
        try:
            with get_sessions().begin() as db:
                receipt, created = receive(
                    db,
                    EventRequest.external(data),
                    lambda: from_source(db, data, configured.similarity_threshold),
                )
        except IdentificationConflict:
            raise HTTPException(409) from None
        response.headers["Cache-Control"] = "no-store"
        response.status_code = 201 if created else 200
        return receipt

    return router

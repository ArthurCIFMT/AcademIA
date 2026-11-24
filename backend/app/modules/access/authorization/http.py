from collections.abc import Callable
from datetime import UTC, datetime
from secrets import compare_digest
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.modules.access.authorization.contracts import DecisionView
from app.modules.access.authorization.delivery import deliver_decision
from app.modules.access.authorization.service import (
    AccessError,
    prepare_decision,
    record_passage,
)
from app.modules.access.integrations.turnstile.contracts import (
    AccessSettings,
    Passage,
    PassageAck,
)
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission

bearer = HTTPBearer(auto_error=False, scheme_name="RetornoCatraca")
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def authorization_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    settings: AccessSettings | None,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(tags=["Autorização de acesso"])

    def verify_turnstile(request: Request, credentials: Credentials) -> None:
        token = settings.turnstile_callback_token if settings else None
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

    @router.post(
        "/api/v1/atendimento/acessos/{event_id}/autorizacao",
        status_code=201,
        responses={
            200: {"model": DecisionView},
            503: {"description": "Configuração inválida"},
        },
    )
    def authorize(
        event_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> DecisionView:
        require_permission(actor, Operation.AUTHORIZE_ACCESS)
        if settings is None:
            raise HTTPException(503)
        try:
            with get_sessions().begin() as db:
                decision_id, created = prepare_decision(db, event_id, settings, clock)
            result = deliver_decision(get_sessions(), decision_id, settings, clock)
        except AccessError as error:
            raise HTTPException(error.status) from None
        response.headers["Cache-Control"] = "no-store"
        response.status_code = 201 if created else 200
        return result

    @router.post(
        "/api/v1/acesso/catraca/passagens",
        status_code=201,
        dependencies=[Depends(verify_turnstile)],
        responses={
            200: {"model": PassageAck},
            410: {"description": "Comando expirado"},
            503: {"description": "Credencial de retorno indisponível"},
        },
    )
    def confirm(data: Passage, response: Response) -> PassageAck:
        try:
            with get_sessions().begin() as db:
                created = record_passage(db, data, clock)
        except AccessError as error:
            raise HTTPException(error.status) from None
        response.headers["Cache-Control"] = "no-store"
        response.status_code = 201 if created else 200
        return PassageAck(schema_version=1, event_id=data.event_id)

    return router

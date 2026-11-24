from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.access.authorization.delivery import deliver_decision
from app.modules.access.authorization.service import AccessError
from app.modules.access.integrations.turnstile.contracts import AccessSettings
from app.modules.access.manual.contracts import ManualConfirmation, ManualReceipt
from app.modules.access.manual.service import prepare_manual_decision
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


def manual_access_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    settings: AccessSettings | None,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(tags=["Confirmação manual de identidade"])

    @router.post(
        "/api/v1/atendimento/acessos/{event_id}/confirmacao-manual",
        status_code=201,
        responses={
            200: {"model": ManualReceipt},
            410: {"description": "A tentativa facial ultrapassou a janela de uso"},
            503: {"description": "Configuração de acesso indisponível"},
        },
    )
    def confirm(
        event_id: UUID,
        data: ManualConfirmation,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> ManualReceipt:
        require_permission(actor, Operation.AUTHORIZE_ACCESS)
        if settings is None:
            raise HTTPException(503)
        sessions = get_sessions()
        try:
            with sessions.begin() as db:
                decision, created = prepare_manual_decision(
                    db,
                    event_id,
                    data,
                    actor_id=actor.user_id,
                    correlation_id=request.state.correlation_id,
                    settings=settings,
                    clock=clock,
                )
            result = deliver_decision(sessions, decision, settings, clock)
        except AccessError as error:
            raise HTTPException(error.status) from None
        response.headers["Cache-Control"] = "no-store"
        response.status_code = 201 if created else 200
        return ManualReceipt(evento_falha_id=event_id, decisao=result)

    return router

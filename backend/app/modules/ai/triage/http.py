from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.ai.triage.contracts import TriageView
from app.modules.ai.triage.service import TriagePermissionError, TriageService
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


def triage_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ia/triagem", tags=["Triagem acadêmica"])

    @router.get("/preparacao")
    def prepare(actor: AuthenticatedActor, response: Response) -> TriageView:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            result = TriageService(get_sessions()).evaluate(actor, actor.user_id)
        except TriagePermissionError:
            raise HTTPException(403) from None
        return TriageView.model_validate(result.model_dump(exclude={"resumo"}))

    return router

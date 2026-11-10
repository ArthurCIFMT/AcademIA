from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.time import UtcTimestamp
from app.modules.notifications.models import NoticeKind
from app.modules.notifications.service import NOTICE_ROLES, pending_notices
from app.policies.http import AuthenticatedActor


class NoticeResponse(BaseModel):
    id: UUID
    tipo: NoticeKind
    criada_em: UtcTimestamp


def notification_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/notificacoes", tags=["Notificações"])

    @router.get("/pendentes")
    def list_pending(
        actor: AuthenticatedActor, response: Response
    ) -> list[NoticeResponse]:
        if actor.roles.isdisjoint(NOTICE_ROLES.values()):
            raise HTTPException(403)
        response.headers["Cache-Control"] = "no-store"
        with get_sessions().begin() as session:
            return [
                NoticeResponse(
                    id=item.id, tipo=NoticeKind(item.tipo), criada_em=item.criada_em
                )
                for item in pending_notices(session, actor)
            ]

    return router

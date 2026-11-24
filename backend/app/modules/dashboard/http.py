from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.dashboard.contracts import DashboardOverview
from app.modules.dashboard.service import overview
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


def dashboard_router(
    get_sessions: Callable[[], sessionmaker[Session]],
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(tags=["Painel administrativo"])

    @router.get("/api/v1/admin/dashboard")
    def administrative_overview(
        actor: AuthenticatedActor, response: Response
    ) -> DashboardOverview:
        require_permission(actor, Operation.READ_DASHBOARD)
        response.headers["Cache-Control"] = "no-store"
        return overview(get_sessions(), at=clock())

    return router

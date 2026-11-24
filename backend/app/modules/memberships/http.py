from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.memberships.schemas import (
    CreateMembership,
    CreatePlan,
    MembershipPage,
    MembershipView,
    PlanView,
    UpdatePlan,
)
from app.modules.memberships.service import (
    MembershipError,
    create_plan,
    enroll,
    list_memberships,
    list_plans,
    update_plan,
)
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def plan_admin(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_PLANS)
    response.headers["Cache-Control"] = "no-store"
    return actor


def attendant(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_MEMBERSHIPS)
    response.headers["Cache-Control"] = "no-store"
    return actor


PlanAdmin = Annotated[Actor, Depends(plan_admin)]
Attendant = Annotated[Actor, Depends(attendant)]
Page = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def memberships_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["Planos e matrículas"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as db:
                yield db
        except MembershipError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/admin/planos")
    def admin_plans(
        _actor: PlanAdmin, pagina: Page = 1, limite: PageSize = 20
    ) -> MembershipPage[PlanView]:
        with transaction() as db:
            return list_plans(db, active_only=False, page=pagina, limit=limite)

    @router.post("/admin/planos", status_code=201)
    def add_plan(data: CreatePlan, request: Request, actor: PlanAdmin) -> PlanView:
        with transaction() as db:
            return create_plan(
                db,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
            )

    @router.put("/admin/planos/{plan_id}")
    def edit_plan(
        plan_id: UUID, data: UpdatePlan, request: Request, actor: PlanAdmin
    ) -> PlanView:
        with transaction() as db:
            return update_plan(
                db,
                plan_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
            )

    @router.get("/atendimento/planos")
    def active_plans(
        _actor: Attendant, pagina: Page = 1, limite: PageSize = 20
    ) -> MembershipPage[PlanView]:
        with transaction() as db:
            return list_plans(db, active_only=True, page=pagina, limit=limite)

    @router.get("/atendimento/clientes/{client_id}/matriculas")
    def history(
        client_id: UUID, _actor: Attendant, pagina: Page = 1, limite: PageSize = 20
    ) -> MembershipPage[MembershipView]:
        with transaction() as db:
            return list_memberships(
                db, client_id, now=datetime.now(UTC), page=pagina, limit=limite
            )

    @router.post(
        "/atendimento/clientes/{client_id}/matriculas",
        status_code=201,
    )
    def create(
        client_id: UUID, data: CreateMembership, request: Request, actor: Attendant
    ) -> MembershipView:
        with transaction() as db:
            return enroll(
                db,
                client_id,
                data,
                attendant_id=actor.user_id,
                correlation=request.state.correlation_id,
                now=datetime.now(UTC),
            )

    return router

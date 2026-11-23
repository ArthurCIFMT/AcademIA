from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.classes.service import (
    ClassError,
    ClassPage,
    ClassRevision,
    CreateClass,
    ManagedClass,
    PublicClass,
    UpdateClass,
    admin_schedule,
    cancel_occurrence,
    create_occurrence,
    public_schedule,
    update_occurrence,
)
from app.policies.access import Actor, Operation
from app.policies.http import AuthenticatedActor, require_permission


def class_admin(actor: AuthenticatedActor, response: Response) -> Actor:
    require_permission(actor, Operation.MANAGE_CLASSES)
    response.headers["Cache-Control"] = "no-store"
    return actor


ClassAdmin = Annotated[Actor, Depends(class_admin)]
PageNumber = Annotated[int, Query(ge=1, le=1_000_000)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def classes_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(tags=["Agenda de aulas"])

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as db:
                yield db
        except ClassError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/api/v1/aulas")
    def public_list(
        response: Response, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> ClassPage[PublicClass]:
        response.headers["Cache-Control"] = "no-store"
        with transaction() as db:
            return public_schedule(db, now=datetime.now(UTC), page=pagina, limit=limite)

    @router.get("/api/v1/admin/aulas")
    def managed_list(
        _actor: ClassAdmin, pagina: PageNumber = 1, limite: PageSize = 20
    ) -> ClassPage[ManagedClass]:
        with transaction() as db:
            return admin_schedule(db, page=pagina, limit=limite)

    @router.post("/api/v1/admin/aulas", status_code=201)
    def create(data: CreateClass, request: Request, actor: ClassAdmin) -> ManagedClass:
        with transaction() as db:
            return create_occurrence(
                db,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
            )

    @router.put("/api/v1/admin/aulas/{occurrence_id}")
    def update(
        occurrence_id: UUID, data: UpdateClass, request: Request, actor: ClassAdmin
    ) -> ManagedClass:
        with transaction() as db:
            return update_occurrence(
                db,
                occurrence_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
            )

    @router.post("/api/v1/admin/aulas/{occurrence_id}/cancelamento")
    def cancel(
        occurrence_id: UUID, data: ClassRevision, request: Request, actor: ClassAdmin
    ) -> ManagedClass:
        with transaction() as db:
            return cancel_occurrence(
                db,
                occurrence_id,
                data,
                actor_id=actor.user_id,
                correlation=request.state.correlation_id,
            )

    return router

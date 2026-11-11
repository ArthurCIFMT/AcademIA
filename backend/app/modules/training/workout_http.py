from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.training.workout_schemas import (
    CreateWorkout,
    UpdateWorkout,
    WorkoutContext,
    WorkoutPage,
    WorkoutView,
)
from app.modules.training.workouts import (
    WorkoutError,
    create_draft,
    get_workout,
    update_draft,
    workout_context,
    workout_history,
)
from app.policies.http import AuthenticatedActor


def workout_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/treinos/clientes/{client_id}", tags=["Fichas manuais"]
    )

    @contextmanager
    def transaction(response: Response) -> Iterator[Session]:
        response.headers["Cache-Control"] = "no-store"
        try:
            with get_sessions().begin() as session:
                yield session
        except WorkoutError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/contexto")
    def context(
        client_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> WorkoutContext:
        with transaction(response) as session:
            return workout_context(session, actor, client_id)

    @router.get("/versoes")
    def history(
        client_id: UUID,
        actor: AuthenticatedActor,
        response: Response,
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> WorkoutPage:
        with transaction(response) as session:
            return workout_history(session, actor, client_id, pagina, limite)

    @router.get("/versoes/{version_id}")
    def detail(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> WorkoutView:
        with transaction(response) as session:
            return get_workout(session, actor, client_id, version_id)

    @router.post("/rascunhos", status_code=201)
    def create(
        client_id: UUID,
        data: CreateWorkout,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> WorkoutView:
        with transaction(response) as session:
            return create_draft(
                session, actor, client_id, data, request.state.correlation_id
            )

    @router.put("/rascunhos/{version_id}")
    def update(
        client_id: UUID,
        version_id: UUID,
        data: UpdateWorkout,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> WorkoutView:
        with transaction(response) as session:
            return update_draft(
                session,
                actor,
                client_id,
                version_id,
                data,
                request.state.correlation_id,
            )

    # Publicação/revisão pertencem ao mesmo módulo e usam a mesma sessão autenticada.
    from app.modules.training.review_http import review_router

    router.include_router(review_router(get_sessions))
    return router

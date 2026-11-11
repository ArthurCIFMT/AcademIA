from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, sessionmaker

from app.modules.equipment.service import available_resources
from app.modules.training.catalog import (
    CatalogError,
    catalog_page,
    create_exercise,
    eligible_exercises,
    exercise_detail,
    update_exercise,
)
from app.modules.training.schemas import (
    ExerciseCandidate,
    ExerciseEquipment,
    ExerciseFields,
    ExercisePage,
    ExerciseUpdate,
    ExerciseView,
)
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


def exercise_access(actor: AuthenticatedActor, response: Response) -> None:
    require_permission(actor, Operation.MANAGE_EXERCISES)
    response.headers["Cache-Control"] = "no-store"


def exercise_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/exercicios",
        tags=["Exercícios"],
        dependencies=[Depends(exercise_access)],
    )

    @contextmanager
    def transaction() -> Iterator[Session]:
        try:
            with get_sessions().begin() as session:
                yield session
        except CatalogError as exc:
            raise HTTPException(exc.status) from None

    @router.get("")
    def listing(
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExercisePage[ExerciseView]:
        with transaction() as session:
            return catalog_page(session, pagina, limite)

    @router.get("/recursos")
    def resources() -> list[ExerciseEquipment]:
        with transaction() as session:
            return [
                ExerciseEquipment(
                    id=item.id, nome=item.nome, disponivel=item.disponivel
                )
                for item in available_resources(session)
            ]

    @router.get("/elegiveis")
    def candidates() -> list[ExerciseCandidate]:
        with transaction() as session:
            return eligible_exercises(session)

    @router.get("/{exercise_id}")
    def detail(exercise_id: UUID) -> ExerciseView:
        with transaction() as session:
            return exercise_detail(session, exercise_id)

    @router.post("", status_code=201)
    def create(
        data: ExerciseFields, actor: AuthenticatedActor, request: Request
    ) -> ExerciseView:
        with transaction() as session:
            return create_exercise(
                session, data, actor.user_id, request.state.correlation_id
            )

    @router.put("/{exercise_id}")
    def edit(
        exercise_id: UUID,
        data: ExerciseUpdate,
        actor: AuthenticatedActor,
        request: Request,
    ) -> ExerciseView:
        with transaction() as session:
            return update_exercise(
                session, exercise_id, data, actor.user_id, request.state.correlation_id
            )

    return router

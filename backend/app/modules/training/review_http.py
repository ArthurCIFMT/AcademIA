from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from app.modules.notifications.models import DeliveryState
from app.modules.training.publication import (
    publish_manual,
    published_workout,
    record_opinion,
    review_detail,
    review_queue,
    send_review_notice,
)
from app.modules.training.published import published_history, read_published
from app.modules.training.published_schemas import PublishedHistory, PublishedWorkout
from app.modules.training.review_schemas import (
    PublishWorkout,
    RetryNotice,
    ReviewDetail,
    ReviewQueue,
    ReviewWorkout,
)
from app.modules.training.workouts import WorkoutError
from app.policies.http import AuthenticatedActor


class MailStatus(BaseModel):
    estado: DeliveryState
    tentativas: int


class PublicationResult(BaseModel):
    treino: ReviewDetail
    aviso_email: MailStatus | None


def review_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(tags=["Publicação e parecer"])

    @contextmanager
    def transaction(response: Response) -> Iterator[Session]:
        response.headers["Cache-Control"] = "no-store"
        try:
            with get_sessions().begin() as session:
                yield session
        except WorkoutError as exc:
            raise HTTPException(exc.status) from None

    @router.get("/versoes/{version_id}/revisao")
    def review(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ReviewDetail:
        with transaction(response) as session:
            return review_detail(session, actor, client_id, version_id)

    @router.post("/versoes/{version_id}/publicacao")
    def publish(
        client_id: UUID,
        version_id: UUID,
        data: PublishWorkout,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> PublicationResult:
        with transaction(response) as session:
            result = publish_manual(
                session,
                actor,
                client_id,
                version_id,
                data,
                request.state.correlation_id,
            )
        try:
            delivery = send_review_notice(get_sessions(), actor, client_id, version_id)
        except WorkoutError:
            # Designação mudou depois do commit. A fila segue a nova designação.
            delivery = None
        return PublicationResult(
            treino=result,
            aviso_email=MailStatus(
                estado=delivery.state,
                tentativas=delivery.attempts,
            )
            if delivery
            else None,
        )

    @router.post("/versoes/{version_id}/parecer")
    def opinion(
        client_id: UUID,
        version_id: UUID,
        data: ReviewWorkout,
        actor: AuthenticatedActor,
        request: Request,
        response: Response,
    ) -> ReviewDetail:
        with transaction(response) as session:
            return record_opinion(
                session,
                actor,
                client_id,
                version_id,
                data,
                request.state.correlation_id,
            )

    @router.post("/versoes/{version_id}/aviso")
    def resend(
        client_id: UUID,
        version_id: UUID,
        data: RetryNotice,
        actor: AuthenticatedActor,
        response: Response,
    ) -> MailStatus | None:
        response.headers["Cache-Control"] = "no-store"
        try:
            result = send_review_notice(
                get_sessions(),
                actor,
                client_id,
                version_id,
                retry_after=data.tentativa_anterior,
            )
        except WorkoutError as exc:
            raise HTTPException(exc.status) from None
        return (
            MailStatus(estado=result.state, tentativas=result.attempts)
            if result
            else None
        )

    @router.get("/publicadas")
    def retained(
        client_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> PublishedHistory:
        with transaction(response) as session:
            return published_history(session, actor, client_id)

    @router.get("/publicadas/{version_id}/ficha")
    def retained_version(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> PublishedWorkout:
        with transaction(response) as session:
            return read_published(session, actor, client_id, version_id)

    @router.get(
        "/publicadas/{version_id}/exportacao",
        response_model=PublishedWorkout,
        response_class=JSONResponse,
    )
    def export(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> JSONResponse:
        with transaction(response) as session:
            data = read_published(session, actor, client_id, version_id)
        filename = f"academia-treino-{data.ficha.numero}-{version_id}.json"
        return JSONResponse(
            data.model_dump(mode="json"),
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.get("/atual")
    def current(
        client_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ReviewDetail | None:
        with transaction(response) as session:
            return published_workout(session, actor, client_id)

    @router.get("/publicadas/{version_id}")
    def published(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ReviewDetail | None:
        with transaction(response) as session:
            return published_workout(session, actor, client_id, version_id)

    return router


def review_queue_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/treinos", tags=["Publicação e parecer"])

    @router.get("/pendentes")
    def queue(
        actor: AuthenticatedActor,
        response: Response,
        pagina: Annotated[int, Query(ge=1, le=1_000_000)] = 1,
        limite: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ReviewQueue:
        response.headers["Cache-Control"] = "no-store"
        try:
            with get_sessions().begin() as session:
                return review_queue(session, actor, pagina, limite)
        except WorkoutError as exc:
            raise HTTPException(exc.status) from None

    return router

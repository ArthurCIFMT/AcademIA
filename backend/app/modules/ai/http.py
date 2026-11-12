from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import StrictModel
from app.modules.ai.followup import FollowupService, GenerationContext, version_context
from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.state import RateLimited
from app.modules.ai.ports.execution import (
    ContextDenied,
    ExecutionConflict,
    ProviderError,
)
from app.modules.ai.schemas.execution import Consumption, RunRequest, RunResult
from app.modules.training.workouts import WorkoutError
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


class GenerateRequest(StrictModel):
    solicitacao_id: UUID


class ExecutionView(StrictModel):
    solicitacao_id: UUID
    estado: str
    motivo: str
    versao_publicada_id: UUID | None
    consumo: list[Consumption]


class FollowupView(StrictModel):
    execucao: ExecutionView
    geracao: GenerationContext | None


def view(result: RunResult) -> ExecutionView:
    return ExecutionView.model_validate(
        result.model_dump(include=set(ExecutionView.model_fields))
    )


def generation_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ia/fichas", tags=["Geração assistida"])

    def service(actor: AuthenticatedActor, response: Response) -> GenerationService:
        response.headers["Cache-Control"] = "no-store"
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        return GenerationService(get_sessions())

    @router.post("/execucoes")
    def generate(
        data: GenerateRequest, actor: AuthenticatedActor, response: Response
    ) -> ExecutionView:
        instance = service(actor, response)
        try:
            return view(
                instance.generate(
                    actor,
                    actor.user_id,
                    RunRequest(
                        solicitacao_id=data.solicitacao_id, finalidade="GERACAO"
                    ),
                )
            )
        except ContextDenied:
            raise HTTPException(403) from None
        except ExecutionConflict:
            raise HTTPException(409) from None
        except ProviderError:
            raise HTTPException(503) from None
        except RateLimited as error:
            raise HTTPException(
                429, headers={"Retry-After": str(error.retry_after)}
            ) from None

    @router.get("/execucoes/{id}")
    def status(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ExecutionView:
        try:
            return view(service(actor, response).status(actor, id))
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None

    @router.delete("/execucoes/{id}")
    def cancel(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ExecutionView:
        try:
            return view(service(actor, response).cancel(actor, id))
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None

    @router.get("/execucoes/{id}/acompanhamento")
    def followup(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> FollowupView:
        service(actor, response)
        try:
            result, context = FollowupService(get_sessions()).own(actor, id)
            return FollowupView(execucao=view(result), geracao=context)
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None
        except WorkoutError as error:
            raise HTTPException(error.status) from None

    @router.get("/clientes/{client_id}/versoes/{version_id}/contexto")
    def context(
        client_id: UUID, version_id: UUID, actor: AuthenticatedActor, response: Response
    ) -> GenerationContext:
        response.headers["Cache-Control"] = "no-store"
        try:
            with get_sessions().begin() as session:
                return version_context(session, actor, client_id, version_id)
        except WorkoutError as error:
            raise HTTPException(error.status) from None

    return router

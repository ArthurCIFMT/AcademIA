from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import StrictModel
from app.modules.ai.generation import GenerationService
from app.modules.ai.persistence.state import RateLimited
from app.modules.ai.ports.execution import ContextDenied, ExecutionConflict
from app.modules.ai.schemas.execution import Consumption, RunRequest, RunResult
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


def view(result: RunResult) -> ExecutionView:
    return ExecutionView.model_validate(
        result.model_dump(include=set(ExecutionView.model_fields))
    )


def generation_router(get_sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ia/fichas/execucoes", tags=["Geração assistida"])

    def service(actor: AuthenticatedActor, response: Response) -> GenerationService:
        response.headers["Cache-Control"] = "no-store"
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        return GenerationService(get_sessions())

    @router.post("")
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
        except RateLimited as error:
            raise HTTPException(
                429, headers={"Retry-After": str(error.retry_after)}
            ) from None

    @router.get("/{id}")
    def status(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ExecutionView:
        try:
            return view(service(actor, response).status(actor, id))
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None

    @router.delete("/{id}")
    def cancel(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> ExecutionView:
        try:
            return view(service(actor, response).cancel(actor, id))
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None

    return router

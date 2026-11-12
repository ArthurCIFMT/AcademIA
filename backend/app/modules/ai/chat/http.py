from collections.abc import Callable
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import Field, StringConstraints, field_validator, model_validator
from sqlalchemy.orm import Session, sessionmaker

from app.contracts.structured import StrictModel
from app.modules.ai.chat.service import ChatService
from app.modules.ai.chat.views import ChatView
from app.modules.ai.persistence.state import RateLimited
from app.modules.ai.ports.execution import (
    ContextDenied,
    ExecutionConflict,
    ProviderError,
)
from app.modules.ai.schemas.execution import RunRequest
from app.modules.training.workouts import WorkoutError
from app.policies.access import Operation
from app.policies.http import AuthenticatedActor, require_permission


class Ask(StrictModel):
    solicitacao_id: UUID
    mensagem: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]
    finalidade: Literal["DUVIDA", "ADAPTACAO"] = "DUVIDA"
    versao_base_id: UUID | None = None
    onboarding_id: UUID | None = None
    dia_alvo: Annotated[int, Field(strict=True, ge=1, le=6)] | None = None

    @field_validator("mensagem")
    @classmethod
    def no_controls(cls, value: str) -> str:
        if any(ord(c) < 32 and c not in "\n\t" for c in value):
            raise ValueError("Mensagem inválida.")
        return value

    @model_validator(mode="after")
    def valid_mode(self) -> "Ask":
        if self.finalidade == "ADAPTACAO":
            if not self.versao_base_id or not self.onboarding_id or not self.dia_alvo:
                raise ValueError("Confirme onboarding, versão e dia-alvo.")
        elif self.versao_base_id or self.onboarding_id or self.dia_alvo:
            raise ValueError("Dúvida não seleciona ficha/onboarding.")
        return self


def chat_router(sessions: Callable[[], sessionmaker[Session]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ia/chat", tags=["Chat de treino"])

    @router.post("")
    def ask(data: Ask, actor: AuthenticatedActor, response: Response) -> ChatView:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            instance = ChatService(sessions())
            instance.ask(
                actor,
                RunRequest(
                    solicitacao_id=data.solicitacao_id,
                    mensagem=data.mensagem,
                    finalidade=data.finalidade,
                    versao_base_id=data.versao_base_id,
                    dia_alvo=data.dia_alvo,
                    onboarding_confirmado_id=data.onboarding_id,
                ),
                data.onboarding_id,
            )
            return instance.turn(actor, data.solicitacao_id)
        except ContextDenied:
            raise HTTPException(403) from None
        except ExecutionConflict:
            raise HTTPException(409) from None
        except ProviderError:
            raise HTTPException(503) from None
        except ValueError:
            raise HTTPException(422) from None
        except WorkoutError as error:
            raise HTTPException(error.status) from None
        except RateLimited as error:
            raise HTTPException(
                429, headers={"Retry-After": str(error.retry_after)}
            ) from None

    @router.get("")
    def history(
        actor: AuthenticatedActor,
        response: Response,
        page: Annotated[int, Query(ge=1, le=10000)] = 1,
    ) -> list[ChatView]:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            return ChatService(sessions()).history(actor, page)
        except ContextDenied:
            raise HTTPException(403) from None

    @router.get("/contexto/adaptacao")
    def adaptation_context(
        actor: AuthenticatedActor, response: Response
    ) -> dict[str, object]:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            return ChatService(sessions()).adaptation_context(actor)
        except ContextDenied:
            raise HTTPException(403) from None
        except WorkoutError as error:
            raise HTTPException(error.status) from None

    @router.get("/{id}")
    def turn(id: UUID, actor: AuthenticatedActor, response: Response) -> ChatView:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            return ChatService(sessions()).turn(actor, id)
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None
        except ExecutionConflict:
            raise HTTPException(409) from None

    @router.get("/{id}/diferencas")
    def differences(
        id: UUID, actor: AuthenticatedActor, response: Response
    ) -> dict[str, object]:
        require_permission(actor, Operation.USE_AI_CONTEXT, client_id=actor.user_id)
        response.headers["Cache-Control"] = "no-store"
        try:
            return ChatService(sessions()).differences(actor, id)
        except ContextDenied:
            raise HTTPException(403) from None
        except KeyError:
            raise HTTPException(404) from None
        except WorkoutError as error:
            raise HTTPException(error.status) from None
        except ExecutionConflict:
            raise HTTPException(409) from None

    return router

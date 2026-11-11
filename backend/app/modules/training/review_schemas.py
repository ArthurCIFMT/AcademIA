from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.contracts.time import UtcTimestamp
from app.modules.onboarding.schemas import PrivateInput
from app.modules.training.workout_schemas import Order, WorkoutView


class PublishWorkout(PrivateInput):
    solicitacao_id: UUID
    revisao: Order
    onboarding_id: UUID
    versao_base_id: UUID | None
    restricoes_conferidas: Literal[True]


class ReviewWorkout(PrivateInput):
    solicitacao_id: UUID
    estado: Literal["ACEITO", "REJEITADO"]
    motivo: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None
    ) = None

    @model_validator(mode="after")
    def require_reason(self) -> Self:
        if self.motivo is not None and "\x00" in self.motivo:
            raise ValueError("Texto inválido.")
        if self.estado == "REJEITADO" and not self.motivo:
            raise ValueError("Informe o motivo da rejeição.")
        return self


class OpinionView(BaseModel):
    id: UUID | None = None
    estado: Literal["PENDENTE", "ACEITO", "REJEITADO"] = "PENDENTE"
    instrutor_id: UUID | None = None
    criado_em: UtcTimestamp | None = None
    motivo: str | None = None


class ValidationView(BaseModel):
    revisao: int
    validado_por: UUID
    validado_em: UtcTimestamp


class ReviewDetail(BaseModel):
    ficha: WorkoutView
    parecer: OpinionView
    validacao: ValidationView | None


class ReviewQueueItem(BaseModel):
    cliente_id: UUID
    cliente_nome: str
    versao_id: UUID
    numero: int
    publicada_em: UtcTimestamp


class ReviewQueue(BaseModel):
    itens: list[ReviewQueueItem]
    pagina: int
    limite: int
    total: int


class RetryNotice(PrivateInput):
    tentativa_anterior: Annotated[int, Field(strict=True, ge=1, le=2)] | None

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.contracts.time import UtcTimestamp
from app.modules.access.integrations.turnstile.contracts import (
    DecisionResult,
    DeliveryFailure,
    TurnstileDirection,
)

DecisionReason = Literal[
    "ENTRADA_PERMITIDA",
    "SAIDA_PERMITIDA",
    "IDENTIDADE_NAO_CONFIRMADA",
    "IDENTIFICACAO_FORA_DA_JANELA",
    "CLIENTE_INABILITADO",
    "SEM_MATRICULA_VIGENTE",
    "MODALIDADE_INCOMPATIVEL",
    "LIMITE_DIARIO",
]


class CommandView(BaseModel):
    request_id: UUID
    direcao: TurnstileDirection
    expira_em: UtcTimestamp
    estado: Literal["CRIADO", "FALHOU", "ACEITO", "CONFIRMADO", "EXPIRADO"]
    falha_envio: DeliveryFailure | None
    passagem_evento_id: UUID | None


class DecisionView(BaseModel):
    id: UUID
    evento_id: UUID
    matricula_id: UUID | None
    resultado: DecisionResult
    motivo: DecisionReason
    criada_em: UtcTimestamp
    regra: dict[str, int | str | None]
    comando: CommandView

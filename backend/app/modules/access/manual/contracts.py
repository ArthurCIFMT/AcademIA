from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.modules.access.authorization.contracts import DecisionView


class ManualConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    cliente_id: UUID
    motivo: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)
    ]
    identidade_confirmada: Literal[True]

    @field_validator("motivo")
    @classmethod
    def valid_reason(cls, value: str) -> str:
        if any(ord(char) < 32 for char in value):
            raise ValueError("Informe um motivo sem caracteres de controle.")
        return value

    @field_validator("identidade_confirmada", mode="before")
    @classmethod
    def explicit_confirmation(cls, value: object) -> object:
        if value is not True:
            raise ValueError("Confirme expressamente a identidade do cliente.")
        return value


class ManualReceipt(BaseModel):
    evento_falha_id: UUID
    origem: Literal["ATENDIMENTO_MANUAL"] = "ATENDIMENTO_MANUAL"
    decisao: DecisionView

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

PositiveInt = Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)]
LimitWindow = Literal["DIA_CIVIL"]
MembershipState = Literal["ATIVA", "ENCERRADA"]
MembershipSituation = Literal["FUTURA", "VIGENTE", "VENCIDA", "ENCERRADA"]


class MembershipInput(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class PlanFields(MembershipInput):
    nome: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    modalidade: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    duracao_dias: PositiveInt
    limite_acessos: PositiveInt | None = None
    ativo: Annotated[bool, Field(strict=True)]

    @field_validator("nome", "modalidade")
    @classmethod
    def valid_text(cls, value: str) -> str:
        if not value or "\x00" in value:
            raise ValueError("Texto inválido.")
        return value


class CreatePlan(PlanFields):
    solicitacao_id: UUID


class UpdatePlan(PlanFields):
    revisao: PositiveInt


class PlanView(PlanFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    revisao: int = Field(validation_alias="revision")


class CreateMembership(MembershipInput):
    solicitacao_id: UUID
    plano_id: UUID
    plano_revisao: PositiveInt
    inicio: date

    @field_validator("inicio", mode="before")
    @classmethod
    def civil_date(cls, value: object) -> date:
        if type(value) is date:
            return value
        if isinstance(value, str):
            result = date.fromisoformat(value)
            if result.isoformat() == value:
                return result
        raise ValueError("Informe a data civil em AAAA-MM-DD.")


class AccessLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    limite_acessos: PositiveInt | None
    janela_limite: LimitWindow | None


class MembershipView(BaseModel):
    id: UUID
    cliente_id: UUID
    plano_id: UUID
    atendente_id: UUID
    inicio: date
    fim: date
    estado: MembershipState
    situacao: MembershipSituation
    modalidade_contratada: str
    limites_snapshot: AccessLimits


class MembershipPage[Item](BaseModel):
    itens: list[Item]
    pagina: int
    limite: int
    total: int

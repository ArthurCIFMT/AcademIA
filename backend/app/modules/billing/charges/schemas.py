from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.contracts.time import UtcTimestamp
from app.modules.billing.money import Amount

ChargeState = Literal["ABERTA", "CANCELADA"]
ChargeSituation = Literal["ABERTA", "VENCIDA", "QUITADA", "CANCELADA"]
OverduePolicy = Literal["SOMENTE_INFORMATIVA"]


def civil_date(value: object) -> date:
    if type(value) is date:
        return value
    if isinstance(value, str):
        result = date.fromisoformat(value)
        if value == result.isoformat():
            return result
    raise ValueError("Informe a data civil em AAAA-MM-DD.")


CivilDate = Annotated[date, BeforeValidator(civil_date)]


class ChargeFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competencia: CivilDate
    vencimento: CivilDate
    valor: Amount
    matricula_id: UUID | None = None

    @field_validator("competencia")
    @classmethod
    def first_of_month(cls, value: date) -> date:
        if value.day != 1:
            raise ValueError("Use o primeiro dia do mês de competência.")
        return value


class CreateCharge(ChargeFields):
    solicitacao_id: UUID


class UpdateCharge(ChargeFields):
    estado: ChargeState
    revisao: Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)]


class ChargeSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    competencia: date
    vencimento: date
    valor: Decimal
    matricula_id: UUID | None
    estado: ChargeState


class ChargeView(ChargeSnapshot):
    id: UUID
    revisao: int
    situacao: ChargeSituation
    valor_pago: Decimal
    saldo: Decimal


class Page[T](BaseModel):
    itens: list[T]
    pagina: int
    limite: int
    total: int


class ChargePage(Page[ChargeView]):
    cliente_nome: str
    politica_inadimplencia: OverduePolicy


class RevisionView(BaseModel):
    revisao: int
    autor_nome: str | None
    registrado_em: UtcTimestamp
    dados: ChargeSnapshot


class MembershipChoice(BaseModel):
    id: UUID
    inicio: date
    fim: date
    modalidade: str

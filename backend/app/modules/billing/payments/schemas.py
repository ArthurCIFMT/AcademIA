from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.contracts.time import UtcTimestamp

Method = Literal["PIX", "DINHEIRO", "CARTAO", "TRANSFERENCIA", "OUTRO"]
Amount = Annotated[
    str, StringConstraints(pattern=r"^(0|[1-9][0-9]{0,9})(\.[0-9]{1,2})?$")
]
Reference = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]


class RegisterPayment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    solicitacao_id: UUID
    valor: Amount
    pago_em: date
    metodo: Method
    referencia_externa: Reference

    @field_validator("valor")
    @classmethod
    def nonzero(cls, value: str) -> str:
        if Decimal(value) <= 0:
            raise ValueError("Informe um valor positivo.")
        return value


class VoidPayment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivo: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)
    ]


class CorrectPayment(RegisterPayment, VoidPayment):
    pass


class PaymentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cliente_id: UUID
    valor: Decimal = Field(gt=0)
    pago_em: date
    metodo: Method
    referencia_externa: str
    estado: Literal["CONFIRMADO", "ANULADO"]
    confirmado_em: UtcTimestamp
    registrado_por_id: UUID
    registrado_por_nome: str | None
    substitui_id: UUID | None
    anulado_em: UtcTimestamp | None
    anulado_por_id: UUID | None
    anulado_por_nome: str | None
    motivo_anulacao: str | None


class PaymentPage(BaseModel):
    cliente_nome: str
    itens: list[PaymentView]
    pagina: int
    limite: int
    total: int

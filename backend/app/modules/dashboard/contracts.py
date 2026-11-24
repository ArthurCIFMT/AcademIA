from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, NonNegativeInt

from app.contracts.time import UtcTimestamp


class Available[T](BaseModel):
    estado: Literal["DISPONIVEL"] = "DISPONIVEL"
    valor: T


class Unavailable(BaseModel):
    estado: Literal["INDISPONIVEL"] = "INDISPONIVEL"


type Indicator[T] = Annotated[Available[T] | Unavailable, Field(discriminator="estado")]


class WeekCount(BaseModel):
    inicio: date
    visitas: NonNegativeInt


class HourCount(BaseModel):
    hora: Annotated[int, Field(ge=0, le=23)]
    visitas: NonNegativeInt


class DayCount(BaseModel):
    data: date
    visitas: NonNegativeInt
    por_hora: list[HourCount]


class Frequency(BaseModel):
    semanas: list[WeekCount]
    dias: list[DayCount]


class DashboardOverview(BaseModel):
    consultado_em: UtcTimestamp
    clientes_ativos: Indicator[NonNegativeInt]
    clientes_matriculados: Indicator[NonNegativeInt]
    funcionarios: Indicator[NonNegativeInt]
    lotacao: Indicator[NonNegativeInt]
    frequencia: Indicator[Frequency]

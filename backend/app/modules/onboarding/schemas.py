from decimal import Decimal
from math import isfinite
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    StrictBool,
    model_validator,
)

from app.contracts.time import UtcTimestamp

Answer = Literal["SIM", "NAO", "NAO_SEI"]
Severity = Literal["NAO_GRAVE", "GRAVE", "NAO_SEI"]
Category = Literal[
    "CARDIACA", "RESPIRATORIA", "METABOLICA", "MUSCULOESQUELETICA", "OUTRA"
]
Goal = Literal["CONDICIONAMENTO", "FORCA", "HIPERTROFIA", "ATIVIDADE_GERAL"]
Experience = Literal["INICIANTE", "INTERMEDIARIO", "AVANCADO"]
Activity = Literal["SEDENTARIO", "LEVE", "MODERADO", "ELEVADO"]


def _integer(value: object) -> object:
    if type(value) is int or (type(value) is float and value.is_integer()):
        return value
    raise ValueError("Informe um número inteiro.")


def _decimal(value: object) -> object:
    if type(value) is int:
        return value
    if type(value) is float and isfinite(value):
        exponent = Decimal(str(value)).normalize().as_tuple().exponent
        if isinstance(exponent, int) and exponent >= -1:
            return value
    raise ValueError("Informe um número com até uma casa decimal.")


Height = Annotated[
    float, Field(ge=50, le=250, multiple_of=0.1), BeforeValidator(_decimal)
]
Weight = Annotated[
    float, Field(ge=20, le=350, multiple_of=0.1), BeforeValidator(_decimal)
]
Days = Annotated[int, Field(ge=1, le=6), BeforeValidator(_integer)]
Duration = Annotated[int, Field(ge=20, le=120), BeforeValidator(_integer)]
Description = Annotated[str, Field(min_length=1, max_length=300)]
MedicineName = Annotated[str, Field(min_length=1, max_length=100)]
MedicineNote = Annotated[str, Field(max_length=300)]
Region = Annotated[str, Field(min_length=1, max_length=80)]
Notes = Annotated[str, Field(max_length=1000)]
Revision = Annotated[int, Field(strict=True, ge=1)]

_FLAGS = (
    ("possui_condicoes_saude", "condicoes_saude"),
    ("usa_medicamentos", "medicamentos"),
    ("possui_dor_lesao_limitacao", "limitacoes"),
)


_CONDITIONS: list[JsonValue] = [
    {
        "if": {"properties": {flag: {"const": "SIM"}}, "required": [flag]},
        "then": {"properties": {items: {"minItems": 1}}},
        "else": {"properties": {items: {"maxItems": 0}}},
    }
    for flag, items in _FLAGS
]


class PrivateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class Condition(PrivateInput):
    categoria: Category
    descricao: Description
    gravidade_declarada: Severity


class Medication(PrivateInput):
    nome: MedicineName
    observacao: MedicineNote


class Limitation(PrivateInput):
    regiao: Region
    descricao: Description
    gravidade_declarada: Severity


class DraftCondition(PrivateInput):
    categoria: Category | None = None
    descricao: Description | None = None
    gravidade_declarada: Severity | None = None


class DraftMedication(PrivateInput):
    nome: MedicineName | None = None
    observacao: MedicineNote | None = None


class DraftLimitation(PrivateInput):
    regiao: Region | None = None
    descricao: Description | None = None
    gravidade_declarada: Severity | None = None


class DraftData(PrivateInput):
    altura_cm: Height | None = None
    peso_kg: Weight | None = None
    objetivo_principal: Goal | None = None
    experiencia: Experience | None = None
    nivel_atividade: Activity | None = None
    dias_semana: Days | None = None
    duracao_sessao_min: Duration | None = None
    possui_condicoes_saude: Answer | None = None
    condicoes_saude: Annotated[list[DraftCondition], Field(max_length=10)] | None = None
    usa_medicamentos: Answer | None = None
    medicamentos: Annotated[list[DraftMedication], Field(max_length=10)] | None = None
    possui_dor_lesao_limitacao: Answer | None = None
    limitacoes: Annotated[list[DraftLimitation], Field(max_length=8)] | None = None
    restricao_exercicio_declarada: Answer | None = None
    evento_saude_importante_recente: Answer | None = None
    observacoes: Notes | None = None


class OnboardingData(PrivateInput):
    model_config = ConfigDict(json_schema_extra={"allOf": _CONDITIONS})

    altura_cm: Height
    peso_kg: Weight
    objetivo_principal: Goal
    experiencia: Experience
    nivel_atividade: Activity
    dias_semana: Days
    duracao_sessao_min: Duration
    possui_condicoes_saude: Answer
    condicoes_saude: Annotated[list[Condition], Field(max_length=10)]
    usa_medicamentos: Answer
    medicamentos: Annotated[list[Medication], Field(max_length=10)]
    possui_dor_lesao_limitacao: Answer
    limitacoes: Annotated[list[Limitation], Field(max_length=8)]
    restricao_exercicio_declarada: Answer
    evento_saude_importante_recente: Answer
    observacoes: Notes

    @model_validator(mode="after")
    def check_answers(self) -> Self:
        for flag, items in _FLAGS:
            if (getattr(self, flag) == "SIM") != bool(getattr(self, items)):
                raise ValueError(
                    "As ocorrências precisam corresponder à resposta declarada."
                )
        return self


class DraftChange(PrivateInput):
    versao_base: UUID | None
    revisao: Revision | None
    dados: DraftData


class Completion(PrivateInput):
    versao_base: UUID | None
    revisao: Revision


class ConfirmUpdate(PrivateInput):
    versao_base: UUID
    revisao: Revision | None = None
    confirmado: StrictBool
    dados: OnboardingData

    @model_validator(mode="after")
    def require_confirmation(self) -> Self:
        if not self.confirmado:
            raise ValueError("Confirme a atualização para salvar uma nova versão.")
        return self


class VersionInfo(BaseModel):
    id: UUID
    numero: int
    schema_version: Literal[1] = 1
    revisao: int
    criado_por: UUID


class DraftView(VersionInfo):
    estado: Literal["RASCUNHO"] = "RASCUNHO"
    dados: DraftData


class SnapshotView(VersionInfo):
    estado: Literal["CONCLUIDO"] = "CONCLUIDO"
    dados: OnboardingData
    idade_snapshot: int
    concluido_em: UtcTimestamp
    concluido_por: UUID


class OwnOnboarding(BaseModel):
    rascunho: DraftView | None
    concluido: SnapshotView | None

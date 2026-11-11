from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.contracts.time import UtcTimestamp
from app.modules.onboarding.schemas import PrivateInput
from app.modules.training.schemas import ExerciseCandidate

ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
]
Order = Annotated[int, Field(strict=True, ge=1)]
MoneyWeight = Annotated[Decimal, Field(ge=0, le=Decimal("999999.99"), decimal_places=2)]


class WorkoutItemInput(PrivateInput):
    exercicio_id: UUID
    equipamento_ids: Annotated[list[UUID], Field(max_length=20)]
    series: Annotated[int, Field(strict=True, ge=1, le=100)]
    repeticoes: ShortText
    carga_kg: MoneyWeight | None = None
    intervalo_segundos: Annotated[int, Field(strict=True, ge=0, le=3600)]
    cadencia: ShortText | None = None
    observacoes: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None
    ) = None

    @field_validator("repeticoes", "cadencia", "observacoes")
    @classmethod
    def valid_text(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("Texto inválido.")
        return value

    @field_validator("equipamento_ids")
    @classmethod
    def unique_resources(cls, ids: list[UUID]) -> list[UUID]:
        if len(set(ids)) != len(ids):
            raise ValueError("Equipamentos repetidos.")
        return sorted(ids)


class WorkoutDayInput(PrivateInput):
    titulo: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
    ]
    itens: Annotated[list[WorkoutItemInput], Field(max_length=30)]

    @field_validator("titulo")
    @classmethod
    def valid_title(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Texto inválido.")
        return value


class WorkoutContent(PrivateInput):
    onboarding_id: UUID
    avaliacao_id: UUID | None = None
    dias: Annotated[list[WorkoutDayInput], Field(max_length=7)]


class CreateWorkout(WorkoutContent):
    solicitacao_id: UUID
    versao_base_id: UUID | None


class UpdateWorkout(WorkoutContent):
    revisao: Order


class WorkoutMeta(BaseModel):
    id: UUID
    numero: int
    origem: Literal["MANUAL", "IA"]
    autor_id: UUID | None
    onboarding_id: UUID
    avaliacao_id: UUID | None
    versao_base_id: UUID | None
    estado_publicacao: Literal[
        "RASCUNHO", "PUBLICADO", "SUBSTITUIDO", "CONTEUDO_EXPIRADO"
    ]
    vigente: bool
    publicada_em: UtcTimestamp | None
    conteudo_excluido_em: UtcTimestamp | None
    motivo_exclusao: str | None
    revisao: int


class WorkoutItemView(WorkoutItemInput):
    exercicio_snapshot: dict[str, object]


class WorkoutDayView(BaseModel):
    titulo: str
    itens: list[WorkoutItemView]


class WorkoutView(WorkoutMeta):
    explicacao: str | None = None
    dias: list[WorkoutDayView]


class WorkoutOnboarding(BaseModel):
    id: UUID
    numero: int


class AssessmentReference(BaseModel):
    id: UUID
    registrado_em: UtcTimestamp


class WorkoutEquipment(BaseModel):
    id: UUID
    nome: str


class WorkoutContext(BaseModel):
    cliente_nome: str
    onboarding: WorkoutOnboarding | None
    avaliacoes: list[AssessmentReference]
    exercicios: list[ExerciseCandidate]
    equipamentos: list[WorkoutEquipment]
    versao_atual_id: UUID | None


class WorkoutPage(BaseModel):
    itens: list[WorkoutMeta]
    pagina: int
    limite: int
    total: int

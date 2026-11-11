from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]
Muscle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]
Combination = Annotated[list[UUID], Field(min_length=1, max_length=20)]


def normalize_name(name: str) -> str:
    return " ".join(name.split()).lower()


class ExerciseFields(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    nome: Name
    descricao: Description
    grupo_muscular: Muscle
    ativo: StrictBool
    dispensa_equipamento: StrictBool
    combinacoes: Annotated[list[Combination], Field(max_length=10)]

    @field_validator("nome", "descricao", "grupo_muscular")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Texto inválido.")
        return value

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        if len(normalize_name(self.nome)) > 120:
            raise ValueError("Nome normalizado acima do limite.")
        if self.dispensa_equipamento and self.combinacoes:
            raise ValueError("A dispensa exige uma lista vazia de combinações.")
        seen: set[frozenset[UUID]] = set()
        for group in self.combinacoes:
            key = frozenset(group)
            if len(key) != len(group) or key in seen:
                raise ValueError(
                    "Cada combinação precisa conter recursos distintos e ser única."
                )
            seen.add(key)
        return self


class ExerciseUpdate(ExerciseFields):
    revisao: Annotated[int, Field(strict=True, ge=1)]


class ExerciseEquipment(BaseModel):
    id: UUID
    nome: str
    disponivel: bool


class ExerciseSummary(BaseModel):
    id: UUID
    nome: str
    descricao: str
    grupo_muscular: str
    dispensa_equipamento: bool


class ExerciseView(ExerciseSummary):
    ativo: bool
    revisao: int
    elegivel: bool
    combinacoes: list[list[ExerciseEquipment]]


class ExerciseCandidate(ExerciseSummary):
    combinacoes_disponiveis: list[list[UUID]]


class ExercisePage[Item](BaseModel):
    itens: list[Item]
    pagina: int
    limite: int
    total: int

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.contracts.time import UtcTimestamp
from app.modules.training.review_schemas import ReviewDetail


class PublishedSummary(BaseModel):
    id: UUID
    numero: int
    origem: Literal["MANUAL", "IA"]
    autor_id: UUID | None
    publicada_em: UtcTimestamp
    vigente: bool
    parecer_estado: Literal["PENDENTE", "ACEITO", "REJEITADO"]


class PublishedHistory(BaseModel):
    schema_version: Literal[1] = 1
    versao_vigente_id: UUID | None
    itens: list[PublishedSummary]


class ResourceStatus(BaseModel):
    id: UUID
    nome: str
    disponivel: bool


class PublishedWorkout(ReviewDetail):
    schema_version: Literal[1] = 1
    consultado_em: UtcTimestamp
    equipamentos: list[ResourceStatus]

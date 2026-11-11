from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator

from app.modules.knowledge.ingestion.contracts import StrictModel
from app.modules.knowledge.schemas import Purpose
from app.modules.knowledge.vector.points import Payload

Short = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
]


class Scope(StrictModel):
    condicao: Short
    populacao: Short
    intervencao: Short


class Request(StrictModel):
    schema_version: Literal[1] = 1
    contexto_id: UUID
    finalidade: Purpose
    consulta: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]
    top_k: Annotated[int, Field(strict=True, ge=1, le=8)] = 5
    escopo_saude: Scope | None = None

    @field_validator("consulta")
    @classmethod
    def no_controls(cls, value: str) -> str:
        if any(ord(c) < 32 and c not in "\n\t" for c in value):
            raise ValueError("Consulta inválida.")
        return value


class Hit(StrictModel):
    id: UUID
    score: Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]
    payload: Payload


class Annotation(StrictModel):
    arquivo_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    texto_hash: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    escopo: Scope
    posicao: Literal["SUPORTE", "CONTRAINDICACAO"]
    justificativa: Short


class Evidence(StrictModel):
    fragmento_id: UUID
    ingestao_id: UUID
    documento_versao_id: UUID
    aprovacao_revisao: int
    titulo: str
    origem_url: str
    idioma: str
    pagina: int | None
    linha_inicio: int | None
    linha_fim: int | None
    secao: str | None
    texto: str
    texto_hash: str
    score: float


class Result(StrictModel):
    schema_version: Literal[1] = 1
    estado: Literal[
        "EVIDENCIAS_ENCONTRADAS",
        "SEM_EVIDENCIAS",
        "EVIDENCIA_INSUFICIENTE",
        "CONFLITO",
        "SERVICO_INDISPONIVEL",
    ]
    evidencias: list[Evidence]
    suporte_saude: Literal[
        "NAO_SOLICITADO", "NAO_VERIFICADO", "PERTINENTE", "CONFLITANTE"
    ]
    motivo: str
    busca_ms: float = 0
    total_ms: float = 0

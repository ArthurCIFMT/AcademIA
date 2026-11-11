import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class VectorErrorCode(StrEnum):
    CONFIGURACAO_INVALIDA = "CONFIGURACAO_INVALIDA"
    CONFIGURACAO_INCOMPATIVEL = "CONFIGURACAO_INCOMPATIVEL"
    SERVICO_INDISPONIVEL = "SERVICO_INDISPONIVEL"


_MESSAGES = {
    VectorErrorCode.CONFIGURACAO_INVALIDA: "Confira a configuração do banco vetorial.",
    VectorErrorCode.CONFIGURACAO_INCOMPATIVEL: (
        "A coleção vetorial possui configuração incompatível. "
        "Use uma nova coleção versionada; os dados existentes foram preservados."
    ),
    VectorErrorCode.SERVICO_INDISPONIVEL: "O banco vetorial não está disponível.",
}


class VectorError(Exception):
    def __init__(self, code: VectorErrorCode) -> None:
        self.code = code
        super().__init__(_MESSAGES[code])


class EmbeddingSpace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal[1] = 1
    model: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    # A revisão dos pesos será fixada em RAG-04, antes de gerar embeddings.
    revision: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40,64}$")] | None
    dimension: Annotated[int, Field(strict=True, ge=1, le=65536)]
    metric: Literal["Cosine"] = "Cosine"
    normalized: Literal[True] = True
    query_prefix: Literal["query: "] = "query: "
    passage_prefix: Literal["passage: "] = "passage: "

    @property
    def fingerprint(self) -> str:
        canonical = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class CollectionStatus:
    collection: str
    model: str
    model_revision: str | None
    dimension: int
    metric: str
    space_sha256: str
    points: int


class VectorStore(Protocol):
    """Porta técnica; RAG-04/05 acrescentarão indexação e busca com proveniência."""

    def check(self) -> CollectionStatus: ...

    def close(self) -> None: ...

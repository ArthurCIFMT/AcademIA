import hashlib
from typing import Literal, Protocol
from uuid import UUID

from app.modules.knowledge.embeddings.encoder import validate_vectors
from app.modules.knowledge.ingestion.contracts import StrictModel, digest
from app.modules.knowledge.schemas import Metadata
from app.modules.knowledge.vector.contracts import VectorStore


class Payload(StrictModel):
    schema_version: Literal[1] = 1
    ingestao_id: UUID
    documento_versao_id: UUID
    fragmento_id: UUID
    aprovacao_revisao: int
    config_hash: str
    space_sha256: str
    texto: str
    texto_hash: str
    metadados: Metadata
    finalidade: str
    pagina: int | None
    linha_inicio: int | None
    linha_fim: int | None
    secao: str | None
    inicio: int
    fim: int
    tokens: int
    input_tokens: int

    @property
    def fingerprint(self) -> str:
        return digest(self.model_dump(mode="json"))

    def check(self) -> None:
        if hashlib.sha256(self.texto.encode()).hexdigest() != self.texto_hash:
            raise ValueError("Texto incompatível com hash.")


class Point(StrictModel):
    id: UUID
    vector: list[float]
    payload: Payload

    def check(self, dimension: int, space: str) -> None:
        self.payload.check()
        if self.id != self.payload.fragmento_id or self.payload.space_sha256 != space:
            raise ValueError("Espaço ou identidade incompatível.")
        validate_vectors([self.vector], 1, dimension)


class VectorIndex(VectorStore, Protocol):
    def present(self, expected: dict[UUID, Payload]) -> set[UUID]: ...
    def upsert(self, points: list[Point]) -> None: ...

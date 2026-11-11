from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.modules.knowledge.embeddings.encoder import Encoder
from app.modules.knowledge.retrieval.contracts import Hit
from app.modules.knowledge.schemas import Purpose
from app.modules.knowledge.vector.points import VectorIndex


class QueryEncoder(Encoder, Protocol):
    def queries(self, texts: Sequence[str], timeout: float) -> list[list[float]]: ...


class SearchIndex(VectorIndex, Protocol):
    def search(
        self, vector: list[float], ingestions: list[UUID], purpose: Purpose, limit: int
    ) -> list[Hit]: ...

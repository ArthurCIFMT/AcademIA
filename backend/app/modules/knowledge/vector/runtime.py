from threading import RLock

from pydantic import ValidationError

from app.modules.knowledge.retrieval.ports import SearchIndex
from app.modules.knowledge.vector.contracts import (
    VectorError,
    VectorErrorCode,
)
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings

_lock = RLock()
_store: SearchIndex | None = None


def get_vector_store() -> SearchIndex:
    """Uma instância por processo, aberta somente ao chamar check/operação vetorial."""
    global _store
    with _lock:
        if _store is None:
            try:
                settings = VectorSettings()
            except (ValidationError, ValueError, OSError):
                raise VectorError(VectorErrorCode.CONFIGURACAO_INVALIDA) from None
            _store = QdrantStore(settings)
        return _store


def close_vector_store() -> None:
    global _store
    with _lock:
        if _store is not None:
            _store.close()
            _store = None

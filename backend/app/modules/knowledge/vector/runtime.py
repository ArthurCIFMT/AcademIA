from threading import RLock

from pydantic import ValidationError

from app.modules.knowledge.vector.contracts import (
    VectorError,
    VectorErrorCode,
    VectorStore,
)
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings

_lock = RLock()
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
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

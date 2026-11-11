from threading import RLock

from app.modules.knowledge.embeddings.encoder import E5Encoder

_lock = RLock()
_encoder: E5Encoder | None = None


def get_encoder() -> E5Encoder:
    global _encoder
    with _lock:
        if _encoder is None:
            _encoder = E5Encoder()
        return _encoder


def close_encoder() -> None:
    global _encoder
    with _lock:
        if _encoder is not None:
            _encoder.close()
            _encoder = None

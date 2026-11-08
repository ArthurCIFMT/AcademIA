from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from threading import Lock


class TooManyAttempts(Exception):
    pass


class LoginLimiter:
    """Janelas de falhas por e-mail normalizado e IP, por processo."""

    def __init__(self, *, max_failures: int, window: timedelta) -> None:
        self._max_failures = max_failures
        self._window = window
        self._attempts: dict[tuple[str, str], dict[object, datetime]] = {}
        self._lock = Lock()

    @contextmanager
    def attempt(self, email: str, ip: str, now: datetime) -> Iterator[None]:
        key = (email, ip)
        reservation = object()
        with self._lock:
            cutoff = now - self._window
            for entry in list(self._attempts):
                bucket = self._attempts[entry]
                for mark in [mark for mark, at in bucket.items() if at <= cutoff]:
                    del bucket[mark]
                if not bucket:
                    del self._attempts[entry]

            if key not in self._attempts and len(self._attempts) >= 4096:
                raise TooManyAttempts
            bucket = self._attempts.setdefault(key, {})
            if len(bucket) >= self._max_failures:
                raise TooManyAttempts
            bucket[reservation] = now

        # Em caso de falha, a reserva conta até o fim da janela.
        yield

        with self._lock:
            current = self._attempts.get(key)
            if current is not None:
                current.pop(reservation, None)
                if not current:
                    del self._attempts[key]

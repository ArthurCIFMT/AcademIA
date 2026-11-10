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


class RecoveryLimiter:
    """Conta pedidos por endereço normalizado e IP no processo do MVP."""

    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], tuple[datetime, int]] = {}
        self._lock = Lock()

    def allow(self, email: str, ip: str, now: datetime) -> bool:
        limits = ((("email", email), 3), (("ip", ip), 20))
        with self._lock:
            self._buckets = {
                key: bucket for key, bucket in self._buckets.items() if bucket[0] > now
            }
            new_keys = sum(key not in self._buckets for key, _ in limits)
            if len(self._buckets) + new_keys > 4096:
                return False
            deadline = now + timedelta(minutes=15)
            if any(
                self._buckets.get(key, (deadline, 0))[1] >= limit
                for key, limit in limits
            ):
                return False
            for key, _ in limits:
                expires, used = self._buckets.get(key, (deadline, 0))
                self._buckets[key] = expires, used + 1
            return True

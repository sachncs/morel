"""Per-IP request rate limiting.

A small in-process token-bucket keyed by source IP. Reads use one
budget, admin endpoints use a tighter one. Limiters expire after a
quiet period so the map stays bounded under steady traffic.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Literal

from fastapi import HTTPException, Request

Scope = Literal["read", "admin"]


class Limiter:
    """Token-bucket limiter keyed by source IP.

    Two budgets are tracked side by side; ``read`` requests consume
    from one bucket and ``admin`` from another. Each bucket refills at
    one token per second, capped at the configured per-minute limit.
    The per-IP record expires after ``ttl_seconds`` of inactivity so
    the limiter map does not grow unbounded under churn.
    """

    def __init__(self) -> None:
        self.per_minute_read: int = 60
        self.per_minute_admin: int = 10
        self._buckets: dict[str, dict[str, tuple[float, float, float]]] = {}
        self._lock = threading.Lock()
        self._ttl: float = 600.0

    def configure(self, *, per_minute_read: int, per_minute_admin: int) -> None:
        """Set the per-minute budgets for both scopes."""
        self.per_minute_read = max(1, int(per_minute_read))
        self.per_minute_admin = max(1, int(per_minute_admin))

    def allow(self, ip: str, scope: Scope) -> tuple[bool, float]:
        """Charge one token from the caller's bucket.

        Returns ``(allowed, retry_after_seconds)``. ``retry_after`` is
        zero on ``allowed`` and a positive delay when the bucket is
        empty.
        """
        capacity = self.per_minute_read if scope == "read" else self.per_minute_admin
        per_second = capacity / 60.0
        now = time.monotonic()
        with self._lock:
            self._evict(now)
            record = self._buckets.setdefault(ip, {})
            tokens, last, _ = record.get(scope, (float(capacity), now, now))
            tokens = min(float(capacity), tokens + (now - last) * per_second)
            if tokens >= 1.0:
                tokens -= 1.0
                record[scope] = (tokens, now, now)
                return True, 0.0
            retry = (1.0 - tokens) / per_second
            record[scope] = (tokens, now, now)
            return False, retry

    def _evict(self, now: float) -> None:
        """Drop per-IP records that have been idle for ``ttl_seconds``."""
        stale_before = now - self._ttl
        for ip in list(self._buckets.keys()):
            scopes = self._buckets[ip]
            stale = True
            for tokens, last, last_used in scopes.values():
                if last_used >= stale_before:
                    stale = False
                    break
                del tokens, last  # placate unused-variable linters; we only read last_used
            if stale:
                self._buckets.pop(ip, None)


limiter = Limiter()


def ratelimit_dependency(scope: Scope) -> Callable[[Request], None]:
    """Return a FastAPI dependency that enforces the per-IP budget.

    The dependency raises ``HTTPException(429, ...)`` with a
    ``Retry-After`` header attached when the caller's bucket is empty
    so naive clients (and most well-behaved ones) back off correctly.
    """

    def scoped(request: Request) -> None:
        ip = request.client.host if request.client is not None else "test"
        allowed, retry_after = limiter.allow(ip, scope)
        if not allowed:
            response = HTTPException(
                status_code=429,
                detail=f"rate limit exceeded for {scope} endpoint",
                headers={"retry-after": f"{retry_after:.3f}"},
            )
            raise response
        return

    return scoped


__all__ = ["Limiter", "Scope", "limiter", "ratelimit_dependency"]

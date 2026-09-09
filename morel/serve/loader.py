"""Thread-safe model loader with LRU cache and per-key factory registry."""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from morel.core.errors import Model


class Loader:
    """Cache of named model pipelines keyed by their checkpoint path.

    Factories are registered up front via :meth:`register` and looked up
    by key from request handlers. The loader is safe to share across
    request threads. Concurrent requests for the same uncached key are
    serialised through a per-key condition so the factory runs exactly
    once per key; requests for different keys remain independent.

    Two failure modes the lock discipline explicitly handles:

    1. **Deadlock on factory exception**: when the first caller's
       factory raises, the building entry is popped and waiters are
       notified. They wake up, find no cache entry, and re-wait. To
       keep the system progressing, every factory call has a
       configurable timeout (default 60 seconds). A timeout raises
       :class:`morel.core.errors.Model` to every waiter.
    2. **Unbounded building map**: the per-key ``Condition`` map is
       bound by ``building_capacity`` (defaults to ``capacity``).

    Attributes
    ----------
        capacity: Maximum number of cached pipelines.
        cache: LRU-ordered dict of cached pipelines.
        lock: Threading lock protecting ``cache`` and ``building``.
        building: Mapping from cache key to a per-key ``Condition``
            that gates the factory invocation.
        factories: Mapping from cache key to a registered factory
            callable. ``None`` is not allowed as a factory result.
    """

    def __init__(
        self,
        *,
        capacity: int = 4,
        building_capacity: int | None = None,
        factory_timeout: float = 60.0,
    ) -> None:
        """Initialize the pipeline loader.

        Args:
            capacity: Maximum number of cached pipelines.
            building_capacity: Maximum number of concurrent in-flight
                factory builds. Defaults to ``capacity`` when ``None``.
            factory_timeout: Seconds to wait for the first caller's
                factory to complete before bailing out with :class:`Model`.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if factory_timeout <= 0:
            raise ValueError("factory_timeout must be positive")
        self.capacity = capacity
        self.building_capacity = (
            capacity if building_capacity is None else int(building_capacity)
        )
        if self.building_capacity <= 0:
            raise ValueError("building_capacity must be positive")
        self.factory_timeout = float(factory_timeout)
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.factories: dict[str, Callable[[], Any]] = {}
        self.lock = threading.Lock()
        self.building: OrderedDict[str, threading.Condition] = OrderedDict()

    def register(self, key: str, factory: Callable[[], Any]) -> None:
        """Register ``factory`` to build the pipeline for ``key``.

        Re-registering an existing key replaces the factory and evicts
        any cached pipeline for that key. Use this at startup; do not
        call it from a hot-path handler.

        Args:
            key: Cache key the factory builds for.
            factory: Callable returning the pipeline object. Must return
                a non-``None`` value.
        """
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        if not callable(factory):
            raise ValueError("factory must be callable")
        with self.lock:
            self.factories[key] = factory
            self.cache.pop(key, None)

    def get(self, key: str, factory: Callable[[], Any] | None = None) -> Any:
        """Return a cached pipeline or build one via ``factory`` or the registry.

        If ``factory`` is given, it takes precedence over any registered
        factory for ``key`` for the duration of this call; the cache
        entry is still keyed on ``key``. If ``factory`` is ``None`` the
        loader looks up the registered factory; if no factory has been
        registered for ``key``, :class:`Model` is raised.

        Concurrent callers asking for the same uncached key wait on a
        per-key condition. The first one through runs the factory; the
        others pick up the cached value as soon as the first one stores
        it. The first caller also runs the per-key factory-timeout
        watchdog so a single hung factory cannot block every waiter
        forever.
        """
        if not isinstance(key, str) or not key:
            raise ValueError("key must be a non-empty string")
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            cond = self.building.get(key)
            if cond is None:
                cond = threading.Condition(self.lock)
                self.building[key] = cond
                first = True
                if len(self.building) > self.building_capacity:
                    self.building.popitem(last=False)
                    cond = self.building[key]
            else:
                first = False
            build_factory = factory if factory is not None else self.factories.get(key)
            if build_factory is None:
                raise Model(f"no factory registered for loader key {key!r}")
        if not first:
            with cond:
                deadline = _Deadline.after(self.factory_timeout)
                while key not in self.cache:
                    remaining = deadline.remaining()
                    if remaining <= 0:
                        raise Model(
                            f"loader factory for {key!r} did not complete within "
                            f"{self.factory_timeout:.1f}s"
                        )
                    cond.wait(timeout=remaining)
                cached = self.cache[key]
                # ``self.lock`` and ``cond`` share the same underlying
                # lock, so we are already holding it here. Update the
                # LRU position without re-acquiring.
                self.cache.move_to_end(key)
                return cached
        deadline = _Deadline.after(self.factory_timeout)
        try:
            model = build_factory()
            if model is None:
                raise Model(f"loader factory returned None for key {key!r}")
        except BaseException:
            with self.lock:
                self.building.pop(key, None)
            with cond:
                cond.notify_all()
            raise
        if deadline.expired():
            # The factory only completed after the per-key timeout.
            # Discard the result so we don't cache a model that exceeded
            # the wait budget, and notify any waiters that the build is
            # over (they will see no cache entry and time out on their
            # next wait).
            with self.lock:
                self.building.pop(key, None)
            with cond:
                cond.notify_all()
            raise Model(
                f"loader factory for {key!r} took longer than "
                f"{self.factory_timeout:.1f}s to complete"
            )
        with self.lock:
            self.cache[key] = model
            while len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
            self.building.pop(key, None)
        with cond:
            cond.notify_all()
        return model

    def registered(self) -> list[str]:
        """Return the keys with a registered factory."""
        with self.lock:
            return list(self.factories.keys())

    def clear(self) -> None:
        """Drop every cached pipeline and registered factory."""
        with self.lock:
            self.cache.clear()
            self.factories.clear()
            self.building.clear()

    def keys(self) -> list[str]:
        """Return currently cached keys (insertion-ordered)."""
        with self.lock:
            return list(self.cache.keys())


class _Deadline:
    """Monotonic deadline helper used by the loader's wait watchdog."""

    __slots__ = ("expires_at",)

    def __init__(self, expires_at: float) -> None:
        self.expires_at = expires_at

    @classmethod
    def after(cls, seconds: float) -> _Deadline:
        """Return a deadline ``seconds`` from now."""
        import time

        return cls(time.monotonic() + seconds)

    def remaining(self) -> float:
        """Return seconds left until the deadline (>=0)."""
        import time

        return max(0.0, self.expires_at - time.monotonic())

    def expired(self) -> bool:
        """Return whether the deadline has passed."""
        return self.remaining() <= 0.0


__all__ = ["Loader"]

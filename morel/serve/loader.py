"""Thread-safe model loader with LRU cache."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

from morel.core.errors import Model


class Loader:
    """Cache of named model pipelines keyed by their checkpoint path.

    The loader is safe to share across request threads. Concurrent requests
    for the same uncached key are serialised through a per-key condition so
    the factory runs exactly once per key; requests for different keys
    remain independent.

    Attributes
    ----------
        capacity: Maximum number of cached pipelines.
        cache: LRU-ordered dict of cached pipelines.
        lock: Threading lock protecting ``cache`` and ``building``.
        building: Mapping from cache key to a per-key ``Condition`` that
            gates the factory invocation.
    """

    def __init__(self, *, capacity: int = 4) -> None:
        """Initialize the pipeline loader.

        Args:
            capacity: Maximum number of cached pipelines.
        """
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.lock = threading.Lock()
        self.building: dict[str, threading.Condition] = {}

    def get(self, key: str, factory: Any) -> Any:
        """Return a cached pipeline or build and cache one via ``factory``.

        Concurrent callers asking for the same uncached key wait on a
        per-key condition. The first one through runs ``factory``; the
        others pick up the cached value as soon as the first one stores
        it.
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
            else:
                first = False
        if not first:
            with cond:
                while key not in self.cache:
                    cond.wait()
                cached = self.cache[key]
                # ``self.lock`` and ``cond`` share the same underlying
                # lock, so we are already holding it here. Update the
                # LRU position without re-acquiring.
                self.cache.move_to_end(key)
                return cached
        try:
            model = factory()
            if model is None:
                raise Model(f"loader factory returned None for key {key!r}")
        except BaseException:
            with self.lock:
                cond = self.building.pop(key, None)
            if cond is not None:
                with cond:
                    cond.notify_all()
            raise
        with self.lock:
            self.cache[key] = model
            while len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
            cond = self.building.pop(key, None)
        if cond is not None:
            with cond:
                cond.notify_all()
        return model

    def clear(self) -> None:
        """Drop every cached pipeline."""
        with self.lock:
            self.cache.clear()
            self.building.clear()

    def keys(self) -> list[str]:
        """Return currently cached keys (insertion-ordered)."""
        with self.lock:
            return list(self.cache.keys())


__all__ = ["Loader"]

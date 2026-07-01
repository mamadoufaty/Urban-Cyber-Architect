"""Cache mémoire TTL — réponses connecteur Wazuh."""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")

DEFAULT_TTL_SECONDS = 60


class TtlCache(Generic[T]):
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: T, *, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        self._store[key] = (time.time() + ttl, value)

    def invalidate(self, key: str | None = None) -> None:
        if key is None:
            self._store.clear()
        elif key in self._store:
            del self._store[key]


_wazuh_cache: TtlCache[Any] = TtlCache()


def get_wazuh_cache() -> TtlCache[Any]:
    return _wazuh_cache

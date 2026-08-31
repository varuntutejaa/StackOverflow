"""Thin cache abstraction. Uses Redis when REDIS_URL is set, otherwise an
in-process TTL dict. Safe to import even if redis is unreachable."""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("cache")


class _MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        expires, value = item
        if expires and expires < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._store[key] = (time.time() + ttl if ttl else 0, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear_prefix(self, prefix: str) -> None:
        for k in list(self._store):
            if k.startswith(prefix):
                self._store.pop(k, None)


class Cache:
    def __init__(self) -> None:
        self._redis = None
        self._mem = _MemoryCache()
        if settings.redis_url:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
                log.info("cache_backend", backend="redis")
            except Exception as exc:  # noqa: BLE001
                log.warning("cache_redis_unavailable", error=str(exc))
                self._redis = None

    @property
    def backend(self) -> str:
        return "redis" if self._redis else "memory"

    def get_json(self, key: str) -> Optional[Any]:
        raw = self._redis.get(key) if self._redis else self._mem.get(key)
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        raw = json.dumps(value, default=str)
        if self._redis:
            self._redis.set(key, raw, ex=ttl)
        else:
            self._mem.set(key, raw, ttl)

    def delete(self, key: str) -> None:
        if self._redis:
            self._redis.delete(key)
        else:
            self._mem.delete(key)

    def invalidate_prefix(self, prefix: str) -> None:
        if self._redis:
            for k in self._redis.scan_iter(f"{prefix}*"):
                self._redis.delete(k)
        else:
            self._mem.clear_prefix(prefix)


cache = Cache()

"""Retries, rate limiting & response caching for provider calls (WBS 1.1.4).

These utilities wrap the raw HTTP call in :class:`~app.services.providers.base.WeatherProvider`
so every provider gets, for free:

* **Retries** with exponential backoff on transient failures.
* **Per-provider rate limiting** to respect upstream quotas.
* **Response caching** (TTL) to cut latency and avoid redundant calls.

State (cache entries, rate limiters) is process-wide and keyed by provider name, since
provider instances are created per request by the registry.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.providers.base import ProviderConfigError, ProviderError

# Injectable async sleep so tests can run without real delays.
_sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


def set_sleep(fn: Callable[[float], Awaitable[None]]) -> None:
    """Override the sleep coroutine (used by tests)."""
    global _sleep
    _sleep = fn


def reset_sleep() -> None:
    global _sleep
    _sleep = asyncio.sleep


class TTLCache:
    """A tiny time-to-live cache keyed by string."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            return
        self._store[key] = (self._clock() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


class RateLimiter:
    """Enforces a minimum interval between calls (a simple per-key throttle).

    ``per_minute <= 0`` disables throttling entirely.
    """

    def __init__(
        self,
        per_minute: int,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._min_interval = 60.0 / per_minute if per_minute > 0 else 0.0
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()
        self._next_allowed = 0.0

    async def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = self._clock()
            wait = self._next_allowed - now
            if wait > 0:
                await (self._sleep or _sleep)(wait)
                now = self._clock()
            self._next_allowed = max(now, self._next_allowed) + self._min_interval


async def with_retries(
    factory: Callable[[], Awaitable[Any]],
    retries: int,
    backoff_base: float,
) -> Any:
    """Call ``factory`` with exponential-backoff retries on transient errors.

    :class:`ProviderConfigError` is never retried (a missing key won't fix itself);
    other :class:`ProviderError` failures retry up to ``retries`` times.
    """
    attempt = 0
    while True:
        try:
            return await factory()
        except ProviderConfigError:
            raise
        except ProviderError:
            if attempt >= retries:
                raise
            await _sleep(backoff_base * (2**attempt))
            attempt += 1


# --- process-wide registries ----------------------------------------------------

_cache = TTLCache()
_limiters: dict[str, RateLimiter] = {}


def get_cache() -> TTLCache:
    return _cache


def get_rate_limiter(name: str, per_minute: int) -> RateLimiter:
    limiter = _limiters.get(name)
    if limiter is None:
        limiter = RateLimiter(per_minute)
        _limiters[name] = limiter
    return limiter


def make_cache_key(name: str, url: str, params: dict) -> str:
    items = ",".join(f"{k}={params[k]}" for k in sorted(params))
    return f"{name}|{url}|{items}"


def reset() -> None:
    """Clear all cached responses and rate limiters (used by tests)."""
    _cache.clear()
    _limiters.clear()

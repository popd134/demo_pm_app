"""Tests for retries, rate limiting & response caching (WBS 1.1.4)."""

from __future__ import annotations

import httpx
import pytest

from app.schemas.weather import GeoPoint
from app.services.providers import resilience
from app.services.providers.base import ProviderConfigError, ProviderError
from app.services.providers.open_meteo import OpenMeteoProvider
from app.services.providers.resilience import (
    RateLimiter,
    TTLCache,
    make_cache_key,
    with_retries,
)

LONDON = GeoPoint(latitude=51.5074, longitude=-0.1278)

OPEN_METEO_CURRENT = {
    "current": {
        "time": "2026-08-05T12:00",
        "temperature_2m": 21.4,
        "weather_code": 0,
    }
}


# --- TTLCache -------------------------------------------------------------------

def test_ttl_cache_hit_and_expiry() -> None:
    now = [1000.0]
    cache = TTLCache(clock=lambda: now[0])
    cache.set("k", {"v": 1}, ttl=10)
    assert cache.get("k") == {"v": 1}
    now[0] += 11
    assert cache.get("k") is None


def test_ttl_cache_zero_ttl_is_noop() -> None:
    cache = TTLCache()
    cache.set("k", 1, ttl=0)
    assert cache.get("k") is None


def test_make_cache_key_is_order_independent() -> None:
    a = make_cache_key("p", "http://u", {"b": 2, "a": 1})
    b = make_cache_key("p", "http://u", {"a": 1, "b": 2})
    assert a == b


# --- with_retries ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_with_retries_succeeds_after_transient_errors() -> None:
    attempts = {"n": 0}

    async def factory() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ProviderError("transient")
        return "ok"

    result = await with_retries(factory, retries=3, backoff_base=0.0)
    assert result == "ok"
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_with_retries_exhausts_and_raises() -> None:
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        raise ProviderError("always")

    with pytest.raises(ProviderError):
        await with_retries(factory, retries=2, backoff_base=0.0)
    assert calls["n"] == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_with_retries_does_not_retry_config_errors() -> None:
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        raise ProviderConfigError("missing key")

    with pytest.raises(ProviderConfigError):
        await with_retries(factory, retries=5, backoff_base=0.0)
    assert calls["n"] == 1


# --- RateLimiter ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiter_disabled_never_sleeps() -> None:
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    limiter = RateLimiter(per_minute=0, sleep=sleep)
    await limiter.acquire()
    await limiter.acquire()
    assert slept == []


@pytest.mark.asyncio
async def test_rate_limiter_throttles_second_call() -> None:
    slept: list[float] = []
    now = [0.0]

    async def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(per_minute=60, clock=lambda: now[0], sleep=sleep)
    await limiter.acquire()  # first call: no wait
    await limiter.acquire()  # second call: must wait ~1s (60/min)
    assert len(slept) == 1
    assert slept[0] == pytest.approx(1.0, rel=1e-3)


# --- Integration through a provider --------------------------------------------

@pytest.mark.asyncio
async def test_provider_caches_responses() -> None:
    resilience.reset()
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=OPEN_METEO_CURRENT)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoProvider(client=client)
        first = await provider.get_current(LONDON)
        second = await provider.get_current(LONDON)

    assert first.observation.temperature_c == 21.4
    assert second.observation.temperature_c == 21.4
    # Identical request served from cache the second time.
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_provider_retries_transient_http_errors() -> None:
    resilience.reset()
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json=OPEN_METEO_CURRENT)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoProvider(client=client)
        result = await provider.get_current(LONDON)

    assert result.observation.temperature_c == 21.4
    assert calls["n"] == 2  # first failed, retry succeeded

"""Provider abstraction shared by all weather sources (WBS 1.1.1)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.schemas.weather import CurrentConditions, Forecast, GeoPoint


class ProviderError(RuntimeError):
    """Raised when a provider request fails or returns an unusable response."""


class ProviderConfigError(ProviderError):
    """Raised when a provider is used without required configuration (e.g. API key)."""


class WeatherProvider(ABC):
    """Base class for external weather providers.

    Concrete providers map credentials/config, call the source endpoints and parse
    responses. An :class:`httpx.AsyncClient` may be injected for testing; otherwise one
    is created per call. Retries, rate limiting and caching are layered on separately in
    WBS 1.1.4 and therefore intentionally live outside this class.
    """

    #: Stable identifier used in config, the registry and stored records.
    name: str = "base"
    #: Base URL for the provider's HTTP API.
    base_url: str = ""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _request(self, path: str, params: dict[str, object]) -> dict:
        """Perform a GET request and return decoded JSON.

        Wraps the raw call with response caching, per-provider rate limiting and
        exponential-backoff retries (WBS 1.1.4).
        """
        # Imported here to avoid a circular import at module load.
        from app.core.config import get_settings
        from app.services.providers import resilience

        url = path if path.startswith("http") else f"{self.base_url}{path}"
        settings = get_settings()

        cache = resilience.get_cache()
        key = resilience.make_cache_key(self.name, url, params)
        cached = cache.get(key)
        if cached is not None:
            return cached

        limiter = resilience.get_rate_limiter(
            self.name, settings.provider_rate_limit_per_minute
        )

        async def _call() -> dict:
            await limiter.acquire()
            return await self._raw_get(url, params)

        data = await resilience.with_retries(
            _call,
            retries=settings.provider_max_retries,
            backoff_base=settings.provider_backoff_base_seconds,
        )
        cache.set(key, data, settings.provider_cache_ttl_seconds)
        return data

    async def _raw_get(self, url: str, params: dict[str, object]) -> dict:
        """Perform a single GET request, wrapping transport errors as ProviderError."""
        try:
            if self._client is not None:
                response = await self._client.get(url, params=params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:  # non-2xx
            raise ProviderError(
                f"{self.name} returned HTTP {exc.response.status_code} for {url}"
            ) from exc
        except httpx.HTTPError as exc:  # transport / timeout / decode
            raise ProviderError(f"{self.name} request to {url} failed: {exc}") from exc

    @abstractmethod
    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        """Return current conditions for a location."""

    @abstractmethod
    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:
        """Return an hourly forecast for a location."""

    @abstractmethod
    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:
        """Return a daily forecast for a location."""

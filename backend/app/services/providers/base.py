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
        """Perform a GET request and return decoded JSON, wrapping transport errors."""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
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
                f"{self.name} returned HTTP {exc.response.status_code} for {path}"
            ) from exc
        except httpx.HTTPError as exc:  # transport / timeout / decode
            raise ProviderError(f"{self.name} request to {path} failed: {exc}") from exc

    @abstractmethod
    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        """Return current conditions for a location."""

    @abstractmethod
    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:
        """Return an hourly forecast for a location."""

    @abstractmethod
    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:
        """Return a daily forecast for a location."""

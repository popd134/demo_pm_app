"""Tests for external weather provider clients (WBS 1.1.1).

Provider HTTP calls are served by an in-process ``httpx.MockTransport`` so the suite
exercises real request building and response parsing with no network access.
"""

from __future__ import annotations

import httpx
import pytest

from app.schemas.weather import GeoPoint
from app.services.providers import (
    ProviderConfigError,
    ProviderError,
    available_providers,
    get_provider,
)
from app.services.providers.open_meteo import OpenMeteoProvider, condition_from_code
from app.services.providers.openweather import OpenWeatherProvider

LONDON = GeoPoint(latitude=51.5074, longitude=-0.1278)


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- Open-Meteo -----------------------------------------------------------------

OPEN_METEO_CURRENT = {
    "current": {
        "time": "2026-08-05T12:00",
        "temperature_2m": 21.4,
        "relative_humidity_2m": 60,
        "wind_speed_10m": 3.2,
        "wind_direction_10m": 180,
        "precipitation": 0.0,
        "surface_pressure": 1012.3,
        "weather_code": 2,
    }
}

OPEN_METEO_DAILY = {
    "daily": {
        "time": ["2026-08-05", "2026-08-06"],
        "temperature_2m_max": [24.0, 26.5],
        "precipitation_sum": [1.2, 0.0],
        "wind_speed_10m_max": [5.0, 4.1],
        "weather_code": [61, 0],
    }
}


@pytest.mark.asyncio
async def test_open_meteo_current_parsing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/forecast"
        assert request.url.params["latitude"] == "51.5074"
        return httpx.Response(200, json=OPEN_METEO_CURRENT)

    async with _client(handler) as client:
        provider = OpenMeteoProvider(client=client)
        result = await provider.get_current(LONDON)

    assert result.observation.provider == "open-meteo"
    assert result.observation.temperature_c == 21.4
    assert result.observation.condition == "Partly cloudy"
    assert result.location == LONDON


@pytest.mark.asyncio
async def test_open_meteo_daily_forecast_parsing() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=OPEN_METEO_DAILY)

    async with _client(handler) as client:
        provider = OpenMeteoProvider(client=client)
        forecast = await provider.get_forecast(LONDON, days=2)

    assert len(forecast.entries) == 2
    assert forecast.entries[0].temperature_c == 24.0
    assert forecast.entries[0].condition == "Slight rain"
    assert forecast.entries[1].precipitation_mm == 0.0


@pytest.mark.asyncio
async def test_open_meteo_missing_current_raises() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    async with _client(handler) as client:
        with pytest.raises(ProviderError):
            await OpenMeteoProvider(client=client).get_current(LONDON)


@pytest.mark.asyncio
async def test_open_meteo_http_error_wrapped() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    async with _client(handler) as client:
        with pytest.raises(ProviderError):
            await OpenMeteoProvider(client=client).get_current(LONDON)


def test_condition_from_code_handles_bad_input() -> None:
    assert condition_from_code(0) == "Clear sky"
    assert condition_from_code(None) is None
    assert condition_from_code("nope") is None


# --- OpenWeatherMap -------------------------------------------------------------

OPENWEATHER_CURRENT = {
    "dt": 1_754_395_200,
    "main": {"temp": 19.0, "humidity": 72, "pressure": 1009},
    "wind": {"speed": 4.6, "deg": 210},
    "rain": {"1h": 0.5},
    "weather": [{"description": "light rain"}],
}


@pytest.mark.asyncio
async def test_openweather_requires_api_key() -> None:
    provider = OpenWeatherProvider(api_key=None)
    with pytest.raises(ProviderConfigError):
        await provider.get_current(LONDON)


@pytest.mark.asyncio
async def test_openweather_current_parsing_and_auth() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["appid"] == "secret-key"
        assert request.url.params["units"] == "metric"
        return httpx.Response(200, json=OPENWEATHER_CURRENT)

    async with _client(handler) as client:
        provider = OpenWeatherProvider(api_key="secret-key", client=client)
        result = await provider.get_current(LONDON)

    assert result.observation.temperature_c == 19.0
    assert result.observation.condition == "light rain"
    assert result.observation.precipitation_mm == 0.5


# --- Registry -------------------------------------------------------------------

def test_registry_lists_and_resolves_default() -> None:
    names = available_providers()
    assert "open-meteo" in names
    assert "openweathermap" in names
    assert isinstance(get_provider(), OpenMeteoProvider)


def test_registry_unknown_provider_raises() -> None:
    with pytest.raises(ProviderError):
        get_provider("does-not-exist")

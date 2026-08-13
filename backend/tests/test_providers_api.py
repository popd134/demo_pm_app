"""API-level tests for the provider integration endpoints (WBS 1.1.1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.schemas.weather import (
    CurrentConditions,
    Forecast,
    ForecastEntry,
    GeoPoint,
    WeatherObservation,
)
from app.services.providers import register_provider
from app.services.providers.base import WeatherProvider


class _FakeProvider(WeatherProvider):
    name = "fake"

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        return CurrentConditions(
            location=location,
            observation=WeatherObservation(
                provider=self.name,
                observed_at=datetime(2026, 8, 5, 12, tzinfo=UTC),
                temperature_c=18.5,
                condition="Clear sky",
            ),
        )

    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:
        return await self.get_forecast(location, days=hours)

    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:
        return Forecast(
            provider=self.name,
            location=location,
            generated_at=datetime(2026, 8, 5, tzinfo=UTC),
            entries=[
                ForecastEntry(
                    valid_at=datetime(2026, 8, 6, tzinfo=UTC), temperature_c=20.0
                )
            ],
        )


@pytest.fixture(autouse=True)
def _register_fake() -> None:
    register_provider("fake", lambda _settings: _FakeProvider())


def test_list_providers_endpoint(client) -> None:
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    assert "open-meteo" in resp.json()["providers"]


def test_current_endpoint_with_fake_provider(client) -> None:
    resp = client.get(
        "/api/providers/current",
        params={"lat": 51.5, "lon": -0.12, "provider": "fake"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["observation"]["temperature_c"] == 18.5
    assert body["observation"]["condition"] == "Clear sky"


def test_current_endpoint_unknown_provider_404(client) -> None:
    resp = client.get("/api/providers/current", params={"lat": 0, "lon": 0, "provider": "nope"})
    assert resp.status_code == 404


def test_current_endpoint_validates_coordinates(client) -> None:
    resp = client.get("/api/providers/current", params={"lat": 200, "lon": 0, "provider": "fake"})
    assert resp.status_code == 422

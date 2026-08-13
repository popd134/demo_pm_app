"""API tests for ingestion status & manual trigger (WBS 1.1.2)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.schemas.weather import CurrentConditions, Forecast, GeoPoint, WeatherObservation
from app.services.ingestion import InMemoryObservationSink
from app.services.ingestion_runtime import runtime
from app.services.providers import register_provider
from app.services.providers.base import WeatherProvider


class _OkProvider(WeatherProvider):
    name = "ok"

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        return CurrentConditions(
            location=location,
            observation=WeatherObservation(
                provider=self.name,
                observed_at=datetime(2026, 8, 5, tzinfo=UTC),
                temperature_c=15.0,
            ),
        )

    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:  # noqa: ARG002
        raise NotImplementedError

    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:  # noqa: ARG002
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _reset_runtime():
    """Point the runtime at a fresh in-memory sink and the 'ok' provider per test."""
    register_provider("ok", lambda _settings: _OkProvider())
    settings = get_settings()
    original_provider = settings.default_weather_provider
    original_locations = settings.ingestion_locations
    settings.default_weather_provider = "ok"
    settings.ingestion_locations = [
        {"name": "London", "latitude": 51.5074, "longitude": -0.1278}
    ]
    runtime.sink = InMemoryObservationSink()
    runtime.scheduler = None
    yield
    settings.default_weather_provider = original_provider
    settings.ingestion_locations = original_locations


def test_status_reports_config(client) -> None:
    resp = client.get("/api/ingestion/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tracked_locations"] == 1
    assert body["enabled"] is False
    assert body["running"] is False


def test_run_once_stores_observations(client) -> None:
    resp = client.post("/api/ingestion/run")
    assert resp.status_code == 200
    assert resp.json()["stored"] == 1

    status = client.get("/api/ingestion/status").json()
    assert status["buffered_observations"] == 1

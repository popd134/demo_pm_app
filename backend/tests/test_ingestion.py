"""Tests for scheduled ingestion & polling (WBS 1.1.2)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from app.schemas.weather import CurrentConditions, Forecast, GeoPoint, WeatherObservation
from app.services.ingestion import (
    IngestionScheduler,
    InMemoryObservationSink,
    TrackedLocation,
    poll_once,
)
from app.services.providers import ProviderError, register_provider
from app.services.providers.base import WeatherProvider

LONDON = TrackedLocation(name="London", latitude=51.5074, longitude=-0.1278)
PARIS = TrackedLocation(name="Paris", latitude=48.8566, longitude=2.3522)


class _StubProvider(WeatherProvider):
    name = "stub"

    def __init__(self, fail_for: set[str] | None = None) -> None:
        super().__init__()
        self._fail_for = fail_for or set()
        self.calls = 0

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        self.calls += 1
        if round(location.latitude, 4) in self._fail_for:
            raise ProviderError("stub failure")
        return CurrentConditions(
            location=location,
            observation=WeatherObservation(
                provider=self.name,
                observed_at=datetime(2026, 8, 5, 12, tzinfo=UTC),
                temperature_c=20.0,
            ),
        )

    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:  # noqa: ARG002
        raise NotImplementedError

    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:  # noqa: ARG002
        raise NotImplementedError


@pytest.fixture()
def stub_provider() -> _StubProvider:
    provider = _StubProvider()
    register_provider("stub", lambda _settings: provider)
    return provider


@pytest.mark.asyncio
async def test_poll_once_stores_all_locations(stub_provider) -> None:
    sink = InMemoryObservationSink()
    stored = await poll_once([LONDON, PARIS], sink, provider_name="stub")
    assert stored == 2
    assert len(sink) == 2
    assert sink.records[0][0].name == "London"


@pytest.mark.asyncio
async def test_poll_once_skips_failing_location() -> None:
    provider = _StubProvider(fail_for={round(PARIS.latitude, 4)})
    register_provider("stub", lambda _settings: provider)
    sink = InMemoryObservationSink()
    stored = await poll_once([LONDON, PARIS], sink, provider_name="stub")
    assert stored == 1
    assert len(sink) == 1


@pytest.mark.asyncio
async def test_scheduler_runs_and_stops(stub_provider) -> None:
    sink = InMemoryObservationSink()
    scheduler = IngestionScheduler(
        [LONDON], sink, interval_seconds=1, provider_name="stub"
    )
    scheduler.start()
    assert scheduler.running
    # Wait for at least one cycle to complete.
    for _ in range(50):
        if scheduler.cycles >= 1:
            break
        await asyncio.sleep(0.01)
    await scheduler.stop()
    assert not scheduler.running
    assert scheduler.cycles >= 1
    assert len(sink) >= 1


@pytest.mark.asyncio
async def test_scheduler_noop_without_locations(stub_provider) -> None:
    scheduler = IngestionScheduler([], InMemoryObservationSink(), interval_seconds=1)
    scheduler.start()
    assert not scheduler.running

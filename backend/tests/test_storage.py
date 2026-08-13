"""Tests for canonical observation persistence & dedup (WBS 1.1.3)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.database import SessionLocal
from app.schemas.weather import CurrentConditions, GeoPoint, WeatherObservation
from app.services.ingestion import TrackedLocation, poll_once
from app.services.providers import register_provider
from app.services.providers.base import WeatherProvider
from app.services.storage import (
    DatabaseObservationSink,
    get_or_create_location,
    recent_observations,
    store_observation,
)

LONDON = TrackedLocation(name="London", latitude=51.5074, longitude=-0.1278)


def _conditions(temp: float = 20.0, when: datetime | None = None) -> CurrentConditions:
    return CurrentConditions(
        location=GeoPoint(latitude=LONDON.latitude, longitude=LONDON.longitude),
        observation=WeatherObservation(
            provider="test",
            observed_at=when or datetime(2026, 8, 5, 12, tzinfo=UTC),
            temperature_c=temp,
        ),
    )


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_get_or_create_location_is_idempotent(db) -> None:
    a = get_or_create_location(db, "London", 51.5074, -0.1278)
    db.flush()
    b = get_or_create_location(db, "London", 51.5074, -0.1278)
    assert a.id == b.id


def test_store_observation_persists_and_dedupes(db) -> None:
    location = get_or_create_location(db, "Dedup City", 10.0, 10.0)
    db.flush()

    assert store_observation(db, location, _conditions()) is True
    # Same (location, provider, observed_at) → duplicate, not stored again.
    assert store_observation(db, location, _conditions(temp=25.0)) is False

    rows = recent_observations(db, location.id)
    assert len(rows) == 1
    assert rows[0].temperature_c == 20.0


def test_store_observation_keeps_distinct_timestamps(db) -> None:
    location = get_or_create_location(db, "Series City", 20.0, 20.0)
    db.flush()
    store_observation(db, location, _conditions(when=datetime(2026, 8, 5, 1, tzinfo=UTC)))
    store_observation(db, location, _conditions(when=datetime(2026, 8, 5, 2, tzinfo=UTC)))
    assert len(recent_observations(db, location.id)) == 2


class _StubProvider(WeatherProvider):
    name = "storage-stub"

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        return CurrentConditions(
            location=location,
            observation=WeatherObservation(
                provider=self.name,
                observed_at=datetime(2026, 8, 5, 6, tzinfo=UTC),
                temperature_c=17.7,
            ),
        )

    async def get_hourly(self, location, hours=24):  # noqa: ANN001, ARG002
        raise NotImplementedError

    async def get_forecast(self, location, days=7):  # noqa: ANN001, ARG002
        raise NotImplementedError


@pytest.mark.asyncio
async def test_database_sink_via_poll_once() -> None:
    register_provider("storage-stub", lambda _settings: _StubProvider())
    sink = DatabaseObservationSink()
    tracked = TrackedLocation(name="Sink City", latitude=30.0, longitude=30.0)

    stored = await poll_once([tracked], sink, provider_name="storage-stub")
    assert stored == 1
    assert sink.stored == 1

    db = SessionLocal()
    try:
        location = get_or_create_location(db, "Sink City", 30.0, 30.0)
        rows = recent_observations(db, location.id)
        assert len(rows) == 1
        assert rows[0].temperature_c == 17.7
    finally:
        db.close()

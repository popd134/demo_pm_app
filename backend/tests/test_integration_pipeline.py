"""End-to-end integration test across ingestion, API and analytics (WBS 1.7.1).

Exercises the full path a reading takes: admin registers a location, observations are
ingested/stored, then queried, aggregated into trends, and evaluated into alerts.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.database import SessionLocal
from app.schemas.weather import (
    CurrentConditions,
    Forecast,
    ForecastEntry,
    GeoPoint,
    WeatherObservation,
)
from app.services.ingestion import TrackedLocation, poll_once
from app.services.providers import register_provider
from app.services.providers.base import WeatherProvider
from app.services.storage import (
    DatabaseObservationSink,
    get_or_create_location,
    store_forecast,
)


class _RampProvider(WeatherProvider):
    """Returns a rising temperature per call, with a final spike."""

    name = "ramp"

    def __init__(self) -> None:
        super().__init__()
        self._temps = [18.0, 19.0, 20.0, 60.0]  # last is an extreme (threshold breach)
        self._i = 0

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        temp = self._temps[min(self._i, len(self._temps) - 1)]
        observed = datetime(2026, 8, 5, 6, tzinfo=UTC) + timedelta(hours=self._i)
        self._i += 1
        return CurrentConditions(
            location=location,
            observation=WeatherObservation(
                provider=self.name, observed_at=observed, temperature_c=temp
            ),
        )

    async def get_hourly(self, location, hours=24):  # noqa: ANN001, ARG002
        raise NotImplementedError

    async def get_forecast(self, location, days=7):  # noqa: ANN001, ARG002
        raise NotImplementedError


@pytest.fixture()
def admin_headers(admin_auth) -> dict[str, str]:
    return admin_auth


@pytest.mark.asyncio
async def test_full_pipeline(client, admin_headers) -> None:
    # 1. Admin registers a location via the API.
    created = client.post(
        "/api/weather/locations",
        headers=admin_headers,
        json={"name": "Pipeline City", "latitude": 40.0, "longitude": -3.0},
    )
    assert created.status_code == 201
    location_id = created.json()["id"]

    # 2. Ingest four readings through the scheduler's poll path into the DB sink.
    # One shared provider instance so the ramp advances across polls.
    ramp = _RampProvider()
    register_provider("ramp", lambda _settings: ramp)
    tracked = TrackedLocation(name="Pipeline City", latitude=40.0, longitude=-3.0)
    sink = DatabaseObservationSink()
    for _ in range(4):
        await poll_once([tracked], sink, provider_name="ramp")
    assert sink.stored == 4

    # Seed a forecast so forecast-accuracy has something to compare against.
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, "Pipeline City", 40.0, -3.0)
        store_forecast(
            db,
            loc,
            Forecast(
                provider="ramp",
                location=GeoPoint(latitude=40.0, longitude=-3.0),
                generated_at=datetime(2026, 8, 5, 0, tzinfo=UTC),
                entries=[
                    ForecastEntry(
                        valid_at=datetime(2026, 8, 5, 6, tzinfo=UTC), temperature_c=17.0
                    )
                ],
            ),
            horizon="hourly",
        )
        db.commit()
    finally:
        db.close()

    # 3. Query current conditions and historical observations.
    current = client.get(f"/api/weather/locations/{location_id}/current")
    assert current.status_code == 200
    assert current.json()["temperature_c"] == 60.0  # newest reading

    history = client.get(f"/api/weather/locations/{location_id}/observations")
    assert history.status_code == 200
    assert history.json()["total"] == 4

    # 4. Aggregate into trends.
    trends = client.get(
        f"/api/analytics/locations/{location_id}/trends",
        params={"metric": "temperature_c", "period": "daily"},
    )
    assert trends.status_code == 200
    assert len(trends.json()["buckets"]) >= 1

    # 5. Evaluate anomalies — the 60°C reading breaches the threshold.
    evaluated = client.post(f"/api/analytics/locations/{location_id}/evaluate")
    assert evaluated.status_code == 200
    assert any(a["kind"] == "threshold_high" for a in evaluated.json())

    alerts = client.get(f"/api/analytics/locations/{location_id}/alerts")
    assert alerts.status_code == 200
    assert len(alerts.json()) >= 1

    # 6. Forecast vs actual accuracy is computable.
    accuracy = client.get(
        f"/api/analytics/locations/{location_id}/forecast-accuracy",
        params={"metric": "temperature_c", "horizon": "hourly"},
    )
    assert accuracy.status_code == 200
    assert accuracy.json()["sample_count"] >= 1

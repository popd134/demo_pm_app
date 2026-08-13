"""API tests for the analytics endpoints (WBS 1.3.1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.database import SessionLocal
from app.schemas.weather import CurrentConditions, GeoPoint, WeatherObservation
from app.services.storage import get_or_create_location, store_observation


def _seed(name: str, lat: float, lon: float, readings: list[tuple[datetime, float]]) -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, name, lat, lon)
        db.flush()
        for when, temp in readings:
            store_observation(
                db,
                loc,
                CurrentConditions(
                    location=GeoPoint(latitude=lat, longitude=lon),
                    observation=WeatherObservation(
                        provider="seed", observed_at=when, temperature_c=temp
                    ),
                ),
            )
        db.commit()
        return loc.id
    finally:
        db.close()


@pytest.fixture()
def location_id() -> int:
    return _seed(
        "TrendCity",
        12.34,
        56.78,
        [
            (datetime(2026, 8, 5, 6, tzinfo=UTC), 10.0),
            (datetime(2026, 8, 5, 18, tzinfo=UTC), 20.0),
            (datetime(2026, 8, 6, 6, tzinfo=UTC), 18.0),
        ],
    )


def test_trends_daily(client, location_id) -> None:
    resp = client.get(
        f"/api/analytics/locations/{location_id}/trends",
        params={"metric": "temperature_c", "period": "daily"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["period"] == "daily"
    assert len(body["buckets"]) == 2
    assert body["buckets"][0]["average"] == 15.0
    assert body["buckets"][1]["change_from_previous"] == 3.0


def test_rolling_endpoint(client, location_id) -> None:
    resp = client.get(
        f"/api/analytics/locations/{location_id}/rolling",
        params={"metric": "temperature_c", "window": 2},
    )
    assert resp.status_code == 200
    points = resp.json()["points"]
    assert [p["value"] for p in points] == [15.0, 19.0]


def test_trends_unknown_metric_422(client, location_id) -> None:
    resp = client.get(
        f"/api/analytics/locations/{location_id}/trends",
        params={"metric": "nonsense"},
    )
    assert resp.status_code == 422


def test_trends_unknown_location_404(client) -> None:
    resp = client.get("/api/analytics/locations/999999/trends")
    assert resp.status_code == 404

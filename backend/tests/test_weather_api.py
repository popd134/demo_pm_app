"""Tests for the weather query REST API (WBS 1.2.2)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.database import SessionLocal
from app.schemas.weather import (
    CurrentConditions,
    Forecast,
    ForecastEntry,
    GeoPoint,
    WeatherObservation,
)
from app.services.storage import (
    get_or_create_location,
    store_forecast,
    store_observation,
)


def _seed_location_with_data(name: str, lat: float, lon: float) -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, name, lat, lon)
        db.flush()
        point = GeoPoint(latitude=lat, longitude=lon)
        for hour, temp in ((9, 15.0), (10, 16.5), (11, 18.0)):
            store_observation(
                db,
                loc,
                CurrentConditions(
                    location=point,
                    observation=WeatherObservation(
                        provider="seed",
                        observed_at=datetime(2026, 8, 5, hour, tzinfo=UTC),
                        temperature_c=temp,
                    ),
                ),
            )
        store_forecast(
            db,
            loc,
            Forecast(
                provider="seed",
                location=point,
                generated_at=datetime(2026, 8, 5, 12, tzinfo=UTC),
                entries=[
                    ForecastEntry(
                        valid_at=datetime(2026, 8, 6, tzinfo=UTC), temperature_c=20.0
                    )
                ],
            ),
        )
        db.commit()
        return loc.id
    finally:
        db.close()


@pytest.fixture()
def location_id() -> int:
    return _seed_location_with_data("Lisbon", 38.7223, -9.1393)


def test_create_and_list_locations(client) -> None:
    resp = client.post(
        "/api/weather/locations",
        json={"name": "Madrid", "latitude": 40.4168, "longitude": -3.7038,
              "country": "ES"},
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["country"] == "ES"

    listing = client.get("/api/weather/locations")
    assert listing.status_code == 200
    assert any(loc["name"] == "Madrid" for loc in listing.json())


def test_get_location_404(client) -> None:
    resp = client.get("/api/weather/locations/999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_current_conditions_returns_latest(client, location_id) -> None:
    resp = client.get(f"/api/weather/locations/{location_id}/current")
    assert resp.status_code == 200
    assert resp.json()["temperature_c"] == 18.0  # newest of the seeded readings


def test_historical_pagination_and_total(client, location_id) -> None:
    resp = client.get(
        f"/api/weather/locations/{location_id}/observations",
        params={"limit": 2, "offset": 0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["temperature_c"] == 18.0  # newest first


def test_historical_time_filter(client, location_id) -> None:
    resp = client.get(
        f"/api/weather/locations/{location_id}/observations",
        params={"start": "2026-08-05T10:00:00Z", "end": "2026-08-05T10:59:00Z"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["temperature_c"] == 16.5


def test_historical_rejects_reversed_range(client, location_id) -> None:
    resp = client.get(
        f"/api/weather/locations/{location_id}/observations",
        params={"start": "2026-08-06T00:00:00Z", "end": "2026-08-05T00:00:00Z"},
    )
    assert resp.status_code == 422


def test_forecast_endpoint_returns_latest(client, location_id) -> None:
    resp = client.get(f"/api/weather/locations/{location_id}/forecast")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "seed"
    assert len(body["points"]) == 1
    assert body["points"][0]["temperature_c"] == 20.0


def test_current_conditions_404_when_no_data(client) -> None:
    empty_id = _seed_empty_location()
    resp = client.get(f"/api/weather/locations/{empty_id}/current")
    assert resp.status_code == 404


def _seed_empty_location() -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, "Empty", 1.0, 1.0)
        db.commit()
        return loc.id
    finally:
        db.close()

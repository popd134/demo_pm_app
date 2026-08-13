"""API/integration tests for alert evaluation & listing (WBS 1.3.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.database import SessionLocal
from app.schemas.weather import CurrentConditions, GeoPoint, WeatherObservation
from app.services.storage import get_or_create_location, store_observation


def _store(loc, db, when, **metrics) -> None:
    store_observation(
        db,
        loc,
        CurrentConditions(
            location=GeoPoint(latitude=loc.latitude, longitude=loc.longitude),
            observation=WeatherObservation(
                provider="seed", observed_at=when, **metrics
            ),
        ),
    )


def _seed(name: str, lat: float, lon: float, temps: list[float]) -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, name, lat, lon)
        db.flush()
        base = datetime(2026, 8, 5, tzinfo=UTC)
        for i, t in enumerate(temps):
            _store(loc, db, base + timedelta(hours=i), temperature_c=t)
        db.commit()
        return loc.id
    finally:
        db.close()


def test_evaluate_flags_threshold_breach(client) -> None:
    # Latest reading 60C exceeds the 45C max threshold.
    loc_id = _seed("HotCity", 1.1, 2.2, [20.0, 21.0, 60.0])
    resp = client.post(f"/api/analytics/locations/{loc_id}/evaluate")
    assert resp.status_code == 200
    alerts = resp.json()
    assert any(a["kind"] == "threshold_high" and a["metric"] == "temperature_c"
               for a in alerts)


def test_evaluate_is_idempotent(client) -> None:
    loc_id = _seed("HotCity2", 3.3, 4.4, [20.0, 21.0, 60.0])
    first = client.post(f"/api/analytics/locations/{loc_id}/evaluate").json()
    assert len(first) >= 1
    # Re-evaluating the same latest observation creates no duplicates.
    second = client.post(f"/api/analytics/locations/{loc_id}/evaluate").json()
    assert second == []


def test_list_alerts_returns_persisted(client) -> None:
    loc_id = _seed("HotCity3", 5.5, 6.6, [20.0, 21.0, 60.0])
    client.post(f"/api/analytics/locations/{loc_id}/evaluate")
    listing = client.get(f"/api/analytics/locations/{loc_id}/alerts")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1


def test_evaluate_no_data_returns_empty(client) -> None:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, "QuietCity", 7.7, 8.8)
        db.commit()
        loc_id = loc.id
    finally:
        db.close()
    resp = client.post(f"/api/analytics/locations/{loc_id}/evaluate")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("path", ["alerts", "evaluate"])
def test_alert_endpoints_404_for_unknown_location(client, path) -> None:
    method = client.get if path == "alerts" else client.post
    resp = method(f"/api/analytics/locations/999999/{path}")
    assert resp.status_code == 404

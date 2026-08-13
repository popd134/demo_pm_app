"""API/integration test for forecast-accuracy (WBS 1.3.3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


def _seed() -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, "AccCity", 9.9, 10.1)
        db.flush()
        point = GeoPoint(latitude=9.9, longitude=10.1)
        base = datetime(2026, 8, 6, 12, tzinfo=UTC)
        # Forecast predicts 20 and 22.
        store_forecast(
            db,
            loc,
            Forecast(
                provider="seed",
                location=point,
                generated_at=datetime(2026, 8, 6, 0, tzinfo=UTC),
                entries=[
                    ForecastEntry(valid_at=base, temperature_c=20.0),
                    ForecastEntry(valid_at=base + timedelta(hours=1), temperature_c=22.0),
                ],
            ),
            horizon="hourly",
        )
        # Actuals near the forecast times: 19 and 25.
        for when, temp in (
            (base + timedelta(minutes=2), 19.0),
            (base + timedelta(hours=1, minutes=3), 25.0),
        ):
            store_observation(
                db,
                loc,
                CurrentConditions(
                    location=point,
                    observation=WeatherObservation(
                        provider="seed", observed_at=when, temperature_c=temp
                    ),
                ),
            )
        db.commit()
        return loc.id
    finally:
        db.close()


def test_forecast_accuracy_endpoint(client) -> None:
    loc_id = _seed()
    resp = client.get(
        f"/api/analytics/locations/{loc_id}/forecast-accuracy",
        params={"metric": "temperature_c", "horizon": "hourly"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sample_count"] == 2
    # errors: 20-19=+1, 22-25=-3 -> MAE=2.0, bias=-1.0
    assert body["mae"] == 2.0
    assert body["bias"] == -1.0


def test_forecast_accuracy_unknown_metric_422(client) -> None:
    loc_id = _seed()
    resp = client.get(
        f"/api/analytics/locations/{loc_id}/forecast-accuracy",
        params={"metric": "pressure_hpa"},
    )
    assert resp.status_code == 422


def test_forecast_accuracy_no_forecast_404(client) -> None:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, "NoForecast", 11.1, 12.2)
        db.commit()
        loc_id = loc.id
    finally:
        db.close()
    resp = client.get(f"/api/analytics/locations/{loc_id}/forecast-accuracy")
    assert resp.status_code == 404

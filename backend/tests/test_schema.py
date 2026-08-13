"""Tests for the database schema: users, forecasts, location metadata (WBS 1.2.1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models import (
    Forecast,
    ForecastPoint,
    Location,
    User,
    UserRole,
)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_location_accepts_metadata(db) -> None:
    loc = Location(
        name="Berlin",
        latitude=52.52,
        longitude=13.405,
        country="DE",
        timezone="Europe/Berlin",
        elevation_m=34.0,
    )
    db.add(loc)
    db.commit()
    fetched = db.get(Location, loc.id)
    assert fetched.timezone == "Europe/Berlin"
    assert fetched.elevation_m == 34.0


def test_user_role_defaults_and_unique_email(db) -> None:
    user = User(email="a@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    assert user.role is UserRole.USER
    assert user.is_active is True

    db.add(User(email="a@example.com", hashed_password="y"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_forecast_with_points_cascade(db) -> None:
    loc = Location(name="Oslo", latitude=59.91, longitude=10.75)
    db.add(loc)
    db.flush()

    forecast = Forecast(
        location_id=loc.id,
        provider="open-meteo",
        horizon="daily",
        generated_at=datetime(2026, 8, 5, tzinfo=UTC),
        points=[
            ForecastPoint(valid_at=datetime(2026, 8, 6, tzinfo=UTC), temperature_c=20.0),
            ForecastPoint(valid_at=datetime(2026, 8, 7, tzinfo=UTC), temperature_c=22.0),
        ],
    )
    db.add(forecast)
    db.commit()

    assert len(forecast.points) == 2
    # Deleting the forecast cascades to its points.
    point_ids = [p.id for p in forecast.points]
    db.delete(forecast)
    db.commit()
    remaining = db.scalars(
        select(ForecastPoint).where(ForecastPoint.id.in_(point_ids))
    ).all()
    assert remaining == []


def test_forecast_point_dedup_constraint(db) -> None:
    loc = Location(name="Rome", latitude=41.9, longitude=12.5)
    db.add(loc)
    db.flush()
    forecast = Forecast(
        location_id=loc.id,
        provider="test",
        generated_at=datetime(2026, 8, 5, tzinfo=UTC),
    )
    db.add(forecast)
    db.flush()

    when = datetime(2026, 8, 6, tzinfo=UTC)
    db.add(ForecastPoint(forecast_id=forecast.id, valid_at=when, temperature_c=1.0))
    db.add(ForecastPoint(forecast_id=forecast.id, valid_at=when, temperature_c=2.0))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

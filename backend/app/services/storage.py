"""Persistence of canonical weather observations (WBS 1.1.3).

Provides repository helpers plus a :class:`DatabaseObservationSink` so the ingestion
scheduler (WBS 1.1.2) can durably store readings. Deduplication is enforced by the
``uq_observation_dedup`` constraint; a duplicate reading is silently ignored.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.forecast import Forecast as ForecastModel
from app.models.forecast import ForecastPoint
from app.models.weather import Location, Observation
from app.schemas.weather import CurrentConditions
from app.schemas.weather import Forecast as ForecastSchema
from app.services.ingestion import TrackedLocation
from app.services.normalization import normalise_observation


def get_or_create_location(
    db: Session, name: str, latitude: float, longitude: float
) -> Location:
    """Return the matching location, creating it if necessary (idempotent)."""
    stmt = select(Location).where(
        Location.latitude == latitude, Location.longitude == longitude
    )
    location = db.scalars(stmt).first()
    if location is None:
        location = Location(name=name, latitude=latitude, longitude=longitude)
        db.add(location)
        db.flush()
    return location


def store_observation(
    db: Session, location: Location, conditions: CurrentConditions
) -> bool:
    """Persist a canonical observation. Returns False if it was a duplicate."""
    reading = normalise_observation(conditions.observation)
    observation = Observation(
        location_id=location.id,
        provider=conditions.observation.provider,
        observed_at=conditions.observation.observed_at,
        temperature_c=reading.temperature_c,
        humidity_pct=reading.humidity_pct,
        wind_speed_ms=reading.wind_speed_ms,
        wind_direction_deg=reading.wind_direction_deg,
        precipitation_mm=reading.precipitation_mm,
        pressure_hpa=reading.pressure_hpa,
        condition=reading.condition,
    )
    # A SAVEPOINT keeps a duplicate insert from rolling back other pending work.
    try:
        with db.begin_nested():
            db.add(observation)
            db.flush()
    except IntegrityError:
        return False
    return True


def store_forecast(
    db: Session, location: Location, forecast: ForecastSchema, horizon: str = "daily"
) -> ForecastModel:
    """Persist a provider forecast run and its points for a location."""
    row = ForecastModel(
        location_id=location.id,
        provider=forecast.provider,
        horizon=horizon,
        generated_at=forecast.generated_at,
        points=[
            ForecastPoint(
                valid_at=entry.valid_at,
                temperature_c=entry.temperature_c,
                precipitation_mm=entry.precipitation_mm,
                wind_speed_ms=entry.wind_speed_ms,
                condition=entry.condition,
            )
            for entry in forecast.entries
        ],
    )
    db.add(row)
    db.flush()
    return row


def recent_observations(
    db: Session, location_id: int, limit: int = 50
) -> list[Observation]:
    """Return the most recent observations for a location, newest first."""
    stmt = (
        select(Observation)
        .where(Observation.location_id == location_id)
        .order_by(Observation.observed_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


class DatabaseObservationSink:
    """An :class:`~app.services.ingestion.ObservationSink` backed by the database."""

    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory
        self.stored = 0

    async def store(
        self, location: TrackedLocation, conditions: CurrentConditions
    ) -> None:
        db = self._session_factory()
        try:
            row = get_or_create_location(
                db, location.name, location.latitude, location.longitude
            )
            if store_observation(db, row, conditions):
                self.stored += 1
            db.commit()
        finally:
            db.close()

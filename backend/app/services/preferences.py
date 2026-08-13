"""User preferences & saved-locations service (WBS 1.6.1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preferences import SavedLocation, UserPreferences
from app.models.weather import Location


class NotFoundError(Exception):
    """Raised when a referenced entity does not exist."""


def get_or_create_preferences(db: Session, user_id: int) -> UserPreferences:
    prefs = db.scalars(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    ).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id, alert_thresholds={})
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def update_preferences(
    db: Session,
    user_id: int,
    *,
    temperature_unit: str | None = None,
    wind_unit: str | None = None,
    alert_thresholds: dict | None = None,
) -> UserPreferences:
    prefs = get_or_create_preferences(db, user_id)
    if temperature_unit is not None:
        prefs.temperature_unit = temperature_unit
    if wind_unit is not None:
        prefs.wind_unit = wind_unit
    if alert_thresholds is not None:
        prefs.alert_thresholds = alert_thresholds
    db.commit()
    db.refresh(prefs)
    return prefs


def list_saved_locations(db: Session, user_id: int) -> list[tuple[SavedLocation, Location]]:
    stmt = (
        select(SavedLocation, Location)
        .join(Location, Location.id == SavedLocation.location_id)
        .where(SavedLocation.user_id == user_id)
        .order_by(Location.name)
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def add_saved_location(db: Session, user_id: int, location_id: int) -> SavedLocation:
    location = db.get(Location, location_id)
    if location is None:
        raise NotFoundError(f"location {location_id} not found")
    existing = db.scalars(
        select(SavedLocation).where(
            SavedLocation.user_id == user_id,
            SavedLocation.location_id == location_id,
        )
    ).first()
    if existing is not None:
        return existing
    saved = SavedLocation(user_id=user_id, location_id=location_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def remove_saved_location(db: Session, user_id: int, location_id: int) -> bool:
    saved = db.scalars(
        select(SavedLocation).where(
            SavedLocation.user_id == user_id,
            SavedLocation.location_id == location_id,
        )
    ).first()
    if saved is None:
        return False
    db.delete(saved)
    db.commit()
    return True

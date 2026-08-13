"""Read-side queries for the weather API (WBS 1.2.2).

Repository helpers for locations, observations (with time-range filtering and
pagination) and the latest stored forecast. Kept separate from the write-side
``storage`` module so the query surface is easy to reason about and test.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.forecast import Forecast
from app.models.weather import Location, Observation


def list_locations(db: Session) -> list[Location]:
    return list(db.scalars(select(Location).order_by(Location.name)).all())


def get_location(db: Session, location_id: int) -> Location | None:
    return db.get(Location, location_id)


def latest_observation(db: Session, location_id: int) -> Observation | None:
    stmt = (
        select(Observation)
        .where(Observation.location_id == location_id)
        .order_by(Observation.observed_at.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def observations_in_range(
    db: Session,
    location_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Observation], int]:
    """Return a page of observations (newest first) and the total match count."""
    filters = [Observation.location_id == location_id]
    if start is not None:
        filters.append(Observation.observed_at >= start)
    if end is not None:
        filters.append(Observation.observed_at <= end)

    total = db.scalar(
        select(func.count()).select_from(Observation).where(*filters)
    )
    stmt = (
        select(Observation)
        .where(*filters)
        .order_by(Observation.observed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(db.scalars(stmt).all())
    return rows, int(total or 0)


def metric_series(
    db: Session,
    location_id: int,
    metric: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[tuple[datetime, float | None]]:
    """Return ``(observed_at, value)`` samples for one metric, oldest first.

    Used by the analytics engine (WBS 1.3.x). ``metric`` must be a column on
    :class:`Observation`.
    """
    column = getattr(Observation, metric)
    filters = [Observation.location_id == location_id]
    if start is not None:
        filters.append(Observation.observed_at >= start)
    if end is not None:
        filters.append(Observation.observed_at <= end)
    stmt = (
        select(Observation.observed_at, column)
        .where(*filters)
        .order_by(Observation.observed_at.asc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def latest_forecast(
    db: Session, location_id: int, horizon: str | None = None
) -> Forecast | None:
    filters = [Forecast.location_id == location_id]
    if horizon is not None:
        filters.append(Forecast.horizon == horizon)
    stmt = (
        select(Forecast)
        .where(*filters)
        .order_by(Forecast.generated_at.desc())
        .limit(1)
        .options(selectinload(Forecast.points))
    )
    return db.scalars(stmt).first()

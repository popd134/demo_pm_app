"""Weather query REST API (WBS 1.2.2).

Read endpoints over the stored time series — current conditions, historical ranges
(filtered + paginated) and the latest forecast — plus location registration. Live
provider calls live under ``/api/providers`` (WBS 1.1.1); these routes serve persisted
data.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.api import (
    ErrorResponse,
    ForecastRead,
    LocationCreate,
    LocationRead,
    ObservationRead,
    Page,
)
from app.services import queries
from app.services.storage import get_or_create_location

router = APIRouter(prefix="/weather", tags=["weather"])

NOT_FOUND = {404: {"model": ErrorResponse}}


def _require_location(db: Session, location_id: int):
    location = queries.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail=f"location {location_id} not found")
    return location


@router.get("/locations", response_model=list[LocationRead])
def list_locations(db: Session = Depends(get_db)) -> list[LocationRead]:
    return [LocationRead.model_validate(loc) for loc in queries.list_locations(db)]


@router.post("/locations", response_model=LocationRead, status_code=201)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> LocationRead:
    location = get_or_create_location(
        db, payload.name, payload.latitude, payload.longitude
    )
    # Fill optional metadata on first registration.
    location.country = location.country or payload.country
    location.timezone = location.timezone or payload.timezone
    if location.elevation_m is None:
        location.elevation_m = payload.elevation_m
    db.commit()
    db.refresh(location)
    return LocationRead.model_validate(location)


@router.get("/locations/{location_id}", response_model=LocationRead, responses=NOT_FOUND)
def get_location(location_id: int, db: Session = Depends(get_db)) -> LocationRead:
    return LocationRead.model_validate(_require_location(db, location_id))


@router.get(
    "/locations/{location_id}/current",
    response_model=ObservationRead,
    responses=NOT_FOUND,
)
def current_conditions(
    location_id: int, db: Session = Depends(get_db)
) -> ObservationRead:
    _require_location(db, location_id)
    observation = queries.latest_observation(db, location_id)
    if observation is None:
        raise HTTPException(
            status_code=404, detail="no observations stored for this location"
        )
    return ObservationRead.model_validate(observation)


@router.get(
    "/locations/{location_id}/observations",
    response_model=Page[ObservationRead],
    responses=NOT_FOUND,
)
def historical_observations(
    location_id: int,
    start: datetime | None = Query(default=None, description="ISO start (inclusive)"),
    end: datetime | None = Query(default=None, description="ISO end (inclusive)"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[ObservationRead]:
    _require_location(db, location_id)
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be before end")
    rows, total = queries.observations_in_range(
        db, location_id, start=start, end=end, limit=limit, offset=offset
    )
    return Page[ObservationRead](
        items=[ObservationRead.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/locations/{location_id}/forecast",
    response_model=ForecastRead,
    responses=NOT_FOUND,
)
def latest_forecast(
    location_id: int,
    horizon: str | None = Query(default=None, pattern="^(hourly|daily)$"),
    db: Session = Depends(get_db),
) -> ForecastRead:
    _require_location(db, location_id)
    forecast = queries.latest_forecast(db, location_id, horizon=horizon)
    if forecast is None:
        raise HTTPException(
            status_code=404, detail="no forecast stored for this location"
        )
    return ForecastRead.model_validate(forecast)

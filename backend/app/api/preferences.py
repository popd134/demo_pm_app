"""User preferences & saved-locations endpoints (WBS 1.6.1). All behind auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.weather import Location
from app.schemas.api import LocationRead
from app.schemas.preferences import (
    PreferencesRead,
    PreferencesUpdate,
    SavedLocationCreate,
    SavedLocationRead,
)
from app.services import preferences as prefs_service

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferencesRead)
def read_preferences(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> PreferencesRead:
    return PreferencesRead.model_validate(
        prefs_service.get_or_create_preferences(db, user.id)
    )


@router.put("", response_model=PreferencesRead)
def update_preferences(
    payload: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesRead:
    prefs = prefs_service.update_preferences(
        db,
        user.id,
        temperature_unit=payload.temperature_unit,
        wind_unit=payload.wind_unit,
        alert_thresholds=payload.alert_thresholds,
    )
    return PreferencesRead.model_validate(prefs)


@router.get("/locations", response_model=list[SavedLocationRead])
def list_saved_locations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SavedLocationRead]:
    rows = prefs_service.list_saved_locations(db, user.id)
    return [
        SavedLocationRead(id=saved.id, location=LocationRead.model_validate(location))
        for saved, location in rows
    ]


@router.post("/locations", response_model=SavedLocationRead, status_code=201)
def add_saved_location(
    payload: SavedLocationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedLocationRead:
    try:
        saved = prefs_service.add_saved_location(db, user.id, payload.location_id)
    except prefs_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    location = db.get(Location, payload.location_id)
    return SavedLocationRead(id=saved.id, location=LocationRead.model_validate(location))


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def remove_saved_location(
    location_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    removed = prefs_service.remove_saved_location(db, user.id, location_id)
    if not removed:
        raise HTTPException(status_code=404, detail="saved location not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

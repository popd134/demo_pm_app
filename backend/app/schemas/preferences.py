"""Schemas for user preferences & saved locations (WBS 1.6.1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.api import LocationRead


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    temperature_unit: str
    wind_unit: str
    alert_thresholds: dict


class PreferencesUpdate(BaseModel):
    temperature_unit: Literal["c", "f"] | None = None
    wind_unit: Literal["ms", "kmh", "mph"] | None = None
    alert_thresholds: dict[str, dict[str, float]] | None = None


class SavedLocationCreate(BaseModel):
    location_id: int


class SavedLocationRead(BaseModel):
    id: int
    location: LocationRead

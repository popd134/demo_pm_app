"""API request/response schemas for the weather query API (WBS 1.2.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class LocationCreate(BaseModel):
    """Payload to register a tracked location."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "London",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "country": "GB",
                "timezone": "Europe/London",
                "elevation_m": 11,
            }
        }
    )

    name: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    country: str | None = None
    timezone: str | None = None
    elevation_m: float | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    timezone: str | None = None
    elevation_m: float | None = None


class ObservationRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "provider": "open-meteo",
                "observed_at": "2026-08-05T12:00:00Z",
                "temperature_c": 21.4,
                "humidity_pct": 60,
                "wind_speed_ms": 3.2,
                "wind_direction_deg": 180,
                "precipitation_mm": 0.0,
                "pressure_hpa": 1012.3,
                "condition": "Partly cloudy",
            }
        },
    )

    id: int
    provider: str
    observed_at: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None
    pressure_hpa: float | None = None
    condition: str | None = None


class ForecastPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    valid_at: datetime
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_ms: float | None = None
    condition: str | None = None


class ForecastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    horizon: str
    generated_at: datetime
    points: list[ForecastPointRead]


class Page(BaseModel, Generic[T]):
    """A paginated result envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    """Consistent error body returned for handled failures."""

    detail: str

"""Provider-facing weather schemas (WBS 1.1.1).

These are the *parsed* shapes returned by provider clients: a normalised, provider-
independent view of a single source's response. Canonical persistence models and unit
conversion are the concern of WBS 1.1.3; the REST query API is WBS 1.2.2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    """A latitude/longitude location a provider was queried for."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class WeatherObservation(BaseModel):
    """A single point-in-time weather reading parsed from a provider response."""

    provider: str
    observed_at: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None
    pressure_hpa: float | None = None
    condition: str | None = None


class CurrentConditions(BaseModel):
    """Current conditions for a location, as reported by one provider."""

    location: GeoPoint
    observation: WeatherObservation


class ForecastEntry(BaseModel):
    """A single forecasted time step (hourly or daily)."""

    valid_at: datetime
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_ms: float | None = None
    condition: str | None = None


class Forecast(BaseModel):
    """A sequence of forecast steps for a location from one provider."""

    provider: str
    location: GeoPoint
    generated_at: datetime
    entries: list[ForecastEntry]

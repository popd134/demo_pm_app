"""Unit conversion & canonicalisation of weather readings (WBS 1.1.3).

Provider clients (WBS 1.1.1) already request canonical units where possible, but
readings still need defensive canonicalisation before storage: convert any non-canonical
units, round to sensible precision, and drop physically impossible values. Canonical
units are °C, m/s, mm, hPa, %, degrees.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.weather import WeatherObservation


def fahrenheit_to_celsius(value: float) -> float:
    return (value - 32.0) * 5.0 / 9.0


def kmh_to_ms(value: float) -> float:
    return value / 3.6


def mph_to_ms(value: float) -> float:
    return value * 0.44704


def mmhg_to_hpa(value: float) -> float:
    return value * 1.33322


def _clamp(value: float | None, low: float, high: float) -> float | None:
    """Return the value if within [low, high], else None (treated as missing)."""
    if value is None:
        return None
    return value if low <= value <= high else None


@dataclass(frozen=True)
class CanonicalReading:
    """A validated, canonical-unit weather reading ready for persistence."""

    temperature_c: float | None
    humidity_pct: float | None
    wind_speed_ms: float | None
    wind_direction_deg: float | None
    precipitation_mm: float | None
    pressure_hpa: float | None
    condition: str | None


def normalise_observation(obs: WeatherObservation) -> CanonicalReading:
    """Validate and round a provider observation into a canonical reading.

    Out-of-range values (e.g. humidity > 100, negative precipitation) are dropped to
    ``None`` rather than stored, so downstream analytics are not skewed by bad data.
    """
    return CanonicalReading(
        temperature_c=_round(_clamp(obs.temperature_c, -100.0, 65.0)),
        humidity_pct=_round(_clamp(obs.humidity_pct, 0.0, 100.0)),
        wind_speed_ms=_round(_clamp(obs.wind_speed_ms, 0.0, 150.0)),
        wind_direction_deg=_round(_clamp(obs.wind_direction_deg, 0.0, 360.0)),
        precipitation_mm=_round(_clamp(obs.precipitation_mm, 0.0, 2000.0)),
        pressure_hpa=_round(_clamp(obs.pressure_hpa, 800.0, 1100.0)),
        condition=obs.condition,
    )


def _round(value: float | None, ndigits: int = 2) -> float | None:
    return round(value, ndigits) if value is not None else None

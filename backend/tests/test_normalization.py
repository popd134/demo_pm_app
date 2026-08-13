"""Tests for unit conversion & canonicalisation (WBS 1.1.3)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.schemas.weather import WeatherObservation
from app.services.normalization import (
    fahrenheit_to_celsius,
    kmh_to_ms,
    mmhg_to_hpa,
    mph_to_ms,
    normalise_observation,
)


@pytest.mark.parametrize(
    ("func", "value", "expected"),
    [
        (fahrenheit_to_celsius, 32.0, 0.0),
        (fahrenheit_to_celsius, 212.0, 100.0),
        (kmh_to_ms, 36.0, 10.0),
        (mph_to_ms, 10.0, 4.4704),
        (mmhg_to_hpa, 760.0, 1013.2472),
    ],
)
def test_unit_conversions(func, value, expected) -> None:
    assert func(value) == pytest.approx(expected, rel=1e-4)


def _obs(**kwargs) -> WeatherObservation:
    base = dict(provider="test", observed_at=datetime(2026, 8, 5, tzinfo=UTC))
    base.update(kwargs)
    return WeatherObservation(**base)


def test_normalise_rounds_values() -> None:
    reading = normalise_observation(_obs(temperature_c=21.456, wind_speed_ms=3.14159))
    assert reading.temperature_c == 21.46
    assert reading.wind_speed_ms == 3.14


def test_normalise_drops_out_of_range_values() -> None:
    reading = normalise_observation(
        _obs(humidity_pct=150.0, precipitation_mm=-5.0, pressure_hpa=10.0)
    )
    assert reading.humidity_pct is None
    assert reading.precipitation_mm is None
    assert reading.pressure_hpa is None


def test_normalise_preserves_condition_and_none() -> None:
    reading = normalise_observation(_obs(condition="Fog", temperature_c=None))
    assert reading.condition == "Fog"
    assert reading.temperature_c is None

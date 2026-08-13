"""Tests for forecast-vs-actual comparison (WBS 1.3.3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.forecast_accuracy import error_metrics, match_series


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 6, hour, minute, tzinfo=UTC)


def test_match_series_pairs_nearest_within_tolerance() -> None:
    predicted = [(_dt(12), 20.0), (_dt(13), 22.0)]
    actual = [(_dt(12, 5), 19.0), (_dt(13, 50), 25.0)]
    pairs = match_series(predicted, actual, tolerance=timedelta(minutes=30))
    # 12:00 pairs with 12:05; 13:00's nearest actual (13:50) is outside 30 min.
    assert pairs == [(20.0, 19.0)]


def test_match_series_skips_none_values() -> None:
    predicted = [(_dt(12), None), (_dt(13), 22.0)]
    actual = [(_dt(13, 1), 20.0)]
    assert match_series(predicted, actual) == [(22.0, 20.0)]


def test_error_metrics_computation() -> None:
    pairs = [(20.0, 18.0), (22.0, 25.0)]  # errors: +2, -3
    m = error_metrics("temperature_c", pairs)
    assert m.sample_count == 2
    assert m.mae == 2.5
    assert m.bias == -0.5
    assert m.rmse == round((((2**2) + (3**2)) / 2) ** 0.5, 4)


def test_error_metrics_empty() -> None:
    m = error_metrics("temperature_c", [])
    assert m.sample_count == 0
    assert m.mae is None and m.rmse is None and m.bias is None

"""Unit tests for anomaly detection (WBS 1.3.2)."""

from __future__ import annotations

from app.services.anomaly import (
    detect_spike,
    detect_threshold_breaches,
    zscore,
)


def test_threshold_high_breach() -> None:
    events = detect_threshold_breaches({"temperature_c": 50.0})
    assert len(events) == 1
    assert events[0].kind == "threshold_high"
    assert events[0].threshold == 45.0
    assert events[0].severity == "critical"


def test_threshold_low_breach() -> None:
    events = detect_threshold_breaches({"temperature_c": -40.0})
    assert events[0].kind == "threshold_low"


def test_no_breach_within_bounds() -> None:
    assert detect_threshold_breaches({"temperature_c": 20.0}) == []


def test_threshold_ignores_none_and_unknown() -> None:
    assert detect_threshold_breaches({"temperature_c": None}) == []


def test_custom_thresholds_override() -> None:
    events = detect_threshold_breaches(
        {"wind_speed_ms": 12.0}, {"wind_speed_ms": {"max": 10.0}}
    )
    assert events and events[0].metric == "wind_speed_ms"


def test_zscore_small_or_flat_history() -> None:
    assert zscore([1.0, 2.0], 5.0) is None  # too few
    assert zscore([5.0, 5.0, 5.0], 5.0) is None  # zero spread


def test_detect_spike_flags_outlier() -> None:
    history = [20.0, 21.0, 19.0, 20.5, 20.0]
    event = detect_spike("temperature_c", history, value=40.0, sensitivity=3.0)
    assert event is not None
    assert event.kind == "spike"


def test_detect_spike_ignores_normal_value() -> None:
    history = [20.0, 21.0, 19.0, 20.5, 20.0]
    assert detect_spike("temperature_c", history, value=20.2, sensitivity=3.0) is None


def test_detect_spike_none_value() -> None:
    assert detect_spike("temperature_c", [1.0, 2.0, 3.0], None) is None

"""Anomaly detection & threshold alerting (WBS 1.3.2).

Two complementary detectors, both database-free and unit-testable:

* **Threshold breaches** — a reading outside configured min/max bounds
  (e.g. temperature spikes, heavy precipitation).
* **Statistical spikes** — a reading whose z-score against recent history exceeds a
  sensitivity, catching unusual values even within absolute bounds.

The API layer supplies readings/history and persists the resulting :class:`AlertEvent`s.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev

# Default absolute bounds per metric. Override via ANOMALY_THRESHOLDS (JSON).
DEFAULT_THRESHOLDS: dict[str, dict[str, float]] = {
    "temperature_c": {"min": -30.0, "max": 45.0},
    "precipitation_mm": {"max": 50.0},
    "wind_speed_ms": {"max": 30.0},
    "humidity_pct": {"min": 0.0, "max": 100.0},
    "pressure_hpa": {"min": 870.0, "max": 1085.0},
}


@dataclass
class AlertEvent:
    metric: str
    value: float
    kind: str  # "threshold_high" | "threshold_low" | "spike"
    severity: str  # "info" | "warning" | "critical"
    message: str
    threshold: float | None = None


def detect_threshold_breaches(
    reading: dict[str, float | None],
    thresholds: dict[str, dict[str, float]] | None = None,
) -> list[AlertEvent]:
    """Return alerts for any metric in ``reading`` outside its configured bounds."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    events: list[AlertEvent] = []
    for metric, bounds in thresholds.items():
        value = reading.get(metric)
        if value is None:
            continue
        high = bounds.get("max")
        low = bounds.get("min")
        if high is not None and value > high:
            events.append(
                AlertEvent(
                    metric=metric,
                    value=value,
                    kind="threshold_high",
                    severity="critical",
                    threshold=high,
                    message=f"{metric} {value} exceeds max {high}",
                )
            )
        elif low is not None and value < low:
            events.append(
                AlertEvent(
                    metric=metric,
                    value=value,
                    kind="threshold_low",
                    severity="critical",
                    threshold=low,
                    message=f"{metric} {value} below min {low}",
                )
            )
    return events


def zscore(history: list[float], value: float) -> float | None:
    """Z-score of ``value`` against ``history``; None if history is too small/flat."""
    if len(history) < 3:
        return None
    spread = pstdev(history)
    if spread == 0:
        return None
    return (value - mean(history)) / spread


def detect_spike(
    metric: str,
    history: list[float],
    value: float | None,
    sensitivity: float = 3.0,
) -> AlertEvent | None:
    """Flag ``value`` as a spike when its z-score magnitude exceeds ``sensitivity``."""
    if value is None:
        return None
    z = zscore(history, value)
    if z is None or abs(z) < sensitivity:
        return None
    severity = "critical" if abs(z) >= sensitivity + 1 else "warning"
    return AlertEvent(
        metric=metric,
        value=value,
        kind="spike",
        severity=severity,
        message=f"{metric} {value} is a statistical spike (z={round(z, 2)})",
    )

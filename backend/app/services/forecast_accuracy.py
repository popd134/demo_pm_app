"""Forecast vs. actual comparison logic (WBS 1.3.3).

Match forecasted values to the observations that later occurred and compute accuracy
metrics (MAE, RMSE, bias). Pure and database-free; the API supplies predicted and
actual series from stored forecasts and observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import sqrt

# Forecast-point / observation metrics that can be compared.
COMPARABLE_METRICS = {"temperature_c", "precipitation_mm", "wind_speed_ms"}

Series = list[tuple[datetime, float | None]]


@dataclass
class AccuracyMetrics:
    metric: str
    sample_count: int
    mae: float | None
    rmse: float | None
    bias: float | None


def match_series(
    predicted: Series, actual: Series, tolerance: timedelta = timedelta(minutes=60)
) -> list[tuple[float, float]]:
    """Pair each predicted value with the nearest actual reading within ``tolerance``.

    Returns ``(predicted, actual)`` pairs; predictions with no actual inside the
    tolerance window (or with missing values) are dropped.
    """
    actual_clean = [(t, v) for t, v in actual if v is not None]
    pairs: list[tuple[float, float]] = []
    for pred_time, pred_value in predicted:
        if pred_value is None:
            continue
        best: tuple[float, float] | None = None
        best_gap: timedelta | None = None
        for act_time, act_value in actual_clean:
            gap = abs(act_time - pred_time)
            if gap <= tolerance and (best_gap is None or gap < best_gap):
                best_gap = gap
                best = (pred_value, act_value)  # type: ignore[assignment]
        if best is not None:
            pairs.append(best)
    return pairs


def error_metrics(metric: str, pairs: list[tuple[float, float]]) -> AccuracyMetrics:
    """Compute MAE, RMSE and bias (mean predicted - actual) for matched pairs."""
    if not pairs:
        return AccuracyMetrics(metric=metric, sample_count=0, mae=None, rmse=None, bias=None)
    errors = [pred - act for pred, act in pairs]
    n = len(errors)
    mae = sum(abs(e) for e in errors) / n
    rmse = sqrt(sum(e * e for e in errors) / n)
    bias = sum(errors) / n
    return AccuracyMetrics(
        metric=metric,
        sample_count=n,
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        bias=round(bias, 4),
    )

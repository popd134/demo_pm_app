"""Historical trend & aggregation computations (WBS 1.3.1).

Pure functions over ``(timestamp, value)`` samples: period bucketing (daily / weekly /
monthly) with min/max/avg/sum, period-over-period change, and rolling averages. Kept
free of the database so they are trivially unit-testable; the API layer supplies the
samples from stored observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

Sample = tuple[datetime, float | None]

PERIODS = {"daily", "weekly", "monthly"}

# Numeric observation metrics that can be aggregated.
METRICS = {
    "temperature_c",
    "humidity_pct",
    "wind_speed_ms",
    "precipitation_mm",
    "pressure_hpa",
}


@dataclass
class AggregateBucket:
    period_start: datetime
    count: int
    average: float | None
    minimum: float | None
    maximum: float | None
    total: float
    change_from_previous: float | None = field(default=None)


def bucket_start(dt: datetime, period: str) -> datetime:
    """Return the start of the period ``dt`` falls into."""
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "daily":
        return midnight
    if period == "weekly":
        return midnight - timedelta(days=dt.weekday())  # back to Monday
    if period == "monthly":
        return midnight.replace(day=1)
    raise ValueError(f"unknown period '{period}'")


def aggregate_series(samples: list[Sample], period: str) -> list[AggregateBucket]:
    """Group samples into period buckets with count/avg/min/max/sum, oldest first.

    ``None`` values are ignored for statistics but timestamps still define buckets.
    Each bucket's ``change_from_previous`` is the delta of averages vs the prior bucket.
    """
    if period not in PERIODS:
        raise ValueError(f"unknown period '{period}'")

    grouped: dict[datetime, list[float]] = {}
    for observed_at, value in samples:
        key = bucket_start(observed_at, period)
        grouped.setdefault(key, [])
        if value is not None:
            grouped[key].append(value)

    buckets: list[AggregateBucket] = []
    for start in sorted(grouped):
        values = grouped[start]
        if values:
            buckets.append(
                AggregateBucket(
                    period_start=start,
                    count=len(values),
                    average=round(sum(values) / len(values), 4),
                    minimum=min(values),
                    maximum=max(values),
                    total=round(sum(values), 4),
                )
            )
        else:
            buckets.append(
                AggregateBucket(
                    period_start=start,
                    count=0,
                    average=None,
                    minimum=None,
                    maximum=None,
                    total=0.0,
                )
            )

    _attach_period_over_period(buckets)
    return buckets


def _attach_period_over_period(buckets: list[AggregateBucket]) -> None:
    previous: float | None = None
    for bucket in buckets:
        if bucket.average is not None and previous is not None:
            bucket.change_from_previous = round(bucket.average - previous, 4)
        if bucket.average is not None:
            previous = bucket.average


def rolling_average(samples: list[Sample], window: int) -> list[Sample]:
    """Simple moving average over ``window`` consecutive samples (by time order).

    Returns ``(timestamp, average)`` pairs aligned to the end of each window. Samples
    with ``None`` values are dropped before the computation.
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    clean = [(ts, v) for ts, v in sorted(samples) if v is not None]
    result: list[Sample] = []
    for i in range(window - 1, len(clean)):
        window_vals = [v for _, v in clean[i - window + 1 : i + 1]]
        result.append((clean[i][0], round(sum(window_vals) / window, 4)))
    return result

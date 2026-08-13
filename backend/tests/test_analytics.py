"""Unit tests for the analytics engine (WBS 1.3.1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.analytics import (
    aggregate_series,
    bucket_start,
    rolling_average,
)


def _dt(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, tzinfo=UTC)


def test_bucket_start_periods() -> None:
    d = datetime(2026, 8, 5, 14, 30, tzinfo=UTC)  # Wednesday
    assert bucket_start(d, "daily") == datetime(2026, 8, 5, tzinfo=UTC)
    assert bucket_start(d, "weekly") == datetime(2026, 8, 3, tzinfo=UTC)  # Monday
    assert bucket_start(d, "monthly") == datetime(2026, 8, 1, tzinfo=UTC)


def test_aggregate_daily_stats() -> None:
    samples = [
        (_dt(5, 0), 10.0),
        (_dt(5, 12), 20.0),
        (_dt(6, 0), 30.0),
    ]
    buckets = aggregate_series(samples, "daily")
    assert len(buckets) == 2
    day1 = buckets[0]
    assert day1.count == 2
    assert day1.average == 15.0
    assert day1.minimum == 10.0
    assert day1.maximum == 20.0
    assert day1.total == 30.0


def test_aggregate_period_over_period_change() -> None:
    samples = [(_dt(5), 10.0), (_dt(6), 15.0), (_dt(7), 12.0)]
    buckets = aggregate_series(samples, "daily")
    assert buckets[0].change_from_previous is None
    assert buckets[1].change_from_previous == 5.0
    assert buckets[2].change_from_previous == -3.0


def test_aggregate_ignores_none_values() -> None:
    samples = [(_dt(5, 0), None), (_dt(5, 1), 8.0)]
    buckets = aggregate_series(samples, "daily")
    assert buckets[0].count == 1
    assert buckets[0].average == 8.0


def test_aggregate_rejects_bad_period() -> None:
    with pytest.raises(ValueError):
        aggregate_series([], "yearly")


def test_rolling_average_window() -> None:
    samples = [(_dt(1), 2.0), (_dt(2), 4.0), (_dt(3), 6.0), (_dt(4), 8.0)]
    points = rolling_average(samples, window=2)
    assert [v for _, v in points] == [3.0, 5.0, 7.0]
    assert points[0][0] == _dt(2)


def test_rolling_average_drops_none_and_validates_window() -> None:
    samples = [(_dt(1), 2.0), (_dt(2), None), (_dt(3), 6.0)]
    assert [v for _, v in rolling_average(samples, 2)] == [4.0]
    with pytest.raises(ValueError):
        rolling_average(samples, 0)

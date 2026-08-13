"""Weather analytics API: trends, aggregates & rolling averages (WBS 1.3.1)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import (
    AggregateBucketRead,
    RollingPoint,
    RollingResponse,
    TrendResponse,
)
from app.services import queries
from app.services.analytics import METRICS, PERIODS, aggregate_series, rolling_average

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _validate_metric(metric: str) -> None:
    if metric not in METRICS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown metric '{metric}'; choose from {sorted(METRICS)}",
        )


def _require_location(db: Session, location_id: int) -> None:
    if queries.get_location(db, location_id) is None:
        raise HTTPException(status_code=404, detail=f"location {location_id} not found")


@router.get("/locations/{location_id}/trends", response_model=TrendResponse)
def trends(
    location_id: int,
    metric: str = Query(default="temperature_c"),
    period: str = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> TrendResponse:
    _require_location(db, location_id)
    _validate_metric(metric)
    if period not in PERIODS:
        raise HTTPException(
            status_code=422, detail=f"unknown period; choose from {sorted(PERIODS)}"
        )
    samples = queries.metric_series(db, location_id, metric, start=start, end=end)
    buckets = aggregate_series(samples, period)
    return TrendResponse(
        location_id=location_id,
        metric=metric,
        period=period,
        buckets=[AggregateBucketRead(**b.__dict__) for b in buckets],
    )


@router.get("/locations/{location_id}/rolling", response_model=RollingResponse)
def rolling(
    location_id: int,
    metric: str = Query(default="temperature_c"),
    window: int = Query(default=3, ge=1, le=168),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RollingResponse:
    _require_location(db, location_id)
    _validate_metric(metric)
    samples = queries.metric_series(db, location_id, metric, start=start, end=end)
    points = rolling_average(samples, window)
    return RollingResponse(
        location_id=location_id,
        metric=metric,
        window=window,
        points=[RollingPoint(timestamp=ts, value=v) for ts, v in points],
    )

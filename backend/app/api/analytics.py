"""Weather analytics API: trends, aggregates & rolling averages (WBS 1.3.1)."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import (
    AggregateBucketRead,
    AlertRead,
    ForecastAccuracyResponse,
    RollingPoint,
    RollingResponse,
    TrendResponse,
)
from app.services import alerting, queries
from app.services.analytics import METRICS, PERIODS, aggregate_series, rolling_average
from app.services.forecast_accuracy import (
    COMPARABLE_METRICS,
    error_metrics,
    match_series,
)

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


@router.get(
    "/locations/{location_id}/forecast-accuracy",
    response_model=ForecastAccuracyResponse,
)
def forecast_accuracy(
    location_id: int,
    metric: str = Query(default="temperature_c"),
    horizon: str | None = Query(default=None, pattern="^(hourly|daily)$"),
    tolerance_minutes: int = Query(default=60, ge=1, le=1440),
    db: Session = Depends(get_db),
) -> ForecastAccuracyResponse:
    """Compare the latest stored forecast against observed readings (MAE/RMSE/bias)."""
    _require_location(db, location_id)
    if metric not in COMPARABLE_METRICS:
        raise HTTPException(
            status_code=422,
            detail=f"metric must be one of {sorted(COMPARABLE_METRICS)}",
        )
    forecast = queries.latest_forecast(db, location_id, horizon=horizon)
    if forecast is None:
        raise HTTPException(status_code=404, detail="no forecast stored for location")

    predicted = [(p.valid_at, getattr(p, metric)) for p in forecast.points]
    times = [t for t, _ in predicted]
    tolerance = timedelta(minutes=tolerance_minutes)
    if times:
        actual = queries.metric_series(
            db, location_id, metric, start=min(times) - tolerance,
            end=max(times) + tolerance,
        )
    else:
        actual = []
    pairs = match_series(predicted, actual, tolerance)
    metrics = error_metrics(metric, pairs)
    return ForecastAccuracyResponse(
        location_id=location_id,
        metric=metric,
        horizon=horizon,
        forecast_id=forecast.id,
        generated_at=forecast.generated_at,
        sample_count=metrics.sample_count,
        mae=metrics.mae,
        rmse=metrics.rmse,
        bias=metrics.bias,
    )


@router.get("/locations/{location_id}/alerts", response_model=list[AlertRead])
def list_alerts(
    location_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AlertRead]:
    _require_location(db, location_id)
    return [
        AlertRead.model_validate(a)
        for a in alerting.list_alerts(db, location_id, limit=limit)
    ]


@router.post("/locations/{location_id}/evaluate", response_model=list[AlertRead])
def evaluate(location_id: int, db: Session = Depends(get_db)) -> list[AlertRead]:
    """Run anomaly detection on the location's latest reading and persist new alerts."""
    _require_location(db, location_id)
    created = alerting.evaluate_location(db, location_id)
    return [AlertRead.model_validate(a) for a in created]

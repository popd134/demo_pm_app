"""Analytics API schemas (WBS 1.3.1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AggregateBucketRead(BaseModel):
    period_start: datetime
    count: int
    average: float | None
    minimum: float | None
    maximum: float | None
    total: float
    change_from_previous: float | None = None


class TrendResponse(BaseModel):
    location_id: int
    metric: str
    period: str
    buckets: list[AggregateBucketRead]


class RollingPoint(BaseModel):
    timestamp: datetime
    value: float


class RollingResponse(BaseModel):
    location_id: int
    metric: str
    window: int
    points: list[RollingPoint]


class ForecastAccuracyResponse(BaseModel):
    location_id: int
    metric: str
    horizon: str | None
    forecast_id: int
    generated_at: datetime
    sample_count: int
    mae: float | None
    rmse: float | None
    bias: float | None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    observation_id: int | None
    metric: str
    value: float
    threshold: float | None
    kind: str
    severity: str
    message: str
    created_at: datetime

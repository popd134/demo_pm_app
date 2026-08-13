"""Analytics API schemas (WBS 1.3.1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


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

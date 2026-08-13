"""Metrics & monitoring endpoints (WBS 1.7.4)."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.metrics import metrics

router = APIRouter(tags=["system"])


@router.get("/metrics", summary="Service metrics (JSON)")
def metrics_json() -> dict:
    return metrics.snapshot()


@router.get("/metrics/prometheus", summary="Service metrics (Prometheus text)")
def metrics_prometheus() -> Response:
    return Response(content=metrics.prometheus(), media_type="text/plain")

"""Tests for monitoring, logging & alerting (WBS 1.7.4)."""

from __future__ import annotations

import json
import logging

import pytest

from app.core.logging import JsonFormatter
from app.core.metrics import Metrics, metrics
from app.core.monitoring import notify_critical
from app.schemas.weather import GeoPoint
from app.services.ingestion import TrackedLocation, poll_once
from app.services.providers import ProviderError, register_provider
from app.services.providers.base import WeatherProvider

# --- metrics registry ----------------------------------------------------------

def test_metrics_counter_and_snapshot() -> None:
    m = Metrics()
    m.inc("requests_total", method="GET")
    m.inc("requests_total", method="GET")
    m.inc("requests_total", method="POST")
    snap = m.snapshot()
    series = {
        tuple(sorted(e["labels"].items())): e["value"]
        for e in snap["counters"]["requests_total"]
    }
    assert series[(("method", "GET"),)] == 2
    assert series[(("method", "POST"),)] == 1


def test_metrics_prometheus_format() -> None:
    m = Metrics()
    m.inc("http_requests_total", method="GET", status="200")
    m.set_gauge("up", 1)
    text = m.prometheus()
    assert "# TYPE http_requests_total counter" in text
    assert 'http_requests_total{method="GET",status="200"} 1.0' in text
    assert "up 1" in text


def test_metrics_reset() -> None:
    m = Metrics()
    m.inc("x")
    m.reset()
    assert m.snapshot() == {"counters": {}, "gauges": {}}


# --- logging -------------------------------------------------------------------

def test_json_formatter_emits_valid_json() -> None:
    record = logging.LogRecord(
        name="app.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello %s", args=("world",), exc_info=None,
    )
    record.context = {"user": "abc"}
    parsed = json.loads(JsonFormatter().format(record))
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["user"] == "abc"


# --- monitoring / endpoints ----------------------------------------------------

def test_notify_critical_never_raises() -> None:
    # No webhook configured: should only log, not raise.
    notify_critical("test_event", detail="x")


def test_metrics_endpoint_reports_requests(client) -> None:
    client.get("/api/health")
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.json()["counters"]


def test_prometheus_endpoint(client) -> None:
    client.get("/api/health")
    resp = client.get("/api/metrics/prometheus")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in resp.text


# --- ingestion failure alerting ------------------------------------------------

class _FailingProvider(WeatherProvider):
    name = "failing"

    async def get_current(self, location: GeoPoint) -> object:
        raise ProviderError("down")

    async def get_hourly(self, location, hours=24):  # noqa: ANN001, ARG002
        raise NotImplementedError

    async def get_forecast(self, location, days=7):  # noqa: ANN001, ARG002
        raise NotImplementedError


@pytest.mark.asyncio
async def test_ingestion_failure_increments_metric() -> None:
    register_provider("failing", lambda _settings: _FailingProvider())
    metrics.reset()

    from app.services.ingestion import InMemoryObservationSink

    stored = await poll_once(
        [TrackedLocation(name="Nowhere", latitude=0.0, longitude=0.0)],
        InMemoryObservationSink(),
        provider_name="failing",
    )
    assert stored == 0
    snap = metrics.snapshot()
    assert "ingestion_failures_total" in snap["counters"]

"""Tests for the health and root endpoints (foundation smoke tests)."""

from __future__ import annotations


def test_health_ok(client) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app_name"]
    assert body["version"]


def test_root_points_to_docs(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["health"] == "/api/health"


def test_openapi_schema_available(client) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"]

"""Tests for the published OpenAPI contract (WBS 1.2.4)."""

from __future__ import annotations

import json

from scripts.export_openapi import build_spec


def test_openapi_has_metadata_and_tags(client) -> None:
    spec = client.get("/openapi.json").json()
    info = spec["info"]
    assert info["title"]
    assert "Authentication" in info["description"]
    assert info["contact"]["name"]
    assert info["license"]["name"] == "MIT"

    tag_names = {t["name"] for t in spec.get("tags", [])}
    assert {"auth", "weather", "providers", "ingestion", "system"} <= tag_names


def test_openapi_documents_key_paths(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/auth/login" in paths
    assert "/api/weather/locations/{location_id}/observations" in paths
    assert "/api/weather/locations/{location_id}/forecast" in paths


def test_schema_examples_present(client) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert schemas["LocationCreate"]["example"]["name"] == "London"
    assert "condition" in schemas["ObservationRead"]["example"]


def test_swagger_and_redoc_served(client) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_export_script_builds_valid_spec(tmp_path) -> None:
    spec = build_spec()
    assert spec["openapi"].startswith("3.")
    # Round-trips through JSON (i.e. it is serialisable).
    out = tmp_path / "openapi.json"
    out.write_text(json.dumps(spec))
    assert json.loads(out.read_text())["info"]["title"]

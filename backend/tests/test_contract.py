"""Contract tests for API responses and providers (WBS 1.7.1)."""

from __future__ import annotations

import inspect

from app.services.providers import available_providers, get_provider
from app.services.providers.base import WeatherProvider

# --- error contract: handled failures return {"detail": ...} -------------------

def test_not_found_returns_detail(client) -> None:
    body = client.get("/api/weather/locations/999999").json()
    assert isinstance(body.get("detail"), str)


def test_unauthorized_returns_detail(client) -> None:
    body = client.get("/api/preferences").json()
    assert isinstance(body.get("detail"), str)


def test_validation_error_returns_detail(client) -> None:
    # limit above the allowed maximum triggers a 422 with a detail payload.
    resp = client.get(
        "/api/weather/locations/1/observations", params={"limit": 100000}
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


# --- provider contract ---------------------------------------------------------

def test_all_registered_providers_satisfy_interface() -> None:
    names = available_providers()
    assert {"open-meteo", "openweathermap"} <= set(names)
    for name in names:
        provider = get_provider(name)
        assert isinstance(provider, WeatherProvider)
        assert provider.name
        for method in ("get_current", "get_hourly", "get_forecast"):
            fn = getattr(provider, method)
            assert callable(fn)
            assert inspect.iscoroutinefunction(fn)


# --- OpenAPI response contract -------------------------------------------------

def test_successful_json_responses_reference_a_schema(client) -> None:
    spec = client.get("/openapi.json").json()
    missing: list[str] = []
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            responses = op.get("responses", {})
            for code, resp in responses.items():
                if not code.startswith("2") or code == "204":
                    continue
                content = resp.get("content", {})
                json_body = content.get("application/json")
                if json_body is not None and "schema" not in json_body:
                    missing.append(f"{method.upper()} {path} -> {code}")
    assert missing == [], f"responses without a schema: {missing}"

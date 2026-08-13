"""Tests for user preferences & saved locations (WBS 1.6.1)."""

from __future__ import annotations

from app.core.database import SessionLocal
from app.services.storage import get_or_create_location


def _seed_location(name: str, lat: float, lon: float) -> int:
    db = SessionLocal()
    try:
        loc = get_or_create_location(db, name, lat, lon)
        db.commit()
        return loc.id
    finally:
        db.close()


# --- preferences ---------------------------------------------------------------

def test_preferences_require_auth(client) -> None:
    assert client.get("/api/preferences").status_code == 401
    assert client.put("/api/preferences", json={}).status_code == 401


def test_preferences_defaults_then_update(client, user_auth) -> None:
    resp = client.get("/api/preferences", headers=user_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["temperature_unit"] == "c"
    assert body["wind_unit"] == "ms"
    assert body["alert_thresholds"] == {}

    updated = client.put(
        "/api/preferences",
        headers=user_auth,
        json={
            "temperature_unit": "f",
            "alert_thresholds": {"temperature_c": {"max": 40}},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["temperature_unit"] == "f"
    assert updated.json()["alert_thresholds"] == {"temperature_c": {"max": 40.0}}

    # Persisted across requests.
    again = client.get("/api/preferences", headers=user_auth)
    assert again.json()["temperature_unit"] == "f"


def test_preferences_validation(client, user_auth) -> None:
    resp = client.put(
        "/api/preferences", headers=user_auth, json={"temperature_unit": "kelvin"}
    )
    assert resp.status_code == 422


# --- saved locations -----------------------------------------------------------

def test_saved_location_crud(client, user_auth) -> None:
    loc_id = _seed_location("Saved City", 33.3, 44.4)

    empty = client.get("/api/preferences/locations", headers=user_auth)
    assert empty.status_code == 200
    assert empty.json() == []

    add = client.post(
        "/api/preferences/locations", headers=user_auth, json={"location_id": loc_id}
    )
    assert add.status_code == 201
    assert add.json()["location"]["name"] == "Saved City"

    # Idempotent add (same location) returns the existing entry, not a duplicate.
    client.post(
        "/api/preferences/locations", headers=user_auth, json={"location_id": loc_id}
    )
    listing = client.get("/api/preferences/locations", headers=user_auth)
    assert len(listing.json()) == 1

    removed = client.delete(f"/api/preferences/locations/{loc_id}", headers=user_auth)
    assert removed.status_code == 204
    assert client.get("/api/preferences/locations", headers=user_auth).json() == []


def test_saved_location_add_unknown_404(client, user_auth) -> None:
    resp = client.post(
        "/api/preferences/locations", headers=user_auth, json={"location_id": 999999}
    )
    assert resp.status_code == 404


def test_saved_location_remove_unknown_404(client, user_auth) -> None:
    resp = client.delete("/api/preferences/locations/999999", headers=user_auth)
    assert resp.status_code == 404


def test_saved_locations_are_per_user(client) -> None:
    from app.models.user import UserRole
    from tests.conftest import _auth_header

    loc_id = _seed_location("Private City", 55.5, 66.6)
    user_a = _auth_header(UserRole.USER)
    user_b = _auth_header(UserRole.USER)

    client.post("/api/preferences/locations", headers=user_a, json={"location_id": loc_id})
    assert len(client.get("/api/preferences/locations", headers=user_a).json()) == 1
    # User B does not see user A's saved locations.
    assert client.get("/api/preferences/locations", headers=user_b).json() == []

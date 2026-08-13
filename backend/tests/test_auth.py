"""Tests for authentication & authorization (WBS 1.2.3)."""

from __future__ import annotations

import uuid

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@test.io"


# --- unit: security primitives --------------------------------------------------

def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip_and_invalid() -> None:
    token = create_access_token(subject="42")
    assert decode_access_token(token) == "42"
    assert decode_access_token("not-a-token") is None


def test_expired_token_rejected() -> None:
    token = create_access_token(subject="1", expires_minutes=-1)
    assert decode_access_token(token) is None


# --- API: register / login / me -------------------------------------------------

def test_register_and_login_flow(client) -> None:
    email = _email()
    reg = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert reg.status_code == 201
    assert reg.json()["role"] == "user"

    login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_duplicate_registration_conflicts(client) -> None:
    email = _email()
    body = {"email": email, "password": "password123"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


def test_login_wrong_password_401(client) -> None:
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": email, "password": "nope"})
    assert resp.status_code == 401


def test_me_requires_token(client) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_weak_password_rejected(client) -> None:
    resp = client.post("/api/auth/register", json={"email": _email(), "password": "short"})
    assert resp.status_code == 422


# --- authorization on protected endpoints --------------------------------------

def test_create_location_requires_auth(client) -> None:
    resp = client.post(
        "/api/weather/locations",
        json={"name": "NoAuth", "latitude": 1.0, "longitude": 2.0},
    )
    assert resp.status_code == 401


def test_create_location_forbidden_for_non_admin(client, user_auth) -> None:
    resp = client.post(
        "/api/weather/locations",
        json={"name": "UserCity", "latitude": 3.0, "longitude": 4.0},
        headers=user_auth,
    )
    assert resp.status_code == 403


def test_create_location_allowed_for_admin(client, admin_auth) -> None:
    resp = client.post(
        "/api/weather/locations",
        json={"name": "AdminCity", "latitude": 5.0, "longitude": 6.0},
        headers=admin_auth,
    )
    assert resp.status_code == 201

"""Shared pytest fixtures.

The database is an in-memory SQLite instance so tests are fast and isolated and need
no external services.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def _setup_schema() -> None:
    """Create the schema once for the test session."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _reset_provider_resilience():
    """Clear provider cache/limiters and disable real sleeps between tests (WBS 1.1.4)."""
    from app.services.providers import resilience

    async def _no_sleep(_seconds: float) -> None:
        return None

    resilience.reset()
    resilience.set_sleep(_no_sleep)
    yield
    resilience.reset_sleep()
    resilience.reset()


@pytest.fixture()
def client() -> TestClient:
    """A FastAPI TestClient bound to a freshly built app."""
    with TestClient(create_app()) as test_client:
        yield test_client


def _auth_header(role) -> dict[str, str]:
    """Create a fresh user with the given role and return a bearer auth header.

    Emails are unique per call because the in-memory DB is shared for the session.
    """
    import uuid

    from app.core.database import SessionLocal
    from app.core.security import create_access_token
    from app.services.auth import create_user

    db = SessionLocal()
    try:
        user = create_user(
            db, f"{role.value}-{uuid.uuid4().hex[:8]}@test.io", "password123", role=role
        )
        return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
    finally:
        db.close()


@pytest.fixture()
def admin_auth() -> dict[str, str]:
    from app.models.user import UserRole

    return _auth_header(UserRole.ADMIN)


@pytest.fixture()
def user_auth() -> dict[str, str]:
    from app.models.user import UserRole

    return _auth_header(UserRole.USER)

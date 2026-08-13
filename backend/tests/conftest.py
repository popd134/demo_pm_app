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

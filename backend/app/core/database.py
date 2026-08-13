"""Database engine, session factory and declarative base."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")
_is_memory = _is_sqlite and (
    ":memory:" in settings.database_url or settings.database_url == "sqlite://"
)

# SQLite needs check_same_thread disabled for use across FastAPI's threadpool.
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# An in-memory SQLite database is per-connection; a StaticPool shares a single
# connection so schema and data are visible across sessions and threads.
_engine_kwargs: dict = {"poolclass": StaticPool} if _is_memory else {"pool_pre_ping": True}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
    **_engine_kwargs,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Superseded by migrations in a later WBS task (1.7)."""
    # Import models so they are registered on the metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

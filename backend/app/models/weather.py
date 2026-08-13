"""Canonical time-series weather ORM models (WBS 1.1.3).

These are the *storage* models the ingestion pipeline persists into. The broader
schema (users, forecasts, richer metadata and indexing/partitioning choices) is refined
under WBS 1.2.1; this task defines the canonical observation record and the location it
belongs to, with a uniqueness constraint that deduplicates repeated readings.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class Location(Base):
    """A geographic location that observations are recorded for."""

    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("latitude", "longitude", name="uq_location_lat_lon"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    observations: Mapped[list[Observation]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class Observation(Base):
    """A single canonical weather reading in the time series.

    Units are canonical: temperature °C, wind m/s, precipitation mm, pressure hPa.
    The (location, provider, observed_at) uniqueness constraint deduplicates readings.
    """

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "location_id", "provider", "observed_at", name="uq_observation_dedup"
        ),
        Index("ix_observation_location_time", "location_id", "observed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(60))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float)
    wind_direction_deg: Mapped[float | None] = mapped_column(Float)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    pressure_hpa: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str | None] = mapped_column(String(120))

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    location: Mapped[Location] = relationship(back_populates="observations")

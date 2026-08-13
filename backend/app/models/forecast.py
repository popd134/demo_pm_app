"""Forecast storage models (WBS 1.2.1).

A ``Forecast`` is one provider's forecast run for a location at a point in time; its
``ForecastPoint`` rows are the individual predicted steps. Persisting forecasts enables
the forecast-vs-actual accuracy analytics in WBS 1.3.3.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class Forecast(Base):
    """A single forecast run for a location from one provider."""

    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecast_location_generated", "location_id", "generated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    provider: Mapped[str] = mapped_column(String(60))
    # "hourly" or "daily".
    horizon: Mapped[str] = mapped_column(String(16), default="daily")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    location = relationship("Location", back_populates="forecasts")
    points: Mapped[list[ForecastPoint]] = relationship(
        back_populates="forecast",
        cascade="all, delete-orphan",
        order_by="ForecastPoint.valid_at",
    )


class ForecastPoint(Base):
    """A single predicted time step within a forecast run."""

    __tablename__ = "forecast_points"
    __table_args__ = (
        UniqueConstraint("forecast_id", "valid_at", name="uq_forecast_point"),
        Index("ix_forecast_point_forecast_valid", "forecast_id", "valid_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("forecasts.id", ondelete="CASCADE")
    )
    valid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    temperature_c: Mapped[float | None] = mapped_column(Float)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    wind_speed_ms: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str | None] = mapped_column(String(120))

    forecast: Mapped[Forecast] = relationship(back_populates="points")

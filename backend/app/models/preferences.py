"""Per-user preferences & saved locations (WBS 1.6.1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class UserPreferences(Base):
    """A user's unit choices and alert thresholds (one row per user)."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    temperature_unit: Mapped[str] = mapped_column(String(1), default="c")  # "c" | "f"
    wind_unit: Mapped[str] = mapped_column(String(4), default="ms")  # ms | kmh | mph
    # {"temperature_c": {"max": 40}, ...} — overrides for anomaly detection.
    alert_thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class SavedLocation(Base):
    """A location a user has saved to their dashboard."""

    __tablename__ = "saved_locations"
    __table_args__ = (
        UniqueConstraint("user_id", "location_id", name="uq_saved_location"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

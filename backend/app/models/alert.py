"""Alert event model (WBS 1.3.2).

Persisted when a reading breaches a configured threshold or is a statistical spike, so
the dashboard and notifications (WBS 1.5.4 / 1.7.4) can surface them.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class Alert(Base):
    """A generated alert event for a location."""

    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alert_location_created", "location_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("observations.id", ondelete="SET NULL")
    )
    metric: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float | None] = mapped_column(Float)
    # "threshold_high", "threshold_low" or "spike".
    kind: Mapped[str] = mapped_column(String(20))
    # "info", "warning" or "critical".
    severity: Mapped[str] = mapped_column(String(12), default="warning")
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

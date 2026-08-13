"""User model & roles (WBS 1.2.1).

Defined as part of the schema design so authentication (WBS 1.2.3) and per-user saved
locations / preferences (WBS 1.6.1) have a table to build on.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Coarse authorization roles."""

    USER = "user"
    ADMIN = "admin"


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class User(Base):
    """An application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=16), default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

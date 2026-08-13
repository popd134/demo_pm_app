"""Password hashing and JWT helpers (WBS 1.2.3).

Uses bcrypt directly for password hashing and PyJWT for signing short-lived access
tokens. No third-party auth framework — small, explicit and easy to audit.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token for the given subject (user id)."""
    settings = get_settings()
    expire = datetime.now(tz=UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(tz=UTC)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Return the subject (user id) from a valid token, or None if invalid/expired."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    return str(subject) if subject is not None else None

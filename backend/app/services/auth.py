"""User creation & authentication service (WBS 1.2.3)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


class EmailAlreadyRegistered(ValueError):
    """Raised when registering an email that already exists."""


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def create_user(
    db: Session, email: str, password: str, role: UserRole = UserRole.USER
) -> User:
    if get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegistered(email)
    user = User(email=email, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user when credentials are valid and the account is active."""
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

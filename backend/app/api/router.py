"""Aggregate API router.

Feature routers (weather queries, auth, analytics, preferences) are mounted here as
the corresponding WBS tasks land, keeping ``main.py`` stable.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import health

api_router = APIRouter()
api_router.include_router(health.router)

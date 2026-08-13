"""Aggregate API router.

Feature routers (weather queries, auth, analytics, preferences) are mounted here as
the corresponding WBS tasks land, keeping ``main.py`` stable.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api import analytics, auth, health, ingestion, providers, weather

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(providers.router)
api_router.include_router(ingestion.router)
api_router.include_router(weather.router)
api_router.include_router(analytics.router)

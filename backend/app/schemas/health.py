"""Schemas for the health/metadata endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Reported by the health check endpoint."""

    status: str
    app_name: str
    environment: str
    version: str

"""FastAPI application factory and wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.services.ingestion_runtime import runtime as ingestion_runtime


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Start-up / shut-down wiring.

    Creates database tables (migrations arrive in WBS 1.7) and starts the scheduled
    ingestion loop when it is enabled (WBS 1.1.2).
    """
    init_db()
    ingestion_runtime.start()
    try:
        yield
    finally:
        await ingestion_runtime.stop()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Backend API for the Weather Tracking & Analysis Dashboard. "
            "Ingests, stores and analyses weather time-series data."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()

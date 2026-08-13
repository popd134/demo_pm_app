"""FastAPI application factory and wiring."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.metrics import metrics
from app.core.monitoring import notify_critical
from app.core.openapi import (
    API_DESCRIPTION,
    CONTACT,
    LICENSE_INFO,
    TAGS_METADATA,
)
from app.services.ingestion_runtime import runtime as ingestion_runtime

access_logger = logging.getLogger("app.access")


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
    setup_logging(level=settings.log_level, json_format=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=API_DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        contact=CONTACT,
        license_info=LICENSE_INFO,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def observe_requests(request: Request, call_next):
        """Record request metrics, latency and errors (WBS 1.7.4)."""
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            metrics.inc("api_errors_total", method=request.method, status="500")
            notify_critical(
                "unhandled_exception",
                path=request.url.path,
                method=request.method,
            )
            raise
        duration = time.perf_counter() - start
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        metrics.inc(
            "http_requests_total",
            method=request.method,
            status=str(response.status_code),
        )
        metrics.inc("http_request_duration_seconds_sum", amount=duration)
        metrics.inc("http_request_duration_seconds_count")
        if response.status_code >= 500:
            metrics.inc("api_errors_total", method=request.method,
                        status=str(response.status_code))
            notify_critical("server_error", path=path, status=response.status_code)
        access_logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            path,
            response.status_code,
            duration * 1000,
        )
        return response

    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()

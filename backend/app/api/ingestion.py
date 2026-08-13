"""Ingestion control & status endpoints (WBS 1.1.2)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.ingestion import InMemoryObservationSink
from app.services.ingestion_runtime import runtime

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionStatus(BaseModel):
    enabled: bool
    running: bool
    interval_seconds: float
    tracked_locations: int
    cycles_completed: int
    buffered_observations: int | None = None


class RunResult(BaseModel):
    stored: int


@router.get("/status", response_model=IngestionStatus)
def status() -> IngestionStatus:
    settings = get_settings()
    scheduler = runtime.scheduler
    buffered = (
        len(runtime.sink) if isinstance(runtime.sink, InMemoryObservationSink) else None
    )
    return IngestionStatus(
        enabled=settings.ingestion_enabled,
        running=bool(scheduler and scheduler.running),
        interval_seconds=settings.ingestion_interval_seconds,
        tracked_locations=len(settings.ingestion_locations),
        cycles_completed=scheduler.cycles if scheduler else 0,
        buffered_observations=buffered,
    )


@router.post("/run", response_model=RunResult, summary="Trigger one ingestion cycle")
async def run_once() -> RunResult:
    stored = await runtime.run_once()
    return RunResult(stored=stored)

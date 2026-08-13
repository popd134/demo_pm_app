"""Scheduled ingestion & polling jobs (WBS 1.1.2).

Polls the configured weather provider for each tracked location on a fixed interval
and hands the resulting observations to an :class:`ObservationSink`. This task owns
*scheduling and enqueueing*; canonical normalisation and durable persistence are added
by WBS 1.1.3 (which supplies a database-backed sink), and retries / rate limiting /
caching by WBS 1.1.4.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Sequence
from typing import Protocol

from pydantic import BaseModel, Field

from app.core.metrics import metrics
from app.core.monitoring import notify_critical
from app.schemas.weather import CurrentConditions, GeoPoint
from app.services.providers import ProviderError, get_provider

logger = logging.getLogger("app.ingestion")


class TrackedLocation(BaseModel):
    """A location the ingestion loop polls."""

    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @property
    def point(self) -> GeoPoint:
        return GeoPoint(latitude=self.latitude, longitude=self.longitude)


class ObservationSink(Protocol):
    """Destination for polled observations.

    WBS 1.1.3 provides a database-backed implementation; the default in-memory sink
    below keeps this task self-contained and testable.
    """

    async def store(self, location: TrackedLocation, conditions: CurrentConditions) -> None:
        ...


class InMemoryObservationSink:
    """A simple sink that buffers observations in memory (dev/testing default)."""

    def __init__(self) -> None:
        self.records: list[tuple[TrackedLocation, CurrentConditions]] = []

    async def store(self, location: TrackedLocation, conditions: CurrentConditions) -> None:
        self.records.append((location, conditions))

    def __len__(self) -> int:
        return len(self.records)


async def poll_once(
    locations: Iterable[TrackedLocation],
    sink: ObservationSink,
    provider_name: str | None = None,
) -> int:
    """Poll every location once and store the results. Returns the count stored.

    Failures for a single location are logged and skipped so one bad source does not
    abort the whole cycle.
    """
    provider = get_provider(provider_name)
    stored = 0
    for location in locations:
        try:
            conditions = await provider.get_current(location.point)
        except ProviderError:
            logger.warning("ingestion: failed to poll %s", location.name, exc_info=True)
            metrics.inc("ingestion_failures_total", location=location.name)
            notify_critical("ingestion_failure", location=location.name)
            continue
        await sink.store(location, conditions)
        stored += 1
    return stored


class IngestionScheduler:
    """Runs :func:`poll_once` on a fixed interval in a background asyncio task."""

    def __init__(
        self,
        locations: Sequence[TrackedLocation],
        sink: ObservationSink,
        interval_seconds: float,
        provider_name: str | None = None,
    ) -> None:
        self._locations = list(locations)
        self._sink = sink
        self._interval = max(1.0, interval_seconds)
        self._provider_name = provider_name
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self.cycles = 0

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run(self) -> None:
        while not self._stop.is_set():
            try:
                await poll_once(self._locations, self._sink, self._provider_name)
                self.cycles += 1
            except Exception:  # never let the loop die on an unexpected error
                logger.exception("ingestion: poll cycle failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except TimeoutError:
                continue

    def start(self) -> None:
        if self.running or not self._locations:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
            self._task = None

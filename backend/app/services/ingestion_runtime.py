"""Process-wide ingestion runtime wiring (WBS 1.1.2).

Holds the active sink and scheduler for the running app so the API and the app
lifespan share one instance. WBS 1.1.3 swaps the in-memory sink for a database-backed
one here without touching the scheduler or API.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.services.ingestion import (
    IngestionScheduler,
    InMemoryObservationSink,
    ObservationSink,
    TrackedLocation,
    poll_once,
)


class IngestionRuntime:
    """Owns the sink and (optional) scheduler for the running application."""

    def __init__(self, sink: ObservationSink | None = None) -> None:
        self.sink: ObservationSink = sink or InMemoryObservationSink()
        self.scheduler: IngestionScheduler | None = None

    def configure_sink(self, settings: Settings | None = None) -> None:
        """Select the persistence sink from settings (WBS 1.1.3).

        When ``ingestion_persist`` is enabled, swap the in-memory sink for the
        database-backed one so polled observations are stored durably.
        """
        settings = settings or get_settings()
        if settings.ingestion_persist:
            from app.services.storage import DatabaseObservationSink

            self.sink = DatabaseObservationSink()

    def configure(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        locations = [TrackedLocation(**loc) for loc in settings.ingestion_locations]
        self.scheduler = IngestionScheduler(
            locations=locations,
            sink=self.sink,
            interval_seconds=settings.ingestion_interval_seconds,
            provider_name=settings.default_weather_provider,
        )

    def start(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self.configure_sink(settings)
        if self.scheduler is None:
            self.configure(settings)
        if settings.ingestion_enabled:
            assert self.scheduler is not None
            self.scheduler.start()

    async def stop(self) -> None:
        if self.scheduler is not None:
            await self.scheduler.stop()

    async def run_once(self, settings: Settings | None = None) -> int:
        """Trigger a single poll cycle on demand (used by the API and tests)."""
        settings = settings or get_settings()
        locations = [TrackedLocation(**loc) for loc in settings.ingestion_locations]
        return await poll_once(locations, self.sink, settings.default_weather_provider)


# Module-level singleton shared by the app and its routers.
runtime = IngestionRuntime()

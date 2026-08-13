"""Application configuration, loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the backend service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Weather Tracking & Analysis Dashboard"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./weather.db"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # External weather providers (WBS 1.1.1).
    default_weather_provider: str = "open-meteo"
    openweather_api_key: str | None = None

    # Scheduled ingestion (WBS 1.1.2).
    ingestion_enabled: bool = False
    ingestion_interval_seconds: float = 900.0
    # JSON list of {"name","latitude","longitude"} objects, e.g.
    # '[{"name":"London","latitude":51.5074,"longitude":-0.1278}]'
    ingestion_locations: list[dict] = []

    @field_validator("ingestion_locations", mode="before")
    @classmethod
    def _parse_locations(cls, value: object) -> object:
        """Allow the tracked-location list to be supplied as a JSON string."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            import json

            return json.loads(value)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow CORS origins to be supplied as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

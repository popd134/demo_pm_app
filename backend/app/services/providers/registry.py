"""Provider registry: resolve a provider by name from configuration (WBS 1.1.1)."""

from __future__ import annotations

from collections.abc import Callable

from app.core.config import Settings, get_settings
from app.services.providers.base import ProviderError, WeatherProvider
from app.services.providers.open_meteo import OpenMeteoProvider
from app.services.providers.openweather import OpenWeatherProvider

# Factories build a provider from Settings, mapping credentials/config to the client.
ProviderFactory = Callable[[Settings], WeatherProvider]

_REGISTRY: dict[str, ProviderFactory] = {
    OpenMeteoProvider.name: lambda _settings: OpenMeteoProvider(),
    OpenWeatherProvider.name: lambda settings: OpenWeatherProvider(
        api_key=settings.openweather_api_key
    ),
}


def register_provider(name: str, factory: ProviderFactory) -> None:
    """Register (or override) a provider factory. Useful for tests and extensions."""
    _REGISTRY[name] = factory


def available_providers() -> list[str]:
    """Return the names of all registered providers."""
    return sorted(_REGISTRY)


def get_provider(name: str | None = None, settings: Settings | None = None) -> WeatherProvider:
    """Return a configured provider instance by name (default from settings)."""
    settings = settings or get_settings()
    resolved = name or settings.default_weather_provider
    factory = _REGISTRY.get(resolved)
    if factory is None:
        raise ProviderError(
            f"unknown weather provider '{resolved}'; "
            f"available: {', '.join(available_providers())}"
        )
    return factory(settings)

"""External weather data provider clients (WBS 1.1.1).

Each provider implements :class:`WeatherProvider` and knows how to call its source's
current / hourly / forecast endpoints and parse the response into the provider-neutral
schemas in :mod:`app.schemas.weather`.
"""

from app.services.providers.base import (
    ProviderConfigError,
    ProviderError,
    WeatherProvider,
)
from app.services.providers.registry import (
    available_providers,
    get_provider,
    register_provider,
)

__all__ = [
    "WeatherProvider",
    "ProviderError",
    "ProviderConfigError",
    "get_provider",
    "available_providers",
    "register_provider",
]

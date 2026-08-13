"""OpenWeatherMap provider client (WBS 1.1.1).

Requires an API key (``OPENWEATHER_API_KEY``). Demonstrates credential mapping for a
keyed source alongside the keyless Open-Meteo provider.
Docs: https://openweathermap.org/current
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.weather import (
    CurrentConditions,
    Forecast,
    ForecastEntry,
    GeoPoint,
    WeatherObservation,
)
from app.services.providers.base import (
    ProviderConfigError,
    ProviderError,
    WeatherProvider,
)


class OpenWeatherProvider(WeatherProvider):
    """Client for the OpenWeatherMap 2.5 API."""

    name = "openweathermap"
    base_url = "https://api.openweathermap.org"

    def __init__(self, api_key: str | None = None, client=None) -> None:
        super().__init__(client=client)
        self._api_key = api_key

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderConfigError(
                "openweathermap requires OPENWEATHER_API_KEY to be configured"
            )
        return self._api_key

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        data = await self._request(
            "/data/2.5/weather",
            {
                "lat": location.latitude,
                "lon": location.longitude,
                "units": "metric",
                "appid": self._require_key(),
            },
        )
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = (data.get("weather") or [{}])[0]
        observation = WeatherObservation(
            provider=self.name,
            observed_at=_from_unix(data.get("dt")),
            temperature_c=main.get("temp"),
            humidity_pct=main.get("humidity"),
            wind_speed_ms=wind.get("speed"),
            wind_direction_deg=wind.get("deg"),
            precipitation_mm=(data.get("rain", {}) or {}).get("1h"),
            pressure_hpa=main.get("pressure"),
            condition=weather.get("description"),
        )
        return CurrentConditions(location=location, observation=observation)

    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:
        # The free 5-day/3-hour forecast endpoint; cap to the requested window.
        steps = max(1, hours // 3)
        return await self._forecast(location, limit=steps)

    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:
        steps = max(1, min(days, 5)) * 8  # 8 three-hour steps per day, 5-day max
        return await self._forecast(location, limit=steps)

    async def _forecast(self, location: GeoPoint, limit: int) -> Forecast:
        data = await self._request(
            "/data/2.5/forecast",
            {
                "lat": location.latitude,
                "lon": location.longitude,
                "units": "metric",
                "appid": self._require_key(),
            },
        )
        rows = data.get("list")
        if rows is None:
            raise ProviderError("openweathermap forecast response missing 'list'")

        entries: list[ForecastEntry] = []
        for row in rows[:limit]:
            main = row.get("main", {})
            wind = row.get("wind", {})
            weather = (row.get("weather") or [{}])[0]
            entries.append(
                ForecastEntry(
                    valid_at=_from_unix(row.get("dt")),
                    temperature_c=main.get("temp"),
                    precipitation_mm=(row.get("rain", {}) or {}).get("3h"),
                    wind_speed_ms=wind.get("speed"),
                    condition=weather.get("description"),
                )
            )
        return Forecast(
            provider=self.name,
            location=location,
            generated_at=datetime.now(tz=UTC),
            entries=entries,
        )


def _from_unix(value: object) -> datetime:
    if value is None:
        raise ProviderError("openweathermap response missing 'dt' timestamp")
    return datetime.fromtimestamp(int(value), tz=UTC)

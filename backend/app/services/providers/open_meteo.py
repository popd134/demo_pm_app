"""Open-Meteo provider client (WBS 1.1.1).

Open-Meteo is a keyless, free weather API — a good default source for the sample.
Docs: https://open-meteo.com/en/docs
"""

from __future__ import annotations

from datetime import datetime

from app.schemas.weather import (
    CurrentConditions,
    Forecast,
    ForecastEntry,
    GeoPoint,
    WeatherObservation,
)
from app.services.providers.base import ProviderError, WeatherProvider

# WMO weather interpretation codes -> human-readable condition.
# https://open-meteo.com/en/docs (Weather variable documentation)
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def condition_from_code(code: object) -> str | None:
    """Translate a WMO weather code into a readable condition string."""
    try:
        return WMO_CODES.get(int(code))
    except (TypeError, ValueError):
        return None


class OpenMeteoProvider(WeatherProvider):
    """Client for the Open-Meteo forecast API."""

    name = "open-meteo"
    base_url = "https://api.open-meteo.com"

    async def get_current(self, location: GeoPoint) -> CurrentConditions:
        data = await self._request(
            "/v1/forecast",
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,wind_speed_10m,"
                    "wind_direction_10m,precipitation,surface_pressure,weather_code"
                ),
                "wind_speed_unit": "ms",
            },
        )
        current = data.get("current")
        if not current:
            raise ProviderError("open-meteo response missing 'current' block")

        observation = WeatherObservation(
            provider=self.name,
            observed_at=_parse_time(current.get("time")),
            temperature_c=current.get("temperature_2m"),
            humidity_pct=current.get("relative_humidity_2m"),
            wind_speed_ms=current.get("wind_speed_10m"),
            wind_direction_deg=current.get("wind_direction_10m"),
            precipitation_mm=current.get("precipitation"),
            pressure_hpa=current.get("surface_pressure"),
            condition=condition_from_code(current.get("weather_code")),
        )
        return CurrentConditions(location=location, observation=observation)

    async def get_hourly(self, location: GeoPoint, hours: int = 24) -> Forecast:
        data = await self._request(
            "/v1/forecast",
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "hourly": "temperature_2m,precipitation,wind_speed_10m,weather_code",
                "wind_speed_unit": "ms",
                "forecast_hours": hours,
            },
        )
        return self._parse_series(location, data.get("hourly", {}), limit=hours)

    async def get_forecast(self, location: GeoPoint, days: int = 7) -> Forecast:
        data = await self._request(
            "/v1/forecast",
            {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "daily": (
                    "temperature_2m_max,precipitation_sum,"
                    "wind_speed_10m_max,weather_code"
                ),
                "wind_speed_unit": "ms",
                "forecast_days": days,
            },
        )
        daily = data.get("daily", {})
        # Daily arrays use *_max/_sum keys; remap to the common series field names.
        series = {
            "time": daily.get("time", []),
            "temperature_2m": daily.get("temperature_2m_max", []),
            "precipitation": daily.get("precipitation_sum", []),
            "wind_speed_10m": daily.get("wind_speed_10m_max", []),
            "weather_code": daily.get("weather_code", []),
        }
        return self._parse_series(location, series, limit=days)

    def _parse_series(
        self, location: GeoPoint, series: dict, limit: int
    ) -> Forecast:
        times = series.get("time", []) or []
        temps = series.get("temperature_2m", []) or []
        precip = series.get("precipitation", []) or []
        winds = series.get("wind_speed_10m", []) or []
        codes = series.get("weather_code", []) or []

        entries: list[ForecastEntry] = []
        for i, ts in enumerate(times[:limit]):
            entries.append(
                ForecastEntry(
                    valid_at=_parse_time(ts),
                    temperature_c=_at(temps, i),
                    precipitation_mm=_at(precip, i),
                    wind_speed_ms=_at(winds, i),
                    condition=condition_from_code(_at(codes, i)),
                )
            )
        return Forecast(
            provider=self.name,
            location=location,
            generated_at=datetime.now().astimezone(),
            entries=entries,
        )


def _at(values: list, index: int):
    return values[index] if index < len(values) else None


def _parse_time(value: object) -> datetime:
    if not value:
        raise ProviderError("open-meteo response missing timestamp")
    return datetime.fromisoformat(str(value))

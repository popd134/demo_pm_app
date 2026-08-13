"""OpenAPI metadata: tag descriptions and the published API contract (WBS 1.2.4).

Centralises the human-readable documentation FastAPI folds into the generated
OpenAPI/Swagger spec served at ``/docs``, ``/redoc`` and ``/openapi.json``.
"""

from __future__ import annotations

API_DESCRIPTION = """
Backend API for the **Weather Tracking & Analysis Dashboard**.

Ingests weather data from external providers, stores and analyses time-series history,
and exposes it to the dashboard frontend.

### Authentication
Obtain a token from `POST /api/auth/login` and send it as `Authorization: Bearer <token>`.
Admin-only endpoints additionally require a user with the `admin` role.

### Conventions
- Timestamps are ISO-8601. Units are canonical: °C, m/s, mm, hPa.
- List endpoints that can grow are paginated via `limit` / `offset` and return a
  `{ items, total, limit, offset }` envelope.
- Errors return `{ "detail": "<message>" }` with an appropriate status code.
""".strip()

TAGS_METADATA = [
    {"name": "system", "description": "Health checks and service metadata."},
    {"name": "auth", "description": "Registration, login and the current user."},
    {
        "name": "providers",
        "description": "Live calls to external weather providers (current & forecast).",
    },
    {
        "name": "ingestion",
        "description": "Status and manual control of the scheduled ingestion loop.",
    },
    {
        "name": "weather",
        "description": "Query stored locations, observations and forecasts.",
    },
    {
        "name": "analytics",
        "description": "Trends, aggregates, anomalies and forecast-accuracy metrics.",
    },
    {
        "name": "preferences",
        "description": "Per-user saved locations, units and alert thresholds.",
    },
]

CONTACT = {"name": "Weather Dashboard Team", "url": "https://github.com/pop134/sample_PM_v2"}
LICENSE_INFO = {"name": "MIT"}

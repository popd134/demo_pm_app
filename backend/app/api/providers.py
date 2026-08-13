"""Provider integration endpoints (WBS 1.1.1).

A thin surface that exercises the provider clients directly against a live source. The
full weather query REST API (filtering, pagination, stored history) is WBS 1.2.2; these
routes exist so provider integration is usable and demonstrable on its own.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import CurrentConditions, Forecast, GeoPoint
from app.services.providers import (
    ProviderConfigError,
    ProviderError,
    available_providers,
    get_provider,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", summary="List available weather providers")
def list_providers() -> dict[str, list[str]]:
    return {"providers": available_providers()}


def _resolve(provider: str | None):
    try:
        return get_provider(provider)
    except ProviderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _handle(exc: ProviderError) -> HTTPException:
    if isinstance(exc, ProviderConfigError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.get("/current", response_model=CurrentConditions)
async def current(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    provider: str | None = Query(default=None),
) -> CurrentConditions:
    client = _resolve(provider)
    try:
        return await client.get_current(GeoPoint(latitude=lat, longitude=lon))
    except ProviderError as exc:
        raise _handle(exc) from exc


@router.get("/forecast", response_model=Forecast)
async def forecast(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    days: int = Query(default=7, ge=1, le=16),
    provider: str | None = Query(default=None),
) -> Forecast:
    client = _resolve(provider)
    try:
        return await client.get_forecast(
            GeoPoint(latitude=lat, longitude=lon), days=days
        )
    except ProviderError as exc:
        raise _handle(exc) from exc

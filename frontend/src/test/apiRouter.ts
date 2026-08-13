import type { MockResult } from "./fetchMock";

/** Canned location fixtures for tests. */
export const LOCATIONS = [
  { id: 1, name: "Alpha", latitude: 1, longitude: 2, country: "AA", timezone: null, elevation_m: null },
  { id: 2, name: "Beta", latitude: 3, longitude: 4, country: "BB", timezone: null, elevation_m: null },
];

function observation(temp: number) {
  return {
    id: 1,
    provider: "test",
    observed_at: "2026-08-05T12:00:00Z",
    temperature_c: temp,
    humidity_pct: 55,
    wind_speed_ms: 3,
    wind_direction_deg: 180,
    precipitation_mm: 0,
    pressure_hpa: 1012,
    condition: "Clear sky",
  };
}

/** A default router covering the dashboard's read endpoints. */
export function dashboardRouter(url: string): MockResult {
  if (url.endsWith("/api/health")) {
    return { body: { status: "ok", app_name: "Weather", environment: "test", version: "0.1.0" } };
  }
  if (url.endsWith("/api/weather/locations")) {
    return { body: LOCATIONS };
  }
  if (url.includes("/api/weather/locations/1/current")) return { body: observation(18) };
  if (url.includes("/api/weather/locations/2/current")) return { body: observation(25) };
  if (url.includes("/trends")) {
    return { body: { location_id: 1, metric: "temperature_c", period: "daily", buckets: [] } };
  }
  if (url.includes("/alerts")) return { body: [] };
  return { status: 404, body: { detail: "not found" } };
}

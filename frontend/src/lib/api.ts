/**
 * Minimal typed fetch wrapper for the backend API.
 *
 * A fuller, OpenAPI-aligned client with caching and error mapping arrives with WBS
 * tasks 1.5.1 and 1.5.2. This foundation version centralises the base URL and JSON
 * handling so feature code has a single place to call.
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new ApiError(`Request to ${path} failed`, res.status);
  }
  return (await res.json()) as T;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  version: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}

// --- Weather domain types & calls (WBS 1.4.3) ---------------------------------

export interface Location {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string | null;
  timezone: string | null;
  elevation_m: number | null;
}

export interface Observation {
  id: number;
  provider: string;
  observed_at: string;
  temperature_c: number | null;
  humidity_pct: number | null;
  wind_speed_ms: number | null;
  wind_direction_deg: number | null;
  precipitation_mm: number | null;
  pressure_hpa: number | null;
  condition: string | null;
}

export function getLocations(): Promise<Location[]> {
  return apiGet<Location[]>("/weather/locations");
}

export function getCurrentConditions(locationId: number): Promise<Observation> {
  return apiGet<Observation>(`/weather/locations/${locationId}/current`);
}

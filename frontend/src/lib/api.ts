/**
 * Typed API surface (WBS 1.5.1).
 *
 * A thin, hand-written client aligned with the backend OpenAPI contract. All calls go
 * through the shared `request` helper (base URL, auth, error mapping) in `client.ts`.
 * Endpoints are grouped under `api`; backward-compatible named helpers are re-exported
 * for existing callers.
 */

import { ApiError, request, tokenStore } from "./client";

export { ApiError, tokenStore };

// --- Types (aligned with backend schemas) -------------------------------------

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  version: string;
}

export interface Location {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string | null;
  timezone: string | null;
  elevation_m: number | null;
}

export interface LocationCreate {
  name: string;
  latitude: number;
  longitude: number;
  country?: string | null;
  timezone?: string | null;
  elevation_m?: number | null;
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

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type AggregatePeriod = "daily" | "weekly" | "monthly";

export interface AggregateBucket {
  period_start: string;
  count: number;
  average: number | null;
  minimum: number | null;
  maximum: number | null;
  total: number;
  change_from_previous: number | null;
}

export interface TrendResponse {
  location_id: number;
  metric: string;
  period: string;
  buckets: AggregateBucket[];
}

export interface Alert {
  id: number;
  location_id: number;
  observation_id: number | null;
  metric: string;
  value: number;
  threshold: number | null;
  kind: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface ForecastAccuracy {
  location_id: number;
  metric: string;
  horizon: string | null;
  forecast_id: number;
  generated_at: string;
  sample_count: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
}

export interface UserProfile {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Preferences {
  temperature_unit: string;
  wind_unit: string;
  alert_thresholds: Record<string, Record<string, number>>;
}

export interface PreferencesUpdate {
  temperature_unit?: string;
  wind_unit?: string;
  alert_thresholds?: Record<string, Record<string, number>>;
}

export interface SavedLocation {
  id: number;
  location: Location;
}

// --- Grouped client -----------------------------------------------------------

export const api = {
  health: () => request<HealthResponse>("/health"),

  auth: {
    async login(email: string, password: string): Promise<Token> {
      const token = await request<Token>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      tokenStore.set(token.access_token);
      return token;
    },
    register: (email: string, password: string) =>
      request<UserProfile>("/auth/register", { method: "POST", body: { email, password } }),
    me: () => request<UserProfile>("/auth/me", { auth: true }),
    logout: () => tokenStore.clear(),
  },

  locations: {
    list: () => request<Location[]>("/weather/locations"),
    get: (id: number) => request<Location>(`/weather/locations/${id}`),
    create: (payload: LocationCreate) =>
      request<Location>("/weather/locations", { method: "POST", body: payload, auth: true }),
    current: (id: number) => request<Observation>(`/weather/locations/${id}/current`),
    observations: (
      id: number,
      params: { start?: string; end?: string; limit?: number; offset?: number } = {},
    ) => request<Page<Observation>>(`/weather/locations/${id}/observations`, { query: params }),
  },

  analytics: {
    trends: (id: number, metric: string, period: AggregatePeriod) =>
      request<TrendResponse>(`/analytics/locations/${id}/trends`, { query: { metric, period } }),
    alerts: (id: number, limit = 50) =>
      request<Alert[]>(`/analytics/locations/${id}/alerts`, { query: { limit } }),
    evaluate: (id: number) =>
      request<Alert[]>(`/analytics/locations/${id}/evaluate`, { method: "POST" }),
    forecastAccuracy: (id: number, metric: string) =>
      request<ForecastAccuracy>(`/analytics/locations/${id}/forecast-accuracy`, {
        query: { metric },
      }),
  },

  preferences: {
    get: () => request<Preferences>("/preferences", { auth: true }),
    update: (payload: PreferencesUpdate) =>
      request<Preferences>("/preferences", { method: "PUT", body: payload, auth: true }),
    listSaved: () => request<SavedLocation[]>("/preferences/locations", { auth: true }),
    addSaved: (locationId: number) =>
      request<SavedLocation>("/preferences/locations", {
        method: "POST",
        body: { location_id: locationId },
        auth: true,
      }),
    removeSaved: (locationId: number) =>
      request<void>(`/preferences/locations/${locationId}`, {
        method: "DELETE",
        auth: true,
      }),
  },
};

// --- Backward-compatible named helpers ----------------------------------------

export const getHealth = () => api.health();
export const getLocations = () => api.locations.list();
export const getCurrentConditions = (id: number) => api.locations.current(id);
export const getTrends = (id: number, metric: string, period: AggregatePeriod) =>
  api.analytics.trends(id, metric, period);

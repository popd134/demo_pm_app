import type { Location, Observation } from "../../lib/api";
import { Badge } from "../ui";
import { StatTile } from "./StatTile";
import "./widgets.css";

interface Props {
  location: Location;
  observation: Observation;
}

function fmt(value: number | null, digits = 1): string {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

function windDirection(deg: number | null): string {
  if (deg === null || deg === undefined) return "";
  const points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return points[Math.round(deg / 45) % 8];
}

/** Current-conditions summary for the selected location (WBS 1.4.3). */
export function CurrentConditions({ location, observation }: Props) {
  const observedAt = new Date(observation.observed_at).toLocaleString();
  return (
    <div className="current-conditions">
      <div className="current-conditions__head">
        <div>
          <div className="current-conditions__temp">{fmt(observation.temperature_c, 0)}°C</div>
          <div className="section-subtle">
            {location.name}
            {observation.condition ? ` · ${observation.condition}` : ""}
          </div>
        </div>
        <Badge>{observation.provider}</Badge>
      </div>

      <div className="stat-grid">
        <StatTile label="Humidity" icon="💧" value={fmt(observation.humidity_pct, 0)} unit="%" />
        <StatTile
          label="Wind"
          icon="🌬️"
          value={`${fmt(observation.wind_speed_ms)} ${windDirection(observation.wind_direction_deg)}`.trim()}
          unit="m/s"
        />
        <StatTile label="Precipitation" icon="🌧️" value={fmt(observation.precipitation_mm)} unit="mm" />
        <StatTile label="Pressure" icon="📊" value={fmt(observation.pressure_hpa, 0)} unit="hPa" />
      </div>

      <p className="section-subtle current-conditions__meta">Observed {observedAt}</p>
    </div>
  );
}

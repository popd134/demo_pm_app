import { Spinner } from "../ui";
import { CurrentConditions } from "./CurrentConditions";
import { useQuery } from "../../hooks/useQuery";
import { ApiError, getCurrentConditions, type Location } from "../../lib/api";

/**
 * Fetches and renders current conditions for a single location (WBS 1.4.3/1.4.5),
 * cached via useQuery (WBS 1.5.2) so switching between locations is instant.
 */
export function CurrentConditionsCard({
  location,
  compact = false,
}: {
  location: Location;
  compact?: boolean;
}) {
  const { data: observation, isLoading, error } = useQuery(
    `current:${location.id}`,
    () => getCurrentConditions(location.id),
    { staleTime: 60_000 },
  );

  if (isLoading) return <Spinner label="Loading…" />;

  if (error) {
    const isMissing = error instanceof ApiError && error.status === 404;
    return (
      <p className="section-subtle">
        {isMissing
          ? `No observations for ${location.name} yet.`
          : "Could not reach the API."}
      </p>
    );
  }

  if (!observation) {
    return <p className="section-subtle">No observations for {location.name} yet.</p>;
  }

  if (compact) {
    return (
      <div>
        <strong>{location.name}</strong>
        <div style={{ fontSize: "var(--font-xl)", fontWeight: 700 }}>
          {observation.temperature_c === null ? "—" : observation.temperature_c.toFixed(0)}°C
        </div>
        <div className="section-subtle">{observation.condition ?? "—"}</div>
      </div>
    );
  }

  return <CurrentConditions location={location} observation={observation} />;
}

import { EmptyState, ErrorState, SkeletonLines } from "../ui";
import { CurrentConditions } from "./CurrentConditions";
import { useQuery } from "../../hooks/useQuery";
import { ApiError, getCurrentConditions, type Location } from "../../lib/api";

/**
 * Fetches and renders current conditions for a single location (WBS 1.4.3/1.4.5),
 * cached via useQuery (1.5.2), with skeleton/empty/retry states (WBS 1.5.3).
 */
export function CurrentConditionsCard({
  location,
  compact = false,
}: {
  location: Location;
  compact?: boolean;
}) {
  const { data: observation, isLoading, error, refetch } = useQuery(
    `current:${location.id}`,
    () => getCurrentConditions(location.id),
    { staleTime: 60_000 },
  );

  const isMissing =
    (error instanceof ApiError && error.status === 404) || (!isLoading && !error && !observation);

  if (isLoading) return <SkeletonLines lines={compact ? 2 : 3} />;

  if (error && !isMissing) {
    return <ErrorState message={`Could not load ${location.name}.`} onRetry={refetch} />;
  }

  if (isMissing || !observation) {
    return (
      <EmptyState
        icon="🌫️"
        title="No observations yet"
        message={`${location.name} has no stored readings. Run ingestion to populate it.`}
      />
    );
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

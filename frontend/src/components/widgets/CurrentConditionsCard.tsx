import { EmptyState, ErrorState, SkeletonLines } from "../ui";
import { CurrentConditions } from "./CurrentConditions";
import { LiveIndicator } from "./LiveIndicator";
import { useQuery } from "../../hooks/useQuery";
import { ApiError, getCurrentConditions, type Location } from "../../lib/api";

const LIVE_REFRESH_MS = 60_000;

/**
 * Fetches and renders current conditions for a single location (WBS 1.4.3/1.4.5),
 * cached via useQuery (1.5.2) with skeleton/empty/retry states (1.5.3). When `live`
 * is set it auto-refreshes on an interval and shows a live indicator (WBS 1.5.4).
 */
export function CurrentConditionsCard({
  location,
  compact = false,
  live = false,
}: {
  location: Location;
  compact?: boolean;
  live?: boolean;
}) {
  const { data: observation, isLoading, error, refetch, dataUpdatedAt } = useQuery(
    `current:${location.id}`,
    () => getCurrentConditions(location.id),
    { staleTime: 60_000, refetchInterval: live ? LIVE_REFRESH_MS : undefined },
  );

  const isMissing =
    (error instanceof ApiError && error.status === 404) ||
    (!isLoading && !error && !observation);

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

  return (
    <div>
      {live && (
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "var(--space-sm)" }}>
          <LiveIndicator updatedAt={dataUpdatedAt} />
        </div>
      )}
      <CurrentConditions location={location} observation={observation} />
    </div>
  );
}

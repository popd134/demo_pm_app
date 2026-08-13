import { Badge, Button, EmptyState, ErrorState, SkeletonLines } from "../ui";
import { LiveIndicator } from "./LiveIndicator";
import { useQuery } from "../../hooks/useQuery";
import { api, type Alert } from "../../lib/api";
import { invalidateQueries } from "../../lib/queryCache";
import "./alerts.css";

const REFRESH_MS = 30_000;

function severityTone(severity: string): "neutral" | "warning" | "danger" {
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warning";
  return "neutral";
}

/**
 * Recent alerts for a location, auto-refreshing on an interval (WBS 1.5.4). A "Check
 * now" action runs server-side evaluation and refreshes the list.
 */
export function AlertsPanel({ locationId }: { locationId: number }) {
  const key = `alerts:${locationId}`;
  const { data, isLoading, isError, refetch, dataUpdatedAt } = useQuery<Alert[]>(
    key,
    () => api.analytics.alerts(locationId),
    { staleTime: 15_000, refetchInterval: REFRESH_MS },
  );

  async function checkNow() {
    try {
      await api.analytics.evaluate(locationId);
    } finally {
      invalidateQueries((k) => k === key);
      refetch();
    }
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-md)",
          marginBottom: "var(--space-md)",
        }}
      >
        <LiveIndicator updatedAt={dataUpdatedAt} />
        <Button variant="secondary" onClick={checkNow}>
          Check now
        </Button>
      </div>

      {isLoading && <SkeletonLines lines={3} />}
      {isError && <ErrorState message="Could not load alerts." onRetry={refetch} />}
      {!isLoading && !isError && data && data.length === 0 && (
        <EmptyState icon="✅" title="No alerts" message="No threshold breaches or spikes detected." />
      )}
      {!isLoading && !isError && data && data.length > 0 && (
        <ul className="alerts-list">
          {data.map((alert) => (
            <li key={alert.id} className="alerts-list__item">
              <Badge tone={severityTone(alert.severity)}>{alert.severity}</Badge>
              <div>
                <div className="alerts-list__message">{alert.message}</div>
                <div className="section-subtle">
                  {new Date(alert.created_at).toLocaleString()}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Card, Spinner } from "../components/ui";
import { DashboardGrid, DashboardRegion } from "../components/layout/DashboardGrid";
import { CurrentConditions } from "../components/widgets/CurrentConditions";
import {
  getCurrentConditions,
  getLocations,
  type Location,
  type Observation,
} from "../lib/api";

/**
 * Dashboard page (WBS 1.4.3): loads locations, shows current-conditions widgets for
 * the first location. Location selection is added in 1.4.5; richer loading/error
 * states in 1.5.3.
 */
export function DashboardPage() {
  const [location, setLocation] = useState<Location | null>(null);
  const [observation, setObservation] = useState<Observation | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "empty" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const locations = await getLocations();
        if (cancelled) return;
        if (locations.length === 0) {
          setState("empty");
          return;
        }
        const first = locations[0];
        setLocation(first);
        try {
          const obs = await getCurrentConditions(first.id);
          if (cancelled) return;
          setObservation(obs);
          setState("ready");
        } catch {
          if (!cancelled) setState("empty");
        }
      } catch {
        if (!cancelled) setState("error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h2 className="section-heading">Dashboard</h2>
      <DashboardGrid>
        <DashboardRegion span="full">
          <Card title="Current conditions">
            {state === "loading" && <Spinner label="Loading current conditions…" />}
            {state === "error" && (
              <p className="section-subtle">Could not reach the API.</p>
            )}
            {state === "empty" && (
              <p className="section-subtle">
                No observations yet. Register a location and run ingestion to populate the
                dashboard.
              </p>
            )}
            {state === "ready" && location && observation && (
              <CurrentConditions location={location} observation={observation} />
            )}
          </Card>
        </DashboardRegion>
        <DashboardRegion span="half">
          <Card title="Temperature trend" subtitle="Chart region — arrives in WBS 1.4.4">
            <p className="section-subtle">Interactive time-series chart.</p>
          </Card>
        </DashboardRegion>
        <DashboardRegion span="half">
          <Card title="Precipitation" subtitle="Chart region — arrives in WBS 1.4.4">
            <p className="section-subtle">Interactive time-series chart.</p>
          </Card>
        </DashboardRegion>
        <DashboardRegion span="full">
          <Card title="Locations" subtitle="Controls region — arrives in WBS 1.4.5">
            <p className="section-subtle">Search and switch between saved locations.</p>
          </Card>
        </DashboardRegion>
      </DashboardGrid>
    </div>
  );
}

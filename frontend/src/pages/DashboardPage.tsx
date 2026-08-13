import { Card, EmptyState, ErrorState, SkeletonLines } from "../components/ui";
import { DashboardGrid, DashboardRegion } from "../components/layout/DashboardGrid";
import { CurrentConditionsCard } from "../components/widgets/CurrentConditionsCard";
import { TrendChart } from "../components/widgets/TrendChart";
import { AlertsPanel } from "../components/widgets/AlertsPanel";
import { LocationBar } from "../components/locations/LocationBar";
import { useLocations } from "../context/LocationsContext";

/**
 * Dashboard page (WBS 1.4.5): driven by the locations context. The active location
 * feeds the current-conditions and chart widgets; compared locations render side by
 * side.
 */
export function DashboardPage() {
  const { status, locations, activeLocation, compareIds, refresh } = useLocations();
  const compared = locations.filter((l) => compareIds.includes(l.id));

  return (
    <div>
      <h2 className="section-heading">Dashboard</h2>
      <DashboardGrid>
        <DashboardRegion span="full">
          <Card title="Current conditions">
            {status === "loading" && <SkeletonLines lines={3} />}
            {status === "error" && (
              <ErrorState message="Could not load locations." onRetry={refresh} />
            )}
            {status === "ready" && !activeLocation && (
              <EmptyState
                icon="📍"
                title="No locations yet"
                message="Register a location and run ingestion to populate the dashboard."
              />
            )}
            {status === "ready" && activeLocation && (
              <CurrentConditionsCard location={activeLocation} live />
            )}
          </Card>
        </DashboardRegion>

        {activeLocation && (
          <DashboardRegion span="full">
            <Card title="Alerts" subtitle="Auto-refreshing threshold breaches & spikes">
              <AlertsPanel locationId={activeLocation.id} />
            </Card>
          </DashboardRegion>
        )}

        <DashboardRegion span="half">
          <Card title="Temperature trend">
            {activeLocation ? (
              <TrendChart
                locationId={activeLocation.id}
                metric="temperature_c"
                unit="°C"
                kind="line"
              />
            ) : (
              <p className="section-subtle">Select a location to see trends.</p>
            )}
          </Card>
        </DashboardRegion>
        <DashboardRegion span="half">
          <Card title="Precipitation">
            {activeLocation ? (
              <TrendChart
                locationId={activeLocation.id}
                metric="precipitation_mm"
                unit="mm"
                kind="bar"
              />
            ) : (
              <p className="section-subtle">Select a location to see totals.</p>
            )}
          </Card>
        </DashboardRegion>

        <DashboardRegion span="full">
          <Card title="Locations" subtitle="Search, switch and compare saved locations">
            <LocationBar />
            {compared.length > 1 && (
              <div className="compare-grid" style={{ marginTop: "var(--space-lg)" }}>
                {compared.map((loc) => (
                  <Card key={loc.id}>
                    <CurrentConditionsCard location={loc} compact />
                  </Card>
                ))}
              </div>
            )}
          </Card>
        </DashboardRegion>
      </DashboardGrid>
    </div>
  );
}

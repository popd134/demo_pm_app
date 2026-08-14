import { Card } from "../components/ui";
import { DashboardGrid, DashboardRegion } from "../components/layout/DashboardGrid";

/**
 * Dashboard page (WBS 1.4.2): lays out the widget regions. The regions are filled by
 * later tasks — current conditions (1.4.3), charts (1.4.4), location controls (1.4.5).
 */
export function DashboardPage() {
  return (
    <div>
      <h2 className="section-heading">Dashboard</h2>
      <DashboardGrid>
        <DashboardRegion span="full">
          <Card title="Current conditions" subtitle="Widget region — arrives in WBS 1.4.3">
            <p className="section-subtle">Live current-conditions summary cards.</p>
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

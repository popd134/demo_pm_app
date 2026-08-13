import { useEffect, useState } from "react";
import { AppLayout } from "./components/layout/AppLayout";
import type { SectionId } from "./components/layout/navigation";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { LocationsProvider } from "./context/LocationsContext";
import { getHealth, type HealthResponse } from "./lib/api";

/**
 * Root application (WBS 1.4.2): owns navigation state and renders the active section
 * inside the themed app shell.
 */
export default function App() {
  const [section, setSection] = useState<SectionId>("dashboard");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  const apiStatus = {
    tone: error ? ("danger" as const) : health ? ("success" as const) : ("neutral" as const),
    label: error ? "API offline" : health ? `API ${health.status}` : "Connecting…",
  };

  return (
    <AppLayout active={section} onNavigate={setSection} apiStatus={apiStatus}>
      <LocationsContent section={section} />
    </AppLayout>
  );
}

function LocationsContent({ section }: { section: SectionId }) {
  return (
    <LocationsProvider>
      {section === "dashboard" && <DashboardPage />}
      {section === "analytics" && (
        <PlaceholderPage
          title="Analytics"
          note="Trends, anomalies and forecast accuracy visualizations arrive in WBS 1.4.4."
        />
      )}
      {section === "settings" && (
        <PlaceholderPage
          title="Settings"
          note="Saved locations, units and alert configuration arrive in WBS 1.6.2."
        />
      )}
    </LocationsProvider>
  );
}

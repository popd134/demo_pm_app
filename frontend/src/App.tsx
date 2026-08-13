import { useEffect, useState } from "react";
import { AppLayout } from "./components/layout/AppLayout";
import type { SectionId } from "./components/layout/navigation";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { SettingsPage } from "./pages/SettingsPage";
import { LocationsProvider } from "./context/LocationsContext";
import { AuthProvider } from "./context/AuthContext";
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
    <AuthProvider>
      <AppLayout active={section} onNavigate={setSection} apiStatus={apiStatus}>
        <LocationsContent section={section} />
      </AppLayout>
    </AuthProvider>
  );
}

function LocationsContent({ section }: { section: SectionId }) {
  return (
    <LocationsProvider>
      {section === "dashboard" && <DashboardPage />}
      {section === "analytics" && (
        <PlaceholderPage
          title="Analytics"
          note="Deeper analytics views build on the dashboard charts (WBS 1.4.4) and API."
        />
      )}
      {section === "settings" && <SettingsPage />}
    </LocationsProvider>
  );
}

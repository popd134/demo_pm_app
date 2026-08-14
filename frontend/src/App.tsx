import { useEffect, useState } from "react";
import { Badge, Button, Card } from "./components/ui";
import { useTheme } from "./design/ThemeProvider";
import { getHealth, type HealthResponse } from "./lib/api";

/**
 * Application shell (WBS 1.4.1).
 *
 * Establishes the design-system-driven frame: header with theme toggle, a content
 * area and footer. The full dashboard layout and widgets arrive in WBS 1.4.2+.
 */
export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setError("Backend unreachable"));
  }, []);

  const apiTone = error ? "danger" : health ? "success" : "neutral";
  const apiLabel = error ? "API offline" : health ? `API ${health.status}` : "Connecting…";

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Weather Tracking &amp; Analysis Dashboard</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
          <Badge tone={apiTone}>{apiLabel}</Badge>
          <Button variant="ghost" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
          </Button>
        </div>
      </header>

      <main className="app-main">
        <Card
          title="Dashboard coming online"
          subtitle="This PR establishes the design system: tokens, theming and shared UI components."
        >
          <p style={{ color: "var(--color-text-muted)" }}>
            Current-conditions widgets, trend charts and location selection land in the
            Dashboard UI requirement (WBS 1.4.2+).
          </p>
          {health && (
            <dl className="meta">
              <div>
                <dt>Service</dt>
                <dd>{health.app_name}</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>{health.environment}</dd>
              </div>
              <div>
                <dt>API version</dt>
                <dd>{health.version}</dd>
              </div>
            </dl>
          )}
        </Card>
      </main>

      <footer className="app-footer">
        <span>Built from Weather_Dashboard_WBS.xlsx</span>
      </footer>
    </div>
  );
}

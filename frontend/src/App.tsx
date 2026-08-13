import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "./lib/api";

/**
 * Application shell. The full dashboard layout (navigation, widget grid, theming)
 * is delivered by WBS tasks 1.4.x. This foundation shell renders the app frame and
 * verifies backend connectivity via the health endpoint.
 */
export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setError("Backend unreachable"));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Weather Tracking &amp; Analysis Dashboard</h1>
        <span className="badge" data-state={error ? "down" : health ? "up" : "pending"}>
          {error ? "API offline" : health ? `API ${health.status}` : "Connecting…"}
        </span>
      </header>

      <main className="app-main">
        <section className="placeholder-card">
          <h2>Dashboard coming online</h2>
          <p>
            This is the project foundation. Current-conditions widgets, trend charts and
            location selection land in the Dashboard UI requirement (WBS 1.4).
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
        </section>
      </main>

      <footer className="app-footer">
        <span>Built from Weather_Dashboard_WBS.xlsx</span>
      </footer>
    </div>
  );
}

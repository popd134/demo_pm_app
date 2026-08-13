import type { ReactNode } from "react";
import { Badge, Button } from "../ui";
import { useTheme } from "../../design/ThemeProvider";
import { NAV_ITEMS, type SectionId } from "./navigation";
import "./layout.css";

interface AppLayoutProps {
  active: SectionId;
  onNavigate: (section: SectionId) => void;
  apiStatus: { tone: "neutral" | "success" | "danger"; label: string };
  children: ReactNode;
}

/**
 * Application shell (WBS 1.4.2): header, sidebar navigation, themed main region.
 * Widget placement within the main region is handled by the dashboard grid.
 */
export function AppLayout({ active, onNavigate, apiStatus, children }: AppLayoutProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="layout">
      <header className="layout__header">
        <div className="layout__brand">
          <span aria-hidden>🌦️</span>
          <span>Weather Dashboard</span>
        </div>
        <div className="layout__header-actions">
          <Badge tone={apiStatus.tone}>{apiStatus.label}</Badge>
          <Button variant="ghost" onClick={toggleTheme} aria-label="Toggle color theme">
            {theme === "dark" ? "☀️" : "🌙"}
          </Button>
        </div>
      </header>

      <div className="layout__body">
        <nav className="layout__sidebar" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={
                "layout__nav-item" +
                (item.id === active ? " layout__nav-item--active" : "")
              }
              aria-current={item.id === active ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              <span aria-hidden>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <main className="layout__main">{children}</main>
      </div>
    </div>
  );
}

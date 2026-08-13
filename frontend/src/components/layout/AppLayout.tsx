import { useEffect, useState, type ReactNode } from "react";
import { Badge, Button } from "../ui";
import { useTheme } from "../../design/ThemeProvider";
import { useMediaQuery } from "../../hooks/useMediaQuery";
import { NAV_ITEMS, type SectionId } from "./navigation";
import "./layout.css";

interface AppLayoutProps {
  active: SectionId;
  onNavigate: (section: SectionId) => void;
  apiStatus: { tone: "neutral" | "success" | "danger"; label: string };
  children: ReactNode;
}

/**
 * Application shell (WBS 1.4.2, responsive in 1.4.6): header, sidebar navigation and
 * themed main region. On mobile the sidebar collapses behind a menu button.
 */
export function AppLayout({ active, onNavigate, apiStatus, children }: AppLayoutProps) {
  const { theme, toggleTheme } = useTheme();
  const isMobile = useMediaQuery("(max-width: 820px)");
  const [navOpen, setNavOpen] = useState(false);

  // Close the mobile menu whenever we grow to desktop width.
  useEffect(() => {
    if (!isMobile) setNavOpen(false);
  }, [isMobile]);

  const navVisible = !isMobile || navOpen;

  function handleNavigate(section: SectionId) {
    onNavigate(section);
    if (isMobile) setNavOpen(false);
  }

  return (
    <div className="layout">
      <header className="layout__header">
        <div className="layout__brand">
          {isMobile && (
            <button
              type="button"
              className="layout__menu-button"
              aria-label="Toggle navigation"
              aria-expanded={navOpen}
              onClick={() => setNavOpen((open) => !open)}
            >
              ☰
            </button>
          )}
          <span aria-hidden>🌦️</span>
          <span className="layout__brand-text">Weather Dashboard</span>
        </div>
        <div className="layout__header-actions">
          <Badge tone={apiStatus.tone}>{apiStatus.label}</Badge>
          <Button variant="ghost" onClick={toggleTheme} aria-label="Toggle color theme">
            {theme === "dark" ? "☀️" : "🌙"}
          </Button>
        </div>
      </header>

      <div className={"layout__body" + (isMobile ? " layout__body--mobile" : "")}>
        {navVisible && (
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
                onClick={() => handleNavigate(item.id)}
              >
                <span aria-hidden>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        )}

        <main className="layout__main">{children}</main>
      </div>
    </div>
  );
}

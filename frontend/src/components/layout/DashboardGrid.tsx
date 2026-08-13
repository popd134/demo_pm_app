import type { ReactNode } from "react";

/**
 * Responsive dashboard grid with named widget regions (WBS 1.4.2).
 *
 * Widgets are slotted into regions by later tasks (current conditions 1.4.3,
 * charts 1.4.4, location controls 1.4.5). The grid collapses to a single column on
 * narrow viewports (refined in 1.4.6).
 */
export function DashboardGrid({ children }: { children: ReactNode }) {
  return <div className="dashboard-grid">{children}</div>;
}

interface RegionProps {
  span?: "full" | "half";
  children: ReactNode;
}

export function DashboardRegion({ span = "full", children }: RegionProps) {
  return <section className={`dashboard-region dashboard-region--${span}`}>{children}</section>;
}

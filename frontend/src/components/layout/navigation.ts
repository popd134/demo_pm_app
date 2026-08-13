/** Navigation model shared by the layout (WBS 1.4.2). */

export type SectionId = "dashboard" | "analytics" | "settings";

export interface NavItem {
  id: SectionId;
  label: string;
  icon: string;
}

export const NAV_ITEMS: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: "🌤️" },
  { id: "analytics", label: "Analytics", icon: "📈" },
  { id: "settings", label: "Settings", icon: "⚙️" },
];

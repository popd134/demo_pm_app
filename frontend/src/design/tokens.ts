/**
 * Design tokens (WBS 1.4.1).
 *
 * The canonical values live as CSS custom properties in `theme.css` (so they can vary
 * by light/dark theme). These TypeScript exports mirror the *names* and scale steps so
 * component code has typed, autocomplete-friendly references instead of magic strings.
 */

export const space = {
  xs: "var(--space-xs)",
  sm: "var(--space-sm)",
  md: "var(--space-md)",
  lg: "var(--space-lg)",
  xl: "var(--space-xl)",
} as const;

export const radius = {
  sm: "var(--radius-sm)",
  md: "var(--radius-md)",
  lg: "var(--radius-lg)",
  pill: "var(--radius-pill)",
} as const;

export const color = {
  bg: "var(--color-bg)",
  surface: "var(--color-surface)",
  surfaceMuted: "var(--color-surface-muted)",
  border: "var(--color-border)",
  text: "var(--color-text)",
  textMuted: "var(--color-text-muted)",
  accent: "var(--color-accent)",
  success: "var(--color-success)",
  warning: "var(--color-warning)",
  danger: "var(--color-danger)",
} as const;

export const fontSize = {
  xs: "var(--font-xs)",
  sm: "var(--font-sm)",
  md: "var(--font-md)",
  lg: "var(--font-lg)",
  xl: "var(--font-xl)",
  xxl: "var(--font-xxl)",
} as const;

export type SpaceToken = keyof typeof space;
export type ColorToken = keyof typeof color;

export const THEME_STORAGE_KEY = "weather-dashboard-theme";
export type ThemeName = "light" | "dark";

export function Spinner({ label }: { label?: string }) {
  return (
    <span
      role="status"
      aria-label={label ?? "Loading"}
      style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-sm)" }}
    >
      <span className="ui-spinner" />
      {label && <span style={{ color: "var(--color-text-muted)" }}>{label}</span>}
    </span>
  );
}

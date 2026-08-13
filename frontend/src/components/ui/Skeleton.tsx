interface SkeletonProps {
  width?: string;
  height?: string;
  radius?: string;
}

/** A shimmering placeholder block for loading states (WBS 1.5.3). */
export function Skeleton({ width = "100%", height = "1rem", radius }: SkeletonProps) {
  return (
    <span
      className="ui-skeleton"
      style={{ width, height, borderRadius: radius ?? "var(--radius-sm)" }}
      aria-hidden
    />
  );
}

/** A small preset arrangement of skeleton lines for a widget body. */
export function SkeletonLines({ lines = 3 }: { lines?: number }) {
  return (
    <div className="ui-skeleton-stack" role="status" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} width={i === lines - 1 ? "60%" : "100%"} height="0.9rem" />
      ))}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Badge } from "../ui";

/**
 * A small "live" badge that shows how long ago data last updated (WBS 1.5.4).
 * Re-renders on a timer so the relative time stays current.
 */
export function LiveIndicator({ updatedAt }: { updatedAt: number }) {
  const [, tick] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => tick((n) => n + 1), 1000);
    return () => window.clearInterval(id);
  }, []);

  if (!updatedAt) return null;
  const seconds = Math.max(0, Math.round((Date.now() - updatedAt) / 1000));
  const label = seconds < 5 ? "just now" : seconds < 60 ? `${seconds}s ago` : `${Math.round(seconds / 60)}m ago`;

  return (
    <Badge tone="success" title="Auto-refreshing">
      ● Live · {label}
    </Badge>
  );
}

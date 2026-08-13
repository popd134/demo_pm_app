import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: string;
  title: string;
  message?: ReactNode;
  action?: ReactNode;
}

/** Consistent empty-state messaging for widgets and charts (WBS 1.5.3). */
export function EmptyState({ icon = "📭", title, message, action }: EmptyStateProps) {
  return (
    <div className="ui-state">
      <div className="ui-state__icon" aria-hidden>
        {icon}
      </div>
      <div className="ui-state__title">{title}</div>
      {message && <p className="ui-state__message">{message}</p>}
      {action}
    </div>
  );
}

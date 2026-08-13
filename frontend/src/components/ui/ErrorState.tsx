import { Button } from "./Button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

/** Retry-able error UI for failed data loads (WBS 1.5.3). */
export function ErrorState({
  title = "Something went wrong",
  message = "The request failed. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="ui-state" role="alert">
      <div className="ui-state__icon" aria-hidden>
        ⚠️
      </div>
      <div className="ui-state__title">{title}</div>
      <p className="ui-state__message">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

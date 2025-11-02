import { Spinner } from "@fluentui/react-components";

type LoadingSpinnerProps = {
  message?: string;
};

/**
 * Loading spinner component with optional message
 */
export function LoadingSpinner({
  message = "Ładowanie...",
}: LoadingSpinnerProps): JSX.Element {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "16px",
        minHeight: "400px",
      }}
      role="status"
      aria-live="polite"
    >
      <Spinner size="huge" />
      <p>{message}</p>
      <span className="sr-only">{message}</span>
    </div>
  );
}


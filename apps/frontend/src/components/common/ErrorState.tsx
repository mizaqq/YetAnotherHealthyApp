import {
  Button,
  Card,
  CardHeader,
  CardFooter,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AlertUrgent24Regular } from "@fluentui/react-icons";

interface ErrorStateProps {
  error?: Error;
  message?: string;
  onRetry?: () => void;
}

const useStyles = makeStyles({
  root: {
    display: "flex",
    minHeight: "400px",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding("24px"),
  },
  card: {
    maxWidth: "448px",
    width: "100%",
  },
  header: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
    backgroundColor: tokens.colorPaletteRedBackground2,
    ...shorthands.padding("8px"),
  },
  icon: {
    color: tokens.colorPaletteRedForeground2,
  },
});

/**
 * Error state component with retry functionality
 */
export function ErrorState({
  error,
  message,
  onRetry,
}: ErrorStateProps): JSX.Element {
  const styles = useStyles();
  const displayMessage =
    message || error?.message || "Wystąpił błąd podczas ładowania danych.";

  return (
    <div className={styles.root}>
      <Card className={styles.card} role="alert" aria-live="polite">
        <CardHeader
          header={
            <div className={styles.header}>
              <div className={styles.iconContainer}>
                <AlertUrgent24Regular className={styles.icon} />
              </div>
              <Text weight="semibold" size={500}>
                Ups! Coś poszło nie tak
              </Text>
            </div>
          }
          description={
            <Text as="p" size={400} style={{ marginTop: tokens.spacingVerticalS }}>
              {displayMessage}
            </Text>
          }
        />
        {onRetry && (
          <CardFooter>
            <Button
              onClick={onRetry}
              appearance="outline"
              style={{ width: "100%" }}
              data-testid="error-retry"
            >
              Spróbuj ponownie
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  );
}


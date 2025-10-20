import {
  Button,
  Spinner,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";

type AnalysisLoadingStepProps = {
  onCancel: () => void;
};

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.gap(tokens.spacingVerticalXL),
    ...shorthands.padding(tokens.spacingVerticalXXXL, tokens.spacingHorizontalXL),
    textAlign: "center",
  },
  spinnerContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  description: {
    color: tokens.colorNeutralForeground2,
    maxWidth: "400px",
  },
});

export function AnalysisLoadingStep({ onCancel }: AnalysisLoadingStepProps) {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      <div className={styles.spinnerContainer}>
        <Spinner
          appearance="primary"
          size="extra-large"
          label="Analizujemy Twój posiłek..."
          labelPosition="below"
        />
        <Text size={400} className={styles.description}>
          To może potrwać do 30 sekund. Nasz AI analizuje składniki i oblicza wartości odżywcze.
        </Text>
      </div>

      <Button appearance="secondary" onClick={onCancel}>
        Anuluj
      </Button>
    </div>
  );
}


import {
  Button,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { MacroDisplay } from "@/components/dashboard/MacroDisplay";
import { IngredientsTable } from "./IngredientsTable";
import type { AnalysisResultsViewModel } from "@/types";

type AnalysisResultsStepProps = {
  results: AnalysisResultsViewModel;
  isLoading: boolean;
  onAccept: () => void;
  onRetry: () => void;
  onCancel: () => void;
};

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXL),
  },
  section: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  sectionTitle: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
  },
  tableContainer: {
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke1),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    backgroundColor: tokens.colorNeutralBackground1,
    overflowX: "auto",
  },
  buttonGroup: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalM),
    justifyContent: "flex-end",
    marginTop: tokens.spacingVerticalL,
    flexWrap: "wrap",
  },
});

export function AnalysisResultsStep({
  results,
  isLoading,
  onAccept,
  onRetry,
  onCancel,
}: AnalysisResultsStepProps) {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <Text size={500} className={styles.sectionTitle}>
          Podsumowanie wartości odżywczych
        </Text>
        <MacroDisplay
          calories={results.totals.calories}
          macros={{
            protein: results.totals.protein,
            fat: results.totals.fat,
            carbs: results.totals.carbs,
          }}
          data-testid="analysis-results-macro-display"
        />
      </div>

      <div className={styles.section}>
        <Text size={500} className={styles.sectionTitle}>
          Wykryte składniki
        </Text>
        <div className={styles.tableContainer}>
          <IngredientsTable items={results.items} data-testid="analysis-results-ingredients-table" />
        </div>
      </div>

      <div className={styles.buttonGroup}>
        <Button appearance="subtle" onClick={onCancel} disabled={isLoading} data-testid="analysis-results-cancel">
          Anuluj
        </Button>
        <Button appearance="secondary" onClick={onRetry} disabled={isLoading} data-testid="analysis-results-retry">
          Popraw i przelicz ponownie
        </Button>
        <Button appearance="primary" onClick={onAccept} disabled={isLoading} data-testid="analysis-results-accept">
          Akceptuj i zapisz
        </Button>
      </div>
    </div>
  );
}


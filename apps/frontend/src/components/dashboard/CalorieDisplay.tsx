import {
  Text,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";

type CalorieDisplayProps = {
  currentCalories: number;
  goalCalories: number | null | undefined;
};

const useStyles = makeStyles({
  caloriesDisplayWithGoal: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    alignItems: "flex-start",
  },
  valueAndLabelContainer: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
    alignItems: "center",
  },
  valueContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    lineHeight: "1",
  },
  caloriesValue: {
    fontSize: "48px",
    lineHeight: "1",
    ...shorthands.margin(0),
  },
  caloriesUnit: {
    color: tokens.colorNeutralForeground2,
  },
  caloriesLabel: {
    color: tokens.colorNeutralForeground2,
    ...shorthands.margin(0),
  },
  goalContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingLeft: tokens.spacingHorizontalL,
    ...shorthands.borderLeft("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  goalValue: {
    color: tokens.colorNeutralForeground2,
  },
  goalUnit: {
    color: tokens.colorNeutralForeground2,
  },
});

export function CalorieDisplay({
  currentCalories,
  goalCalories,
}: CalorieDisplayProps): JSX.Element {
  const styles = useStyles();
  const hasValidGoal = goalCalories && goalCalories > 0;

  return (
    <div data-testid="dashboard-calorie-display">
      {hasValidGoal ? (
        <div className={styles.caloriesDisplayWithGoal}>
          <div className={styles.valueAndLabelContainer}>
            <Text as="p" size={300} className={styles.caloriesLabel}>
              Spożyte kalorie
            </Text>
            <div className={styles.valueContainer}>
              <Text as="p" weight="bold" className={styles.caloriesValue}>
                {currentCalories.toLocaleString("pl-PL", {
                  maximumFractionDigits: 0,
                })}
              </Text>
              <Text as="span" size={400} className={styles.caloriesUnit}>
                kcal
              </Text>
            </div>
          </div>
          <div className={styles.goalContainer}>
            <Text as="p" size={300} className={styles.caloriesLabel}>
              Cel dzienny
            </Text>
            <div className={styles.valueContainer}>
              <Text as="p" weight="semibold" className={styles.caloriesValue} style={{ color: tokens.colorNeutralForeground2 }}>
                {goalCalories.toLocaleString("pl-PL", {
                  maximumFractionDigits: 0,
                })}
              </Text>
              <Text as="span" size={400} className={styles.caloriesUnit}>
                kcal
              </Text>
            </div>
          </div>
        </div>
      ) : (
        <div className={styles.valueAndLabelContainer}>
          <Text as="p" size={300} className={styles.caloriesLabel}>
            Spożyte kalorie
          </Text>
          <div className={styles.valueContainer}>
            <Text as="p" weight="bold" className={styles.caloriesValue}>
              {currentCalories.toLocaleString("pl-PL", {
                maximumFractionDigits: 0,
              })}
            </Text>
            <Text as="span" size={400} className={styles.caloriesUnit}>
              kcal
            </Text>
          </div>
        </div>
      )}
    </div>
  );
}

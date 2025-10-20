import {
  Text,
  ProgressBar,
  makeStyles,
  tokens,
} from "@fluentui/react-components";

interface ProgressDisplayProps {
  currentCalories: number;
  goalCalories: number | null | undefined;
}

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: "100%",
    gap: tokens.spacingVerticalM,
  },
  progressInfo: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    width: "100%",
  },
});

export function ProgressDisplay({
  currentCalories,
  goalCalories,
}: ProgressDisplayProps): JSX.Element {
  const styles = useStyles();
  const hasValidGoal = goalCalories && goalCalories > 0;
  const percentage = hasValidGoal
    ? Math.min(Math.round((currentCalories / goalCalories) * 100), 100)
    : 0;
  const value = hasValidGoal ? currentCalories / goalCalories : 0;

  if (!hasValidGoal) {
    return (
      <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
        Brak ustawionego celu kalorycznego. Ustaw cel w ustawieniach
        profilu.
      </Text>
    );
  }

  return (
    <div className={styles.container}>
      <ProgressBar value={value} style={{ height: "12px" }} />
      <div className={styles.progressInfo}>
        <Text
          size={300}
          weight="semibold"
          style={{ color: tokens.colorBrandForeground1 }}
        >
          {percentage}% celu
        </Text>
        {percentage < 100 && (
          <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
            Pozostało{" "}
            {(goalCalories - currentCalories).toLocaleString("pl-PL", {
              maximumFractionDigits: 0,
            })}{" "}
            kcal
          </Text>
        )}
        {percentage >= 100 && (
          <Text
            size={300}
            weight="semibold"
            style={{ color: tokens.colorBrandForeground1 }}
          >
            Cel osiągnięty! 🎉
          </Text>
        )}
      </div>
    </div>
  );
}

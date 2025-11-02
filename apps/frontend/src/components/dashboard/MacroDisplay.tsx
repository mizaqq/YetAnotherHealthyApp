import {
  Card,
  CardHeader,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { Food24Regular, DrinkBeer24Regular, FoodApple24Regular, Fire24Regular } from "@fluentui/react-icons";

interface MacroDisplayProps {
  macros: {
    protein: number;
    fat: number;
    carbs: number;
  };
  calories?: number;
  "data-testid"?: string;
}

const useStyles = makeStyles({
  card: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    ...shorthands.gap("16px"),
  },
  header: {
    paddingBottom: "0px",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
    ...shorthands.padding("0"),
    margin: "0",
  },
  listItem: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  macroInfo: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  macroValues: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "40px",
    height: "40px",
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
  protein: {
    backgroundColor: tokens.colorPaletteBlueBackground2,
    color: tokens.colorPaletteBlueForeground2,
  },
  fat: {
    backgroundColor: tokens.colorPaletteGreenBackground2,
    color: tokens.colorPaletteGreenForeground2,
  },
  carbs: {
    backgroundColor: tokens.colorPaletteYellowBackground2,
    color: tokens.colorPaletteYellowForeground2,
  },
  calories: {
    backgroundColor: tokens.colorPaletteRedBackground2,
    color: tokens.colorPaletteRedForeground2,
  },
});

export function MacroDisplay({ macros, calories, "data-testid": testId }: MacroDisplayProps) {
  const styles = useStyles();

  // Calculate total calories from macros if not provided
  const CALORIES_PER_GRAM_PROTEIN = 4;
  const CALORIES_PER_GRAM_FAT = 9;
  const CALORIES_PER_GRAM_CARBS = 4;

  const calculatedCalories =
    macros.protein * CALORIES_PER_GRAM_PROTEIN +
    macros.fat * CALORIES_PER_GRAM_FAT +
    macros.carbs * CALORIES_PER_GRAM_CARBS;

  const totalCalories = calories ?? calculatedCalories;

  const macroData = [
    ...(calories !== undefined
      ? [
          {
            name: "Kalorie",
            value: calories,
            icon: <Fire24Regular />,
            style: styles.calories,
            percentage: null,
            unit: "kcal",
          },
        ]
      : []),
    {
      name: "Białko",
      value: macros.protein,
      icon: <Food24Regular />,
      style: styles.protein,
      percentage:
        totalCalories > 0
          ? ((macros.protein * CALORIES_PER_GRAM_PROTEIN) / totalCalories) * 100
          : 0,
      unit: "g",
    },
    {
      name: "Tłuszcze",
      value: macros.fat,
      icon: <DrinkBeer24Regular />,
      style: styles.fat,
      percentage:
        totalCalories > 0
          ? ((macros.fat * CALORIES_PER_GRAM_FAT) / totalCalories) * 100
          : 0,
      unit: "g",
    },
    {
      name: "Węglowodany",
      value: macros.carbs,
      icon: <FoodApple24Regular />,
      style: styles.carbs,
      percentage:
        totalCalories > 0
          ? ((macros.carbs * CALORIES_PER_GRAM_CARBS) / totalCalories) * 100
          : 0,
      unit: "g",
    },
  ];

  return (
    <Card className={styles.card} data-testid={testId || "dashboard-macro-display"}>
      <CardHeader
        header={<Text size={500} weight="semibold">Makroskładniki</Text>}
        description={<Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>Dzisiejsze spożycie</Text>}
        className={styles.header}
      />
      <ul className={styles.list}>
        {macroData.map((macro) => (
          <li key={macro.name} className={styles.listItem}>
            <div className={styles.macroInfo}>
              <div className={`${styles.iconContainer} ${macro.style}`}>
                {macro.icon}
              </div>
              <Text size={400}>{macro.name}</Text>
            </div>
            <div className={styles.macroValues}>
              <Text size={400} weight="semibold">
                {macro.value.toFixed(macro.unit === "kcal" ? 0 : 1)}
                {macro.unit}
              </Text>
              {macro.percentage !== null && (
                <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                  {macro.percentage.toFixed(0)}%
                </Text>
              )}
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}


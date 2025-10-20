import {
  Card,
  CardHeader,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { useMealCategories } from "@/hooks/useMealCategories";
import type { Meal } from "@/types";

type MealListProps = {
  meals: Meal[];
  onMealClick?: (mealId: string) => void;
};

const useStyles = makeStyles({
  card: {
    paddingBottom: tokens.spacingVerticalL,
  },
  list: {
    listStyleType: "none",
    ...shorthands.padding(0),
    ...shorthands.margin(0),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  listItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    cursor: "pointer",
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    transitionProperty: "background-color",
    transitionDuration: tokens.durationNormal,
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
    ":active": {
      backgroundColor: tokens.colorNeutralBackground1Pressed,
    },
  },
  mealDetails: {
    display: "flex",
    flexDirection: "column",
  },
  mealMacros: {
    textAlign: "right",
  },
});

export function MealList({ meals, onMealClick }: MealListProps) {
  const styles = useStyles();
  const { categories, getCategoryLabel } = useMealCategories();

  const handleMealClick = (mealId: string) => {
    onMealClick?.(mealId);
  };

  // Sort meals by category sort_order
  const sortedMeals = [...meals].sort((a, b) => {
    const categoryA = categories.find((c) => c.code === a.category);
    const categoryB = categories.find((c) => c.code === b.category);
    const sortOrderA = categoryA?.sort_order ?? 999;
    const sortOrderB = categoryB?.sort_order ?? 999;
    return sortOrderA - sortOrderB;
  });

  return (
    <Card className={styles.card}>
      <CardHeader header={<Text size={500} weight="semibold">Dzisiejsze posiłki</Text>} />
      <ul className={styles.list}>
        {sortedMeals.map((meal) => (
          <li
            key={meal.id}
            className={styles.listItem}
            onClick={() => handleMealClick(meal.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleMealClick(meal.id);
              }
            }}
            role="button"
            tabIndex={0}
            aria-label={`Szczegóły posiłku: ${getCategoryLabel(meal.category)}`}
          >
            <div className={styles.mealDetails}>
              <Text as="h3" size={400} weight="semibold">
                {getCategoryLabel(meal.category)}
              </Text>
            </div>
            <div className={styles.mealMacros}>
              <Text weight="semibold">{meal.calories.toFixed(0)} kcal</Text>
              <Text as="p" size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                B: {(meal.protein ?? 0).toFixed(1)}g, T: {(meal.fat ?? 0).toFixed(1)}g, W:{" "}
                {(meal.carbs ?? 0).toFixed(1)}g
              </Text>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}


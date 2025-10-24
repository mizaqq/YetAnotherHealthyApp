import { Link } from "react-router-dom";
import { Card, Text, makeStyles, shorthands, tokens } from "@fluentui/react-components";
import {
  FoodRegular,
  ClockRegular,
  FireRegular,
} from "@fluentui/react-icons";
import type { MealListItemDTO } from "@/types";

const useStyles = makeStyles({
  card: {
    cursor: "pointer",
    transition: "all 0.2s ease-in-out",
    ":hover": {
      transform: "translateY(-2px)",
      boxShadow: tokens.shadow8,
    },
  },
  content: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  leftSection: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalM),
    flex: 1,
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "40px",
    height: "40px",
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground3,
  },
  mealInfo: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXXS),
  },
  timeContainer: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
  },
  caloriesContainer: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
    flexShrink: 0,
  },
  link: {
    textDecoration: "none",
    color: "inherit",
    display: "block",
  },
});

type MealListItemProps = {
  meal: MealListItemDTO;
};

/**
 * MealListItem represents a single meal in the history list
 * Shows meal category, time, and calories
 * Clickable to navigate to meal details
 */
export function MealListItem({ meal }: MealListItemProps) {
  const styles = useStyles();

  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString("pl-PL", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getCategoryLabel = (category: string): string => {
    const categoryMap: Record<string, string> = {
      breakfast: "Śniadanie",
      lunch: "Obiad",
      dinner: "Kolacja",
      snack: "Przekąska",
    };
    return categoryMap[category] || category;
  };

  return (
    <li>
      <Link to={`/meals/${meal.id}`} className={styles.link}>
        <Card className={styles.card}>
          <div className={styles.content}>
            <div className={styles.leftSection}>
              <div className={styles.iconContainer}>
                <FoodRegular />
              </div>
              <div className={styles.mealInfo}>
                <Text weight="semibold">{getCategoryLabel(meal.category)}</Text>
                <div className={styles.timeContainer}>
                  <ClockRegular fontSize={14} />
                  <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                    {formatTime(meal.eaten_at)}
                  </Text>
                </div>
              </div>
            </div>
            <div className={styles.caloriesContainer}>
              <FireRegular fontSize={20} style={{ color: tokens.colorPaletteDarkOrangeForeground1 }} />
              <Text weight="semibold" size={400}>
                {Math.round(meal.calories)} kcal
              </Text>
            </div>
          </div>
        </Card>
      </Link>
    </li>
  );
}


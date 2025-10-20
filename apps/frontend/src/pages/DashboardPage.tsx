import { lazy, Suspense, useState } from "react";
import { useDashboardData } from "@/hooks/useDashboardData";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorState } from "@/components/common/ErrorState";
import { MacroDisplay } from "@/components/dashboard/MacroDisplay";
import { MealList } from "@/components/dashboard/MealList";
import { EmptyState } from "@/components/dashboard/EmptyState";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { ChartSkeleton } from "@/components/dashboard/ChartSkeleton";
import { CalorieDisplay } from "@/components/dashboard/CalorieDisplay";
import { ProgressDisplay } from "@/components/dashboard/ProgressDisplay";
import { MealDetailsDialog } from "@/components/meal-details/MealDetailsDialog";
import { DashboardRefreshProvider } from "@/lib/DashboardRefreshContext";
import { toast } from "sonner";
import {
  Title1,
  Divider,
  Card,
  makeStyles,
  shorthands,
  tokens,
  Text,
} from "@fluentui/react-components";
import { CalendarLtr24Regular } from "@fluentui/react-icons";

// Lazy load heavy chart components
const WeeklyTrendChart = lazy(() =>
  import("@/components/dashboard/WeeklyTrendChart").then((module) => ({
    default: module.WeeklyTrendChart,
  }))
);

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  container: {
    maxWidth: "1280px",
    ...shorthands.margin("0", "auto"),
    ...shorthands.padding(tokens.spacingVerticalXXL, tokens.spacingHorizontalXXL),
  },
  header: {
    display: "flex",
    flexDirection: "column",
    "@media (min-width: 640px)": {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    ...shorthands.gap(tokens.spacingVerticalL),
    marginBottom: tokens.spacingVerticalXXL,
  },
  titleContainer: {
    ...shorthands.gap(tokens.spacingVerticalS),
    display: "flex",
    flexDirection: "column",
  },
  headerActions: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  dateContainer: {
    display: "flex",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    color: tokens.colorNeutralForeground2,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(1, 1fr)",
    gridAutoRows: "minmax(200px, auto)",
    "@media (min-width: 768px)": {
      gridTemplateColumns: "repeat(3, 1fr)",
    },
    ...shorthands.gap(tokens.spacingHorizontalL),
    marginBottom: tokens.spacingVerticalL,
  },
  dailyProgress: {
    gridColumn: "auto",
    "@media (min-width: 768px)": {
      gridColumn: "span 2",
    },
    "@media (min-width: 1024px)": {
      gridColumn: "span 2",
    },
  },
  dailyProgressCard: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
  progressDivider: {
    marginTop: tokens.spacingVerticalXXL,
    marginBottom: tokens.spacingVerticalS,
  },
  macroDisplay: {
    gridColumn: "auto",
  },
  weeklyTrend: {
    gridColumn: "auto",
    "@media (min-width: 768px)": {
      gridColumn: "span 3",
    },
    "@media (min-width: 1024px)": {
      gridColumn: "span 3",
    },
  },
  fullWidth: {
    gridColumn: "auto",
    "@media (min-width: 768px)": {
      gridColumn: "span 3",
    },
  },
});

/**
 * Main dashboard page showing daily progress, macros, weekly trend, and meals
 * Route: /
 */
export default function DashboardPage() {
  const styles = useStyles();
  const { dailySummary, weeklyTrend, isLoading, error, hasMeals, refetch } =
    useDashboardData();
  const [mealDetailsOpen, setMealDetailsOpen] = useState(false);
  const [selectedMealId, setSelectedMealId] = useState<string | null>(null);

  const handleMealClick = (mealId: string) => {
    setSelectedMealId(mealId);
    setMealDetailsOpen(true);
  };

  const handleMealDeleted = () => {
    void refetch();
    toast.success("Posiłek został usunięty");
  };

  return (
    <DashboardRefreshProvider refresh={refetch}>
      {/* Loading state */}
      {isLoading && (
        <div className={styles.root}>
          <div className={styles.container} aria-busy="true">
            <LoadingSpinner message="Ładowanie panelu..." />
          </div>
        </div>
      )}

      {/* Error state */}
      {!isLoading && error && (
        <div className={styles.root}>
          <div className={styles.container}>
            <ErrorState error={error} onRetry={refetch} />
          </div>
        </div>
      )}

      {/* No profile state */}
      {!isLoading && !error && !dailySummary && (
        <div className={styles.root}>
          <div className={styles.container}>
            <ErrorState
              message="Nie znaleziono profilu użytkownika. Uzupełnij swój profil, aby kontynuować."
              onRetry={refetch}
            />
          </div>
        </div>
      )}

      {/* Main content */}
      {!isLoading && !error && dailySummary && (
        <div className={styles.root}>
          <div className={styles.container}>
          {/* Header */}
          <header className={styles.header}>
            <div className={styles.titleContainer}>
              <Title1 as="h1">Dzisiaj</Title1>
              <div className={styles.dateContainer}>
                <CalendarLtr24Regular />
                <Text>
                  {new Date(dailySummary.date).toLocaleDateString("pl-PL", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </Text>
              </div>
            </div>
            <div className={styles.headerActions}>
              <ThemeToggle />
            </div>
          </header>

        <Divider />

        {/* Main content grid - 12 column layout */}
        <div className={styles.grid}>
          {/* Daily Progress Chart - 8 cols on md+ */}
          <div className={styles.dailyProgress}>
            <Card className={styles.dailyProgressCard}>
              <CalorieDisplay
                currentCalories={dailySummary.totals.calories}
                goalCalories={dailySummary.calorie_goal}
              />
              <Divider className={styles.progressDivider} />
              <ProgressDisplay
                currentCalories={dailySummary.totals.calories}
                goalCalories={dailySummary.calorie_goal}
              />
            </Card>
          </div>

          {/* Macro Display - 4 cols on md+ */}
          <div className={styles.macroDisplay}>
            <MacroDisplay
              macros={{
                protein: dailySummary.totals.protein,
                fat: dailySummary.totals.fat,
                carbs: dailySummary.totals.carbs,
              }}
            />
          </div>

          {/* Weekly Trend Chart - full width */}
          {weeklyTrend && (
            <div className={styles.weeklyTrend}>
              <Suspense fallback={<ChartSkeleton />}>
                <WeeklyTrendChart data={weeklyTrend.points} />
              </Suspense>
            </div>
          )}
        </div>

        <Divider />

        {/* Meals section - full width */}
        <div className={styles.fullWidth}>
          {hasMeals ? (
            <MealList meals={dailySummary.meals} onMealClick={handleMealClick} />
          ) : (
            <EmptyState />
          )}
        </div>
        </div>
      </div>
      )}

      {/* Meal Details Dialog */}
      <MealDetailsDialog
        open={mealDetailsOpen}
        mealId={selectedMealId}
        onOpenChange={setMealDetailsOpen}
        onDeleted={handleMealDeleted}
      />
    </DashboardRefreshProvider>
  );
}


import { lazy, Suspense, useState, useEffect } from "react";
import {
  Title1,
  Divider,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { getWeeklyTrend } from "@/lib/api";
import { MealHistoryList } from "@/components/history/MealHistoryList";
import { ErrorState } from "@/components/common/ErrorState";
import { ChartSkeleton } from "@/components/dashboard/ChartSkeleton";
import type { WeeklyTrendReportDTO } from "@/types";

// Lazy load chart component for better performance
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
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  header: {
    marginBottom: tokens.spacingVerticalL,
  },
  chartSection: {
    marginBottom: tokens.spacingVerticalL,
  },
});

/**
 * HistoryPage displays a chronological list of all user's meals
 * with weekly trend chart at the top and infinite scroll for the meal list
 * Route: /history
 */
export default function HistoryPage() {
  const styles = useStyles();
  const [weeklyTrend, setWeeklyTrend] = useState<WeeklyTrendReportDTO | null>(null);
  const [isLoadingTrend, setIsLoadingTrend] = useState(true);
  const [trendError, setTrendError] = useState<Error | null>(null);

  // Fetch weekly trend data
  useEffect(() => {
    const fetchTrendData = async () => {
      setIsLoadingTrend(true);
      setTrendError(null);

      try {
        const data = await getWeeklyTrend();
        setWeeklyTrend(data);
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to fetch weekly trend");
        setTrendError(error);
        console.error("Failed to fetch weekly trend:", error);
      } finally {
        setIsLoadingTrend(false);
      }
    };

    void fetchTrendData();
  }, []);

  const handleTrendRetry = () => {
    void (async () => {
      setIsLoadingTrend(true);
      setTrendError(null);
      try {
        const data = await getWeeklyTrend();
        setWeeklyTrend(data);
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to fetch weekly trend");
        setTrendError(error);
      } finally {
        setIsLoadingTrend(false);
      }
    })();
  };

  return (
    <div className={styles.root}>
      <div className={styles.container}>
        {/* Header */}
        <header className={styles.header}>
          <Title1 as="h1">Historia</Title1>
        </header>

        <Divider />

        {/* Weekly Trend Chart Section */}
        <section className={styles.chartSection} aria-label="Trend tygodniowy">
          {isLoadingTrend && <ChartSkeleton />}
          
          {!isLoadingTrend && trendError && (
            <ErrorState
              error={trendError}
              onRetry={handleTrendRetry}
              message="Nie udało się załadować trendu."
            />
          )}
          
          {!isLoadingTrend && !trendError && weeklyTrend && (
            <Suspense fallback={<ChartSkeleton />}>
              <WeeklyTrendChart data={weeklyTrend.points} />
            </Suspense>
          )}
        </section>

        <Divider />

        {/* Meal History List Section */}
        <section aria-label="Historia posiłków">
          <MealHistoryList />
        </section>
      </div>
    </div>
  );
}



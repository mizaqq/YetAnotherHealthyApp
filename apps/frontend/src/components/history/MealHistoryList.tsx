import { Text, makeStyles, shorthands, tokens } from "@fluentui/react-components";
import { useMealHistory } from "@/hooks/useMealHistory";
import { DateGroupHeader } from "./DateGroupHeader";
import { MealListItem } from "./MealListItem";
import { InfiniteScrollLoader } from "./InfiniteScrollLoader";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorState } from "@/components/common/ErrorState";

const useStyles = makeStyles({
  list: {
    listStyle: "none",
    ...shorthands.padding(0),
    ...shorthands.margin(0),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding(tokens.spacingVerticalXXXL),
    ...shorthands.gap(tokens.spacingVerticalM),
    textAlign: "center",
  },
  mealGroup: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
});

/**
 * MealHistoryList manages and displays the paginated, grouped list of meals
 * Uses infinite scroll for loading more meals
 */
export function MealHistoryList() {
  const styles = useStyles();
  const { groupedMeals, isLoading, error, hasMore, loadMoreMeals, isLoadingMore } = useMealHistory();

  // Initial loading state
  if (isLoading) {
    return <LoadingSpinner message="Ładowanie historii posiłków..." />;
  }

  // Error state
  if (error && groupedMeals.length === 0) {
    return (
      <ErrorState
        error={error}
        onRetry={() => window.location.reload()}
        message="Nie udało się załadować historii posiłków."
      />
    );
  }

  // Empty state
  if (groupedMeals.length === 0) {
    return (
      <div className={styles.emptyState}>
        <Text size={500} weight="semibold">
          Nie masz jeszcze żadnych zapisanych posiłków
        </Text>
        <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
          Dodaj swój pierwszy posiłek, aby zobaczyć go tutaj
        </Text>
      </div>
    );
  }

  // Main content with grouped meals
  return (
    <>
      <ul className={styles.list}>
        {groupedMeals.map((group) => (
          <li key={group.date} className={styles.mealGroup}>
            <DateGroupHeader date={group.date} />
            <ul className={styles.list}>
              {group.meals.map((meal) => (
                <MealListItem key={meal.id} meal={meal} />
              ))}
            </ul>
          </li>
        ))}
      </ul>
      
      {/* Infinite scroll loader */}
      <InfiniteScrollLoader
        onLoadMore={loadMoreMeals}
        isLoading={isLoadingMore}
        hasMore={hasMore}
        error={error && groupedMeals.length > 0 ? error : null}
      />
    </>
  );
}


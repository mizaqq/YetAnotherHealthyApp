import { useState, useEffect, useCallback } from "react";
import { getMeals } from "@/lib/api";
import { groupMealsByDate } from "@/components/history/utils";
import type { MealListItemDTO, GroupedMealViewModel } from "@/types";

const PAGE_SIZE = 20;

type UseMealHistoryReturn = {
  groupedMeals: GroupedMealViewModel[];
  isLoading: boolean;
  error: Error | null;
  hasMore: boolean;
  loadMoreMeals: () => void;
  isLoadingMore: boolean;
};

/**
 * Custom hook for managing meal history with pagination and grouping
 * Handles fetching, infinite scroll, and date-based grouping of meals
 */
export function useMealHistory(): UseMealHistoryReturn {
  const [allMeals, setAllMeals] = useState<MealListItemDTO[]>([]);
  const [groupedMeals, setGroupedMeals] = useState<GroupedMealViewModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);

  // Initial fetch
  const fetchInitialMeals = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getMeals(PAGE_SIZE);
      setAllMeals(response.data);
      setNextCursor(response.page.after ?? null);
      setHasMore(Boolean(response.page.after));
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to fetch meals");
      setError(error);
      console.error("Failed to fetch initial meals:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load more meals (pagination)
  const loadMoreMeals = useCallback(async () => {
    if (!hasMore || isLoadingMore || isLoading) {
      return;
    }

    setIsLoadingMore(true);
    setError(null);

    try {
      const response = await getMeals(PAGE_SIZE, nextCursor);
      setAllMeals((prev) => [...prev, ...response.data]);
      setNextCursor(response.page.after ?? null);
      setHasMore(Boolean(response.page.after));
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to load more meals");
      setError(error);
      console.error("Failed to load more meals:", error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, isLoading, nextCursor]);

  // Group meals whenever allMeals changes
  useEffect(() => {
    if (allMeals.length > 0) {
      const grouped = groupMealsByDate(allMeals);
      setGroupedMeals(grouped);
    } else {
      setGroupedMeals([]);
    }
  }, [allMeals]);

  // Fetch initial data on mount
  useEffect(() => {
    void fetchInitialMeals();
  }, [fetchInitialMeals]);

  return {
    groupedMeals,
    isLoading,
    error,
    hasMore,
    loadMoreMeals: () => { void loadMoreMeals(); },
    isLoadingMore,
  };
}


import { useState, useEffect, useCallback } from "react";
import { getMealCategories } from "@/lib/api";
import type { MealCategoryDTO } from "@/types";

type UseMealCategoriesState = {
  categories: MealCategoryDTO[];
  isLoading: boolean;
  error: string | null;
};

/**
 * Hook to fetch and cache meal categories
 * Returns categories with helper function to get label by code
 */
export function useMealCategories() {
  const [state, setState] = useState<UseMealCategoriesState>({
    categories: [],
    isLoading: false,
    error: null,
  });

  const fetchCategories = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const categoriesData = await getMealCategories();
      // Sort by sort_order ascending
      const sortedCategories = [...categoriesData].sort(
        (a, b) => a.sort_order - b.sort_order
      );
      setState({ categories: sortedCategories, isLoading: false, error: null });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Nie udało się pobrać kategorii";
      setState({ categories: [], isLoading: false, error: errorMessage });
    }
  }, []);

  useEffect(() => {
    void fetchCategories();
  }, [fetchCategories]);

  /**
   * Get category label by code
   * @param code Category code (e.g. 'breakfast', 'lunch')
   * @returns Localized label or code if not found
   */
  const getCategoryLabel = useCallback(
    (code: string): string => {
      const category = state.categories.find((c) => c.code === code);
      return category?.label ?? code;
    },
    [state.categories]
  );

  return {
    categories: state.categories,
    isLoading: state.isLoading,
    error: state.error,
    getCategoryLabel,
    refetch: fetchCategories,
  };
}


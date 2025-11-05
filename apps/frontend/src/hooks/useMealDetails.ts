import { useState, useCallback, useEffect } from "react";
import { getMealDetail } from "@/lib/api";
import type { MealDetailDTO } from "@/types";

type UseMealDetailsState = {
  mealDetails: MealDetailDTO | null;
  isLoading: boolean;
  error: string | null;
};

export function useMealDetails(mealId: string | null) {
  const [state, setState] = useState<UseMealDetailsState>({
    mealDetails: null,
    isLoading: false,
    error: null,
  });

  const fetchMealDetails = useCallback(async () => {
    if (!mealId) {
      setState({ mealDetails: null, isLoading: false, error: null });
      return;
    }

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const details = await getMealDetail(mealId);
      setState({ mealDetails: details, isLoading: false, error: null });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Nie udało się pobrać szczegółów posiłku";
      setState({ mealDetails: null, isLoading: false, error: errorMessage });
    }
  }, [mealId]);

  useEffect(() => {
    void fetchMealDetails();
  }, [fetchMealDetails]);

  return {
    mealDetails: state.mealDetails,
    isLoading: state.isLoading,
    error: state.error,
    refetch: fetchMealDetails,
  };
}


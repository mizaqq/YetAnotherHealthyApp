import { useState, useCallback } from "react";
import { toast } from "sonner";
import {
  getMealCategories,
  createAnalysisRun,
  getAnalysisRunItems,
  retryAnalysisRun,
  cancelAnalysisRun,
  createMeal,
} from "@/lib/api";
import type {
  MealCategoryDTO,
  MealInputFormViewModel,
  AnalysisResultsViewModel,
} from "@/types";

type StepType = "input" | "loading" | "results";

type UseAddMealStepperState = {
  step: StepType;
  formData: MealInputFormViewModel;
  analysisRunId: string | null;
  analysisResults: AnalysisResultsViewModel | null;
  error: string | null;
  isSubmitting: boolean;
  categories: MealCategoryDTO[];
  isCategoriesLoading: boolean;
};

const initialFormData: MealInputFormViewModel = {
  category: "",
  description: "",
  isManualMode: false,
  manualCalories: null,
};

export function useAddMealStepper() {
  const [state, setState] = useState<UseAddMealStepperState>({
    step: "input",
    formData: initialFormData,
    analysisRunId: null,
    analysisResults: null,
    error: null,
    isSubmitting: false,
    categories: [],
    isCategoriesLoading: true,
  });

  // Load categories on mount
  const loadCategories = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, isCategoriesLoading: true, error: null }));
      const categories = await getMealCategories();
      setState((prev) => ({ ...prev, categories, isCategoriesLoading: false }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Nie udało się pobrać kategorii";
      setState((prev) => ({
        ...prev,
        error: errorMessage,
        isCategoriesLoading: false,
      }));
      toast.error(errorMessage);
    }
  }, []);

  // Start AI analysis
  const handleStartAnalysis = useCallback(
    async (data: MealInputFormViewModel) => {
      try {
        setState((prev) => ({
          ...prev,
          formData: data,
          step: "loading",
          error: null,
          isSubmitting: true,
        }));

        const analysisRun = await createAnalysisRun({
          input_text: data.description,
          meal_id: null,
        });

        // Fetch analysis items
        const analysisItems = await getAnalysisRunItems(analysisRun.id);

        // Calculate totals from items
        const totals = analysisItems.items.reduce(
          (acc, item) => ({
            calories: acc.calories + (item.calories ?? 0),
            protein: acc.protein + (item.protein ?? 0),
            fat: acc.fat + (item.fat ?? 0),
            carbs: acc.carbs + (item.carbs ?? 0),
          }),
          { calories: 0, protein: 0, fat: 0, carbs: 0 }
        );

        setState((prev) => ({
          ...prev,
          step: "results",
          analysisRunId: analysisRun.id,
          analysisResults: {
            runId: analysisRun.id,
            totals,
            items: analysisItems.items,
          },
          isSubmitting: false,
        }));
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Nie udało się przeanalizować posiłku";
        setState((prev) => ({
          ...prev,
          step: "input",
          error: errorMessage,
          isSubmitting: false,
        }));
        toast.error(errorMessage);
      }
    },
    []
  );

  // Accept AI results and create meal
  const handleAcceptResults = useCallback(async () => {
    if (!state.analysisResults || !state.analysisRunId) {
      toast.error("Brak wyników analizy do zaakceptowania");
      return;
    }

    try {
      setState((prev) => ({ ...prev, isSubmitting: true, error: null }));

      await createMeal({
        category: state.formData.category,
        eaten_at: new Date().toISOString(),
        source: "ai",
        calories: state.analysisResults.totals.calories,
        protein: state.analysisResults.totals.protein,
        fat: state.analysisResults.totals.fat,
        carbs: state.analysisResults.totals.carbs,
        analysis_run_id: state.analysisRunId,
      });

      toast.success("Posiłek został dodany");
      
      // Reset state after success
      setState({
        step: "input",
        formData: initialFormData,
        analysisRunId: null,
        analysisResults: null,
        error: null,
        isSubmitting: false,
        categories: state.categories,
        isCategoriesLoading: false,
      });

      return true; // Signal success to parent
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Nie udało się zapisać posiłku";
      setState((prev) => ({ ...prev, error: errorMessage, isSubmitting: false }));
      toast.error(errorMessage);
      return false;
    }
  }, [state.analysisResults, state.analysisRunId, state.formData.category, state.categories]);

  // Retry analysis with same or modified input
  const handleRetryAnalysis = useCallback(async () => {
    if (!state.analysisRunId) {
      toast.error("Brak analizy do ponowienia");
      return;
    }

    try {
      setState((prev) => ({ ...prev, step: "loading", error: null, isSubmitting: true }));

      const analysisRun = await retryAnalysisRun(state.analysisRunId, {});

      // Fetch new analysis items
      const analysisItems = await getAnalysisRunItems(analysisRun.id);

      // Calculate totals from items
      const totals = analysisItems.items.reduce(
        (acc, item) => ({
          calories: acc.calories + (item.calories ?? 0),
          protein: acc.protein + (item.protein ?? 0),
          fat: acc.fat + (item.fat ?? 0),
          carbs: acc.carbs + (item.carbs ?? 0),
        }),
        { calories: 0, protein: 0, fat: 0, carbs: 0 }
      );

      setState((prev) => ({
        ...prev,
        step: "results",
        analysisRunId: analysisRun.id,
        analysisResults: {
          runId: analysisRun.id,
          totals,
          items: analysisItems.items,
        },
        isSubmitting: false,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Nie udało się ponowić analizy";
      setState((prev) => ({
        ...prev,
        step: "input",
        error: errorMessage,
        isSubmitting: false,
      }));
      toast.error(errorMessage);
    }
  }, [state.analysisRunId]);

  // Create manual meal without AI analysis
  const handleCreateManualMeal = useCallback(
    async (data: MealInputFormViewModel) => {
      if (!data.manualCalories || data.manualCalories <= 0) {
        toast.error("Podaj prawidłową wartość kalorii");
        return false;
      }

      try {
        setState((prev) => ({ ...prev, isSubmitting: true, error: null }));

        await createMeal({
          category: data.category,
          eaten_at: new Date().toISOString(),
          source: "manual",
          calories: data.manualCalories,
        });

        toast.success("Posiłek został dodany");

        // Reset state after success
        setState((prev) => ({
          step: "input",
          formData: initialFormData,
          analysisRunId: null,
          analysisResults: null,
          error: null,
          isSubmitting: false,
          categories: prev.categories,
          isCategoriesLoading: false,
        }));

        return true; // Signal success to parent
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Nie udało się zapisać posiłku";
        setState((prev) => ({ ...prev, error: errorMessage, isSubmitting: false }));
        toast.error(errorMessage);
        return false;
      }
    },
    []
  );

  // Cancel ongoing analysis
  const handleCancel = useCallback(async () => {
    if (state.analysisRunId && state.step === "loading") {
      try {
        await cancelAnalysisRun(state.analysisRunId);
      } catch (error) {
        // Log but don't block cancellation
        console.error("Failed to cancel analysis run:", error);
      }
    }

    setState((prev) => ({
      ...prev,
      step: "input",
      analysisRunId: null,
      analysisResults: null,
      error: null,
      isSubmitting: false,
    }));
  }, [state.analysisRunId, state.step]);

  // Reset to initial state
  const handleReset = useCallback(() => {
    setState((prev) => ({
      step: "input",
      formData: initialFormData,
      analysisRunId: null,
      analysisResults: null,
      error: null,
      isSubmitting: false,
      categories: prev.categories,
      isCategoriesLoading: false,
    }));
  }, []);

  return {
    step: state.step,
    formData: state.formData,
    analysisResults: state.analysisResults,
    error: state.error,
    isSubmitting: state.isSubmitting,
    categories: state.categories,
    isCategoriesLoading: state.isCategoriesLoading,
    loadCategories,
    handleStartAnalysis,
    handleAcceptResults,
    handleRetryAnalysis,
    handleCreateManualMeal,
    handleCancel,
    handleReset,
  };
}


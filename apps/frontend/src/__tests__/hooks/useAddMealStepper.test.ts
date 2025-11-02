import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAddMealStepper } from '@/hooks/useAddMealStepper';
import * as api from '@/lib/api';
import { toast } from 'sonner';
import { setDeterministicDate, restoreRealTimers } from '../test-utils';
import type {
  MealCategoryDTO,
  AnalysisRunDetailDTO,
  AnalysisRunItemsDTO,
  MealListItemDTO,
} from '@/types';

// Mock dependencies
vi.mock('@/lib/api');
vi.mock('sonner');

describe('useAddMealStepper', () => {
  const mockCategories: MealCategoryDTO[] = [
    { code: 'breakfast', locale: 'pl', label: 'Śniadanie' },
    { code: 'lunch', locale: 'pl', label: 'Obiad' },
  ];

  const mockAnalysisRun: AnalysisRunDetailDTO = {
    id: 'run-123',
    user_id: 'user-1',
    meal_id: null,
    status: 'completed',
    raw_input: '2 jajka',
    created_at: '2025-01-15T12:00:00Z',
    started_at: '2025-01-15T12:00:01Z',
    completed_at: '2025-01-15T12:00:05Z',
  };

  const mockAnalysisItems: AnalysisRunItemsDTO = {
    run_id: 'run-123',
    items: [
      {
        id: 'item-1',
        analysis_run_id: 'run-123',
        ordinal: 1,
        raw_name: 'Jajka',
        matched_product_id: 'product-1',
        weight_grams: 100,
        calories: 155.567, // Will be rounded to 2 decimals
        protein: 13.234,
        fat: 11.789,
        carbs: 1.123,
        confidence: 0.95,
        created_at: '2025-01-15T12:00:00Z',
      },
      {
        id: 'item-2',
        analysis_run_id: 'run-123',
        ordinal: 2,
        raw_name: 'Chleb',
        matched_product_id: 'product-2',
        weight_grams: 50,
        calories: 130.999,
        protein: 4.567,
        fat: 1.234,
        carbs: 24.876,
        confidence: 0.85,
        created_at: '2025-01-15T12:00:00Z',
      },
    ],
  };

  const mockMeal: MealListItemDTO = {
    id: 'meal-1',
    user_id: 'user-1',
    category: 'breakfast',
    eaten_at: '2025-01-15T12:00:00.000Z',
    source: 'ai',
    calories: 286.57,
    protein: 17.8,
    fat: 13.02,
    carbs: 26,
    analysis_run_id: 'run-123',
    created_at: '2025-01-15T12:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    setDeterministicDate('2025-01-15T12:00:00.000Z');
  });

  afterEach(() => {
    restoreRealTimers();
  });

  describe('initial state', () => {
    it('should initialize with correct default state', () => {
      const { result } = renderHook(() => useAddMealStepper());

      expect(result.current.step).toBe('input');
      expect(result.current.isSubmitting).toBe(false);
      expect(result.current.isCategoriesLoading).toBe(true);
      expect(result.current.categories).toEqual([]);
      expect(result.current.analysisResults).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.formData).toEqual({
        category: '',
        description: '',
        isManualMode: false,
        manualCalories: null,
      });
    });
  });

  describe('loadCategories', () => {
    it('should load categories successfully', async () => {
      vi.mocked(api.getMealCategories).mockResolvedValue(mockCategories);

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.loadCategories();
      });

      expect(api.getMealCategories).toHaveBeenCalledTimes(1);
      expect(result.current.categories).toEqual(mockCategories);
      expect(result.current.isCategoriesLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle error when loading categories fails', async () => {
      const errorMessage = 'Failed to fetch categories';
      vi.mocked(api.getMealCategories).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.loadCategories();
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isCategoriesLoading).toBe(false);
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });

    it('should handle non-Error exceptions', async () => {
      vi.mocked(api.getMealCategories).mockRejectedValue('String error');

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.loadCategories();
      });

      expect(result.current.error).toBe('Nie udało się pobrać kategorii');
      expect(toast.error).toHaveBeenCalledWith('Nie udało się pobrać kategorii');
    });
  });

  describe('handleStartAnalysis', () => {
    it('should start analysis and calculate rounded totals', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      const { result } = renderHook(() => useAddMealStepper());

      const formData = {
        category: 'breakfast',
        description: '2 jajka',
        isManualMode: false,
        manualCalories: null,
      };

      await act(async () => {
        await result.current.handleStartAnalysis(formData);
      });

      expect(api.createAnalysisRun).toHaveBeenCalledWith({
        input_text: '2 jajka',
        meal_id: null,
      });
      expect(api.getAnalysisRunItems).toHaveBeenCalledWith('run-123');
      
      expect(result.current.step).toBe('results');
      expect(result.current.analysisResults).toBeDefined();
      
      // Check that totals are summed and rounded to 2 decimal places
      const totals = result.current.analysisResults!.totals;
      expect(totals.calories).toBeCloseTo(286.57, 2); // 155.567 + 130.999 rounded
      expect(totals.protein).toBeCloseTo(17.8, 2); // 13.234 + 4.567 rounded
      expect(totals.fat).toBeCloseTo(13.02, 2); // 11.789 + 1.234 rounded
      expect(totals.carbs).toBeCloseTo(26, 2); // 1.123 + 24.876 rounded
      
      expect(result.current.analysisResults!.items).toEqual(mockAnalysisItems.items);
      expect(result.current.isSubmitting).toBe(false);
    });

    it('should transition to loading step before analysis', () => {
      vi.mocked(api.createAnalysisRun).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockAnalysisRun), 100))
      );

      const { result } = renderHook(() => useAddMealStepper());

      const formData = {
        category: 'breakfast',
        description: '2 jajka',
        isManualMode: false,
        manualCalories: null,
      };

      act(() => {
        void result.current.handleStartAnalysis(formData);
      });

      // Should immediately transition to loading
      expect(result.current.step).toBe('loading');
      expect(result.current.isSubmitting).toBe(true);
    });

    it('should handle analysis error and return to input step', async () => {
      const errorMessage = 'Analysis failed';
      vi.mocked(api.createAnalysisRun).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAddMealStepper());

      const formData = {
        category: 'breakfast',
        description: '2 jajka',
        isManualMode: false,
        manualCalories: null,
      };

      await act(async () => {
        await result.current.handleStartAnalysis(formData);
      });

      expect(result.current.step).toBe('input');
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isSubmitting).toBe(false);
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });

    it('should store form data when starting analysis', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      const { result } = renderHook(() => useAddMealStepper());

      const formData = {
        category: 'lunch',
        description: 'pizza',
        isManualMode: false,
        manualCalories: null,
      };

      await act(async () => {
        await result.current.handleStartAnalysis(formData);
      });

      expect(result.current.formData).toEqual(formData);
    });
  });

  describe('handleRetryAnalysis', () => {
    it('should show toast error when analysisRunId is missing', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.handleRetryAnalysis();
      });

      expect(toast.error).toHaveBeenCalledWith('Brak analizy do ponowienia');
      expect(api.retryAnalysisRun).not.toHaveBeenCalled();
    });

    it('should retry analysis with existing runId', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);
      vi.mocked(api.retryAnalysisRun).mockResolvedValue(mockAnalysisRun);

      const { result } = renderHook(() => useAddMealStepper());

      // First start an analysis to get a runId
      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      // Clear mock calls from initial analysis
      vi.clearAllMocks();
      vi.mocked(api.retryAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      // Now retry
      await act(async () => {
        await result.current.handleRetryAnalysis();
      });

      expect(api.retryAnalysisRun).toHaveBeenCalledWith('run-123', {});
      expect(api.getAnalysisRunItems).toHaveBeenCalledWith('run-123');
      expect(result.current.step).toBe('results');
      expect(result.current.analysisResults).toBeDefined();
    });

    it('should recalculate and round macros on retry', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);
      vi.mocked(api.retryAnalysisRun).mockResolvedValue(mockAnalysisRun);

      const { result } = renderHook(() => useAddMealStepper());

      // Start analysis
      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      // Retry
      await act(async () => {
        await result.current.handleRetryAnalysis();
      });

      const totals = result.current.analysisResults!.totals;
      expect(totals.calories).toBeCloseTo(286.57, 2);
      expect(totals.protein).toBeCloseTo(17.8, 2);
      expect(totals.fat).toBeCloseTo(13.02, 2);
      expect(totals.carbs).toBeCloseTo(26, 2);
    });

    it('should handle retry error', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      const { result } = renderHook(() => useAddMealStepper());

      // Start analysis
      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      // Mock retry failure
      const errorMessage = 'Retry failed';
      vi.mocked(api.retryAnalysisRun).mockRejectedValue(new Error(errorMessage));

      await act(async () => {
        await result.current.handleRetryAnalysis();
      });

      expect(result.current.step).toBe('input');
      expect(result.current.error).toBe(errorMessage);
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });
  });

  describe('handleAcceptResults', () => {
    it('should show toast error when results are missing', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        const success = await result.current.handleAcceptResults();
        expect(success).toBeUndefined();
      });

      expect(toast.error).toHaveBeenCalledWith('Brak wyników analizy do zaakceptowania');
      expect(api.createMeal).not.toHaveBeenCalled();
    });

    it('should create meal with AI source and rounded macros', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);
      vi.mocked(api.createMeal).mockResolvedValue(mockMeal);

      const { result } = renderHook(() => useAddMealStepper());

      // Start analysis first
      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      // Accept results
      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleAcceptResults();
      });

      expect(success).toBe(true);
      expect(api.createMeal).toHaveBeenCalledWith({
        category: 'breakfast',
        eaten_at: '2025-01-15T12:00:00.000Z',
        source: 'ai',
        calories: expect.closeTo(286.57, 2) as number,
        protein: expect.closeTo(17.8, 2) as number,
        fat: expect.closeTo(13.02, 2) as number,
        carbs: expect.closeTo(26, 2) as number,
        analysis_run_id: 'run-123',
      });
      expect(toast.success).toHaveBeenCalledWith('Posiłek został dodany');
    });

    it('should reset state after successful meal creation', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);
      vi.mocked(api.createMeal).mockResolvedValue(mockMeal);

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      await act(async () => {
        await result.current.handleAcceptResults();
      });

      expect(result.current.step).toBe('input');
      expect(result.current.analysisResults).toBeFalsy();
      expect(result.current.analysisRunId).toBeFalsy();
      expect(result.current.error).toBeFalsy();
      expect(result.current.isSubmitting).toBe(false);
    });

    it('should handle meal creation error', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      const errorMessage = 'Failed to create meal';
      vi.mocked(api.createMeal).mockRejectedValue(new Error(errorMessage));

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleAcceptResults();
      });

      expect(success).toBe(false);
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isSubmitting).toBe(false);
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });
  });

  describe('handleCreateManualMeal', () => {
    it('should show toast error when manualCalories is null', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: null,
        });
      });

      expect(success).toBe(false);
      expect(toast.error).toHaveBeenCalledWith('Podaj prawidłową wartość kalorii');
      expect(api.createMeal).not.toHaveBeenCalled();
    });

    it('should show toast error when manualCalories is 0', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: 0,
        });
      });

      expect(success).toBe(false);
      expect(toast.error).toHaveBeenCalledWith('Podaj prawidłową wartość kalorii');
    });

    it('should show toast error when manualCalories is negative', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: -10,
        });
      });

      expect(success).toBe(false);
      expect(toast.error).toHaveBeenCalledWith('Podaj prawidłową wartość kalorii');
    });

    it('should create meal with manual source and calories only', async () => {
      vi.mocked(api.createMeal).mockResolvedValue(mockMeal);

      const { result } = renderHook(() => useAddMealStepper());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: 650,
        });
      });

      expect(success).toBe(true);
      expect(api.createMeal).toHaveBeenCalledWith({
        category: 'lunch',
        eaten_at: '2025-01-15T12:00:00.000Z',
        source: 'manual',
        calories: 650,
      });
      expect(toast.success).toHaveBeenCalledWith('Posiłek został dodany');
    });

    it('should reset state after successful manual meal creation', async () => {
      vi.mocked(api.createMeal).mockResolvedValue(mockMeal);

      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: 650,
        });
      });

      expect(result.current.step).toBe('input');
      expect(result.current.formData).toEqual({
        category: '',
        description: '',
        isManualMode: false,
        manualCalories: null,
      });
      expect(result.current.isSubmitting).toBe(false);
    });

    it('should handle manual meal creation error', async () => {
      const errorMessage = 'Failed to create meal';
      vi.mocked(api.createMeal).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAddMealStepper());

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.handleCreateManualMeal({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: 650,
        });
      });

      expect(success).toBe(false);
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.isSubmitting).toBe(false);
      expect(toast.error).toHaveBeenCalledWith(errorMessage);
    });
  });

  describe('handleCancel', () => {
    it('should cancel analysis run when analysisRunId exists', async () => {
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);
      vi.mocked(api.cancelAnalysisRun).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAddMealStepper());

      // Start analysis and wait for completion
      act(() => {
        void result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      // Wait for analysis to complete
      await waitFor(() => expect(result.current.step).toBe('results'));

      // Verify analysis completed successfully
      expect(result.current.analysisResults).toBeDefined();
      expect(result.current.step).toBe('results');

      // Now cancel (analysis is complete but runId should still exist)
      await act(async () => {
        await result.current.handleCancel();
      });

      // Verify cancel was called and state was reset
      expect(api.cancelAnalysisRun).toHaveBeenCalledWith('run-123');
      expect(result.current.step).toBe('input');
      expect(result.current.analysisResults).toBeFalsy();
      expect(result.current.analysisRunId).toBeFalsy();
    });

    it('should not call cancelAnalysisRun when no analysisRunId exists', async () => {
      const { result } = renderHook(() => useAddMealStepper());

      await act(async () => {
        await result.current.handleCancel();
      });

      expect(api.cancelAnalysisRun).not.toHaveBeenCalled();
      expect(result.current.step).toBe('input');
    });
  });

  describe('handleReset', () => {
    it('should reset all state to initial values except categories', async () => {
      vi.mocked(api.getMealCategories).mockResolvedValue(mockCategories);
      vi.mocked(api.createAnalysisRun).mockResolvedValue(mockAnalysisRun);
      vi.mocked(api.getAnalysisRunItems).mockResolvedValue(mockAnalysisItems);

      const { result } = renderHook(() => useAddMealStepper());

      // Load categories
      await act(async () => {
        await result.current.loadCategories();
      });

      // Start analysis
      await act(async () => {
        await result.current.handleStartAnalysis({
          category: 'breakfast',
          description: '2 jajka',
          isManualMode: false,
          manualCalories: null,
        });
      });

      expect(result.current.step).toBe('results');
      expect(result.current.analysisResults).not.toBeNull();

      // Reset
      act(() => {
        result.current.handleReset();
      });

      expect(result.current.step).toBe('input');
      expect(result.current.formData).toEqual({
        category: '',
        description: '',
        isManualMode: false,
        manualCalories: null,
      });
      expect(result.current.analysisRunId).toBeFalsy();
      expect(result.current.analysisResults).toBeFalsy();
      expect(result.current.error).toBeFalsy();
      expect(result.current.isSubmitting).toBe(false);
      
      // Categories should be preserved
      expect(result.current.categories).toEqual(mockCategories);
      expect(result.current.isCategoriesLoading).toBe(false);
    });
  });
});


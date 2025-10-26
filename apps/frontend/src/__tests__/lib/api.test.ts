import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createMockFetchResponse, createMockSession } from '../test-utils';
import type {
  ProfileDTO,
  MealCategoryDTO,
  AnalysisRunDetailDTO,
  AnalysisRunItemsDTO,
  MealListItemDTO,
  MealDetailDTO,
  DailySummaryReportDTO,
  WeeklyTrendReportDTO,
} from '@/types';

// Mock supabase client before importing api
vi.mock('@/lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
    },
  },
}));

// Import after mocking
import * as api from '@/lib/api';
import { supabase } from '@/lib/supabaseClient';

// Extract the mock function after import
const mockGetSession = vi.mocked(supabase.auth.getSession);

describe('API Client', () => {
  const mockFetch = vi.fn();
  const mockSession = createMockSession('test-token-123');

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = mockFetch;
    
    // Mock getSession to return test session
    mockGetSession.mockResolvedValue({
      data: { session: mockSession },
      error: null,
    });
    
    // Set window.location.origin for URL construction
    Object.defineProperty(window, 'location', {
      value: { origin: 'http://localhost:3000' },
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Profile endpoints', () => {
    describe('getProfile', () => {
      it('should fetch profile with auth header', async () => {
        const mockProfile: ProfileDTO = {
          user_id: 'user-1',
          daily_calorie_goal: 2000,
          onboarding_completed_at: '2025-01-01T00:00:00Z',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockProfile));

        const result = await api.getProfile();

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/profile',
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token-123',
            }),
          })
        );
        expect(result).toEqual(mockProfile);
      });

      it('should handle 404 error', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(404, null, 'Not Found'));

        await expect(api.getProfile()).rejects.toThrow(
          'Resource not found. Please complete your profile setup.'
        );
      });
    });

    describe('updateProfile', () => {
      it('should send PATCH request with updates', async () => {
        const mockProfile: ProfileDTO = {
          user_id: 'user-1',
          daily_calorie_goal: 2500,
          onboarding_completed_at: '2025-01-01T00:00:00Z',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-15T00:00:00Z',
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockProfile));

        const result = await api.updateProfile({ daily_calorie_goal: 2500 });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/profile',
          expect.objectContaining({
            method: 'PATCH',
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token-123',
              'Content-Type': 'application/json',
            }),
            body: JSON.stringify({ daily_calorie_goal: 2500 }),
          })
        );
        expect(result).toEqual(mockProfile);
      });
    });

    describe('completeOnboarding', () => {
      it('should send POST request to onboarding endpoint', async () => {
        const mockProfile: ProfileDTO = {
          user_id: 'user-1',
          daily_calorie_goal: 2000,
          onboarding_completed_at: '2025-01-15T00:00:00Z',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-15T00:00:00Z',
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockProfile));

        const result = await api.completeOnboarding({ daily_calorie_goal: 2000 });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/profile/onboarding',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ daily_calorie_goal: 2000 }),
          })
        );
        expect(result).toEqual(mockProfile);
      });
    });
  });

  describe('Health endpoint', () => {
    it('should fetch health status without auth header', async () => {
      mockFetch.mockResolvedValue(createMockFetchResponse(200, { status: 'ok' }));

      const result = await api.getHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/health',
        expect.objectContaining({
          method: 'GET',
          headers: { Accept: 'application/json' },
        })
      );
      expect(result).toEqual({ status: 'ok' });
    });
  });

  describe('Reports endpoints', () => {
    describe('getDailySummary', () => {
      it('should fetch daily summary without date parameter', async () => {
        const mockSummary: DailySummaryReportDTO = {
          date: '2025-01-15',
          totals: { calories: 1500, protein: 75, fat: 50, carbs: 150 },
          goal: { daily_calorie_goal: 2000 },
          meals_count: 3,
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockSummary));

        const result = await api.getDailySummary();

        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:3000/api/v1/reports/daily-summary',
          expect.any(Object)
        );
        expect(result).toEqual(mockSummary);
      });

      it('should fetch daily summary with date parameter', async () => {
        const mockSummary: DailySummaryReportDTO = {
          date: '2025-01-10',
          totals: { calories: 1800, protein: 90, fat: 60, carbs: 180 },
          goal: { daily_calorie_goal: 2000 },
          meals_count: 4,
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockSummary));

        const result = await api.getDailySummary('2025-01-10');

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('date=2025-01-10');
        expect(result).toEqual(mockSummary);
      });
    });

    describe('getWeeklyTrend', () => {
      it('should fetch weekly trend with default parameters', async () => {
        const mockTrend: WeeklyTrendReportDTO = {
          end_date: '2025-01-15',
          days: [],
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockTrend));

        const result = await api.getWeeklyTrend();

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('include_macros=false');
        expect(result).toEqual(mockTrend);
      });

      it('should fetch weekly trend with endDate and includeMacros parameters', async () => {
        const mockTrend: WeeklyTrendReportDTO = {
          end_date: '2025-01-10',
          days: [],
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockTrend));

        const result = await api.getWeeklyTrend('2025-01-10', true);

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('end_date=2025-01-10');
        expect(callUrl).toContain('include_macros=true');
        expect(result).toEqual(mockTrend);
      });
    });
  });

  describe('Meal Categories endpoint', () => {
    it('should fetch meal categories without locale', async () => {
      const mockCategories: MealCategoryDTO[] = [
        { code: 'breakfast', locale: 'pl', label: 'Śniadanie' },
        { code: 'lunch', locale: 'pl', label: 'Obiad' },
      ];

      mockFetch.mockResolvedValue(
        createMockFetchResponse(200, { data: mockCategories })
      );

      const result = await api.getMealCategories();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/v1/meal-categories',
        expect.any(Object)
      );
      expect(result).toEqual(mockCategories);
    });

    it('should fetch meal categories with locale parameter', async () => {
      const mockCategories: MealCategoryDTO[] = [
        { code: 'breakfast', locale: 'en', label: 'Breakfast' },
      ];

      mockFetch.mockResolvedValue(
        createMockFetchResponse(200, { data: mockCategories })
      );

      const result = await api.getMealCategories('en');

      const callUrl = mockFetch.mock.calls[0][0];
      expect(callUrl).toContain('locale=en');
      expect(result).toEqual(mockCategories);
    });
  });

  describe('Analysis Run endpoints', () => {
    describe('createAnalysisRun', () => {
      it('should create analysis run with correct parameters', async () => {
        const mockRun: AnalysisRunDetailDTO = {
          id: 'run-123',
          user_id: 'user-1',
          meal_id: null,
          status: 'queued',
          raw_input: '2 jajka',
          created_at: '2025-01-15T12:00:00Z',
          started_at: null,
          completed_at: null,
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockRun));

        const result = await api.createAnalysisRun({
          input_text: '2 jajka',
          meal_id: null,
        });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/analysis-runs',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ input_text: '2 jajka', meal_id: null }),
          })
        );
        expect(result).toEqual(mockRun);
      });
    });

    describe('getAnalysisRunItems', () => {
      it('should fetch analysis run items', async () => {
        const mockItems: AnalysisRunItemsDTO = {
          run_id: 'run-123',
          items: [
            {
              id: 'item-1',
              analysis_run_id: 'run-123',
              ordinal: 1,
              raw_name: 'Jajka',
              matched_product_id: 'product-1',
              weight_grams: 100,
              calories: 155,
              protein: 13,
              fat: 11,
              carbs: 1.1,
              confidence: 0.95,
              created_at: '2025-01-15T12:00:00Z',
            },
          ],
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockItems));

        const result = await api.getAnalysisRunItems('run-123');

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/analysis-runs/run-123/items',
          expect.any(Object)
        );
        expect(result).toEqual(mockItems);
      });
    });

    describe('retryAnalysisRun', () => {
      it('should retry analysis run with empty command', async () => {
        const mockRun: AnalysisRunDetailDTO = {
          id: 'run-123',
          user_id: 'user-1',
          meal_id: null,
          status: 'queued',
          raw_input: '2 jajka',
          created_at: '2025-01-15T12:00:00Z',
          started_at: null,
          completed_at: null,
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockRun));

        const result = await api.retryAnalysisRun('run-123', {});

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/analysis-runs/run-123/retry',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({}),
          })
        );
        expect(result).toEqual(mockRun);
      });
    });

    describe('cancelAnalysisRun', () => {
      it('should cancel analysis run', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(200, {}));

        await api.cancelAnalysisRun('run-123');

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/analysis-runs/run-123/cancel',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({}),
          })
        );
      });
    });
  });

  describe('Meals endpoints', () => {
    describe('createMeal', () => {
      it('should create meal with AI source', async () => {
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

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockMeal));

        const result = await api.createMeal({
          category: 'breakfast',
          eaten_at: '2025-01-15T12:00:00.000Z',
          source: 'ai',
          calories: 286.57,
          protein: 17.8,
          fat: 13.02,
          carbs: 26,
          analysis_run_id: 'run-123',
        });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/meals',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"source":"ai"'),
          })
        );
        expect(result).toEqual(mockMeal);
      });

      it('should create meal with manual source', async () => {
        const mockMeal: MealListItemDTO = {
          id: 'meal-2',
          user_id: 'user-1',
          category: 'lunch',
          eaten_at: '2025-01-15T14:00:00.000Z',
          source: 'manual',
          calories: 650,
          protein: null,
          fat: null,
          carbs: null,
          analysis_run_id: null,
          created_at: '2025-01-15T14:00:00Z',
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockMeal));

        const result = await api.createMeal({
          category: 'lunch',
          eaten_at: '2025-01-15T14:00:00.000Z',
          source: 'manual',
          calories: 650,
        });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/meals',
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"source":"manual"'),
          })
        );
        expect(result).toEqual(mockMeal);
      });
    });

    describe('getMealDetail', () => {
      it('should fetch meal detail with include_analysis_items=true', async () => {
        const mockDetail: MealDetailDTO = {
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
          updated_at: '2025-01-15T12:00:00Z',
          deleted_at: null,
          analysis_items: [],
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockDetail));

        const result = await api.getMealDetail('meal-1');

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('include_analysis_items=true');
        expect(result).toEqual(mockDetail);
      });
    });

    describe('deleteMeal', () => {
      it('should delete meal and handle 204 No Content response', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(204));

        await api.deleteMeal('meal-1');

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/meals/meal-1',
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });

    describe('getMeals', () => {
      it('should fetch meals with default page size', async () => {
        const mockResponse = {
          data: [] as MealListItemDTO[],
          page: { size: 20, after: null },
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockResponse));

        const result = await api.getMeals();

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('page%5Bsize%5D=20');
        expect(result).toEqual(mockResponse);
      });

      it('should fetch meals with custom page size and cursor', async () => {
        const mockResponse = {
          data: [] as MealListItemDTO[],
          page: { size: 10, after: 'next-cursor' },
        };

        mockFetch.mockResolvedValue(createMockFetchResponse(200, mockResponse));

        const result = await api.getMeals(10, 'current-cursor');

        const callUrl = mockFetch.mock.calls[0][0];
        expect(callUrl).toContain('page%5Bsize%5D=10');
        expect(callUrl).toContain('page%5Bafter%5D=current-cursor');
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Auth endpoints (unauthenticated)', () => {
    describe('postAuthRegister', () => {
      it('should register without auth header', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(200, {}));

        await api.postAuthRegister({ email: 'test@example.com', password: 'password123' });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/auth/register',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify({ email: 'test@example.com', password: 'password123' }),
          })
        );
      });
    });

    describe('postAuthPasswordResetRequest', () => {
      it('should request password reset without auth header', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(200, {}));

        await api.postAuthPasswordResetRequest({ email: 'test@example.com' });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/auth/password/reset-request',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ email: 'test@example.com' }),
          })
        );
      });
    });

    describe('postAuthPasswordResetConfirm', () => {
      it('should confirm password reset with auth header', async () => {
        mockFetch.mockResolvedValue(createMockFetchResponse(200, {}));

        await api.postAuthPasswordResetConfirm({ password: 'newpassword123' });

        expect(mockFetch).toHaveBeenCalledWith(
          '/api/v1/auth/password/reset-confirm',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token-123',
            }),
            body: JSON.stringify({ password: 'newpassword123' }),
          })
        );
      });
    });
  });

  describe('Error handling', () => {
    it('should throw specific error message for 401 Unauthorized', async () => {
      mockFetch.mockResolvedValue(createMockFetchResponse(401, null, 'Unauthorized'));

      await expect(api.getProfile()).rejects.toThrow('Unauthorized. Please log in again.');
    });

    it('should throw specific error message for 404 Not Found', async () => {
      mockFetch.mockResolvedValue(createMockFetchResponse(404, null, 'Not Found'));

      await expect(api.getProfile()).rejects.toThrow(
        'Resource not found. Please complete your profile setup.'
      );
    });

    it('should throw "Conflict" for 409 status', async () => {
      mockFetch.mockResolvedValue(createMockFetchResponse(409, null, 'Conflict'));

      await expect(api.getProfile()).rejects.toThrow('Conflict');
    });

    it('should throw generic error with status code and text for other errors', async () => {
      mockFetch.mockResolvedValue(
        createMockFetchResponse(500, { error: 'Server error' }, 'Internal Server Error')
      );

      await expect(api.getProfile()).rejects.toThrow(/API error \(500\):/);
    });

    it('should include status text when response text is empty', async () => {
      mockFetch.mockResolvedValue(createMockFetchResponse(503, null, 'Service Unavailable'));

      await expect(api.getProfile()).rejects.toThrow('API error (503): Service Unavailable');
    });
  });
});


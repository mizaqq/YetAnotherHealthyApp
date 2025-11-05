import { supabase } from "./supabaseClient";
import type {
  DailySummaryReportDTO,
  WeeklyTrendReportDTO,
  ProfileDTO,
  MealCategoryDTO,
  CreateAnalysisRunCommand,
  AnalysisRunDetailDTO,
  AnalysisRunItemsDTO,
  RetryAnalysisRunCommand,
  CreateMealCommand,
  MealListItemDTO,
  MealDetailDTO,
  CreateOnboardingCommand,
  PaginatedResponse,
} from "../types";

export type HealthResponse = { status: string };

const DEFAULT_API_BASE = "/api/v1";
type ImportMetaEnv = {
  readonly VITE_API_BASE?: string;
};

const { env } = import.meta as unknown as { env: ImportMetaEnv };
const API_BASE = env?.VITE_API_BASE ?? DEFAULT_API_BASE;

// Temporary debug logging
console.log("🔍 API_BASE configured as:", API_BASE);
console.log("🔍 VITE_API_BASE env var:", env?.VITE_API_BASE);

/**
 * Authenticated fetch wrapper that includes Supabase auth token
 */
async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (session?.access_token) {
    headers.Authorization = `Bearer ${session.access_token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

/**
 * Handle API errors consistently
 */
async function handleApiError(response: Response): Promise<never> {
  const text = await response.text().catch(() => "");

  if (response.status === 401) {
    throw new Error("Unauthorized. Please log in again.");
  }

  if (response.status === 404) {
    throw new Error("Resource not found. Please complete your profile setup.");
  }

  if (response.status === 409) {
    throw new Error("Conflict");
  }

  throw new Error(`API error (${response.status}): ${text && text !== 'null' ? text : response.statusText}`);
}

export async function getProfile(): Promise<ProfileDTO> {
  const response = await authenticatedFetch(`${API_BASE}/profile`);

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as ProfileDTO;
}

/**
 * Update user profile (e.g., daily calorie goal)
 * @param updates Partial profile updates
 */
export async function updateProfile(
  updates: Partial<Pick<ProfileDTO, "daily_calorie_goal">>
): Promise<ProfileDTO> {
  const response = await authenticatedFetch(`${API_BASE}/profile`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as ProfileDTO;
}

/**
 * Complete onboarding by setting daily calorie goal
 * @param command Onboarding command with daily_calorie_goal
 */
export async function completeOnboarding(
  command: CreateOnboardingCommand
): Promise<ProfileDTO> {
  const response = await authenticatedFetch(`${API_BASE}/profile/onboarding`, {
    method: "POST",
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as ProfileDTO;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as HealthResponse;
}

/**
 * Get daily meal summary with aggregated totals and progress
 * @param date Optional date in YYYY-MM-DD format. Defaults to today.
 */
export async function getDailySummary(
  date?: string
): Promise<DailySummaryReportDTO> {
  const url = new URL(`${API_BASE}/reports/daily-summary`, window.location.origin);
  if (date) {
    url.searchParams.set("date", date);
  }

  const response = await authenticatedFetch(url.toString());

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as DailySummaryReportDTO;
}

/**
 * Get 7-day rolling trend of calorie consumption
 * @param endDate Optional end date in YYYY-MM-DD format. Defaults to today.
 * @param includeMacros Whether to include macronutrient breakdown. Defaults to false.
 */
export async function getWeeklyTrend(
  endDate?: string,
  includeMacros = false
): Promise<WeeklyTrendReportDTO> {
  const url = new URL(`${API_BASE}/reports/weekly-trend`, window.location.origin);
  if (endDate) {
    url.searchParams.set("end_date", endDate);
  }
  url.searchParams.set("include_macros", includeMacros.toString());

  const response = await authenticatedFetch(url.toString());

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as WeeklyTrendReportDTO;
}

/**
 * Get meal categories
 * @param locale Optional locale code (e.g. 'pl', 'en'). Defaults to user's locale.
 */
export async function getMealCategories(
  locale?: string
): Promise<MealCategoryDTO[]> {
  const url = new URL(`${API_BASE}/meal-categories`, window.location.origin);
  if (locale) {
    url.searchParams.set("locale", locale);
  }

  const response = await authenticatedFetch(url.toString());

  if (!response.ok) {
    await handleApiError(response);
  }

  const data: unknown = await response.json();
  return (data as { data: MealCategoryDTO[] }).data;
}

/**
 * Create a new analysis run for meal text description
 * @param command Analysis run creation command with input_text and optional threshold
 */
export async function createAnalysisRun(
  command: CreateAnalysisRunCommand
): Promise<AnalysisRunDetailDTO> {
  const response = await authenticatedFetch(`${API_BASE}/analysis-runs`, {
    method: "POST",
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as AnalysisRunDetailDTO;
}

/**
 * Get analysis run items (ingredients)
 * @param runId Analysis run UUID
 */
export async function getAnalysisRunItems(
  runId: string
): Promise<AnalysisRunItemsDTO> {
  const response = await authenticatedFetch(
    `${API_BASE}/analysis-runs/${runId}/items`
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as AnalysisRunItemsDTO;
}

/**
 * Retry an analysis run with optional overrides
 * @param runId Analysis run UUID to retry
 * @param command Retry command with optional threshold and raw_input overrides
 */
export async function retryAnalysisRun(
  runId: string,
  command: RetryAnalysisRunCommand
): Promise<AnalysisRunDetailDTO> {
  const response = await authenticatedFetch(
    `${API_BASE}/analysis-runs/${runId}/retry`,
    {
      method: "POST",
      body: JSON.stringify(command),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as AnalysisRunDetailDTO;
}

/**
 * Cancel a running or queued analysis run
 * @param runId Analysis run UUID to cancel
 */
export async function cancelAnalysisRun(runId: string): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/analysis-runs/${runId}/cancel`,
    {
      method: "POST",
      body: JSON.stringify({}),
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }
}

/**
 * Create a new meal entry
 * @param command Meal creation command
 */
export async function createMeal(
  command: CreateMealCommand
): Promise<MealListItemDTO> {
  const response = await authenticatedFetch(`${API_BASE}/meals`, {
    method: "POST",
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as MealListItemDTO;
}

/**
 * Get meal details with analysis items
 * @param mealId UUID of the meal to retrieve
 */
export async function getMealDetail(mealId: string): Promise<MealDetailDTO> {
  const url = new URL(`${API_BASE}/meals/${mealId}`, window.location.origin);
  url.searchParams.set("include_analysis_items", "true");

  const response = await authenticatedFetch(url.toString());

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as MealDetailDTO;
}

/**
 * Delete a meal (soft delete)
 * @param mealId UUID of the meal to delete
 */
export async function deleteMeal(mealId: string): Promise<void> {
  const response = await authenticatedFetch(`${API_BASE}/meals/${mealId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  // 204 No Content response has no body
}

/**
 * Get paginated list of meals
 * @param pageSize Number of meals to fetch per page
 * @param afterCursor Cursor for pagination (from previous response)
 */
export async function getMeals(
  pageSize = 20,
  afterCursor?: string | null
): Promise<PaginatedResponse<MealListItemDTO>> {
  const url = new URL(`${API_BASE}/meals`, window.location.origin);
  url.searchParams.set("page[size]", pageSize.toString());
  if (afterCursor) {
    url.searchParams.set("page[after]", afterCursor);
  }

  const response = await authenticatedFetch(url.toString());

  if (!response.ok) {
    await handleApiError(response);
  }

  return (await response.json()) as PaginatedResponse<MealListItemDTO>;
}

/**
 * Register a new user account
 * @param payload Email and password for the new account
 */
export async function postAuthRegister(payload: {
  email: string;
  password: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await handleApiError(response);
}

/**
 * Request a password reset email
 * @param payload Email address to send reset link to
 */
export async function postAuthPasswordResetRequest(payload: {
  email: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/password/reset-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await handleApiError(response);
}

/**
 * Confirm password reset with new password
 * @param payload New password for the account
 */
export async function postAuthPasswordResetConfirm(payload: {
  password: string;
}): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/auth/password/reset-confirm`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) await handleApiError(response);
}



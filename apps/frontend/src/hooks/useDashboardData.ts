import { useState, useEffect } from "react";
import { getDailySummary, getWeeklyTrend } from "@/lib/api";
import type { DailySummaryReportDTO, WeeklyTrendReportDTO } from "@/types";

type UseDashboardDataReturn = {
  dailySummary: DailySummaryReportDTO | null;
  weeklyTrend: WeeklyTrendReportDTO | null;
  isLoading: boolean;
  error: Error | null;
  hasMeals: boolean;
  refetch: () => void;
}

/**
 * Custom hook for fetching and managing dashboard data
 * Fetches both daily summary and weekly trend data in parallel
 */
export function useDashboardData(): UseDashboardDataReturn {
  const [dailySummary, setDailySummary] = useState<DailySummaryReportDTO | null>(null);
  const [weeklyTrend, setWeeklyTrend] = useState<WeeklyTrendReportDTO | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch both endpoints in parallel for better performance
      const [summaryData, trendData] = await Promise.all([
        getDailySummary(),
        getWeeklyTrend(),
      ]);

      setDailySummary(summaryData);
      setWeeklyTrend(trendData);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Unknown error occurred");
      setError(error);
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const hasMeals = Boolean(dailySummary?.meals && dailySummary.meals.length > 0);

  return {
    dailySummary,
    weeklyTrend,
    isLoading,
    error,
    hasMeals,
    refetch: () => { void fetchData(); },
  };
}


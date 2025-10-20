"""Reports API endpoints."""

from __future__ import annotations

from datetime import date as Date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.reports import DailySummaryResponse, WeeklyTrendReportDTO
from app.core.dependencies import get_current_user_id, get_reports_service
from app.services.reports_service import ReportsService

router = APIRouter()


@router.get(
    "/daily-summary",
    response_model=DailySummaryResponse,
    summary="Get daily meal summary",
    description=(
        "Retrieve aggregated daily meal data including totals, "
        "progress against calorie goal, and list of meals for a specific date. "
        "Date defaults to today in the user's timezone."
    ),
)
async def get_daily_summary(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ReportsService, Depends(get_reports_service)],
    target_date: Annotated[
        Date | None,
        Query(
            alias="date",
            description=(
                "Target date for the summary (YYYY-MM-DD format). "
                "Defaults to today in user's timezone."
            ),
            example="2025-01-15",
        ),
    ] = None,
) -> DailySummaryResponse:
    """Get daily meal summary with aggregated totals and progress metrics.

    This endpoint provides a comprehensive daily view of the user's meal consumption:
    - Aggregated nutritional totals (calories, protein, fat, carbs)
    - Progress percentage against daily calorie goal
    - List of all meals for the day, ordered chronologically

    The date is interpreted in the user's timezone (from their profile). If no date
    is provided, it defaults to today in the user's timezone.

    Query Parameters:
        date: Target date in YYYY-MM-DD format (ISO 8601). Optional.
              Defaults to today in the user's timezone if not provided.

    Returns:
        DailySummaryResponse containing:
        - date: The date of the summary
        - calorie_goal: User's daily calorie goal (null if not set)
        - totals: Aggregated calories and macros for the day
        - progress: Progress percentage against calorie goal
        - meals: List of meals ordered by eaten_at (ascending)

    Raises:
        400 Bad Request:
            - Invalid date format (not YYYY-MM-DD)
            - Date is before the user's profile creation date
        401 Unauthorized:
            - Missing or invalid authentication token
        404 Not Found:
            - User profile not found
        500 Internal Server Error:
            - Database or unexpected errors

    Examples:
        Get summary for today:
        GET /api/v1/reports/daily-summary

        Get summary for specific date:
        GET /api/v1/reports/daily-summary?date=2025-01-15

    Notes:
        - All timestamps in the response are timezone-aware (ISO 8601 with offset)
        - Soft-deleted meals are excluded from the summary
        - Manual meals (with null macros) are included in calorie totals only
        - Progress percentage is 0 if calorie goal is not set or is zero
        - Totals default to 0 if no meals exist for the date
    """
    return await service.get_daily_summary(
        user_id=user_id,
        target_date=target_date,
    )


@router.get(
    "/weekly-trend",
    response_model=WeeklyTrendReportDTO,
    summary="Get 7-day calorie trend",
    description=(
        "Retrieve a 7-day rolling trend of calorie consumption with progress "
        "against daily goal. Optionally includes macronutrient breakdown. "
        "Days without meals show zero values. Date range is inclusive."
    ),
)
async def get_weekly_trend(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ReportsService, Depends(get_reports_service)],
    end_date: Annotated[
        Date | None,
        Query(
            description=("End date of 7-day period (YYYY-MM-DD format). Defaults to today in UTC."),
            example="2025-10-18",
        ),
    ] = None,
    include_macros: Annotated[
        bool,
        Query(
            description=("Include protein, fat, and carbs breakdown for each day. Default: false."),
        ),
    ] = False,
) -> WeeklyTrendReportDTO:
    """Get 7-day rolling trend of calorie and macro consumption.

    This endpoint provides a weekly view of nutritional intake:
    - 7 consecutive days of data (including end_date)
    - Daily calorie totals compared against daily goal
    - Optional macronutrient breakdown (protein, fat, carbs)
    - Days without meals return zero values
    - All dates in UTC timezone

    The 7-day period is calculated as [end_date - 6 days, end_date] inclusive.

    Query Parameters:
        end_date: End date of the 7-day window (YYYY-MM-DD). Optional.
                  Defaults to today in UTC if not provided.
        include_macros: If true, includes protein/fat/carbs for each day.
                        If false, macro fields are omitted. Default: false.

    Returns:
        WeeklyTrendReportDTO containing:
        - start_date: First date in the 7-day range
        - end_date: Last date in the 7-day range
        - points: List of 7 daily data points with calories, goal, and optional macros

    Raises:
        400 Bad Request:
            - Invalid end_date format (not YYYY-MM-DD)
        401 Unauthorized:
            - Missing or invalid authentication token
        404 Not Found:
            - User profile not found
        500 Internal Server Error:
            - Database or unexpected errors

    Examples:
        Get trend ending today (default):
        GET /api/v1/reports/weekly-trend

        Get trend for specific week:
        GET /api/v1/reports/weekly-trend?end_date=2025-10-18

        Get trend with macros:
        GET /api/v1/reports/weekly-trend?end_date=2025-10-18&include_macros=true

    Notes:
        - All dates are interpreted in UTC timezone
        - Days without meals show 0.00 for all nutritional values
        - When include_macros=false, protein/fat/carbs fields are omitted from response
        - When include_macros=true, protein/fat/carbs are included (may be 0.00)
        - Soft-deleted meals are excluded from calculations
        - Calorie goal comes from user's profile; defaults to 0 if not set
    """
    return await service.get_weekly_trend(
        user_id=user_id,
        end_date=end_date,
        include_macros=include_macros,
    )

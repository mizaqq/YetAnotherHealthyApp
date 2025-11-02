"""Service layer for reports operations."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.api.v1.schemas.reports import (
    DailySummaryMeal,
    DailySummaryProgress,
    DailySummaryResponse,
    DailySummaryTotals,
    ReportPointDTO,
    WeeklyTrendReportDTO,
)
from app.db.repositories.profile_repository import ProfileRepository  # type: ignore[TCH001]
from app.db.repositories.reports_repository import ReportsRepository  # type: ignore[TCH001]

logger = logging.getLogger(__name__)


class ReportsService:
    """Orchestrates report generation with proper business logic and error handling."""

    def __init__(
        self,
        reports_repository: ReportsRepository,
        profile_repository: ProfileRepository,
    ):
        self._reports_repository = reports_repository
        self._profile_repository = profile_repository

    async def get_daily_summary(
        self,
        *,
        user_id: UUID,
        target_date: date | None = None,
    ) -> DailySummaryResponse:
        """Generate daily summary report for a user.

        Args:
            user_id: UUID of the authenticated user
            target_date: Date for the report (defaults to today in user's timezone)

        Returns:
            DailySummaryResponse with aggregated data and meals list

        Raises:
            HTTPException:
                - 404: Profile not found
                - 400: Invalid date (e.g., before profile creation)
                - 500: Database or unexpected errors
        """
        try:
            # Step 1: Fetch user profile for calorie goal and timezone
            profile = self._profile_repository.get_profile(user_id)

            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            # Step 2: Determine target date in user's timezone
            user_timezone = self._get_timezone(profile.timezone)

            if target_date is None:
                # Default to today in user's timezone
                target_date = datetime.now(user_timezone).date()

            # Step 3: Validate date is not before profile creation
            if profile.created_at:
                profile_created_date = profile.created_at.astimezone(user_timezone).date()
                if target_date < profile_created_date:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Date cannot be before profile creation date ({profile_created_date})"
                        ),
                    )

            # Step 4: Calculate UTC time boundaries for the target date
            start_ts, end_ts = self._calculate_utc_boundaries(target_date, user_timezone)

            logger.info(
                "Fetching daily summary for user: %s, date: %s (UTC: %s to %s)",
                user_id,
                target_date,
                start_ts,
                end_ts,
                extra={
                    "user_id": str(user_id),
                    "target_date": target_date.isoformat(),
                    "timezone": profile.timezone,
                },
            )

            # Step 5: Fetch aggregates and meals list concurrently
            aggregates_task = self._reports_repository.get_daily_meal_aggregates(
                user_id=user_id,
                start_ts=start_ts,
                end_ts=end_ts,
            )
            meals_task = self._reports_repository.get_daily_meals_list(
                user_id=user_id,
                start_ts=start_ts,
                end_ts=end_ts,
            )

            aggregates, meals_data = await asyncio.gather(aggregates_task, meals_task)

            # Step 6: Build response components
            totals = DailySummaryTotals(
                calories=aggregates["calories"],
                protein=aggregates["protein"],
                fat=aggregates["fat"],
                carbs=aggregates["carbs"],
            )

            # Step 7: Calculate progress percentage with zero-division protection
            calories_percentage = self._calculate_progress_percentage(
                consumed=aggregates["calories"],
                goal=profile.daily_calorie_goal,
            )

            progress = DailySummaryProgress(calories_percentage=calories_percentage)

            # Step 8: Convert meals data to response models
            meals = [
                DailySummaryMeal(
                    id=meal["id"],
                    category=meal["category"],
                    calories=meal["calories"],
                    eaten_at=meal["eaten_at"],
                )
                for meal in meals_data
            ]

            # Step 9: Assemble final response
            return DailySummaryResponse(
                date=target_date,
                calorie_goal=profile.daily_calorie_goal,
                totals=totals,
                progress=progress,
                meals=meals,
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to generate daily summary: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "target_date": target_date.isoformat() if target_date else None,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to generate daily summary",
            ) from exc

    def _get_timezone(self, timezone_str: str) -> ZoneInfo:
        """Get ZoneInfo object from timezone string with fallback to UTC.

        Args:
            timezone_str: IANA timezone string (e.g., "Europe/Warsaw")

        Returns:
            ZoneInfo object
        """
        try:
            return ZoneInfo(timezone_str)
        except Exception as exc:
            logger.warning(
                "Invalid timezone '%s', falling back to UTC: %s",
                timezone_str,
                exc,
                extra={"timezone": timezone_str},
            )
            return ZoneInfo("UTC")

    def _calculate_utc_boundaries(
        self,
        target_date: date,
        user_timezone: ZoneInfo,
    ) -> tuple[datetime, datetime]:
        """Calculate UTC start and end timestamps for a date in user's timezone.

        Args:
            target_date: Date in user's timezone
            user_timezone: User's timezone

        Returns:
            Tuple of (start_ts, end_ts) as timezone-aware datetime objects in UTC
        """
        # Start of day in user's timezone
        start_local = datetime.combine(target_date, time.min, tzinfo=user_timezone)
        # End of day in user's timezone (start of next day)
        end_local = datetime.combine(target_date, time.max, tzinfo=user_timezone)

        # Convert to UTC
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        # Add 1 microsecond to get to the start of next day, then use it as exclusive upper bound
        end_utc = (end_local.astimezone(ZoneInfo("UTC"))).replace(microsecond=999999)
        # Actually, for proper exclusive upper bound, use start of next day
        from datetime import timedelta

        end_utc = start_utc + timedelta(days=1)

        return start_utc, end_utc

    def _calculate_progress_percentage(
        self,
        consumed: Decimal,
        goal: Decimal | None,
    ) -> Decimal:
        """Calculate progress percentage with zero-division protection.

        Args:
            consumed: Calories consumed
            goal: Daily calorie goal (may be None)

        Returns:
            Progress percentage (0-100+), rounded to 1 decimal place
        """
        if goal is None or goal == 0:
            return Decimal("0.0")

        percentage = (consumed / goal) * Decimal("100")
        # Round to 1 decimal place
        return percentage.quantize(Decimal("0.1"))

    async def get_weekly_trend(
        self,
        *,
        user_id: UUID,
        end_date: date | None = None,
        include_macros: bool = False,
    ) -> WeeklyTrendReportDTO:
        """Generate 7-day rolling trend report for a user.

        Args:
            user_id: UUID of the authenticated user
            end_date: End date of the 7-day period (defaults to today in UTC)
            include_macros: Whether to include protein/fat/carbs breakdown

        Returns:
            WeeklyTrendReportDTO with 7 days of data points

        Raises:
            HTTPException:
                - 404: Profile not found
                - 500: Database or unexpected errors
        """
        try:
            # Step 1: Fetch user profile for calorie goal
            profile = self._profile_repository.get_profile(user_id)

            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found",
                )

            # Step 2: Determine end_date (default to today in UTC)
            if end_date is None:
                end_date = datetime.now(ZoneInfo("UTC")).date()

            # Step 3: Calculate start_date (end_date - 6 days for 7-day range inclusive)
            from datetime import timedelta

            start_date = end_date - timedelta(days=6)

            logger.info(
                "Fetching weekly trend for user: %s, date range: %s to %s",
                user_id,
                start_date,
                end_date,
                extra={
                    "user_id": str(user_id),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "include_macros": include_macros,
                },
            )

            # Step 4: Fetch aggregated data grouped by date
            daily_aggregates = await self._reports_repository.get_meals_aggregated_by_date(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )

            # Step 5: Build list of 7 data points, filling missing days with zeros
            points: list[ReportPointDTO] = []
            current_date = start_date

            # Use profile's calorie goal, default to 0 if not set
            calorie_goal = (
                profile.daily_calorie_goal if profile.daily_calorie_goal else Decimal("0.00")
            )

            for _ in range(7):
                # Get aggregates for this date, or use zeros if no meals
                day_data = daily_aggregates.get(
                    current_date,
                    {
                        "calories": Decimal("0.00"),
                        "protein": Decimal("0.00"),
                        "fat": Decimal("0.00"),
                        "carbs": Decimal("0.00"),
                    },
                )

                # Create data point
                point = ReportPointDTO(
                    date=current_date,
                    calories=day_data["calories"],
                    goal=calorie_goal,
                    # Set macros to None if not requested, otherwise use values (including 0)
                    protein=day_data["protein"] if include_macros else None,
                    fat=day_data["fat"] if include_macros else None,
                    carbs=day_data["carbs"] if include_macros else None,
                )

                points.append(point)
                current_date += timedelta(days=1)

            # Step 6: Assemble final response
            return WeeklyTrendReportDTO(
                start_date=start_date,
                end_date=end_date,
                points=points,
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to generate weekly trend: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "end_date": end_date.isoformat() if end_date else None,
                    "include_macros": include_macros,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to generate weekly trend report",
            ) from exc

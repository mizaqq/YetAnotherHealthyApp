"""Repository for reports data access operations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client


class ReportsRepository:
    """Handles database operations for reports."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    async def get_daily_meal_aggregates(
        self,
        *,
        user_id: UUID,
        start_ts: datetime,
        end_ts: datetime,
    ) -> dict[str, Decimal]:
        """Get aggregated meal totals for a specific time range.

        Returns totals with COALESCE to ensure zero defaults when no meals exist.

        Args:
            user_id: UUID of the user
            start_ts: Start of time range (UTC, inclusive)
            end_ts: End of time range (UTC, exclusive)

        Returns:
            Dictionary with keys: calories, protein, fat, carbs (all as Decimal)

        Raises:
            Exception: For database errors
        """
        # Use RPC function for complex aggregation or execute raw query
        # Note: Supabase Python client may need to use .rpc() for custom functions
        # or construct the query using filters

        # Query meals within the time range
        # RLS automatically filters by user_id
        response = (
            self.client.table("meals")
            .select("calories, protein, fat, carbs")
            .eq("user_id", str(user_id))
            .gte("eaten_at", start_ts.isoformat())
            .lt("eaten_at", end_ts.isoformat())
            .is_("deleted_at", "null")
            .execute()
        )

        # Aggregate in Python (Supabase client doesn't support direct aggregation)
        meals = response.data if response and response.data else []

        total_calories = Decimal("0.00")
        total_protein = Decimal("0.00")
        total_fat = Decimal("0.00")
        total_carbs = Decimal("0.00")

        for meal in meals:
            # Handle calories (always present)
            if meal.get("calories") is not None:
                total_calories += Decimal(str(meal["calories"]))

            # Handle macros (may be NULL for manual meals)
            if meal.get("protein") is not None:
                total_protein += Decimal(str(meal["protein"]))
            if meal.get("fat") is not None:
                total_fat += Decimal(str(meal["fat"]))
            if meal.get("carbs") is not None:
                total_carbs += Decimal(str(meal["carbs"]))

        return {
            "calories": total_calories,
            "protein": total_protein,
            "fat": total_fat,
            "carbs": total_carbs,
        }

    async def get_daily_meals_list(
        self,
        *,
        user_id: UUID,
        start_ts: datetime,
        end_ts: datetime,
    ) -> list[dict[str, Any]]:
        """Get list of meals for a specific time range.

        Returns meals ordered by eaten_at ascending.

        Args:
            user_id: UUID of the user
            start_ts: Start of time range (UTC, inclusive)
            end_ts: End of time range (UTC, exclusive)

        Returns:
            List of meal dictionaries with keys: id, category, calories, eaten_at

        Raises:
            Exception: For database errors
        """
        # Query meals within the time range
        # RLS automatically filters by user_id
        response = (
            self.client.table("meals")
            .select("id, category, calories, eaten_at")
            .eq("user_id", str(user_id))
            .gte("eaten_at", start_ts.isoformat())
            .lt("eaten_at", end_ts.isoformat())
            .is_("deleted_at", "null")
            .order("eaten_at", desc=False)
            .execute()
        )

        meals = response.data if response and response.data else []

        # Convert string values to appropriate types
        result = []
        for meal in meals:
            result.append(
                {
                    "id": meal["id"],
                    "category": meal["category"],
                    "calories": Decimal(str(meal["calories"])),
                    "eaten_at": datetime.fromisoformat(meal["eaten_at"].replace("Z", "+00:00")),
                }
            )

        return result

    async def get_meals_aggregated_by_date(
        self,
        *,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> dict[date, dict[str, Decimal]]:
        """Get aggregated meal totals grouped by date.

        Groups meals by date (in UTC) and sums nutritional values for each day.
        Date range is inclusive: [start_date, end_date].

        Args:
            user_id: UUID of the user
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            Dictionary mapping date -> {calories, protein, fat, carbs}
            Missing dates will not be in the dictionary.

        Raises:
            Exception: For database errors
        """
        # Calculate UTC datetime boundaries for the date range
        # Start: beginning of start_date in UTC (00:00:00)
        # End: end of end_date in UTC (23:59:59.999999)
        from datetime import time
        from zoneinfo import ZoneInfo

        utc = ZoneInfo("UTC")
        start_ts = datetime.combine(start_date, time.min, tzinfo=utc)
        # End of day is start of next day minus 1 microsecond, but we'll use < next day
        from datetime import timedelta

        end_ts = datetime.combine(end_date, time.max, tzinfo=utc) + timedelta(microseconds=1)

        # Query meals within the date range
        response = (
            self.client.table("meals")
            .select("eaten_at, calories, protein, fat, carbs")
            .eq("user_id", str(user_id))
            .gte("eaten_at", start_ts.isoformat())
            .lt("eaten_at", end_ts.isoformat())
            .is_("deleted_at", "null")
            .execute()
        )

        meals = response.data if response and response.data else []

        # Group meals by date and aggregate
        daily_aggregates: dict[date, dict[str, Decimal]] = {}

        for meal in meals:
            # Parse eaten_at and extract date
            eaten_at_str = meal.get("eaten_at")
            if not eaten_at_str:
                continue

            eaten_dt = datetime.fromisoformat(eaten_at_str.replace("Z", "+00:00"))
            meal_date = eaten_dt.date()

            # Initialize aggregates for this date if not present
            if meal_date not in daily_aggregates:
                daily_aggregates[meal_date] = {
                    "calories": Decimal("0.00"),
                    "protein": Decimal("0.00"),
                    "fat": Decimal("0.00"),
                    "carbs": Decimal("0.00"),
                }

            # Add meal values to daily totals
            if meal.get("calories") is not None:
                daily_aggregates[meal_date]["calories"] += Decimal(str(meal["calories"]))

            if meal.get("protein") is not None:
                daily_aggregates[meal_date]["protein"] += Decimal(str(meal["protein"]))

            if meal.get("fat") is not None:
                daily_aggregates[meal_date]["fat"] += Decimal(str(meal["fat"]))

            if meal.get("carbs") is not None:
                daily_aggregates[meal_date]["carbs"] += Decimal(str(meal["carbs"]))

        return daily_aggregates

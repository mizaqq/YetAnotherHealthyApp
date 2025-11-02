"""Pydantic models for reports endpoints."""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class DailySummaryQuery(BaseModel):
    """Query parameters for daily summary endpoint."""

    date: Annotated[
        Date | None,
        Field(
            default=None,
            description="Target date for the summary (YYYY-MM-DD). Defaults to today in user's timezone.",
        ),
    ] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: str | Date | None) -> Date | None:
        """Parse ISO 8601 date string (YYYY-MM-DD) to date object.

        Args:
            v: Date string, date object, or None

        Returns:
            date object or None

        Raises:
            ValueError: If date format is invalid
        """
        if v is None:
            return None
        if isinstance(v, Date):
            return v
        if isinstance(v, str):
            try:
                # Parse YYYY-MM-DD format
                return Date.fromisoformat(v)
            except ValueError as exc:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {v}") from exc
        raise ValueError(f"Unsupported date type: {type(v)}")


class DailySummaryTotals(BaseModel):
    """Aggregated nutritional totals for a day."""

    calories: Annotated[
        Decimal,
        Field(
            description="Total calories consumed (kcal)",
            ge=0,
            decimal_places=2,
        ),
    ]

    protein: Annotated[
        Decimal,
        Field(
            description="Total protein consumed (grams)",
            ge=0,
            decimal_places=2,
        ),
    ]

    fat: Annotated[
        Decimal,
        Field(
            description="Total fat consumed (grams)",
            ge=0,
            decimal_places=2,
        ),
    ]

    carbs: Annotated[
        Decimal,
        Field(
            description="Total carbohydrates consumed (grams)",
            ge=0,
            decimal_places=2,
        ),
    ]

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories", "protein", "fat", "carbs", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class DailySummaryProgress(BaseModel):
    """Progress metrics for daily calorie goal."""

    calories_percentage: Annotated[
        Decimal,
        Field(
            description="Percentage of daily calorie goal achieved (0-100+)",
            ge=0,
            decimal_places=1,
        ),
    ]

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories_percentage", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class DailySummaryMeal(BaseModel):
    """Minimal meal information for daily summary."""

    id: UUID = Field(description="Meal identifier")
    category: str = Field(description="Meal category code")
    calories: Annotated[
        Decimal,
        Field(
            description="Meal calories (kcal)",
            ge=0,
            decimal_places=2,
        ),
    ]
    eaten_at: datetime = Field(description="When the meal was eaten (ISO 8601 with timezone)")

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class DailySummaryResponse(BaseModel):
    """Response model for daily summary endpoint."""

    date: Date = Field(description="The date of this summary")

    calorie_goal: Annotated[
        Decimal | None,
        Field(
            description="User's daily calorie goal (kcal). Null if not set.",
            ge=0,
            decimal_places=2,
        ),
    ] = None

    totals: DailySummaryTotals = Field(description="Aggregated nutritional totals for the day")

    progress: DailySummaryProgress = Field(description="Progress metrics against daily goal")

    meals: list[DailySummaryMeal] = Field(
        description="List of meals for the day, ordered by eaten_at (ascending)"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "date": "2025-01-15",
                "calorie_goal": 2000.00,
                "totals": {
                    "calories": 1650.50,
                    "protein": 95.5,
                    "fat": 60.0,
                    "carbs": 180.0,
                },
                "progress": {
                    "calories_percentage": 82.5,
                },
                "meals": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "category": "breakfast",
                        "calories": 450.50,
                        "eaten_at": "2025-01-15T08:30:00+01:00",
                    },
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "category": "lunch",
                        "calories": 600.00,
                        "eaten_at": "2025-01-15T13:00:00+01:00",
                    },
                    {
                        "id": "323e4567-e89b-12d3-a456-426614174002",
                        "category": "dinner",
                        "calories": 600.00,
                        "eaten_at": "2025-01-15T19:30:00+01:00",
                    },
                ],
            }
        },
    )

    @field_serializer("calorie_goal", when_used="json")
    def serialize_calorie_goal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None


class ReportPointDTO(BaseModel):
    """Single day data point in weekly trend report."""

    date: Date = Field(description="Date for this data point")

    calories: Annotated[
        Decimal,
        Field(
            description="Total calories consumed on this date (kcal)",
            ge=0,
            decimal_places=2,
        ),
    ]

    goal: Annotated[
        Decimal,
        Field(
            description="Daily calorie goal (kcal)",
            ge=0,
            decimal_places=2,
        ),
    ]

    protein: Annotated[
        Decimal | None,
        Field(
            description="Total protein consumed (grams). Present only when include_macros=true.",
            ge=0,
            decimal_places=2,
        ),
    ] = None

    fat: Annotated[
        Decimal | None,
        Field(
            description="Total fat consumed (grams). Present only when include_macros=true.",
            ge=0,
            decimal_places=2,
        ),
    ] = None

    carbs: Annotated[
        Decimal | None,
        Field(
            description="Total carbohydrates consumed (grams). Present only when include_macros=true.",
            ge=0,
            decimal_places=2,
        ),
    ] = None

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories", "goal", "protein", "fat", "carbs", when_used="json")
    def serialize_decimals(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None


class WeeklyTrendReportDTO(BaseModel):
    """Response model for 7-day rolling trend report."""

    start_date: Date = Field(description="Start date of the 7-day period")

    end_date: Date = Field(description="End date of the 7-day period")

    points: list[ReportPointDTO] = Field(
        description="Daily data points for the 7-day period, ordered chronologically"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "start_date": "2025-10-06",
                "end_date": "2025-10-12",
                "points": [
                    {
                        "date": "2025-10-06",
                        "calories": 1950.50,
                        "goal": 2000.00,
                        "protein": 150.00,
                        "fat": 70.00,
                        "carbs": 180.50,
                    },
                    {
                        "date": "2025-10-07",
                        "calories": 0.00,
                        "goal": 2000.00,
                        "protein": 0.00,
                        "fat": 0.00,
                        "carbs": 0.00,
                    },
                    {
                        "date": "2025-10-08",
                        "calories": 2100.00,
                        "goal": 2000.00,
                    },
                ],
            }
        },
    )

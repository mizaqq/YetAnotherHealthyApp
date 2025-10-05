"""Summary endpoint response models."""

from datetime import date as DateType
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.log import LogItemOutput, MealTotals


class MealSummary(BaseModel):
    """Summary of a single meal."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "meal_abc123",
                    "eaten_at": "2025-10-05T12:30:00Z",
                    "note": "Lunch",
                    "items": [
                        {
                            "food_id": "food_12345",
                            "label": "kurczak pierś",
                            "grams": 150.0,
                            "macros": {
                                "kcal": 247.5,
                                "protein_g": 46.5,
                                "fat_g": 5.4,
                                "carbs_g": 0.0,
                            },
                        }
                    ],
                    "totals": {"kcal": 247.5, "protein_g": 46.5, "fat_g": 5.4, "carbs_g": 0.0},
                }
            ]
        }
    )

    id: str = Field(
        ...,
        description="Unique meal identifier",
    )

    eaten_at: datetime = Field(
        ...,
        description="ISO 8601 timestamp when the meal was consumed",
    )

    note: str | None = Field(
        default=None,
        description="Optional user note about the meal",
    )

    items: list[LogItemOutput] = Field(
        ...,
        description="List of food items in this meal with computed macros",
    )

    totals: MealTotals = Field(
        ...,
        description="Total macros for this meal",
    )


class DayTotals(BaseModel):
    """Aggregate totals for a full day."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"kcal": 1850.0, "protein_g": 120.0, "fat_g": 65.0, "carbs_g": 180.0}]
        }
    )

    kcal: float = Field(
        ...,
        description="Total kilocalories for the day",
        ge=0.0,
    )

    protein_g: float = Field(
        ...,
        description="Total protein in grams for the day",
        ge=0.0,
    )

    fat_g: float = Field(
        ...,
        description="Total fat in grams for the day",
        ge=0.0,
    )

    carbs_g: float = Field(
        ...,
        description="Total carbohydrates in grams for the day",
        ge=0.0,
    )


class SummaryResponse(BaseModel):
    """Response body for GET /api/v1/summary."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "date": "2025-10-05",
                    "totals": {"kcal": 1850.0, "protein_g": 120.0, "fat_g": 65.0, "carbs_g": 180.0},
                    "meals": [
                        {
                            "id": "meal_abc123",
                            "eaten_at": "2025-10-05T12:30:00Z",
                            "note": "Lunch",
                            "items": [
                                {
                                    "food_id": "food_12345",
                                    "label": "kurczak pierś",
                                    "grams": 150.0,
                                    "macros": {
                                        "kcal": 247.5,
                                        "protein_g": 46.5,
                                        "fat_g": 5.4,
                                        "carbs_g": 0.0,
                                    },
                                }
                            ],
                            "totals": {
                                "kcal": 247.5,
                                "protein_g": 46.5,
                                "fat_g": 5.4,
                                "carbs_g": 0.0,
                            },
                        }
                    ],
                }
            ]
        }
    )

    date: DateType = Field(
        ...,
        description="Date for this summary (YYYY-MM-DD)",
    )

    totals: DayTotals = Field(
        ...,
        description="Aggregate totals for the entire day",
    )

    meals: list[MealSummary] = Field(
        ...,
        description="List of meals for this day ordered by eaten_at",
    )

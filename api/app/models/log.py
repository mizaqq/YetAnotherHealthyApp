"""Log endpoint request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogItemInput(BaseModel):
    """Input item for logging a meal."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"food_id": "food_12345", "label": "kurczak pierś", "grams": 150.0}]
        }
    )

    food_id: str = Field(
        ...,
        description="Unique food identifier from the database",
    )

    label: str = Field(
        ...,
        description="Food label for display purposes",
    )

    grams: float = Field(
        ...,
        description="Consumed quantity in grams",
        gt=0.0,
    )


class LogRequest(BaseModel):
    """Request body for POST /api/v1/log."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "eaten_at": "2025-10-05T12:30:00Z",
                    "note": "Lunch with colleagues",
                    "items": [
                        {"food_id": "food_12345", "label": "kurczak pierś", "grams": 150.0},
                        {"food_id": "food_67890", "label": "ryż biały", "grams": 100.0},
                    ],
                }
            ]
        }
    )

    eaten_at: datetime | None = Field(
        default=None,
        description="ISO 8601 timestamp when the meal was consumed; defaults to now if omitted",
    )

    note: str | None = Field(
        default=None,
        description="Optional user note about the meal",
        max_length=500,
    )

    items: list[LogItemInput] = Field(
        ...,
        description="List of food items consumed in this meal",
        min_length=1,
    )


class MealTotals(BaseModel):
    """Total macronutrients for a meal or day."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"kcal": 395.0, "protein_g": 59.5, "fat_g": 5.4, "carbs_g": 28.0}]
        }
    )

    kcal: float = Field(
        ...,
        description="Total kilocalories",
        ge=0.0,
    )

    protein_g: float = Field(
        ...,
        description="Total protein in grams",
        ge=0.0,
    )

    fat_g: float = Field(
        ...,
        description="Total fat in grams",
        ge=0.0,
    )

    carbs_g: float = Field(
        ...,
        description="Total carbohydrates in grams",
        ge=0.0,
    )


class LogItemOutput(BaseModel):
    """Output item with computed macros."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "food_id": "food_12345",
                    "label": "kurczak pierś",
                    "grams": 150.0,
                    "macros": {"kcal": 247.5, "protein_g": 46.5, "fat_g": 5.4, "carbs_g": 0.0},
                }
            ]
        }
    )

    food_id: str = Field(
        ...,
        description="Unique food identifier",
    )

    label: str = Field(
        ...,
        description="Food label",
    )

    grams: float = Field(
        ...,
        description="Consumed quantity in grams",
        gt=0.0,
    )

    macros: MealTotals = Field(
        ...,
        description="Computed macros for this item based on grams consumed",
    )


class LogResponse(BaseModel):
    """Response body for POST /api/v1/log."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "meal_id": "meal_abc123",
                    "totals": {"kcal": 395.0, "protein_g": 59.5, "fat_g": 5.4, "carbs_g": 28.0},
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
                }
            ]
        }
    )

    meal_id: str = Field(
        ...,
        description="Unique identifier for the logged meal",
    )

    totals: MealTotals = Field(
        ...,
        description="Total macros for the entire meal",
    )

    items: list[LogItemOutput] = Field(
        ...,
        description="List of items with computed macros",
    )

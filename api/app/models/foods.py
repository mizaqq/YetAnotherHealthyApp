"""Foods search endpoint response models."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.match import MacrosPer100g


class FoodItem(BaseModel):
    """A single food item from the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "food_12345",
                    "name": "Kurczak pierś bez skóry",
                    "brand": None,
                    "source": "usda",
                    "macros_per_100g": {
                        "kcal": 165.0,
                        "protein_g": 31.0,
                        "fat_g": 3.6,
                        "carbs_g": 0.0,
                    },
                },
                {
                    "id": "food_67890",
                    "name": "Mleko 2%",
                    "brand": "Łaciate",
                    "source": "branded",
                    "macros_per_100g": {
                        "kcal": 50.0,
                        "protein_g": 3.2,
                        "fat_g": 2.0,
                        "carbs_g": 4.8,
                    },
                },
            ]
        }
    )

    id: str = Field(
        ...,
        description="Unique food identifier",
    )

    name: str = Field(
        ...,
        description="Food name in Polish",
    )

    brand: str | None = Field(
        default=None,
        description="Brand name for branded foods",
    )

    source: str = Field(
        ...,
        description="Data source (e.g., 'usda', 'custom', 'branded')",
    )

    macros_per_100g: MacrosPer100g = Field(
        ...,
        description="Macronutrient values per 100g",
    )


class FoodSearchResponse(BaseModel):
    """Response body for GET /api/v1/foods/search."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "results": [
                        {
                            "id": "food_12345",
                            "name": "Kurczak pierś bez skóry",
                            "brand": None,
                            "source": "usda",
                            "macros_per_100g": {
                                "kcal": 165.0,
                                "protein_g": 31.0,
                                "fat_g": 3.6,
                                "carbs_g": 0.0,
                            },
                        }
                    ],
                    "total": 1,
                }
            ]
        }
    )

    results: list[FoodItem] = Field(
        ...,
        description="List of matching food items",
    )

    total: int = Field(
        ...,
        description="Total number of results found",
        ge=0,
    )

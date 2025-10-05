"""Match endpoint request/response models."""

from pydantic import BaseModel, ConfigDict, Field


class MatchItemInput(BaseModel):
    """Input item for food matching."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"label": "kurczak", "grams": 100.0},
                {"label": "mleko 2%", "grams": 250.0},
            ]
        }
    )

    label: str = Field(
        ...,
        description="Food label to search for in the database",
        min_length=1,
    )

    grams: float = Field(
        ...,
        description="Quantity in grams for this item",
        gt=0.0,
    )


class MatchRequest(BaseModel):
    """Request body for POST /api/v1/match."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"items": [{"label": "kurczak", "grams": 100.0}, {"label": "ryż", "grams": 80.0}]}
            ]
        }
    )

    items: list[MatchItemInput] = Field(
        ...,
        description="List of food items to match against the database",
        min_length=1,
    )


class MacrosPer100g(BaseModel):
    """Macronutrient values per 100g of food."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"kcal": 165.0, "protein_g": 31.0, "fat_g": 3.6, "carbs_g": 0.0}]
        }
    )

    kcal: float = Field(
        ...,
        description="Kilocalories per 100g",
        ge=0.0,
    )

    protein_g: float = Field(
        ...,
        description="Protein in grams per 100g",
        ge=0.0,
    )

    fat_g: float = Field(
        ...,
        description="Fat in grams per 100g",
        ge=0.0,
    )

    carbs_g: float = Field(
        ...,
        description="Carbohydrates in grams per 100g",
        ge=0.0,
    )


class MatchItemOutput(BaseModel):
    """A matched food item with metadata and macros."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "label": "kurczak",
                    "food_id": "food_12345",
                    "source": "usda",
                    "source_ref": "05006",
                    "match_score": 0.92,
                    "macros_per_100g": {
                        "kcal": 165.0,
                        "protein_g": 31.0,
                        "fat_g": 3.6,
                        "carbs_g": 0.0,
                    },
                }
            ]
        }
    )

    label: str = Field(
        ...,
        description="Matched food label from the database",
    )

    food_id: str = Field(
        ...,
        description="Unique food identifier in the database",
    )

    source: str = Field(
        ...,
        description="Data source (e.g., 'usda', 'custom', 'branded')",
    )

    source_ref: str | None = Field(
        default=None,
        description="External reference ID from the source database",
    )

    match_score: float = Field(
        ...,
        description="Hybrid search match score (0.0-1.0); higher is better",
        ge=0.0,
        le=1.0,
    )

    macros_per_100g: MacrosPer100g = Field(
        ...,
        description="Macronutrient values per 100g of this food",
    )


class MatchResponse(BaseModel):
    """Response body for POST /api/v1/match."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "matches": [
                        {
                            "label": "kurczak pierś bez skóry",
                            "food_id": "food_12345",
                            "source": "usda",
                            "source_ref": "05006",
                            "match_score": 0.92,
                            "macros_per_100g": {
                                "kcal": 165.0,
                                "protein_g": 31.0,
                                "fat_g": 3.6,
                                "carbs_g": 0.0,
                            },
                        }
                    ]
                }
            ]
        }
    )

    matches: list[MatchItemOutput] = Field(
        ...,
        description="List of matched food items ordered by match score (best first)",
    )

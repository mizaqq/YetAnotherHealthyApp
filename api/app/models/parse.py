"""Parse endpoint request/response models."""

from pydantic import BaseModel, ConfigDict, Field


class ParseRequest(BaseModel):
    """Request body for POST /api/v1/parse."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"text": "2 jajka, 100g kurczaka, szklanka mleka"},
                {"text": "duża kromka chleba z masłem"},
            ]
        }
    )

    text: str = Field(
        ...,
        description="Natural language description of consumed food items in Polish",
        min_length=1,
        max_length=2000,
    )


class ParsedItem(BaseModel):
    """A single parsed food item with optional quantity normalization."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"label": "jajko", "quantity_expr": "2 sztuki", "grams": 100.0, "confidence": 0.95},
                {"label": "kurczak", "quantity_expr": "100g", "grams": 100.0, "confidence": 1.0},
                {
                    "label": "mleko",
                    "quantity_expr": "szklanka",
                    "ml": 250.0,
                    "grams": 257.5,
                    "confidence": 0.85,
                },
            ]
        }
    )

    label: str = Field(
        ...,
        description="Normalized food label extracted from input text",
    )

    quantity_expr: str | None = Field(
        default=None,
        description="Original quantity expression as found in text (e.g., '2 sztuki', 'szklanka')",
    )

    grams: float | None = Field(
        default=None,
        description="Normalized quantity in grams; None if unable to normalize",
        ge=0.0,
    )

    ml: float | None = Field(
        default=None,
        description="Volume in milliliters if applicable; converted to grams using density",
        ge=0.0,
    )

    confidence: float = Field(
        ...,
        description="Confidence score for the parsing and normalization (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )


class ParseResponse(BaseModel):
    """Response body for POST /api/v1/parse."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "label": "jajko",
                            "quantity_expr": "2 sztuki",
                            "grams": 100.0,
                            "confidence": 0.95,
                        },
                        {
                            "label": "kurczak",
                            "quantity_expr": "100g",
                            "grams": 100.0,
                            "confidence": 1.0,
                        },
                    ],
                    "needs_clarification": False,
                },
                {
                    "items": [{"label": "jabłko", "quantity_expr": "duże", "confidence": 0.6}],
                    "needs_clarification": True,
                },
            ]
        }
    )

    items: list[ParsedItem] = Field(
        ...,
        description="List of parsed food items with normalized quantities",
    )

    needs_clarification: bool = Field(
        ...,
        description="True if input is ambiguous and requires user clarification",
    )

"""Pydantic models for analysis runs endpoint."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

# Type alias for analysis run status
AnalysisRunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]

# Type alias for sort fields
AnalysisRunSortField = Literal["created_at", "-created_at"]


class AnalysisRunCreateRequest(BaseModel):
    """Request model for creating a new analysis run.

    Used by POST /api/v1/analysis-runs to queue a new AI analysis
    for either an existing meal or raw text input.
    """

    meal_id: UUID | None = Field(
        default=None,
        description="Existing meal UUID to analyze (mutually exclusive with input_text)",
    )
    input_text: str | None = Field(
        default=None,
        description="Raw text description to analyze (mutually exclusive with meal_id)",
        min_length=1,
        max_length=2000,
    )
    threshold: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.8,
        description="Confidence threshold for matching (0-1)",
    )

    @field_validator("input_text")
    @classmethod
    def normalize_input_text(cls, v: str | None) -> str | None:
        """Strip whitespace and remove control characters from input text."""
        if v is None:
            return None

        # Strip leading/trailing whitespace
        normalized = v.strip()

        # Remove control characters (keep only printable + whitespace)
        normalized = "".join(char for char in normalized if char.isprintable() or char.isspace())

        # Re-validate length after normalization
        if not normalized:
            msg = "input_text cannot be empty after normalization"
            raise ValueError(msg)
        if len(normalized) > 2000:
            msg = "input_text exceeds 2000 characters after normalization"
            raise ValueError(msg)

        return normalized

    @model_validator(mode="after")
    def validate_mutual_exclusivity(self) -> "AnalysisRunCreateRequest":
        """Ensure exactly one of meal_id or input_text is provided."""
        has_meal = self.meal_id is not None
        has_text = self.input_text is not None

        if not has_meal and not has_text:
            msg = "Either meal_id or input_text must be provided"
            raise ValueError(msg)

        if has_meal and has_text:
            msg = "Only one of meal_id or input_text can be provided"
            raise ValueError(msg)

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "input_text": "Owsianka z bananem i miodem",
                    "threshold": 0.8,
                },
                {
                    "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                    "threshold": 0.75,
                },
            ]
        }
    )


class AnalysisRunQueuedResponse(BaseModel):
    """Response model for successfully queued analysis run.

    Returned by POST /api/v1/analysis-runs with 202 Accepted status.
    Contains minimal information about the created run.
    """

    id: UUID = Field(description="Unique analysis run identifier")
    meal_id: UUID | None = Field(
        default=None,
        description="Meal this analysis belongs to (null for ad-hoc text analysis)",
    )
    run_no: int = Field(description="Sequential run number for this meal", ge=1)
    status: AnalysisRunStatus = Field(
        description="Current status (typically 'queued' immediately after creation)"
    )
    threshold_used: Decimal = Field(
        description="Confidence threshold that will be applied (0-1)",
        ge=0,
        le=1,
    )
    model: str = Field(description="AI model identifier that will be used")
    retry_of_run_id: UUID | None = Field(
        default=None,
        description="Previous run being retried (if applicable)",
    )
    latency_ms: int | None = Field(
        default=None,
        description="Processing time (null until completed)",
        ge=0,
    )
    created_at: datetime = Field(description="When the analysis run was created")

    @field_serializer("threshold_used", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "223e4567-e89b-12d3-a456-426614174001",
                "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                "run_no": 1,
                "status": "queued",
                "threshold_used": 0.8,
                "model": "openrouter/gpt-4o-mini",
                "retry_of_run_id": None,
                "latency_ms": None,
                "created_at": "2025-10-12T07:29:30Z",
            }
        },
    )


class AnalysisRunDetailResponse(BaseModel):
    """Response model for detailed analysis run information.

    Used by GET /api/v1/analysis-runs/{run_id} to expose metadata
    about a single AI analysis execution.
    """

    id: UUID = Field(description="Unique analysis run identifier")
    meal_id: UUID | None = Field(
        default=None,
        description="Meal this analysis belongs to (null for ad-hoc text analysis)",
    )
    run_no: int = Field(description="Sequential run number for this meal", ge=1)
    status: AnalysisRunStatus = Field(
        description="Current status: queued, running, succeeded, failed, cancelled"
    )
    latency_ms: int | None = Field(
        default=None,
        description="Processing time in milliseconds",
        ge=0,
    )
    tokens: int | None = Field(
        default=None,
        description="Total tokens consumed by the model",
        ge=0,
    )
    cost_minor_units: int | None = Field(
        default=None,
        description="Cost in minor currency units (e.g., cents for USD)",
        ge=0,
    )
    cost_currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        max_length=3,
    )
    threshold_used: Decimal | None = Field(
        default=None,
        description="Confidence threshold applied during matching (0-1)",
        ge=0,
        le=1,
    )
    model: str = Field(description="AI model identifier used for analysis")
    retry_of_run_id: UUID | None = Field(
        default=None,
        description="Previous run that was retried (if applicable)",
    )
    error_code: str | None = Field(
        default=None,
        description="Error code if status is failed",
    )
    error_message: str | None = Field(
        default=None,
        description="Detailed error message if status is failed",
    )
    created_at: datetime = Field(description="When the analysis run was created")
    completed_at: datetime | None = Field(
        default=None,
        description="When the analysis run completed (NULL if still running)",
    )

    @field_serializer("threshold_used", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "223e4567-e89b-12d3-a456-426614174001",
                "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                "run_no": 2,
                "status": "failed",
                "latency_ms": 10500,
                "tokens": 2200,
                "cost_minor_units": 32,
                "cost_currency": "USD",
                "threshold_used": 0.8,
                "model": "openrouter/gpt-4o-mini",
                "retry_of_run_id": "113e4567-e89b-12d3-a456-426614174002",
                "error_code": "TIMEOUT",
                "error_message": "Model response exceeded limit",
                "created_at": "2025-10-12T07:40:00Z",
                "completed_at": "2025-10-12T07:40:11Z",
            }
        },
    )


class AnalysisRunListQuery(BaseModel):
    """Query parameters for listing analysis runs.

    Supports filtering by meal, status, date range, and cursor-based pagination.
    """

    meal_id: UUID | None = Field(
        default=None,
        description="Filter by specific meal UUID",
    )
    status: AnalysisRunStatus | None = Field(
        default=None,
        description="Filter by run status",
    )
    created_from: datetime | None = Field(
        default=None,
        description="Filter runs created on or after this timestamp (RFC3339)",
    )
    created_to: datetime | None = Field(
        default=None,
        description="Filter runs created on or before this timestamp (RFC3339)",
    )
    page_size: Annotated[int, Field(ge=1, le=50)] = Field(
        default=20,
        alias="page[size]",
        description="Number of items per page (1-50, default 20)",
    )
    page_after: str | None = Field(
        default=None,
        alias="page[after]",
        description="Opaque cursor for fetching next page",
    )
    sort: AnalysisRunSortField = Field(
        default="-created_at",
        description="Sort field (created_at or -created_at for descending)",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "AnalysisRunListQuery":
        """Ensure created_from <= created_to when both provided."""
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            msg = "created_from must be less than or equal to created_to"
            raise ValueError(msg)
        return self

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "succeeded",
                "created_from": "2025-10-01T00:00:00Z",
                "created_to": "2025-10-31T23:59:59Z",
                "page[size]": 20,
                "page[after]": None,
                "sort": "-created_at",
            }
        },
    )


class AnalysisRunSummaryResponse(BaseModel):
    """Summary information for a single analysis run in list view.

    Contains essential fields for displaying runs in a table or list.
    """

    id: UUID = Field(description="Unique analysis run identifier")
    meal_id: UUID | None = Field(
        default=None,
        description="Meal this analysis belongs to (null for ad-hoc text analysis)",
    )
    run_no: int = Field(description="Sequential run number for this meal", ge=1)
    status: AnalysisRunStatus = Field(description="Current run status")
    threshold_used: Decimal | None = Field(
        default=None,
        description="Confidence threshold applied (0-1)",
        ge=0,
        le=1,
    )
    model: str = Field(description="AI model identifier used")
    created_at: datetime = Field(description="When the analysis run was created")
    completed_at: datetime | None = Field(
        default=None,
        description="When the run completed (NULL if still running)",
    )

    @field_serializer("threshold_used", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "223e4567-e89b-12d3-a456-426614174001",
                "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                "run_no": 1,
                "status": "succeeded",
                "threshold_used": 0.8,
                "model": "openrouter/gpt-4o-mini",
                "created_at": "2025-10-12T07:29:30Z",
                "completed_at": "2025-10-12T07:29:39Z",
            }
        },
    )


class AnalysisRunRetryRequest(BaseModel):
    """Request model for retrying an analysis run.

    Allows optional override of threshold and raw_input from the source run.
    """

    threshold: Annotated[float, Field(ge=0.0, le=1.0)] | None = Field(
        default=None,
        description="Optional new confidence threshold (0-1). If omitted, uses source run's threshold.",
    )
    raw_input: dict | None = Field(
        default=None,
        description="Optional override for raw input. If omitted, uses source run's raw_input.",
    )

    @field_validator("raw_input")
    @classmethod
    def validate_raw_input_structure(cls, v: dict | None) -> dict | None:
        """Validate raw_input structure if provided."""
        if v is None:
            return None

        # Check for required 'text' field
        if "text" not in v:
            msg = "raw_input must contain 'text' field"
            raise ValueError(msg)

        text = v["text"]
        if not isinstance(text, str):
            msg = "raw_input.text must be a string"
            raise ValueError(msg)

        # Validate text length
        text_stripped = text.strip()
        if not text_stripped:
            msg = "raw_input.text cannot be empty"
            raise ValueError(msg)
        if len(text_stripped) > 2000:
            msg = "raw_input.text cannot exceed 2000 characters"
            raise ValueError(msg)

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "threshold": 0.75,
                },
                {
                    "raw_input": {
                        "text": "Owsianka z jabłkiem",
                        "overrides": {"excluded_ingredients": ["orzechy"]},
                    }
                },
                {
                    "threshold": 0.85,
                    "raw_input": {
                        "text": "Grillowany kurczak z ryżem i warzywami",
                    },
                },
            ]
        }
    )


class AnalysisRunItemResponse(BaseModel):
    """Response model for a single analysis run item (ingredient).

    Represents one ingredient identified by the AI analysis with
    nutritional data and confidence score.
    """

    id: UUID = Field(description="Unique identifier for this item")
    ordinal: int = Field(description="Position in the analysis (1-based)", gt=0)
    raw_name: str = Field(description="Ingredient name as returned by the AI model")
    raw_unit: str | None = Field(
        default=None,
        description="Unit as raw text (e.g. 'łyżka', 'szklanka')",
    )
    quantity: Decimal = Field(description="Quantity in the source unit", gt=0)
    unit_definition_id: UUID | None = Field(
        default=None,
        description="Normalized unit definition ID after matching",
    )
    product_id: UUID | None = Field(
        default=None,
        description="Matched product from canonical list (optional)",
    )
    product_portion_id: UUID | None = Field(
        default=None,
        description="Used product portion if available",
    )
    weight_grams: Decimal | None = Field(
        default=None,
        description="Weight converted to grams",
        ge=0,
    )
    confidence: Decimal = Field(
        description="Confidence score for the match (0-1)",
        ge=0,
        le=1,
    )
    calories: Decimal = Field(description="Calories for this ingredient", ge=0)
    protein: Decimal = Field(description="Protein in grams", ge=0)
    fat: Decimal = Field(description="Fat in grams", ge=0)
    carbs: Decimal = Field(description="Carbohydrates in grams", ge=0)

    @field_serializer(
        "quantity", "weight_grams", "confidence", "calories", "protein", "fat", "carbs"
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Serialize Decimal fields to float for JSON compatibility."""
        return float(value) if value is not None else None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "ordinal": 1,
                "raw_name": "płatki owsiane",
                "raw_unit": "łyżka",
                "quantity": 3.5,
                "unit_definition_id": "789e4567-e89b-12d3-a456-426614174000",
                "product_id": "456e4567-e89b-12d3-a456-426614174000",
                "product_portion_id": None,
                "weight_grams": 105.0,
                "confidence": 0.92,
                "calories": 380.0,
                "protein": 13.0,
                "fat": 7.0,
                "carbs": 65.0,
            }
        }
    )


class AnalysisRunItemsResponse(BaseModel):
    """Response model for GET /api/v1/analysis-runs/{run_id}/items.

    Returns the list of ingredients (items) generated during an analysis run
    with nutritional details and confidence scores.
    """

    run_id: UUID = Field(description="Analysis run identifier")
    model: str = Field(description="AI model used for analysis")
    items: list[AnalysisRunItemResponse] = Field(
        description="List of ingredients sorted by ordinal"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "model": "openrouter/gpt-4o-mini",
                "items": [
                    {
                        "id": "234e4567-e89b-12d3-a456-426614174000",
                        "ordinal": 1,
                        "raw_name": "płatki owsiane",
                        "raw_unit": "łyżka",
                        "quantity": 3.5,
                        "unit_definition_id": "789e4567-e89b-12d3-a456-426614174000",
                        "product_id": "456e4567-e89b-12d3-a456-426614174000",
                        "product_portion_id": None,
                        "weight_grams": 105.0,
                        "confidence": 0.92,
                        "calories": 380.0,
                        "protein": 13.0,
                        "fat": 7.0,
                        "carbs": 65.0,
                    }
                ],
            }
        }
    )


class AnalysisRunCancelResponse(BaseModel):
    """Response model for POST /api/v1/analysis-runs/{run_id}/cancel.

    Returns the final state of the analysis run after cancellation.
    """

    id: UUID = Field(description="Analysis run identifier")
    status: AnalysisRunStatus = Field(description="Run status (should be 'cancelled')")
    model: str = Field(description="AI model used for this run")
    cancelled_at: datetime | None = Field(
        default=None,
        description="Timestamp when the run was cancelled",
    )
    error_code: str | None = Field(
        default=None,
        description="Error code (e.g., USER_CANCELLED)",
    )
    error_message: str | None = Field(
        default=None,
        description="Human-readable error message if any",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "cancelled",
                "model": "openrouter/gpt-4o-mini",
                "cancelled_at": "2025-10-12T07:45:00Z",
                "error_code": "USER_CANCELLED",
                "error_message": None,
            }
        }
    )

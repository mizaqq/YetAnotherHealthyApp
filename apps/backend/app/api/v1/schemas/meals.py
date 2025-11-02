"""Pydantic models for meals endpoint."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

if TYPE_CHECKING:
    from decimal import Decimal
else:
    from decimal import Decimal  # type: ignore[TCH003]


class MealSource(str, Enum):
    """Enumeration of valid meal data sources."""

    AI = "ai"
    EDITED = "edited"
    MANUAL = "manual"


class MealListQuery(BaseModel):
    """Query parameters for listing meals with filtering and pagination."""

    from_date: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Start of date range filter (ISO8601 format)",
            alias="from",
        ),
    ] = None

    to_date: Annotated[
        datetime | None,
        Field(
            default=None,
            description="End of date range filter (ISO8601 format)",
            alias="to",
        ),
    ] = None

    category: Annotated[
        str | None,
        Field(
            default=None,
            max_length=50,
            description="Filter by meal category code",
        ),
    ] = None

    source: Annotated[
        MealSource | None,
        Field(
            default=None,
            description="Filter by meal data source",
        ),
    ] = None

    include_deleted: Annotated[
        bool,
        Field(
            default=False,
            description="Include soft-deleted meals in results",
        ),
    ] = False

    page_size: Annotated[
        int,
        Field(
            default=20,
            ge=1,
            le=100,
            description="Number of results per page",
            alias="page[size]",
        ),
    ] = 20

    page_after: Annotated[
        str | None,
        Field(
            default=None,
            description="Cursor for pagination (base64 encoded JSON)",
            alias="page[after]",
        ),
    ] = None

    sort: Annotated[
        str,
        Field(
            default="-eaten_at",
            description="Sort field and direction (eaten_at or -eaten_at)",
        ),
    ] = "-eaten_at"

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime | None) -> datetime | None:
        """Parse ISO8601 datetime strings."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid datetime format: {v}") from exc

    @field_validator("to_date")
    @classmethod
    def validate_date_range(cls, v: datetime | None, info: object) -> datetime | None:
        """Ensure 'to' date is not before 'from' date."""
        if v is None:
            return None
        from_date = info.data.get("from_date")
        if from_date and v < from_date:
            raise ValueError("'to' date must be greater than or equal to 'from' date")
        return v

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        """Validate sort parameter to prevent SQL injection."""
        allowed_sorts = {"eaten_at", "-eaten_at"}
        if v not in allowed_sorts:
            raise ValueError(f"Invalid sort field. Allowed: {', '.join(allowed_sorts)}")
        return v


class MealCursorData(BaseModel):
    """Internal structure for cursor pagination based on eaten_at and id."""

    last_eaten_at: datetime
    last_id: UUID

    model_config = ConfigDict(extra="forbid")


class PageInfo(BaseModel):
    """Pagination metadata."""

    size: int
    after: str | None = None

    model_config = ConfigDict(extra="forbid")


class MealListItem(BaseModel):
    """Meal summary for list views."""

    id: UUID
    category: str
    eaten_at: datetime
    calories: Annotated[
        Decimal,
        Field(
            description="Total calories in kcal",
            ge=0,
            decimal_places=2,
        ),
    ]
    protein: Annotated[
        Decimal | None,
        Field(
            description="Total protein in grams",
            ge=0,
            decimal_places=2,
        ),
    ] = None
    fat: Annotated[
        Decimal | None,
        Field(
            description="Total fat in grams",
            ge=0,
            decimal_places=2,
        ),
    ] = None
    carbs: Annotated[
        Decimal | None,
        Field(
            description="Total carbohydrates in grams",
            ge=0,
            decimal_places=2,
        ),
    ] = None
    source: MealSource
    accepted_analysis_run_id: UUID | None = None

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories", "protein", "fat", "carbs")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        if value is None:
            return None
        return float(value)


class MealListResponse(BaseModel):
    """Response model for paginated meal list."""

    data: list[MealListItem]
    page: PageInfo

    model_config = ConfigDict(extra="forbid")


class MealSearchFilter(BaseModel):
    """Encapsulates meal search criteria and pagination."""

    user_id: UUID
    from_date: datetime | None = None
    to_date: datetime | None = None
    category: str | None = None
    source: MealSource | None = None
    include_deleted: bool = False
    page_size: int = 20
    cursor: MealCursorData | None = None
    sort_desc: bool = True  # True for -eaten_at, False for eaten_at

    model_config = ConfigDict(extra="forbid")


# Cursor encoding/decoding utilities


def encode_meal_cursor(*, last_eaten_at: datetime, last_id: UUID) -> str:
    """Encode cursor data to base64 string.

    Args:
        last_eaten_at: Timestamp of last meal item
        last_id: UUID of last meal item

    Returns:
        Base64 encoded cursor string
    """
    cursor_data = {
        "last_eaten_at": last_eaten_at.isoformat(),
        "last_id": str(last_id),
    }
    json_str = json.dumps(cursor_data, separators=(",", ":"))
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_meal_cursor(cursor: str) -> MealCursorData:
    """Decode base64 cursor string to MealCursorData.

    Args:
        cursor: Base64 encoded cursor string

    Returns:
        MealCursorData instance

    Raises:
        ValueError: If cursor format is invalid
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(json_str)
        return MealCursorData(
            last_eaten_at=datetime.fromisoformat(data["last_eaten_at"]),
            last_id=UUID(data["last_id"]),
        )
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc


# ============================================================================
# POST /api/v1/meals - Create Meal Schemas
# ============================================================================


class MealCreatePayload(BaseModel):
    """Request payload for creating a new meal with conditional validation.

    Validation rules based on source:
    - AI/EDITED: requires protein, fat, carbs, analysis_run_id
    - MANUAL: forbids protein, fat, carbs, analysis_run_id
    """

    category: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="Meal category code (must exist in meal_categories)",
        ),
    ]

    eaten_at: Annotated[
        datetime,
        Field(description="When the meal was consumed (ISO8601 format, UTC-aware)"),
    ]

    source: Annotated[
        MealSource,
        Field(description="Data source: ai, edited, or manual"),
    ]

    calories: Annotated[
        Decimal,
        Field(
            ge=0,
            decimal_places=2,
            description="Total calories (kcal), must be >= 0",
        ),
    ]

    protein: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            decimal_places=2,
            description="Protein in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    fat: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            decimal_places=2,
            description="Fat in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    carbs: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            decimal_places=2,
            description="Carbohydrates in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    analysis_run_id: Annotated[
        UUID | None,
        Field(
            default=None,
            description=(
                "Reference to accepted analysis run (required for ai/edited, forbidden for manual)"
            ),
        ),
    ] = None

    @field_validator("eaten_at")
    @classmethod
    def validate_eaten_at(cls, v: datetime) -> datetime:
        """Ensure eaten_at is timezone-aware (UTC)."""
        if v.tzinfo is None:
            msg = "eaten_at must be timezone-aware (UTC)"
            raise ValueError(msg)
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Normalize category to lowercase and strip whitespace."""
        return v.strip().lower()

    def model_post_init(self, __context: object) -> None:
        """Validate conditional requirements based on source after model initialization."""
        if self.source in (MealSource.AI, MealSource.EDITED):
            # AI and EDITED require macros and analysis_run_id
            missing_fields = []
            if self.protein is None:
                missing_fields.append("protein")
            if self.fat is None:
                missing_fields.append("fat")
            if self.carbs is None:
                missing_fields.append("carbs")
            if self.analysis_run_id is None:
                missing_fields.append("analysis_run_id")

            if missing_fields:
                fields_list = ", ".join(missing_fields)
                msg = f"For source '{self.source.value}', these fields are required: {fields_list}"
                raise ValueError(msg)

        elif self.source == MealSource.MANUAL:
            # MANUAL forbids macros and analysis_run_id
            forbidden_fields = []
            if self.protein is not None:
                forbidden_fields.append("protein")
            if self.fat is not None:
                forbidden_fields.append("fat")
            if self.carbs is not None:
                forbidden_fields.append("carbs")
            if self.analysis_run_id is not None:
                forbidden_fields.append("analysis_run_id")

            if forbidden_fields:
                fields_list = ", ".join(forbidden_fields)
                msg = f"For source 'manual', these fields must not be provided: {fields_list}"
                raise ValueError(msg)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "category": "breakfast",
                    "eaten_at": "2025-01-15T08:30:00Z",
                    "source": "ai",
                    "calories": 450.50,
                    "protein": 25.5,
                    "fat": 18.0,
                    "carbs": 42.0,
                    "analysis_run_id": "223e4567-e89b-12d3-a456-426614174001",
                    "notes": "Scrambled eggs with toast",
                },
                {
                    "category": "lunch",
                    "eaten_at": "2025-01-15T13:00:00Z",
                    "source": "manual",
                    "calories": 600.0,
                    "notes": "Restaurant meal, estimate only",
                },
            ]
        }
    )


class MealResponse(BaseModel):
    """Response model for a single meal with all details."""

    id: UUID = Field(description="Unique meal identifier")
    user_id: UUID = Field(description="User who owns this meal")
    category: str = Field(description="Meal category code")
    eaten_at: datetime = Field(description="When the meal was consumed")
    source: MealSource = Field(description="Data source: ai, edited, or manual")
    calories: Decimal = Field(description="Total calories (kcal)")
    protein: Decimal | None = Field(default=None, description="Protein in grams")
    fat: Decimal | None = Field(default=None, description="Fat in grams")
    carbs: Decimal | None = Field(default=None, description="Carbohydrates in grams")
    accepted_analysis_run_id: UUID | None = Field(
        default=None, description="Reference to accepted analysis run"
    )
    created_at: datetime = Field(description="When the record was created")
    updated_at: datetime = Field(description="When the record was last updated")
    deleted_at: datetime | None = Field(default=None, description="Soft delete timestamp")

    @field_serializer("calories", "protein", "fat", "carbs", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987e4567-e89b-12d3-a456-426614174999",
                "category": "breakfast",
                "eaten_at": "2025-01-15T08:30:00Z",
                "source": "ai",
                "calories": 450.50,
                "protein": 25.5,
                "fat": 18.0,
                "carbs": 42.0,
                "accepted_analysis_run_id": "223e4567-e89b-12d3-a456-426614174001",
                "notes": "Scrambled eggs with toast",
                "created_at": "2025-01-15T08:35:00Z",
                "updated_at": "2025-01-15T08:35:00Z",
                "deleted_at": None,
            }
        },
    )


# ============================================================================
# Schemas for GET /api/v1/meals/{meal_id} endpoint
# ============================================================================


class MealDetailParams(BaseModel):
    """Query parameters for meal detail endpoint."""

    include_analysis_items: Annotated[
        bool,
        Field(
            default=False,
            description="Include analysis run items (ingredients) in response",
        ),
    ] = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "include_analysis_items": True,
            }
        }
    )


class MealAnalysisItem(BaseModel):
    """Single ingredient item from an analysis run."""

    id: UUID = Field(description="Item identifier")
    ordinal: int = Field(description="Position in the list (1-based)", ge=1)
    raw_name: str = Field(description="Original ingredient name from user input")
    raw_unit: str | None = Field(default=None, description="Original unit from input")
    product_id: UUID | None = Field(default=None, description="Matched product from database")
    quantity: Decimal = Field(description="Amount of ingredient", gt=0)
    unit_definition_id: UUID | None = Field(default=None, description="Matched unit definition")
    product_portion_id: UUID | None = Field(default=None, description="Matched product portion")
    weight_grams: Decimal | None = Field(
        default=None, description="Weight in grams if calculated", ge=0
    )
    confidence: Decimal | None = Field(
        default=None, description="AI confidence score (0-1)", ge=0, le=1
    )
    calories: Decimal | None = Field(default=None, description="Calories (kcal)", ge=0)
    protein: Decimal | None = Field(default=None, description="Protein in grams", ge=0)
    fat: Decimal | None = Field(default=None, description="Fat in grams", ge=0)
    carbs: Decimal | None = Field(default=None, description="Carbohydrates in grams", ge=0)
    created_at: datetime = Field(description="When item was created")

    @field_serializer(
        "quantity",
        "weight_grams",
        "confidence",
        "calories",
        "protein",
        "fat",
        "carbs",
        when_used="json",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(from_attributes=True)


class MealAnalysisRun(BaseModel):
    """Analysis run metadata for a meal."""

    id: UUID = Field(description="Analysis run identifier")
    run_no: int = Field(description="Sequential run number for this meal", ge=1)
    status: str = Field(description="Run status: pending, succeeded, failed")
    model: str = Field(description="AI model used for analysis")
    latency_ms: int | None = Field(
        default=None, description="Processing time in milliseconds", ge=0
    )
    tokens: int | None = Field(default=None, description="Tokens consumed", ge=0)
    cost_minor_units: int | None = Field(
        default=None, description="Cost in minor currency units", ge=0
    )
    cost_currency: str = Field(default="USD", description="Currency code")
    threshold_used: Decimal | None = Field(
        default=None, description="Confidence threshold applied (0-1)", ge=0, le=1
    )
    retry_of_run_id: UUID | None = Field(default=None, description="Previous run that was retried")
    error_code: str | None = Field(default=None, description="Error code if failed")
    error_message: str | None = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(description="When analysis started")
    completed_at: datetime | None = Field(default=None, description="When analysis completed")
    items: list[MealAnalysisItem] | None = Field(
        default=None, description="Ingredient items (if requested)"
    )

    @field_serializer("threshold_used", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(from_attributes=True)


class MealDetailResponse(BaseModel):
    """Detailed meal response including optional analysis data."""

    id: UUID = Field(description="Meal identifier")
    user_id: UUID = Field(description="Owner of the meal")
    category: str = Field(description="Meal category code")
    eaten_at: datetime = Field(description="When the meal was eaten")
    source: MealSource = Field(description="Data source: ai, edited, or manual")
    calories: Decimal = Field(description="Total calories (kcal)")
    protein: Decimal | None = Field(default=None, description="Protein in grams")
    fat: Decimal | None = Field(default=None, description="Fat in grams")
    carbs: Decimal | None = Field(default=None, description="Carbohydrates in grams")
    created_at: datetime = Field(description="When the record was created")
    updated_at: datetime = Field(description="When the record was last updated")
    deleted_at: datetime | None = Field(default=None, description="Soft delete timestamp")
    analysis: MealAnalysisRun | None = Field(
        default=None, description="Analysis run data (if meal has accepted analysis)"
    )

    @field_serializer("calories", "protein", "fat", "carbs", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987e4567-e89b-12d3-a456-426614174999",
                "category": "breakfast",
                "eaten_at": "2025-01-15T08:30:00Z",
                "source": "ai",
                "calories": 450.50,
                "protein": 25.5,
                "fat": 18.0,
                "carbs": 42.0,
                "notes": "Scrambled eggs with toast",
                "created_at": "2025-01-15T08:35:00Z",
                "updated_at": "2025-01-15T08:35:00Z",
                "deleted_at": None,
                "analysis": {
                    "id": "223e4567-e89b-12d3-a456-426614174001",
                    "run_no": 1,
                    "status": "succeeded",
                    "model": "gpt-4",
                    "latency_ms": 1500,
                    "tokens": 250,
                    "items": None,
                },
            }
        },
    )


class MealUpdatePayload(BaseModel):
    """Payload for updating an existing meal.

    All fields are optional, but at least one field must be provided.
    Conditional validation applies based on source (if provided):
    - AI/EDITED: require protein, fat, carbs, analysis_run_id
    - MANUAL: forbid protein, fat, carbs, analysis_run_id

    Business rule: source cannot be changed back to 'manual' if macros
    or analysis_run_id are already set (enforced in service layer).
    """

    category: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=50,
            description="Meal category code (must exist in meal_categories)",
        ),
    ] = None

    eaten_at: Annotated[
        datetime | None,
        Field(
            default=None,
            description="When the meal was eaten (ISO8601 timestamp)",
        ),
    ] = None

    source: Annotated[
        MealSource | None,
        Field(
            default=None,
            description="Data source (ai, edited, manual)",
        ),
    ] = None

    calories: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            description="Total calories (must be >= 0)",
        ),
    ] = None

    protein: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            description="Protein in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    fat: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            description="Fat in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    carbs: Annotated[
        Decimal | None,
        Field(
            default=None,
            ge=0,
            description="Carbs in grams (required for ai/edited, forbidden for manual)",
        ),
    ] = None

    analysis_run_id: Annotated[
        UUID | None,
        Field(
            default=None,
            description=(
                "Reference to accepted analysis run (required for ai/edited, forbidden for manual)"
            ),
        ),
    ] = None

    notes: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1000,
            description="Optional notes about the meal",
        ),
    ] = None

    def model_post_init(self, __context: object) -> None:
        """Validate conditional requirements based on source if provided."""
        # Only validate if source is being changed
        if self.source is None:
            return

        # For AI/EDITED sources: if any macro or analysis_run_id is provided,
        # all must be provided (partial updates not allowed for consistency)
        if self.source in (MealSource.AI, MealSource.EDITED):
            macro_fields = [
                ("protein", self.protein),
                ("fat", self.fat),
                ("carbs", self.carbs),
                ("analysis_run_id", self.analysis_run_id),
            ]
            provided_fields = [name for name, value in macro_fields if value is not None]

            # If any macro field is provided when changing to AI/EDITED,
            # all must be provided
            if provided_fields and len(provided_fields) < 4:
                missing_fields = [name for name, value in macro_fields if value is None]
                fields_list = ", ".join(missing_fields)
                msg = (
                    f"When changing source to '{self.source.value}', "
                    f"if any macro is provided, all must be provided. "
                    f"Missing: {fields_list}"
                )
                raise ValueError(msg)

        # For MANUAL source: macros and analysis_run_id must NOT be provided
        elif self.source == MealSource.MANUAL:
            forbidden_fields = []
            if self.protein is not None:
                forbidden_fields.append("protein")
            if self.fat is not None:
                forbidden_fields.append("fat")
            if self.carbs is not None:
                forbidden_fields.append("carbs")
            if self.analysis_run_id is not None:
                forbidden_fields.append("analysis_run_id")

            if forbidden_fields:
                fields_list = ", ".join(forbidden_fields)
                msg = (
                    f"When changing source to 'manual', "
                    f"these fields must not be provided: {fields_list}"
                )
                raise ValueError(msg)

    @field_validator("eaten_at", mode="before")
    @classmethod
    def parse_datetime_update(cls, v: str | datetime | None) -> datetime | None:
        """Parse ISO8601 string to datetime if needed."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"Invalid datetime format: {v}") from exc
        raise ValueError(f"Unsupported datetime type: {type(v)}")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "category": "lunch",
                "eaten_at": "2025-01-15T13:30:00Z",
                "calories": 550.0,
                "notes": "Updated meal description",
            }
        },
    )

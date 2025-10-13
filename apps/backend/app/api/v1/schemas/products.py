"""Pydantic models for products endpoint."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ProductSource(str, Enum):
    """Enumeration of valid product data sources."""

    OPEN_FOOD_FACTS = "open_food_facts"
    USER_DEFINED = "user_defined"
    MANUAL = "manual"
    USDA_SR_LEGACY = "usda_sr_legacy"


class SearchMode(str, Enum):
    """Search mode for product queries."""

    SIMPLE = "simple"  # Basic ILIKE search (default, backward compatible)
    FULLTEXT = "fulltext"  # Full-text search with word stemming
    FUZZY = "fuzzy"  # Trigram similarity search (typo-tolerant)


class MacroBreakdownDTO(BaseModel):
    """Macronutrient breakdown per 100g."""

    calories: Annotated[
        Decimal,
        Field(
            description="Calories in kcal per 100g",
            ge=0,
            decimal_places=2,
        ),
    ]

    protein: Annotated[
        Decimal,
        Field(
            description="Protein in grams per 100g",
            ge=0,
            decimal_places=2,
        ),
    ]

    fat: Annotated[
        Decimal,
        Field(
            description="Fat in grams per 100g",
            ge=0,
            decimal_places=2,
        ),
    ]

    carbs: Annotated[
        Decimal,
        Field(
            description="Carbohydrates in grams per 100g",
            ge=0,
            decimal_places=2,
        ),
    ]

    model_config = ConfigDict(extra="forbid")

    @field_serializer("calories", "protein", "fat", "carbs")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class ProductListParams(BaseModel):
    """Query parameters for listing products with filtering and pagination."""

    search: Annotated[
        str | None,
        Field(
            default=None,
            min_length=2,
            max_length=200,
            description="Case-insensitive search on product name (min 2 chars)",
        ),
    ] = None

    search_mode: Annotated[
        SearchMode,
        Field(
            default=SearchMode.FULLTEXT,
            description="Search mode: simple (ILIKE), fulltext (word matching), fuzzy (typo-tolerant)",
            alias="search_mode",
        ),
    ] = SearchMode.FULLTEXT

    off_id: Annotated[
        str | None,
        Field(
            default=None,
            max_length=100,
            description="Filter by Open Food Facts identifier",
        ),
    ] = None

    source: Annotated[
        ProductSource | None,
        Field(
            default=None,
            description="Filter by product data source",
        ),
    ] = None

    page_size: Annotated[
        int,
        Field(
            default=20,
            ge=1,
            le=50,
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

    include_macros: Annotated[
        bool,
        Field(
            default=False,
            description="Include macronutrient breakdown in response",
            alias="include_macros",
        ),
    ] = False

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("search")
    @classmethod
    def sanitize_search(cls, v: str | None) -> str | None:
        """Trim and sanitize search input."""
        if v is None:
            return None
        # Trim whitespace and remove control characters
        sanitized = v.strip()
        if not sanitized or len(sanitized) < 2:
            return None
        # Remove any control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32)
        return sanitized if len(sanitized) >= 2 else None

    @field_validator("off_id")
    @classmethod
    def sanitize_off_id(cls, v: str | None) -> str | None:
        """Trim OFF ID."""
        if v is None:
            return None
        sanitized = v.strip()
        return sanitized if sanitized else None


class ProductDetailParams(BaseModel):
    """Query parameters for retrieving product detail."""

    include_portions: Annotated[
        bool,
        Field(
            default=False,
            description="Include portion definitions in response",
            alias="include_portions",
        ),
    ] = False

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CursorData(BaseModel):
    """Internal structure for cursor pagination based on created_at and id."""

    last_created_at: datetime
    last_id: UUID

    model_config = ConfigDict(extra="forbid")


class PageInfo(BaseModel):
    """Pagination metadata."""

    size: int
    after: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProductPortionDTO(BaseModel):
    """Product portion definition."""

    id: UUID
    unit_definition_id: UUID
    grams_per_portion: Annotated[
        Decimal,
        Field(
            description="Mass of one portion in grams",
            gt=0,
            decimal_places=4,
        ),
    ]
    is_default: bool
    source: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_serializer("grams_per_portion")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class ProductSummaryDTO(BaseModel):
    """Product summary for list views."""

    id: UUID
    name: str
    source: ProductSource
    macros_per_100g: MacroBreakdownDTO | None = None
    # Internal field for cursor pagination - not serialized in API response
    created_at: datetime | None = Field(default=None, exclude=True)

    model_config = ConfigDict(extra="forbid")


class ProductDetailDTO(BaseModel):
    """Detailed product information."""

    id: UUID
    name: str
    source: ProductSource
    off_id: str | None = None
    macros_per_100g: MacroBreakdownDTO
    created_at: datetime
    updated_at: datetime
    portions: list[ProductPortionDTO] | None = None

    model_config = ConfigDict(extra="forbid")


class ProductsListResponse(BaseModel):
    """Response model for paginated product list."""

    data: list[ProductSummaryDTO]
    page: PageInfo

    model_config = ConfigDict(extra="forbid")


class ProductPortionsResponse(BaseModel):
    """Response model for product portions list."""

    product_id: UUID
    portions: list[ProductPortionDTO]

    model_config = ConfigDict(extra="forbid")


# Cursor encoding/decoding utilities


def encode_cursor(*, last_created_at: datetime, last_id: UUID) -> str:
    """Encode cursor data to base64 string.

    Args:
        last_created_at: Timestamp of last item
        last_id: UUID of last item

    Returns:
        Base64 encoded cursor string
    """
    cursor_data = {
        "last_created_at": last_created_at.isoformat(),
        "last_id": str(last_id),
    }
    json_str = json.dumps(cursor_data, separators=(",", ":"))
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> CursorData:
    """Decode base64 cursor string to CursorData.

    Args:
        cursor: Base64 encoded cursor string

    Returns:
        CursorData instance

    Raises:
        ValueError: If cursor format is invalid
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(json_str)
        return CursorData(
            last_created_at=datetime.fromisoformat(data["last_created_at"]),
            last_id=UUID(data["last_id"]),
        )
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc


# Domain command models


class ProductSearchFilter(BaseModel):
    """Encapsulates product search criteria and pagination."""

    search: str | None = None
    search_mode: SearchMode = SearchMode.FULLTEXT
    off_id: str | None = None
    source: ProductSource | None = None
    page_size: int = 20
    cursor: CursorData | None = None
    include_macros: bool = False

    model_config = ConfigDict(extra="forbid")


class ProductLookupCommand(BaseModel):
    """Command to fetch a single product with optional portions."""

    product_id: UUID
    include_portions: bool = False

    model_config = ConfigDict(extra="forbid")

"""Pydantic models for units endpoint."""

from __future__ import annotations

import base64
import json
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class UnitType(str, Enum):
    """Enumeration of valid unit types."""

    MASS = "mass"
    PIECE = "piece"
    PORTION = "portion"
    UTENSIL = "utensil"


class UnitsListQuery(BaseModel):
    """Query parameters for listing units with filtering and pagination."""

    unit_type: Annotated[
        UnitType | None,
        Field(
            default=None,
            description="Filter by unit type classification",
        ),
    ] = None

    search: Annotated[
        str | None,
        Field(
            default=None,
            max_length=100,
            description="Case-insensitive search on unit code",
        ),
    ] = None

    page_size: Annotated[
        int,
        Field(
            default=50,
            ge=1,
            le=100,
            description="Number of results per page",
            alias="page[size]",
        ),
    ] = 50

    page_after: Annotated[
        str | None,
        Field(
            default=None,
            description="Cursor for pagination (base64 encoded JSON)",
            alias="page[after]",
        ),
    ] = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("search")
    @classmethod
    def sanitize_search(cls, v: str | None) -> str | None:
        """Trim and sanitize search input."""
        if v is None:
            return None
        # Trim whitespace and remove control characters
        sanitized = v.strip()
        if not sanitized:
            return None
        # Remove any control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32)
        return sanitized if sanitized else None


class CursorData(BaseModel):
    """Internal structure for cursor pagination."""

    last_id: UUID
    last_code: str

    model_config = ConfigDict(extra="forbid")


class PageInfo(BaseModel):
    """Pagination metadata."""

    size: int
    after: str | None = None

    model_config = ConfigDict(extra="forbid")


class UnitDefinition(BaseModel):
    """Single unit definition returned by the API."""

    id: UUID
    code: str
    unit_type: str
    grams_per_unit: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("grams_per_unit")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal to string to avoid precision loss."""
        return str(value)


class UnitsListResponse(BaseModel):
    """Envelope for the units list response with pagination."""

    data: list[UnitDefinition]
    page: PageInfo

    model_config = ConfigDict(from_attributes=True)


class UnitAliasesQuery(BaseModel):
    """Query parameters for unit aliases endpoint."""

    locale: Annotated[
        str,
        Field(
            default="pl-PL",
            max_length=5,
            pattern=r"^[a-z]{2}-[A-Z]{2}$",
            description="BCP 47 locale code (e.g. pl-PL)",
        ),
    ] = "pl-PL"

    model_config = ConfigDict(extra="forbid")


class UnitAlias(BaseModel):
    """Single unit alias with localization info."""

    alias: str
    locale: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class UnitAliasesResponse(BaseModel):
    """Envelope for unit aliases response."""

    unit_id: UUID
    aliases: list[UnitAlias]

    model_config = ConfigDict(from_attributes=True)


def encode_cursor(last_id: UUID, last_code: str) -> str:
    """Encode cursor data to base64 JSON string."""
    cursor_data = CursorData(last_id=last_id, last_code=last_code)
    json_str = cursor_data.model_dump_json()
    return base64.b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> CursorData:
    """Decode base64 JSON cursor string.

    Args:
        cursor: Base64 encoded JSON cursor string

    Returns:
        CursorData with last_id and last_code

    Raises:
        ValueError: If cursor format is invalid
    """
    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        cursor_data = CursorData.model_validate_json(decoded)
        return cursor_data
    except (ValueError, json.JSONDecodeError, Exception) as exc:
        raise ValueError(f"Invalid cursor format: {exc}") from exc

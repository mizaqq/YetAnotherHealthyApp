"""Cursor-based pagination utilities for API endpoints."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    """Metadata for paginated responses.

    Contains information about current page size and cursor for next page.
    """

    size: int = Field(description="Number of items in current page", ge=0)
    after: str | None = Field(
        default=None,
        description="Opaque cursor for fetching next page (null if no more pages)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "size": 20,
                "after": "eyJjcmVhdGVkX2F0IjoiMjAyNS0xMC0xMlQwNzoyOTozMFoiLCJpZCI6IjEyM2U0NTY3LWU4OWItMTJkMy1hNDU2LTQyNjYxNDE3NDAwMCJ9",
            }
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Wraps a list of items with pagination metadata.
    """

    data: list[T] = Field(description="Array of items in current page")
    page: PageMeta = Field(description="Pagination metadata")


class AnalysisRunCursor(BaseModel):
    """Cursor for analysis runs pagination.

    Encodes sorting key (created_at) and unique identifier (id) for stable pagination.
    """

    created_at: datetime = Field(description="Timestamp used for sorting")
    id: UUID = Field(description="Unique run ID for tie-breaking")

    @classmethod
    def decode(cls, cursor_str: str) -> AnalysisRunCursor:
        """Decode base64-encoded cursor string to cursor object.

        Args:
            cursor_str: Base64-encoded JSON cursor

        Returns:
            Decoded cursor object

        Raises:
            ValueError: If cursor is malformed or cannot be decoded
        """
        try:
            # Decode base64
            decoded_bytes = base64.urlsafe_b64decode(cursor_str)
            decoded_str = decoded_bytes.decode("utf-8")

            # Parse JSON
            data = json.loads(decoded_str)

            # Validate and construct cursor
            return cls(**data)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            msg = "Invalid cursor format"
            raise ValueError(msg) from exc

    def encode(self) -> str:
        """Encode cursor object to base64 string.

        Returns:
            Base64-encoded JSON cursor suitable for page[after] parameter
        """
        # Serialize to JSON with ISO datetime
        data = {
            "created_at": self.created_at.isoformat(),
            "id": str(self.id),
        }
        json_str = json.dumps(data, separators=(",", ":"))

        # Encode to base64
        encoded_bytes = base64.urlsafe_b64encode(json_str.encode("utf-8"))
        return encoded_bytes.decode("utf-8")

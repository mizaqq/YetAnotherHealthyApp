"""Repository for accessing meal categories dictionary data."""

from __future__ import annotations

import logging
from typing import Any, Final, Iterable

from supabase import Client

from app.api.v1.schemas import MealCategoryResponseItem

logger = logging.getLogger(__name__)


class MealCategoriesRepository:
    """Data access layer for meal categories stored in Supabase."""

    _TABLE_NAME: Final[str] = "meal_categories"
    _COLUMNS: Final[tuple[str, ...]] = ("code", "label", "sort_order")

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    def list_categories(self) -> list[MealCategoryResponseItem]:
        """Fetch meal categories ordered by sort order.

        Returns:
            List of MealCategoryResponseItem instances ordered by sort_order.

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """

        query = (
            self._client.table(self._TABLE_NAME)
            .select(",".join(self._COLUMNS))
            .order("sort_order", desc=False)
        )

        response = query.execute()

        if not response or response.data is None:
            return []

        return [
            MealCategoryResponseItem(**self._normalize_record(record)) for record in response.data
        ]

    @staticmethod
    def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
        """Ensure record contains required fields with proper types."""

        missing = [column for column in MealCategoriesRepository._COLUMNS if column not in record]
        if missing:
            raise ValueError(f"Meal category record missing required fields: {missing}")

        return {
            "code": record["code"],
            "label": record["label"],
            "sort_order": int(record["sort_order"]),
        }

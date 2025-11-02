"""Repository for accessing products and product portions data."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

from supabase import Client  # type: ignore[TCH002]

from app.api.v1.schemas.products import (
    CursorData,
    MacroBreakdownDTO,
    ProductDetailDTO,
    ProductPortionDTO,
    ProductSource,
    ProductSummaryDTO,
    SearchMode,
)

logger = logging.getLogger(__name__)


class ProductRepository:
    """Data access layer for products stored in Supabase."""

    _PRODUCTS_TABLE: Final[str] = "products"
    _PRODUCT_PORTIONS_TABLE: Final[str] = "product_portions"

    _PRODUCT_LIST_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "name",
        "source",
        "created_at",
    )
    _PRODUCT_LIST_WITH_MACROS_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "name",
        "source",
        "macros_per_100g",
        "created_at",
    )
    _PRODUCT_DETAIL_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "name",
        "source",
        "off_id",
        "macros_per_100g",
        "created_at",
        "updated_at",
    )
    _PORTION_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "unit_definition_id",
        "grams_per_portion",
        "is_default",
        "source",
    )

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    def list_products(
        self,
        *,
        search: str | None = None,
        search_mode: SearchMode = SearchMode.FULLTEXT,
        off_id: str | None = None,
        source: ProductSource | None = None,
        page_size: int = 20,
        cursor: CursorData | None = None,
        include_macros: bool = False,
    ) -> list[ProductSummaryDTO]:
        """Fetch products with filtering and cursor pagination.

        Args:
            search: Optional case-insensitive search on name field
            search_mode: Search algorithm (simple ILIKE, fulltext, or fuzzy)
            off_id: Optional filter by Open Food Facts ID
            source: Optional filter by data source
            page_size: Number of results to return (1-50)
            cursor: Cursor for pagination with last_created_at and last_id
            include_macros: Whether to include macronutrient data

        Returns:
            List of ProductSummaryDTO instances ordered by created_at DESC, id.
            Returns page_size + 1 results to detect if there are more pages.

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        # Select appropriate columns based on include_macros flag
        columns = (
            self._PRODUCT_LIST_WITH_MACROS_COLUMNS if include_macros else self._PRODUCT_LIST_COLUMNS
        )

        query = self._client.table(self._PRODUCTS_TABLE).select(",".join(columns))

        # Apply search filter based on search mode
        if search:
            if search_mode == SearchMode.SIMPLE:
                # Simple ILIKE pattern matching - exact phrase
                query = query.ilike("name", f"%{search}%")
            elif search_mode in (SearchMode.FULLTEXT, SearchMode.FUZZY):
                # For both fulltext and fuzzy modes, use flexible word matching
                # Split search into words and match each word independently
                # This allows matching "raw chicken breast" to find products with
                # those words in any order
                words = search.lower().split()
                if len(words) == 1:
                    # Single word - simple ILIKE
                    query = query.ilike("name", f"%{words[0]}%")
                else:
                    # Multiple words - build OR conditions for flexible matching
                    # Each word must appear somewhere in the name
                    for word in words:
                        query = query.ilike("name", f"%{word}%")

        # Apply off_id filter
        if off_id:
            query = query.eq("off_id", off_id)

        # Apply source filter
        if source:
            query = query.eq("source", source.value)

        # Apply cursor-based pagination
        if cursor:
            # Keyset pagination: (created_at, id) < (last_created_at, last_id)
            # For descending order, we use "less than" semantics
            query = query.or_(
                f"created_at.lt.{cursor.last_created_at.isoformat()},"
                f"and(created_at.eq.{cursor.last_created_at.isoformat()},id.gt.{cursor.last_id})"
            )

        # Order by created_at DESC, then id ASC for stable pagination
        query = query.order("created_at", desc=True).order("id", desc=False)

        # Fetch page_size + 1 to detect if there are more results
        query = query.limit(page_size + 1)

        response = query.execute()

        if not response or response.data is None:
            return []

        return [
            ProductSummaryDTO(**self._normalize_product_summary(record, include_macros))
            for record in response.data
        ]

    def get_product_by_id(
        self,
        product_id: UUID,
        *,
        include_portions: bool = False,
    ) -> ProductDetailDTO | None:
        """Fetch a single product by ID with optional portions.

        Args:
            product_id: UUID of the product
            include_portions: Whether to fetch and include portion definitions

        Returns:
            ProductDetailDTO if found, None otherwise

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = (
            self._client.table(self._PRODUCTS_TABLE)
            .select(",".join(self._PRODUCT_DETAIL_COLUMNS))
            .eq("id", str(product_id))
            .limit(1)
        )

        response = query.execute()

        if not response or not response.data:
            return None

        product_data = self._normalize_product_detail(response.data[0])

        # Optionally fetch portions
        if include_portions:
            portions = self.list_product_portions(product_id)
            product_data["portions"] = portions
        else:
            product_data["portions"] = None

        return ProductDetailDTO(**product_data)

    def list_product_portions(self, product_id: UUID) -> list[ProductPortionDTO]:
        """Fetch portions for a specific product.

        Args:
            product_id: UUID of the product

        Returns:
            List of ProductPortionDTO instances ordered by is_default DESC,
            grams_per_portion ASC

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = (
            self._client.table(self._PRODUCT_PORTIONS_TABLE)
            .select(",".join(self._PORTION_COLUMNS))
            .eq("product_id", str(product_id))
            .order("is_default", desc=True)
            .order("grams_per_portion", desc=False)
        )

        response = query.execute()

        if not response or response.data is None:
            return []

        return [
            ProductPortionDTO(**self._normalize_portion_record(record)) for record in response.data
        ]

    @staticmethod
    def _normalize_product_summary(
        record: dict[str, Any],
        include_macros: bool,
    ) -> dict[str, Any]:
        """Normalize product record for summary view.

        Args:
            record: Raw database record
            include_macros: Whether macros should be included

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "name", "source"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Product record missing required fields: {missing}")

        result = {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "name": record["name"],
            "source": ProductSource(record["source"]),
            "created_at": datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
        }

        # Include macros only if requested and present
        if include_macros and "macros_per_100g" in record:
            macros_data = record["macros_per_100g"]
            result["macros_per_100g"] = MacroBreakdownDTO(
                calories=Decimal(str(macros_data["calories"])),
                protein=Decimal(str(macros_data["protein"])),
                fat=Decimal(str(macros_data["fat"])),
                carbs=Decimal(str(macros_data["carbs"])),
            )
        else:
            result["macros_per_100g"] = None

        return result

    @staticmethod
    def _normalize_product_detail(record: dict[str, Any]) -> dict[str, Any]:
        """Normalize product record for detail view.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "name", "source", "macros_per_100g", "created_at", "updated_at"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Product detail record missing required fields: {missing}")

        macros_data = record["macros_per_100g"]

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "name": record["name"],
            "source": ProductSource(record["source"]),
            "off_id": record.get("off_id"),
            "macros_per_100g": MacroBreakdownDTO(
                calories=Decimal(str(macros_data["calories"])),
                protein=Decimal(str(macros_data["protein"])),
                fat=Decimal(str(macros_data["fat"])),
                carbs=Decimal(str(macros_data["carbs"])),
            ),
            "created_at": datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
            "updated_at": datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00")),
        }

    @staticmethod
    def _normalize_portion_record(record: dict[str, Any]) -> dict[str, Any]:
        """Normalize portion record.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "unit_definition_id", "grams_per_portion", "is_default"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Portion record missing required fields: {missing}")

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "unit_definition_id": (
                UUID(record["unit_definition_id"])
                if isinstance(record["unit_definition_id"], str)
                else record["unit_definition_id"]
            ),
            "grams_per_portion": Decimal(str(record["grams_per_portion"])),
            "is_default": bool(record["is_default"]),
            "source": record.get("source"),
        }

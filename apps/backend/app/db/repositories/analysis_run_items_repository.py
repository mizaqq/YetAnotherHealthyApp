"""Repository for analysis run items (ingredients) data access."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client  # type: ignore[TCH002]

logger = logging.getLogger(__name__)


class AnalysisRunItemsRepository:
    """Data access layer for analysis run items.

    Provides methods to fetch ingredients generated during analysis runs.
    """

    _ANALYSIS_RUN_ITEMS_TABLE = "analysis_run_items"

    # Columns for item response (excludes user_id and created_at)
    _ITEM_COLUMNS = [
        "id",
        "ordinal",
        "raw_name",
        "raw_unit",
        "quantity",
        "unit_definition_id",
        "product_id",
        "product_portion_id",
        "weight_grams",
        "confidence",
        "calories",
        "protein",
        "fat",
        "carbs",
    ]

    def __init__(self, client: Client) -> None:
        """Initialize repository with Supabase client.

        Args:
            client: Supabase client instance
        """
        self._client = client

    async def insert_item(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        ordinal: int,
        ingredient_name: str,
        amount: Decimal,
        unit: str,
        confidence_score: Decimal,
        matched_product_id: str | None,
        protein_g: Decimal,
        carbs_g: Decimal,
        fat_g: Decimal,
        calories_kcal: Decimal,
    ) -> dict[str, Any]:
        """Insert a new analysis run item (ingredient).

        Args:
            run_id: Analysis run identifier
            user_id: User identifier
            ordinal: Item ordinal (1-based position)
            ingredient_name: Ingredient name as extracted by AI
            amount: Ingredient amount
            unit: Unit of measurement
            confidence_score: AI confidence score (0-1)
            matched_product_id: Optional matched product ID
            protein_g: Protein in grams
            carbs_g: Carbohydrates in grams
            fat_g: Fat in grams
            calories_kcal: Calories in kcal

        Returns:
            Created item record

        Raises:
            RuntimeError: If database insert fails
        """
        try:
            payload = {
                "run_id": str(run_id),
                "user_id": str(user_id),
                "ordinal": ordinal,
                "raw_name": ingredient_name,
                "raw_unit": unit,
                "quantity": str(amount),
                "unit_definition_id": None,  # TODO: map unit to unit_definition
                "product_id": matched_product_id,
                "product_portion_id": None,
                "weight_grams": str(amount) if unit == "g" else None,
                "confidence": str(confidence_score),
                "calories": str(calories_kcal),
                "protein": str(protein_g),
                "fat": str(fat_g),
                "carbs": str(carbs_g),
            }

            response = self._client.table(self._ANALYSIS_RUN_ITEMS_TABLE).insert(payload).execute()

            if not response.data or len(response.data) == 0:
                raise RuntimeError("Insert returned no data")

            return self._normalize_item_record(response.data[0])

        except Exception as exc:
            logger.exception(
                "Failed to insert analysis run item",
                exc_info=True,
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "ordinal": ordinal,
                },
            )
            msg = "Failed to insert analysis run item into database"
            raise RuntimeError(msg) from exc

    async def list_items(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> list[dict[str, Any]]:
        """List all items for an analysis run, sorted by ordinal.

        Fetches ingredients generated during the analysis run.
        Filters by both run_id and user_id to enforce authorization.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier (for authorization via RLS)

        Returns:
            List of item records sorted by ordinal (1-based)

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table(self._ANALYSIS_RUN_ITEMS_TABLE)
                .select(",".join(self._ITEM_COLUMNS))
                .eq("run_id", str(run_id))
                .eq("user_id", str(user_id))
                .order("ordinal", desc=False)
                .execute()
            )

            if not response.data:
                # Return empty list if no items found
                return []

            # Normalize each record
            return [self._normalize_item_record(record) for record in response.data]

        except Exception as exc:
            logger.exception(
                "Failed to list analysis run items",
                exc_info=True,
                extra={"run_id": str(run_id), "user_id": str(user_id)},
            )
            msg = "Failed to fetch analysis run items from database"
            raise RuntimeError(msg) from exc

    def _normalize_item_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normalize item record from Supabase to typed dict.

        Converts string UUIDs to UUID objects and numeric strings to Decimal.

        Args:
            record: Raw record from Supabase

        Returns:
            Normalized record with proper types

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Required fields
        required_fields = [
            "id",
            "ordinal",
            "raw_name",
            "quantity",
            "confidence",
            "calories",
            "protein",
            "fat",
            "carbs",
        ]
        for field in required_fields:
            if field not in record:
                msg = f"Missing required field: {field}"
                raise ValueError(msg)

        # Parse UUID fields
        item_id = UUID(record["id"]) if isinstance(record["id"], str) else record["id"]
        unit_definition_id = (
            UUID(record["unit_definition_id"])
            if record.get("unit_definition_id") and isinstance(record["unit_definition_id"], str)
            else record.get("unit_definition_id")
        )
        product_id = (
            UUID(record["product_id"])
            if record.get("product_id") and isinstance(record["product_id"], str)
            else record.get("product_id")
        )
        product_portion_id = (
            UUID(record["product_portion_id"])
            if record.get("product_portion_id") and isinstance(record["product_portion_id"], str)
            else record.get("product_portion_id")
        )

        # Parse numeric fields to Decimal
        quantity = Decimal(str(record["quantity"]))
        weight_grams = (
            Decimal(str(record["weight_grams"])) if record.get("weight_grams") is not None else None
        )
        confidence = Decimal(str(record["confidence"]))
        calories = Decimal(str(record["calories"]))
        protein = Decimal(str(record["protein"]))
        fat = Decimal(str(record["fat"]))
        carbs = Decimal(str(record["carbs"]))

        return {
            "id": item_id,
            "ordinal": int(record["ordinal"]),
            "raw_name": record["raw_name"],
            "raw_unit": record.get("raw_unit"),
            "quantity": quantity,
            "unit_definition_id": unit_definition_id,
            "product_id": product_id,
            "product_portion_id": product_portion_id,
            "weight_grams": weight_grams,
            "confidence": confidence,
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
        }

"""Repository for accessing meals data."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

from supabase import Client

from app.api.v1.schemas.meals import (
    MealCursorData,
    MealListItem,
    MealSource,
)

logger = logging.getLogger(__name__)


class MealRepository:
    """Data access layer for meals stored in Supabase."""

    _MEALS_TABLE: Final[str] = "meals"

    _MEAL_LIST_COLUMNS: Final[tuple[str, ...]] = (
        "id",
        "category",
        "eaten_at",
        "calories",
        "protein",
        "fat",
        "carbs",
        "source",
        "accepted_analysis_run_id",
    )

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    def list_meals(
        self,
        *,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        category: str | None = None,
        source: MealSource | None = None,
        include_deleted: bool = False,
        page_size: int = 20,
        cursor: MealCursorData | None = None,
        sort_desc: bool = True,
    ) -> list[MealListItem]:
        """Fetch meals for a user with filtering and cursor pagination.

        Args:
            user_id: UUID of the user whose meals to fetch
            from_date: Optional start date filter (inclusive)
            to_date: Optional end date filter (inclusive)
            category: Optional filter by meal category code
            source: Optional filter by meal data source
            include_deleted: Whether to include soft-deleted meals
            page_size: Number of results to return (1-100)
            cursor: Cursor for pagination with last_eaten_at and last_id
            sort_desc: Sort by eaten_at descending (True) or ascending (False)

        Returns:
            List of MealListItem instances ordered by eaten_at and id.
            Returns page_size + 1 results to detect if there are more pages.

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = self._client.table(self._MEALS_TABLE).select(",".join(self._MEAL_LIST_COLUMNS))

        # Filter by user_id (required)
        query = query.eq("user_id", str(user_id))

        # Apply date range filters
        if from_date:
            query = query.gte("eaten_at", from_date.isoformat())
        if to_date:
            query = query.lte("eaten_at", to_date.isoformat())

        # Apply category filter
        if category:
            query = query.eq("category", category)

        # Apply source filter
        if source:
            query = query.eq("source", source.value)

        # Apply deleted_at filter
        if not include_deleted:
            query = query.is_("deleted_at", "null")

        # Apply cursor-based pagination
        if cursor:
            # Keyset pagination using (eaten_at, id) composite key
            # For descending: (eaten_at, id) < (last_eaten_at, last_id)
            # For ascending: (eaten_at, id) > (last_eaten_at, last_id)
            cursor_iso = cursor.last_eaten_at.isoformat()
            cursor_id = str(cursor.last_id)

            if sort_desc:
                # For descending order: fetch records before the cursor
                query = query.or_(
                    f"eaten_at.lt.{cursor_iso},and(eaten_at.eq.{cursor_iso},id.gt.{cursor_id})"
                )
            else:
                # For ascending order: fetch records after the cursor
                query = query.or_(
                    f"eaten_at.gt.{cursor_iso},and(eaten_at.eq.{cursor_iso},id.gt.{cursor_id})"
                )

        # Apply sorting
        query = query.order("eaten_at", desc=sort_desc).order("id", desc=False)

        # Fetch page_size + 1 to detect if there are more results
        query = query.limit(page_size + 1)

        response = query.execute()

        if not response or response.data is None:
            return []

        return [MealListItem(**self._normalize_meal_record(record)) for record in response.data]

    @staticmethod
    def _normalize_meal_record(record: dict[str, Any]) -> dict[str, Any]:
        """Normalize meal record for list view.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        required = ["id", "category", "eaten_at", "calories", "source"]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"Meal record missing required fields: {missing}")

        # Parse datetime - handle both ISO format and already parsed datetime objects
        eaten_at = record["eaten_at"]
        if isinstance(eaten_at, str):
            eaten_at = datetime.fromisoformat(eaten_at.replace("Z", "+00:00"))

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "category": record["category"],
            "eaten_at": eaten_at,
            "calories": Decimal(str(record["calories"])),
            "protein": Decimal(str(record["protein"]))
            if record.get("protein") is not None
            else None,
            "fat": Decimal(str(record["fat"])) if record.get("fat") is not None else None,
            "carbs": Decimal(str(record["carbs"])) if record.get("carbs") is not None else None,
            "source": MealSource(record["source"]),
            "accepted_analysis_run_id": (
                UUID(record["accepted_analysis_run_id"])
                if record.get("accepted_analysis_run_id")
                else None
            ),
        }

    async def category_exists(self, *, category_code: str) -> bool:
        """Check if a meal category exists.

        Args:
            category_code: Category code to check

        Returns:
            True if category exists, False otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            response = (
                self._client.table("meal_categories")
                .select("code", count="exact")
                .eq("code", category_code)
                .limit(1)
                .execute()
            )
            return len(response.data) > 0
        except Exception as exc:
            logger.exception("Failed to check category existence: %s", category_code)
            raise RuntimeError(f"Failed to check category existence: {exc}") from exc

    async def get_analysis_run_for_acceptance(
        self, *, user_id: UUID, analysis_run_id: UUID
    ) -> dict[str, Any] | None:
        """Fetch analysis run for acceptance validation.

        Verifies that:
        - Analysis run exists and belongs to the user
        - Status is 'succeeded'
        - Not already accepted by another meal

        Args:
            user_id: User who owns the analysis run
            analysis_run_id: Analysis run ID to validate

        Returns:
            Analysis run record if valid for acceptance, None otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            # Query analysis_runs with meal check
            response = (
                self._client.table("analysis_runs")
                .select("id,user_id,meal_id,status")
                .eq("id", str(analysis_run_id))
                .eq("user_id", str(user_id))
                .eq("status", "succeeded")
                .maybe_single()
                .execute()
            )

            if not response or not response.data:
                return None

            analysis_run = response.data

            # Check if already accepted by checking meals table
            meals_response = (
                self._client.table("meals")
                .select("id")
                .eq("accepted_analysis_run_id", str(analysis_run_id))
                .maybe_single()
                .execute()
            )

            # If already accepted by another meal, return None
            if meals_response and meals_response.data:
                return None

            return analysis_run

        except Exception as exc:
            logger.exception(
                "Failed to fetch analysis run: %s for user: %s",
                analysis_run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to fetch analysis run: {exc}") from exc

    async def create_meal(
        self,
        *,
        user_id: UUID,
        category: str,
        eaten_at: datetime,
        source: MealSource,
        calories: Decimal,
        protein: Decimal | None,
        fat: Decimal | None,
        carbs: Decimal | None,
        analysis_run_id: UUID | None,
    ) -> dict[str, Any]:
        """Create a new meal record.

        Args:
            user_id: User who owns the meal
            category: Meal category code
            eaten_at: When the meal was consumed
            source: Data source (ai, edited, manual)
            calories: Total calories
            protein: Protein in grams (None for manual)
            fat: Fat in grams (None for manual)
            carbs: Carbohydrates in grams (None for manual)
            analysis_run_id: Reference to analysis run (None for manual)

        Returns:
            Created meal record with all fields

        Raises:
            Exception: If database insert fails
        """
        try:
            meal_data = {
                "user_id": str(user_id),
                "category": category,
                "eaten_at": eaten_at.isoformat(),
                "source": source.value,
                "calories": float(calories),
            }

            # Add macros and analysis_run_id based on source
            if source in (MealSource.AI, MealSource.EDITED):
                meal_data.update(
                    {
                        "protein": float(protein) if protein is not None else None,
                        "fat": float(fat) if fat is not None else None,
                        "carbs": float(carbs) if carbs is not None else None,
                        "accepted_analysis_run_id": str(analysis_run_id)
                        if analysis_run_id
                        else None,
                    }
                )
            else:
                # For MANUAL source, explicitly set macros and analysis_run_id to None
                # to satisfy database CHECK constraint
                meal_data.update(
                    {
                        "protein": None,
                        "fat": None,
                        "carbs": None,
                        "accepted_analysis_run_id": None,
                    }
                )

            response = self._client.table(self._MEALS_TABLE).insert(meal_data).execute()

            if not response.data or len(response.data) == 0:
                raise RuntimeError("Failed to create meal: no data returned")

            return response.data[0]

        except Exception as exc:
            logger.exception("Failed to create meal for user: %s", user_id)
            raise RuntimeError(f"Failed to create meal: {exc}") from exc

    async def get_meal_by_id(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
        include_deleted: bool = False,
    ) -> dict | None:
        """Retrieve a single meal by ID for a specific user.

        Args:
            meal_id: Meal identifier
            user_id: User identifier (for authorization)
            include_deleted: Whether to include soft-deleted meals

        Returns:
            Meal record dict or None if not found

        Raises:
            RuntimeError: If database query fails
        """
        try:
            query = (
                self._client.table(self._MEALS_TABLE)
                .select(
                    "id, user_id, category, eaten_at, source, calories, "
                    "protein, fat, carbs, accepted_analysis_run_id, "
                    "created_at, updated_at, deleted_at"
                )
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
            )

            if not include_deleted:
                query = query.is_("deleted_at", "null")

            response = query.execute()

            if not response.data or len(response.data) == 0:
                return None

            record = response.data[0]

            # Parse datetime fields
            eaten_at = (
                datetime.fromisoformat(record["eaten_at"].replace("Z", "+00:00"))
                if isinstance(record["eaten_at"], str)
                else record["eaten_at"]
            )
            created_at = (
                datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                if isinstance(record["created_at"], str)
                else record["created_at"]
            )
            updated_at = (
                datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
                if isinstance(record["updated_at"], str)
                else record["updated_at"]
            )
            deleted_at = None
            if record.get("deleted_at"):
                deleted_at = (
                    datetime.fromisoformat(record["deleted_at"].replace("Z", "+00:00"))
                    if isinstance(record["deleted_at"], str)
                    else record["deleted_at"]
                )

            return {
                "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
                "user_id": (
                    UUID(record["user_id"])
                    if isinstance(record["user_id"], str)
                    else record["user_id"]
                ),
                "category": record["category"],
                "eaten_at": eaten_at,
                "source": MealSource(record["source"]),
                "calories": Decimal(str(record["calories"])),
                "protein": (
                    Decimal(str(record["protein"])) if record.get("protein") is not None else None
                ),
                "fat": (Decimal(str(record["fat"])) if record.get("fat") is not None else None),
                "carbs": (
                    Decimal(str(record["carbs"])) if record.get("carbs") is not None else None
                ),
                "accepted_analysis_run_id": (
                    UUID(record["accepted_analysis_run_id"])
                    if record.get("accepted_analysis_run_id")
                    else None
                ),
                "created_at": created_at,
                "updated_at": updated_at,
                "deleted_at": deleted_at,
            }

        except Exception as exc:
            logger.exception("Failed to fetch meal: %s for user: %s", meal_id, user_id)
            raise RuntimeError(f"Failed to fetch meal: {exc}") from exc

    async def get_analysis_run_details(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict | None:
        """Retrieve analysis run metadata.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier (for authorization)

        Returns:
            Analysis run record dict or None if not found

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table("analysis_runs")
                .select(
                    "id, run_no, status, model, latency_ms, tokens, "
                    "cost_minor_units, cost_currency, threshold_used, "
                    "retry_of_run_id, error_code, error_message, "
                    "created_at, completed_at"
                )
                .eq("id", str(run_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                return None

            record = response.data[0]

            # Parse datetime fields
            created_at = (
                datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                if isinstance(record["created_at"], str)
                else record["created_at"]
            )
            completed_at = None
            if record.get("completed_at"):
                completed_at = (
                    datetime.fromisoformat(record["completed_at"].replace("Z", "+00:00"))
                    if isinstance(record["completed_at"], str)
                    else record["completed_at"]
                )

            return {
                "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
                "run_no": record["run_no"],
                "status": record["status"],
                "model": record["model"],
                "latency_ms": record.get("latency_ms"),
                "tokens": record.get("tokens"),
                "cost_minor_units": record.get("cost_minor_units"),
                "cost_currency": record.get("cost_currency", "USD"),
                "threshold_used": (
                    Decimal(str(record["threshold_used"]))
                    if record.get("threshold_used") is not None
                    else None
                ),
                "retry_of_run_id": (
                    UUID(record["retry_of_run_id"]) if record.get("retry_of_run_id") else None
                ),
                "error_code": record.get("error_code"),
                "error_message": record.get("error_message"),
                "created_at": created_at,
                "completed_at": completed_at,
            }

        except Exception as exc:
            logger.exception("Failed to fetch analysis run: %s for user: %s", run_id, user_id)
            raise RuntimeError(f"Failed to fetch analysis run: {exc}") from exc

    async def get_analysis_run_items(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> list[dict]:
        """Retrieve all items (ingredients) for an analysis run.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier (for authorization)

        Returns:
            List of analysis run item dicts, ordered by ordinal

        Raises:
            RuntimeError: If database query fails
        """
        try:
            response = (
                self._client.table("analysis_run_items")
                .select(
                    "id, ordinal, raw_name, raw_unit, product_id, quantity, "
                    "unit_definition_id, product_portion_id, weight_grams, "
                    "confidence, calories, protein, fat, carbs, created_at"
                )
                .eq("run_id", str(run_id))
                .eq("user_id", str(user_id))
                .order("ordinal")
                .execute()
            )

            if not response.data:
                return []

            items = []
            for record in response.data:
                created_at = (
                    datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                    if isinstance(record["created_at"], str)
                    else record["created_at"]
                )

                items.append(
                    {
                        "id": (
                            UUID(record["id"]) if isinstance(record["id"], str) else record["id"]
                        ),
                        "ordinal": record["ordinal"],
                        "raw_name": record["raw_name"],
                        "raw_unit": record.get("raw_unit"),
                        "product_id": (
                            UUID(record["product_id"]) if record.get("product_id") else None
                        ),
                        "quantity": Decimal(str(record["quantity"])),
                        "unit_definition_id": (
                            UUID(record["unit_definition_id"])
                            if record.get("unit_definition_id")
                            else None
                        ),
                        "product_portion_id": (
                            UUID(record["product_portion_id"])
                            if record.get("product_portion_id")
                            else None
                        ),
                        "weight_grams": (
                            Decimal(str(record["weight_grams"]))
                            if record.get("weight_grams") is not None
                            else None
                        ),
                        "confidence": (
                            Decimal(str(record["confidence"]))
                            if record.get("confidence") is not None
                            else None
                        ),
                        "calories": (
                            Decimal(str(record["calories"]))
                            if record.get("calories") is not None
                            else None
                        ),
                        "protein": (
                            Decimal(str(record["protein"]))
                            if record.get("protein") is not None
                            else None
                        ),
                        "fat": (
                            Decimal(str(record["fat"])) if record.get("fat") is not None else None
                        ),
                        "carbs": (
                            Decimal(str(record["carbs"]))
                            if record.get("carbs") is not None
                            else None
                        ),
                        "created_at": created_at,
                    }
                )

            return items

        except Exception as exc:
            logger.exception(
                "Failed to fetch analysis run items for run: %s, user: %s",
                run_id,
                user_id,
            )
            raise RuntimeError(f"Failed to fetch analysis run items: {exc}") from exc

    async def update_meal(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
        updates: dict[str, Any],
    ) -> dict | None:
        """Update an existing meal with provided fields.

        Args:
            meal_id: Meal identifier
            user_id: User identifier (for authorization)
            updates: Dictionary of fields to update

        Returns:
            Updated meal record dict or None if meal not found

        Raises:
            RuntimeError: If database operation fails
        """
        if not updates:
            msg = "No fields to update"
            raise ValueError(msg)

        try:
            # Build the update query - only update provided fields
            # Note: .select() must be called after .update() but before filters
            response = (
                self._client.table(self._MEALS_TABLE)
                .update(updates)
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .is_("deleted_at", "null")
                .execute()
            )

            if not response.data:
                return None

            record = response.data[0]

            # Parse datetime fields
            eaten_at = (
                datetime.fromisoformat(record["eaten_at"].replace("Z", "+00:00"))
                if isinstance(record["eaten_at"], str)
                else record["eaten_at"]
            )
            created_at = (
                datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                if isinstance(record["created_at"], str)
                else record["created_at"]
            )
            updated_at = (
                datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
                if isinstance(record["updated_at"], str)
                else record["updated_at"]
            )
            deleted_at = None
            if record.get("deleted_at"):
                deleted_at = (
                    datetime.fromisoformat(record["deleted_at"].replace("Z", "+00:00"))
                    if isinstance(record["deleted_at"], str)
                    else record["deleted_at"]
                )

            return {
                "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
                "user_id": (
                    UUID(record["user_id"])
                    if isinstance(record["user_id"], str)
                    else record["user_id"]
                ),
                "category": record["category"],
                "eaten_at": eaten_at,
                "source": MealSource(record["source"]),
                "calories": Decimal(str(record["calories"])),
                "protein": (
                    Decimal(str(record["protein"])) if record.get("protein") is not None else None
                ),
                "fat": (Decimal(str(record["fat"])) if record.get("fat") is not None else None),
                "carbs": (
                    Decimal(str(record["carbs"])) if record.get("carbs") is not None else None
                ),
                "accepted_analysis_run_id": (
                    UUID(record["accepted_analysis_run_id"])
                    if record.get("accepted_analysis_run_id")
                    else None
                ),
                "created_at": created_at,
                "updated_at": updated_at,
                "deleted_at": deleted_at,
            }

        except Exception as exc:
            logger.exception("Failed to update meal: %s for user: %s", meal_id, user_id)
            raise RuntimeError(f"Failed to update meal: {exc}") from exc

    async def soft_delete_meal(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft-delete a meal by setting deleted_at timestamp.

        Args:
            meal_id: Meal identifier
            user_id: User identifier (for authorization)

        Returns:
            True if meal was deleted, False if meal not found or already deleted

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            # Update deleted_at for the meal if it exists, belongs to user,
            # and is not already soft-deleted
            response = (
                self._client.table(self._MEALS_TABLE)
                .update({"deleted_at": "now()"})
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .is_("deleted_at", "null")
                .execute()
            )

            # If no rows affected, meal doesn't exist, already deleted,
            # or doesn't belong to user
            return bool(response.data)

        except Exception as exc:
            logger.exception("Failed to soft-delete meal: %s for user: %s", meal_id, user_id)
            raise RuntimeError(f"Failed to soft-delete meal: {exc}") from exc

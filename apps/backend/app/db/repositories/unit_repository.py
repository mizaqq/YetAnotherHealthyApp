"""Repository for accessing unit definitions and aliases data."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Final
from uuid import UUID

from supabase import Client

from app.api.v1.schemas.units import CursorData, UnitAlias, UnitDefinition, UnitType

logger = logging.getLogger(__name__)


class UnitRepository:
    """Data access layer for unit definitions and aliases stored in Supabase."""

    _UNIT_DEFINITIONS_TABLE: Final[str] = "unit_definitions"
    _UNIT_ALIASES_TABLE: Final[str] = "unit_aliases"
    _UNIT_COLUMNS: Final[tuple[str, ...]] = ("id", "code", "unit_type", "grams_per_unit")
    _ALIAS_COLUMNS: Final[tuple[str, ...]] = ("alias", "locale", "is_primary")

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    def list_units(
        self,
        *,
        unit_type: UnitType | None = None,
        search: str | None = None,
        page_size: int = 50,
        cursor: CursorData | None = None,
    ) -> list[UnitDefinition]:
        """Fetch unit definitions with filtering and cursor pagination.

        Args:
            unit_type: Optional filter by unit type classification
            search: Optional case-insensitive search on code field
            page_size: Number of results to return (1-100)
            cursor: Cursor for pagination with last_id and last_code

        Returns:
            List of UnitDefinition instances ordered by code, id.
            Returns page_size + 1 results to detect if there are more pages.

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = self._client.table(self._UNIT_DEFINITIONS_TABLE).select(
            ",".join(self._UNIT_COLUMNS)
        )

        # Apply unit_type filter
        if unit_type is not None:
            query = query.eq("unit_type", unit_type.value)

        # Apply search filter (case-insensitive LIKE on code)
        if search:
            query = query.ilike("code", f"%{search}%")

        # Apply cursor-based pagination
        if cursor:
            # Using composite ordering: (code, id) > (last_code, last_id)
            # Note: Supabase doesn't support composite tuple comparisons directly,
            # so we need to use a combination of filters
            query = query.or_(
                f"code.gt.{cursor.last_code},and(code.eq.{cursor.last_code},id.gt.{cursor.last_id})"
            )

        # Order by code, then id for stable pagination
        query = query.order("code", desc=False).order("id", desc=False)

        # Fetch page_size + 1 to detect if there are more results
        query = query.limit(page_size + 1)

        response = query.execute()

        if not response or response.data is None:
            return []

        return [UnitDefinition(**self._normalize_unit_record(record)) for record in response.data]

    def get_unit_by_id(self, unit_id: UUID) -> UnitDefinition | None:
        """Fetch a single unit definition by ID.

        Args:
            unit_id: UUID of the unit definition

        Returns:
            UnitDefinition if found, None otherwise

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = (
            self._client.table(self._UNIT_DEFINITIONS_TABLE)
            .select(",".join(self._UNIT_COLUMNS))
            .eq("id", str(unit_id))
            .limit(1)
        )

        response = query.execute()

        if not response or not response.data:
            return None

        return UnitDefinition(**self._normalize_unit_record(response.data[0]))

    def get_unit_aliases(
        self,
        unit_id: UUID,
        locale: str | None = None,
    ) -> list[UnitAlias]:
        """Fetch aliases for a specific unit definition.

        Args:
            unit_id: UUID of the unit definition
            locale: Optional locale filter (e.g., 'pl-PL')

        Returns:
            List of UnitAlias instances ordered by is_primary DESC, alias ASC

        Raises:
            Exception: Propagates underlying Supabase client errors.
        """
        query = (
            self._client.table(self._UNIT_ALIASES_TABLE)
            .select(",".join(self._ALIAS_COLUMNS))
            .eq("unit_definition_id", str(unit_id))
        )

        # Apply optional locale filter
        if locale:
            query = query.eq("locale", locale)

        # Order by is_primary descending (true first), then alias ascending
        query = query.order("is_primary", desc=True).order("alias", desc=False)

        response = query.execute()

        if not response or response.data is None:
            return []

        return [UnitAlias(**self._normalize_alias_record(record)) for record in response.data]

    @staticmethod
    def _normalize_unit_record(record: dict[str, Any]) -> dict[str, Any]:
        """Ensure unit record contains required fields with proper types.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        missing = [column for column in UnitRepository._UNIT_COLUMNS if column not in record]
        if missing:
            raise ValueError(f"Unit definition record missing required fields: {missing}")

        return {
            "id": UUID(record["id"]) if isinstance(record["id"], str) else record["id"],
            "code": record["code"],
            "unit_type": record["unit_type"],
            "grams_per_unit": Decimal(str(record["grams_per_unit"])),
        }

    @staticmethod
    def _normalize_alias_record(record: dict[str, Any]) -> dict[str, Any]:
        """Ensure alias record contains required fields with proper types.

        Args:
            record: Raw database record

        Returns:
            Normalized dictionary with proper types

        Raises:
            ValueError: If required fields are missing
        """
        missing = [column for column in UnitRepository._ALIAS_COLUMNS if column not in record]
        if missing:
            raise ValueError(f"Unit alias record missing required fields: {missing}")

        return {
            "alias": record["alias"],
            "locale": record["locale"],
            "is_primary": bool(record["is_primary"]),
        }

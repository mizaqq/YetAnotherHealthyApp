"""Service layer for units operations."""

from __future__ import annotations

import logging
from uuid import UUID  # type: ignore[TCH003]

from fastapi import HTTPException, status

from app.api.v1.schemas.units import (
    PageInfo,
    UnitAliasesResponse,
    UnitsListQuery,
    UnitsListResponse,
    decode_cursor,
    encode_cursor,
)
from app.db.repositories.unit_repository import UnitRepository  # type: ignore[TCH001]

logger = logging.getLogger(__name__)


class UnitsService:
    """Orchestrates fetching unit definitions and aliases with proper error handling."""

    def __init__(self, repository: UnitRepository):
        self._repository = repository

    async def list_units(
        self,
        *,
        query: UnitsListQuery,
    ) -> UnitsListResponse:
        """Retrieve paginated unit definitions with optional filtering.

        Args:
            query: Query parameters including filters and pagination

        Returns:
            UnitsListResponse with unit definitions and pagination metadata

        Raises:
            HTTPException: 400 for invalid cursor, 500 for unexpected errors
        """
        cursor_data = None

        # Decode cursor if provided
        if query.page_after:
            try:
                cursor_data = decode_cursor(query.page_after)
            except ValueError as exc:
                logger.warning(
                    "Invalid cursor format: %s",
                    exc,
                    extra={"cursor": query.page_after},
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination cursor format",
                ) from exc

        try:
            # Fetch page_size + 1 to detect if there are more results
            units = self._repository.list_units(
                unit_type=query.unit_type,
                search=query.search,
                page_size=query.page_size,
                cursor=cursor_data,
            )

            # Check if there are more results
            has_more = len(units) > query.page_size
            data = units[: query.page_size] if has_more else units

            # Generate next cursor if there are more results
            next_cursor = None
            if has_more and data:
                last_item = data[-1]
                next_cursor = encode_cursor(
                    last_id=last_item.id,
                    last_code=last_item.code,
                )

            page_info = PageInfo(size=len(data), after=next_cursor)

            return UnitsListResponse(data=data, page=page_info)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch units: %s",
                exc,
                exc_info=True,
                extra={
                    "unit_type": query.unit_type.value if query.unit_type else None,
                    "search": query.search,
                    "page_size": query.page_size,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve units at this time",
            ) from exc

    async def get_unit_aliases(
        self,
        *,
        unit_id: UUID,
        locale: str | None = None,
    ) -> UnitAliasesResponse:
        """Retrieve aliases for a specific unit definition.

        Args:
            unit_id: UUID of the unit definition
            locale: Optional locale filter (e.g., 'pl-PL')

        Returns:
            UnitAliasesResponse with unit_id and list of aliases

        Raises:
            HTTPException: 404 if unit not found, 500 for unexpected errors
        """
        try:
            # First verify the unit exists (enforces RLS)
            unit = self._repository.get_unit_by_id(unit_id)
            if unit is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with id {unit_id} not found",
                )

            # Fetch aliases with optional locale filter
            aliases = self._repository.get_unit_aliases(
                unit_id=unit_id,
                locale=locale,
            )

            return UnitAliasesResponse(unit_id=unit_id, aliases=aliases)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch unit aliases: %s",
                exc,
                exc_info=True,
                extra={"unit_id": str(unit_id), "locale": locale},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve unit aliases at this time",
            ) from exc

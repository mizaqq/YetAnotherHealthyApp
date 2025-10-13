"""Units API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas import (
    UnitAliasesQuery,
    UnitAliasesResponse,
    UnitsListQuery,
    UnitsListResponse,
)
from app.core.dependencies import (
    get_current_user_id,
    get_units_service,
)
from app.services.units_service import UnitsService

router = APIRouter()


@router.get(
    "",
    response_model=UnitsListResponse,
    summary="List unit definitions",
    description="Retrieve paginated unit definitions with optional filtering by type and search.",
)
async def list_units(
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[UnitsService, Depends(get_units_service)],
    unit_type: Annotated[str | None, Query(alias="unit_type")] = None,
    search: Annotated[str | None, Query(alias="search")] = None,
    page_size: Annotated[int, Query(alias="page[size]", ge=1, le=100)] = 50,
    page_after: Annotated[str | None, Query(alias="page[after]")] = None,
) -> UnitsListResponse:
    """List available unit definitions with cursor-based pagination.

    Authenticated users receive unit definitions filtered by optional criteria.
    Results are ordered by code and id for stable pagination.

    Query Parameters:
        unit_type: Filter by unit type (mass, piece, portion, utensil)
        search: Case-insensitive search on unit code
        page[size]: Number of results per page (1-100, default 50)
        page[after]: Cursor for next page (base64 encoded)

    Returns:
        UnitsListResponse with data array and pagination metadata
    """
    # Construct query DTO from individual parameters
    query = UnitsListQuery(
        unit_type=unit_type,
        search=search,
        page_size=page_size,
        page_after=page_after,
    )

    return await service.list_units(query=query)


@router.get(
    "/{unit_id}/aliases",
    response_model=UnitAliasesResponse,
    summary="Get unit aliases",
    description="Retrieve localized aliases for a specific unit definition.",
)
async def get_unit_aliases(
    unit_id: UUID,
    query: Annotated[UnitAliasesQuery, Depends()],
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[UnitsService, Depends(get_units_service)],
) -> UnitAliasesResponse:
    """Get aliases for a specific unit definition.

    Authenticated users receive aliases optionally filtered by locale.
    Results are ordered by is_primary descending, then alias ascending.

    Path Parameters:
        unit_id: UUID of the unit definition

    Query Parameters:
        locale: BCP 47 locale code (e.g., pl-PL, default: pl-PL)

    Returns:
        UnitAliasesResponse with unit_id and aliases array

    Raises:
        404: Unit definition not found or not accessible
    """
    return await service.get_unit_aliases(
        unit_id=unit_id,
        locale=query.locale,
    )

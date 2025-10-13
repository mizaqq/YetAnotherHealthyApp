"""Products API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.products import (
    ProductDetailDTO,
    ProductDetailParams,
    ProductListParams,
    ProductPortionsResponse,
    ProductsListResponse,
    ProductSource,
)
from app.core.dependencies import (
    get_current_user_id,
    get_product_service,
)
from app.services.product_service import ProductService

router = APIRouter()


@router.get(
    "",
    response_model=ProductsListResponse,
    summary="List products",
    description="Retrieve paginated products with optional filtering by name, OFF ID, and source.",
)
async def list_products(
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ProductService, Depends(get_product_service)],
    search: Annotated[str | None, Query(alias="search", min_length=2)] = None,
    off_id: Annotated[str | None, Query(alias="off_id")] = None,
    source: Annotated[ProductSource | None, Query(alias="source")] = None,
    page_size: Annotated[int, Query(alias="page[size]", ge=1, le=50)] = 20,
    page_after: Annotated[str | None, Query(alias="page[after]")] = None,
    include_macros: Annotated[bool, Query(alias="include_macros")] = False,
) -> ProductsListResponse:
    """List available products with cursor-based pagination.

    Authenticated users can search and filter products by name, Open Food Facts ID,
    or data source. Results are ordered by creation date (newest first) for stable pagination.

    Query Parameters:
        search: Case-insensitive search on product name (min 2 characters)
        off_id: Filter by Open Food Facts identifier
        source: Filter by data source (open_food_facts, user_defined, manual)
        page[size]: Number of results per page (1-50, default 20)
        page[after]: Cursor for next page (base64 encoded)
        include_macros: Include macronutrient breakdown in response (default false)

    Returns:
        ProductsListResponse with data array and pagination metadata

    Raises:
        400: Invalid pagination cursor
        401: Missing or invalid authentication
        500: Internal server error
    """
    # Construct query DTO from individual parameters
    query = ProductListParams(
        search=search,
        off_id=off_id,
        source=source,
        page_size=page_size,
        page_after=page_after,
        include_macros=include_macros,
    )

    return await service.list_products(query=query)


@router.get(
    "/{product_id}",
    response_model=ProductDetailDTO,
    summary="Get product details",
    description="Retrieve detailed information about a specific product by ID.",
)
async def get_product(
    product_id: UUID,
    params: Annotated[ProductDetailParams, Depends()],
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductDetailDTO:
    """Get detailed information about a specific product.

    Authenticated users can retrieve full product details including macronutrients
    and optionally portion definitions.

    Path Parameters:
        product_id: UUID of the product

    Query Parameters:
        include_portions: Include portion definitions in response (default false)

    Returns:
        ProductDetailDTO with complete product information

    Raises:
        401: Missing or invalid authentication
        404: Product not found
        500: Internal server error
    """
    return await service.get_product(
        product_id=product_id,
        include_portions=params.include_portions,
    )


@router.get(
    "/{product_id}/portions",
    response_model=ProductPortionsResponse,
    summary="Get product portions",
    description="Retrieve portion definitions for a specific product.",
)
async def get_product_portions(
    product_id: UUID,
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductPortionsResponse:
    """Get portion definitions for a specific product.

    Authenticated users can retrieve all available portion sizes for a product,
    ordered by default status and portion size.

    Path Parameters:
        product_id: UUID of the product

    Returns:
        ProductPortionsResponse with product_id and list of portions

    Raises:
        401: Missing or invalid authentication
        404: Product not found
        500: Internal server error
    """
    return await service.list_product_portions(product_id=product_id)


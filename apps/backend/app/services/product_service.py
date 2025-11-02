"""Service layer for products operations."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status

from app.api.v1.schemas.products import (
    PageInfo,
    ProductDetailDTO,
    ProductListParams,
    ProductPortionsResponse,
    ProductSearchFilter,
    ProductsListResponse,
    decode_cursor,
    encode_cursor,
)
from app.db.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    """Orchestrates fetching products with proper error handling."""

    def __init__(self, repository: ProductRepository):
        self._repository = repository

    async def list_products(
        self,
        *,
        query: ProductListParams,
    ) -> ProductsListResponse:
        """Retrieve paginated products with optional filtering.

        Args:
            query: Query parameters including filters and pagination

        Returns:
            ProductsListResponse with product summaries and pagination metadata

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
            # Build search filter
            search_filter = ProductSearchFilter(
                search=query.search,
                search_mode=query.search_mode,
                off_id=query.off_id,
                source=query.source,
                page_size=query.page_size,
                cursor=cursor_data,
                include_macros=query.include_macros,
            )

            # Fetch page_size + 1 to detect if there are more results
            products = self._repository.list_products(
                search=search_filter.search,
                search_mode=search_filter.search_mode,
                off_id=search_filter.off_id,
                source=search_filter.source,
                page_size=search_filter.page_size,
                cursor=search_filter.cursor,
                include_macros=search_filter.include_macros,
            )

            # Check if there are more results
            has_more = len(products) > query.page_size
            data = products[: query.page_size] if has_more else products

            # Generate next cursor if there are more results
            next_cursor = None
            if has_more and data:
                last_item = data[-1]
                # created_at is included in ProductSummaryDTO but excluded from serialization
                if last_item.created_at is None:
                    raise ValueError("Product missing created_at for cursor generation")
                next_cursor = encode_cursor(
                    last_created_at=last_item.created_at,
                    last_id=last_item.id,
                )

            page_info = PageInfo(size=len(data), after=next_cursor)

            return ProductsListResponse(data=data, page=page_info)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch products: %s",
                exc,
                exc_info=True,
                extra={
                    "search": query.search,
                    "off_id": query.off_id,
                    "source": query.source.value if query.source else None,
                    "page_size": query.page_size,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve products at this time",
            ) from exc

    async def get_product(
        self,
        *,
        product_id: UUID,
        include_portions: bool = False,
    ) -> ProductDetailDTO:
        """Retrieve a single product by ID.

        Args:
            product_id: UUID of the product
            include_portions: Whether to include portion definitions

        Returns:
            ProductDetailDTO with product details

        Raises:
            HTTPException: 404 if product not found, 500 for unexpected errors
        """
        try:
            product = self._repository.get_product_by_id(
                product_id=product_id,
                include_portions=include_portions,
            )

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {product_id} not found",
                )

            return product

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch product: %s",
                exc,
                exc_info=True,
                extra={"product_id": str(product_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve product at this time",
            ) from exc

    async def list_product_portions(
        self,
        *,
        product_id: UUID,
    ) -> ProductPortionsResponse:
        """Retrieve portions for a specific product.

        Args:
            product_id: UUID of the product

        Returns:
            ProductPortionsResponse with list of portions

        Raises:
            HTTPException: 404 if product not found, 500 for unexpected errors
        """
        try:
            # First verify the product exists
            product = self._repository.get_product_by_id(
                product_id=product_id,
                include_portions=False,
            )

            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {product_id} not found",
                )

            # Fetch portions
            portions = self._repository.list_product_portions(product_id)

            return ProductPortionsResponse(
                product_id=product_id,
                portions=portions,
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch product portions: %s",
                exc,
                exc_info=True,
                extra={"product_id": str(product_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve product portions at this time",
            ) from exc

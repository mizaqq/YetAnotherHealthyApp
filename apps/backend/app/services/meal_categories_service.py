"""Service layer for meal categories operations."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.api.v1.schemas import MealCategoriesResponse, MealCategoryResponseItem
from app.db.repositories.meal_categories_repository import (  # type: ignore[TCH001]
    MealCategoriesRepository,
)

logger = logging.getLogger(__name__)


class MealCategoriesService:
    """Orchestrates fetching meal categories with proper error handling."""

    def __init__(self, repository: MealCategoriesRepository):
        self._repository = repository

    async def list_categories(
        self,
        *,
        locale: str,
    ) -> MealCategoriesResponse:
        """Retrieve meal categories with localization awareness.

        Args:
            locale: Requested locale identifier (currently ignored until localization is available).

        Returns:
            MealCategoriesResponse with ordered category items.

        Raises:
            HTTPException: 500 for unexpected errors.
        """

        try:
            categories = self._repository.list_categories()

            # TODO: apply locale-based label selection when translations table is available
            data: list[MealCategoryResponseItem] = categories

            return MealCategoriesResponse(data=data)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to fetch meal categories: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve meal categories at this time",
            ) from exc

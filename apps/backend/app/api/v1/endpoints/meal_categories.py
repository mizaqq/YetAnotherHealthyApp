"""Meal categories API endpoint."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # type: ignore[TCH003]

from fastapi import APIRouter, Depends

from app.api.v1.schemas import MealCategoriesQueryParams, MealCategoriesResponse
from app.core.dependencies import (  # type: ignore[TCH001]
    get_current_user_id,
    get_meal_categories_service,
)
from app.services.meal_categories_service import MealCategoriesService  # type: ignore[TCH001]

router = APIRouter()


@router.get(
    "",
    response_model=MealCategoriesResponse,
    summary="List meal categories",
    description="Retrieve canonical meal category dictionary for the authenticated user.",
)
async def list_meal_categories(
    query: Annotated[MealCategoriesQueryParams, Depends()],
    _: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[
        MealCategoriesService,
        Depends(get_meal_categories_service),
    ],
) -> MealCategoriesResponse:
    """List available meal categories.

    Authenticated users receive canonical categories tailored to locale preferences.
    """

    return await service.list_categories(locale=query.locale)

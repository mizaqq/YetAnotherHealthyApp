"""Meals API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # type: ignore[TCH003]

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.meals import (
    MealCreatePayload,
    MealDetailResponse,
    MealListQuery,
    MealListResponse,
    MealResponse,
    MealSource,
    MealUpdatePayload,
)
from app.core.dependencies import (  # type: ignore[TCH001]
    get_current_user_id,
    get_meal_service,
)
from app.services.meal_service import MealService  # type: ignore[TCH001]

router = APIRouter()


@router.get(
    "",
    response_model=MealListResponse,
    summary="List meals",
    description=(
        "Retrieve paginated meals for the authenticated user "
        "with optional filtering by date, category, and source."
    ),
)
async def list_meals(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[MealService, Depends(get_meal_service)],
    from_date: Annotated[str | None, Query(alias="from")] = None,
    to_date: Annotated[str | None, Query(alias="to")] = None,
    category: Annotated[str | None, Query(alias="category", max_length=50)] = None,
    source: Annotated[MealSource | None, Query(alias="source")] = None,
    include_deleted: Annotated[bool, Query(alias="include_deleted")] = False,
    page_size: Annotated[int, Query(alias="page[size]", ge=1, le=100)] = 20,
    page_after: Annotated[str | None, Query(alias="page[after]")] = None,
    sort: Annotated[str, Query(alias="sort")] = "-eaten_at",
) -> MealListResponse:
    """List meals for the authenticated user with cursor-based pagination.

    Authenticated users can filter meals by date range, category, and source.
    Results are ordered by eaten_at (ascending or descending) for stable pagination.

    Query Parameters:
        from: Start of date range filter (ISO8601 format, inclusive)
        to: End of date range filter (ISO8601 format, inclusive)
        category: Filter by meal category code
        source: Filter by meal data source (ai, edited, manual)
        include_deleted: Include soft-deleted meals in results (default false)
        page[size]: Number of results per page (1-100, default 20)
        page[after]: Cursor for next page (base64 encoded)
        sort: Sort field and direction - 'eaten_at' (ascending) or '-eaten_at' (descending, default)

    Returns:
        MealListResponse with data array and pagination metadata

    Raises:
        400: Invalid pagination cursor or date range
        401: Missing or invalid authentication
        500: Internal server error
    """
    # Construct query DTO from individual parameters
    query = MealListQuery(
        from_date=from_date,
        to_date=to_date,
        category=category,
        source=source,
        include_deleted=include_deleted,
        page_size=page_size,
        page_after=page_after,
        sort=sort,
    )

    return await service.list_meals(user_id=user_id, query=query)


@router.post(
    "",
    response_model=MealResponse,
    status_code=201,
    summary="Create a new meal",
    description=(
        "Create a new meal entry for the authenticated user. "
        "Source determines required fields: AI/EDITED require macros "
        "and analysis_run_id, MANUAL forbids them."
    ),
)
async def create_meal(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[MealService, Depends(get_meal_service)],
    payload: MealCreatePayload,
) -> MealResponse:
    """Create a new meal for the authenticated user.

    The request payload must satisfy conditional validation based on source:
    - AI/EDITED sources: require protein, fat, carbs, analysis_run_id
    - MANUAL source: forbids protein, fat, carbs, analysis_run_id

    Request Body:
        category: Meal category code (must exist in meal_categories)
        eaten_at: When the meal was consumed (ISO8601 format, UTC-aware)
        source: Data source - ai, edited, or manual
        calories: Total calories (kcal), must be >= 0
        protein: Protein in grams (required for ai/edited, forbidden for manual)
        fat: Fat in grams (required for ai/edited, forbidden for manual)
        carbs: Carbohydrates in grams (required for ai/edited, forbidden for manual)
        analysis_run_id: Reference to analysis run (required for ai/edited, forbidden for manual)

    Returns:
        MealResponse with complete meal data including timestamps

    Raises:
        400: Validation errors (conditional fields, negative values, etc.)
        401: Missing or invalid authentication
        404: Category not found or analysis_run invalid
        500: Internal server error
    """
    meal_record = await service.create_meal(user_id=user_id, payload=payload)

    # Convert dict to MealResponse
    return MealResponse(**meal_record)


@router.get(
    "/{meal_id}",
    response_model=MealDetailResponse,
    summary="Get meal details",
    description=(
        "Retrieve detailed information about a specific meal, "
        "optionally including analysis run items (ingredients)."
    ),
)
async def get_meal_detail(
    meal_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[MealService, Depends(get_meal_service)],
    include_analysis_items: Annotated[
        bool, Query(description="Include analysis run items (ingredients) in response")
    ] = False,
) -> MealDetailResponse:
    """Retrieve detailed meal information for the authenticated user.

    Returns comprehensive meal data including all fields, timestamps, and optionally
    the associated analysis run metadata with ingredient items.

    Path Parameters:
        meal_id: UUID of the meal to retrieve

    Query Parameters:
        include_analysis_items: If true, includes analysis run items (ingredients)
                                in the response. Default is false for performance.

    Returns:
        MealDetailResponse with:
        - Complete meal data (id, category, eaten_at, macros, etc.)
        - Analysis run metadata (if meal has accepted_analysis_run_id)
        - Analysis run items/ingredients (if include_analysis_items=true)

    Raises:
        400: Invalid meal_id format (not a valid UUID)
        401: Missing or invalid authentication
        404: Meal not found or doesn't belong to the authenticated user
        500: Internal server error

    Security:
        - Requires valid JWT authentication
        - Only returns meals owned by the authenticated user
        - Soft-deleted meals are excluded by default
    """
    meal_data = await service.get_meal_detail(
        user_id=user_id,
        meal_id=meal_id,
        include_analysis_items=include_analysis_items,
    )

    return MealDetailResponse(**meal_data)


@router.patch(
    "/{meal_id}",
    response_model=MealResponse,
    summary="Update a meal",
    description=(
        "Update an existing meal entry. All fields are optional. "
        "Source changes enforce business rules: cannot change to 'manual' "
        "if macros are already set."
    ),
)
async def update_meal(
    meal_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[MealService, Depends(get_meal_service)],
    payload: MealUpdatePayload,
) -> MealResponse:
    """Update an existing meal for the authenticated user.

    All fields are optional, but at least one field must be provided.
    Conditional validation applies when changing source:
    - AI/EDITED sources: if any macro is provided, all must be provided
    - MANUAL source: macros and analysis_run_id are forbidden

    Business rule: Cannot change source back to 'manual' if macros or
    analysis_run_id are already set in the existing meal.

    Path Parameters:
        meal_id: UUID of the meal to update

    Request Body (all optional):
        category: Meal category code (must exist in meal_categories)
        eaten_at: When the meal was consumed (ISO8601 format, UTC-aware)
        source: Data source - ai, edited, or manual (with restrictions)
        calories: Total calories (kcal), must be >= 0
        protein: Protein in grams (conditional based on source)
        fat: Fat in grams (conditional based on source)
        carbs: Carbohydrates in grams (conditional based on source)
        analysis_run_id: Reference to analysis run (conditional based on source)

    Returns:
        MealResponse with updated meal data including new updated_at timestamp

    Raises:
        400: Validation errors (no fields provided, conditional requirements,
             attempt to change to 'manual' with existing macros)
        401: Missing or invalid authentication
        404: Meal not found or doesn't belong to the authenticated user
        409: analysis_run_id already accepted in another meal
        500: Internal server error

    Security:
        - Requires valid JWT authentication
        - Only allows updates to meals owned by the authenticated user
        - Soft-deleted meals cannot be updated
    """
    updated_meal = await service.update_meal(
        user_id=user_id,
        meal_id=meal_id,
        payload=payload,
    )

    return MealResponse(**updated_meal)


@router.delete(
    "/{meal_id}",
    status_code=204,
    summary="Delete a meal",
    description=(
        "Soft-delete a meal by setting deleted_at timestamp. "
        "Soft-deleted meals can be restored in the future."
    ),
)
async def delete_meal(
    meal_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[MealService, Depends(get_meal_service)],
) -> None:
    """Soft-delete a meal for the authenticated user.

    Sets the deleted_at timestamp to mark the meal as deleted without
    permanently removing it from the database. This allows for potential
    restoration and maintains referential integrity.

    Path Parameters:
        meal_id: UUID of the meal to delete

    Returns:
        204 No Content on success (no response body)

    Raises:
        401: Missing or invalid authentication
        404: Meal not found, already deleted, or doesn't belong to the user
        500: Internal server error

    Security:
        - Requires valid JWT authentication
        - Only allows deletion of meals owned by the authenticated user
        - Already soft-deleted meals return 404
        - Does not reveal existence of meals belonging to other users

    Note:
        This is a soft-delete operation. The meal record remains in the
        database with deleted_at timestamp set. Use include_deleted=true
        in GET /meals to view soft-deleted meals.
    """
    await service.soft_delete_meal(
        user_id=user_id,
        meal_id=meal_id,
    )

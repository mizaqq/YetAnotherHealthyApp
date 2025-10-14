"""Service layer for meals operations."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status

from app.api.v1.schemas.meals import (
    MealCreatePayload,
    MealListQuery,
    MealListResponse,
    MealUpdatePayload,
    PageInfo,
    decode_meal_cursor,
    encode_meal_cursor,
)
from app.db.repositories.meal_repository import MealRepository

logger = logging.getLogger(__name__)


class MealService:
    """Orchestrates fetching meals with proper error handling."""

    def __init__(self, repository: MealRepository):
        self._repository = repository

    async def list_meals(
        self,
        *,
        user_id: UUID,
        query: MealListQuery,
    ) -> MealListResponse:
        """Retrieve paginated meals for a user with optional filtering.

        Args:
            user_id: UUID of the authenticated user
            query: Query parameters including filters and pagination

        Returns:
            MealListResponse with meal items and pagination metadata

        Raises:
            HTTPException: 400 for invalid cursor or date range, 500 for unexpected errors
        """
        cursor_data = None

        # Decode cursor if provided
        if query.page_after:
            try:
                cursor_data = decode_meal_cursor(query.page_after)
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

        # Determine sort direction
        sort_desc = query.sort.startswith("-")

        try:
            # Fetch page_size + 1 to detect if there are more results
            meals = self._repository.list_meals(
                user_id=user_id,
                from_date=query.from_date,
                to_date=query.to_date,
                category=query.category,
                source=query.source,
                include_deleted=query.include_deleted,
                page_size=query.page_size,
                cursor=cursor_data,
                sort_desc=sort_desc,
            )

            # Check if there are more results
            has_more = len(meals) > query.page_size
            data = meals[: query.page_size] if has_more else meals

            # Generate next cursor if there are more results
            next_cursor = None
            if has_more and data:
                last_item = data[-1]
                next_cursor = encode_meal_cursor(
                    last_eaten_at=last_item.eaten_at,
                    last_id=last_item.id,
                )

            page_info = PageInfo(size=len(data), after=next_cursor)

            return MealListResponse(data=data, page=page_info)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to fetch meals: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "from_date": query.from_date.isoformat() if query.from_date else None,
                    "to_date": query.to_date.isoformat() if query.to_date else None,
                    "category": query.category,
                    "source": query.source.value if query.source else None,
                    "page_size": query.page_size,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve meals at this time",
            ) from exc

    async def create_meal(self, *, user_id: UUID, payload: MealCreatePayload) -> dict:
        """Create a new meal with validation of category and analysis run.

        Args:
            user_id: UUID of the user creating the meal
            payload: Validated meal creation data

        Returns:
            Created meal record with all fields

        Raises:
            HTTPException:
                - 400: Invalid category or analysis_run validation failed
                - 404: Category or analysis_run not found
                - 409: Analysis run already accepted by another meal
                - 500: Database or unexpected errors
        """
        # Step 1: Validate category exists
        try:
            category_exists = await self._repository.category_exists(category_code=payload.category)
            if not category_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal category '{payload.category}' not found",
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(
                "Failed to validate category: %s",
                exc,
                exc_info=True,
                extra={"user_id": str(user_id), "category": payload.category},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to validate meal category",
            ) from exc

        # Step 2: For AI/EDITED sources, validate analysis_run
        if (
            payload.source
            in (
                payload.source.AI,
                payload.source.EDITED,
            )
            and payload.analysis_run_id
        ):
            try:
                analysis_run = await self._repository.get_analysis_run_for_acceptance(
                    user_id=user_id,
                    analysis_run_id=payload.analysis_run_id,
                )

                if analysis_run is None:
                    # Could be: not found, not owned by user, wrong status, or already accepted
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f"Analysis run '{payload.analysis_run_id}' not found, "
                            "not in 'succeeded' status, or already accepted"
                        ),
                    )

            except HTTPException:
                raise
            except Exception as exc:
                logger.error(
                    "Failed to validate analysis run: %s",
                    exc,
                    exc_info=True,
                    extra={
                        "user_id": str(user_id),
                        "analysis_run_id": str(payload.analysis_run_id),
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to validate analysis run",
                ) from exc

        # Step 3: Create the meal
        try:
            meal_record = await self._repository.create_meal(
                user_id=user_id,
                category=payload.category,
                eaten_at=payload.eaten_at,
                source=payload.source,
                calories=payload.calories,
                protein=payload.protein,
                fat=payload.fat,
                carbs=payload.carbs,
                analysis_run_id=payload.analysis_run_id,
            )

            logger.info(
                "Created meal successfully",
                extra={
                    "user_id": str(user_id),
                    "meal_id": meal_record["id"],
                    "source": payload.source.value,
                },
            )

            return meal_record

        except Exception as exc:
            logger.error(
                "Failed to create meal: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "category": payload.category,
                    "source": payload.source.value,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create meal",
            ) from exc

    async def get_meal_detail(
        self,
        *,
        user_id: UUID,
        meal_id: UUID,
        include_analysis_items: bool = False,
    ) -> dict:
        """Retrieve detailed meal data with optional analysis information.

        Args:
            user_id: UUID of the authenticated user
            meal_id: UUID of the meal to retrieve
            include_analysis_items: Whether to include analysis run items (ingredients)

        Returns:
            Dict with meal data and optional analysis details

        Raises:
            HTTPException: 404 if meal not found, 500 for other errors
        """
        try:
            # Step 1: Fetch the meal
            meal = await self._repository.get_meal_by_id(
                meal_id=meal_id,
                user_id=user_id,
                include_deleted=False,
            )

            if not meal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal with id {meal_id} not found",
                )

            # Step 2: Build response with meal data
            response = {
                "id": meal["id"],
                "user_id": meal["user_id"],
                "category": meal["category"],
                "eaten_at": meal["eaten_at"],
                "source": meal["source"],
                "calories": meal["calories"],
                "protein": meal["protein"],
                "fat": meal["fat"],
                "carbs": meal["carbs"],
                "created_at": meal["created_at"],
                "updated_at": meal["updated_at"],
                "deleted_at": meal["deleted_at"],
                "analysis": None,
            }

            # Step 3: If meal has accepted analysis, fetch analysis details
            if meal.get("accepted_analysis_run_id"):
                analysis_run = await self._repository.get_analysis_run_details(
                    run_id=meal["accepted_analysis_run_id"],
                    user_id=user_id,
                )

                if analysis_run:
                    # Build analysis object
                    analysis_data = {
                        "id": analysis_run["id"],
                        "run_no": analysis_run["run_no"],
                        "status": analysis_run["status"],
                        "model": analysis_run["model"],
                        "latency_ms": analysis_run["latency_ms"],
                        "tokens": analysis_run["tokens"],
                        "cost_minor_units": analysis_run["cost_minor_units"],
                        "cost_currency": analysis_run["cost_currency"],
                        "threshold_used": analysis_run["threshold_used"],
                        "retry_of_run_id": analysis_run["retry_of_run_id"],
                        "error_code": analysis_run["error_code"],
                        "error_message": analysis_run["error_message"],
                        "created_at": analysis_run["created_at"],
                        "completed_at": analysis_run["completed_at"],
                        "items": None,
                    }

                    # Step 4: If requested, fetch analysis run items
                    if include_analysis_items:
                        items = await self._repository.get_analysis_run_items(
                            run_id=meal["accepted_analysis_run_id"],
                            user_id=user_id,
                        )
                        analysis_data["items"] = items

                    response["analysis"] = analysis_data

            logger.info(
                "Retrieved meal detail: %s for user: %s",
                meal_id,
                user_id,
                extra={
                    "meal_id": str(meal_id),
                    "user_id": str(user_id),
                    "has_analysis": response["analysis"] is not None,
                    "include_items": include_analysis_items,
                },
            )

            return response

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to retrieve meal detail: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "meal_id": str(meal_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve meal details",
            ) from exc

    async def update_meal(
        self,
        *,
        user_id: UUID,
        meal_id: UUID,
        payload: MealUpdatePayload,
    ) -> dict:
        """Update an existing meal with validation and business rules.

        Args:
            user_id: UUID of the authenticated user
            meal_id: UUID of the meal to update
            payload: MealUpdatePayload with fields to update

        Returns:
            Dict with updated meal data

        Raises:
            HTTPException: 400 (validation/no changes), 404 (not found),
                          409 (conflict), 500 (server error)
        """
        try:
            # Step 1: Check if at least one field is provided
            update_fields = {
                k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None
            }

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field must be provided for update",
                )

            # Step 2: Fetch current meal to validate ownership and check current state
            current_meal = await self._repository.get_meal_by_id(
                meal_id=meal_id,
                user_id=user_id,
                include_deleted=False,
            )

            if not current_meal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal with ID {meal_id} not found",
                )

            # Step 3: Validate business rules for source changes
            if "source" in update_fields:
                new_source = update_fields["source"]
                current_has_macros = (
                    current_meal.get("protein") is not None
                    or current_meal.get("fat") is not None
                    or current_meal.get("carbs") is not None
                    or current_meal.get("accepted_analysis_run_id") is not None
                )

                # Prevent changing to 'manual' if macros/analysis already set
                if new_source == "manual" and current_has_macros:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "Cannot change source to 'manual' when macros or "
                            "analysis_run_id are already set"
                        ),
                    )

            # Step 4: Validate category exists if being updated
            if "category" in update_fields:
                category_exists = await self._repository.category_exists(update_fields["category"])
                if not category_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Category '{update_fields['category']}' does not exist",
                    )

            # Step 5: Validate analysis_run_id if being updated
            if "analysis_run_id" in update_fields:
                analysis_run = await self._repository.get_analysis_run_for_acceptance(
                    run_id=update_fields["analysis_run_id"],
                    user_id=user_id,
                )

                if not analysis_run:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Analysis run {update_fields['analysis_run_id']} "
                            "not found or not in succeeded status"
                        ),
                    )

                # Check if this analysis_run is already accepted in another meal
                if analysis_run.get("accepted_in_meal_id"):
                    existing_meal_id = analysis_run["accepted_in_meal_id"]
                    # Allow if it's already accepted in THIS meal
                    if str(existing_meal_id) != str(meal_id):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"Analysis run {update_fields['analysis_run_id']} "
                                f"is already accepted in meal {existing_meal_id}"
                            ),
                        )

            # Step 6: Prepare database update dict (convert enums, Decimals, etc.)
            db_updates = {}
            for key, value in update_fields.items():
                if key == "source":
                    db_updates[key] = value.value if hasattr(value, "value") else value
                elif key in ("calories", "protein", "fat", "carbs") and value is not None:
                    # Convert Decimal to float for database
                    db_updates[key] = float(value)
                elif key == "eaten_at" and value is not None:
                    # Convert datetime to ISO string
                    db_updates[key] = value.isoformat()
                else:
                    db_updates[key] = value

            # Step 7: Update the meal in database
            updated_meal = await self._repository.update_meal(
                meal_id=meal_id,
                user_id=user_id,
                updates=db_updates,
            )

            if not updated_meal:
                # This shouldn't happen as we checked earlier, but handle it
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal with ID {meal_id} not found",
                )

            logger.info(
                "Successfully updated meal: %s for user: %s",
                meal_id,
                user_id,
                extra={
                    "meal_id": str(meal_id),
                    "user_id": str(user_id),
                    "updated_fields": list(update_fields.keys()),
                },
            )

            return updated_meal

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except ValueError as exc:
            # Handle validation errors from repository
            logger.warning(
                "Validation error updating meal: %s",
                exc,
                extra={"user_id": str(user_id), "meal_id": str(meal_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.error(
                "Failed to update meal: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "meal_id": str(meal_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update meal",
            ) from exc

    async def soft_delete_meal(
        self,
        *,
        user_id: UUID,
        meal_id: UUID,
    ) -> None:
        """Soft-delete a meal (set deleted_at timestamp).

        Args:
            user_id: UUID of the authenticated user
            meal_id: UUID of the meal to delete

        Raises:
            HTTPException: 404 (not found), 500 (server error)
        """
        try:
            # Attempt to soft-delete the meal
            deleted = await self._repository.soft_delete_meal(
                meal_id=meal_id,
                user_id=user_id,
            )

            if not deleted:
                # Meal doesn't exist, already deleted, or doesn't belong to user
                # Return 404 to avoid leaking information about existence
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal with ID {meal_id} not found",
                )

            logger.info(
                "Successfully soft-deleted meal: %s for user: %s",
                meal_id,
                user_id,
                extra={
                    "meal_id": str(meal_id),
                    "user_id": str(user_id),
                },
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to soft-delete meal: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "meal_id": str(meal_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to delete meal",
            ) from exc

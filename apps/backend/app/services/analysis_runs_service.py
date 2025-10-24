"""Service layer for analysis runs operations."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.api.v1.pagination import AnalysisRunCursor, PageMeta
from app.core.config import settings
from app.db.repositories.analysis_run_items_repository import AnalysisRunItemsRepository
from app.db.repositories.analysis_runs_repository import AnalysisRunsRepository
from app.db.repositories.meal_repository import MealRepository, MealSource
from app.services.analysis_processor import AnalysisRunProcessor
from app.services.openrouter_service import OpenRouterService
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalysisRunsService:
    """Orchestrates analysis runs operations with proper error handling."""

    def __init__(
        self,
        repository: AnalysisRunsRepository,
        items_repository: AnalysisRunItemsRepository | None = None,
        product_repository=None,
        openrouter_service: OpenRouterService | None = None,
    ):
        """Initialize service with repository dependencies.

        Args:
            repository: AnalysisRunsRepository instance for data access
            items_repository: Optional AnalysisRunItemsRepository for items access
            product_repository: Optional ProductRepository for product lookups
        """
        self._repository = repository
        self._items_repository = items_repository
        self._product_repository = product_repository
        self._openrouter_service = openrouter_service
        if items_repository and product_repository:
            self._processor = AnalysisRunProcessor(
                repository=repository,
                items_repository=items_repository,
                product_repository=product_repository,
                openrouter_service=openrouter_service,
            )
        else:
            self._processor = None

    async def get_run_detail(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict:
        """Retrieve detailed information about a single analysis run.

        Validates that the run exists and belongs to the authenticated user.
        Logs access for audit purposes.

        Args:
            run_id: UUID of the analysis run to retrieve
            user_id: UUID of the authenticated user (for authorization)

        Returns:
            Dict with complete analysis run metadata

        Raises:
            HTTPException:
                - 404: Analysis run not found or doesn't belong to user
                - 500: Database or unexpected errors
        """
        try:
            # Fetch analysis run from repository
            analysis_run = await self._repository.get_by_id(
                run_id=run_id,
                user_id=user_id,
            )

            if analysis_run is None:
                # Run doesn't exist or doesn't belong to this user
                # Don't reveal which case to avoid information leakage
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "analysis_run_not_found"},
                )

            # Log successful access for audit trail
            logger.info(
                "analysis_runs.view",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "status": analysis_run["status"],
                    "meal_id": str(analysis_run["meal_id"]),
                },
            )

            return analysis_run

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to retrieve analysis run detail: %s",
                exc,
                exc_info=True,
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def create_run(
        self,
        *,
        user_id: UUID,
        meal_id: UUID | None,
        input_text: str | None,
        threshold: float,
        retry_of_run_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Create a new analysis run for a meal or text input.

        Validates preconditions (meal ownership, no active runs),
        creates the run record, and synchronously processes the analysis (MVP approach).

        Args:
            user_id: UUID of the authenticated user
            meal_id: Optional UUID of existing meal to analyze
            input_text: Optional raw text description to analyze
            threshold: Confidence threshold (0-1) for matching
            retry_of_run_id: Optional UUID of previous run being retried

        Returns:
            Dict with created analysis run metadata (queued response format)

        Raises:
            HTTPException:
                - 400: Invalid input (both meal_id and input_text, or neither)
                - 404: Meal not found or doesn't belong to user
                - 409: Active analysis run already exists for this meal
                - 500: Database or unexpected errors
        """
        try:
            # Validate: exactly one of meal_id or input_text must be provided
            has_meal = meal_id is not None
            has_text = input_text is not None

            if not has_meal and not has_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "missing_input",
                        "message": "Either meal_id or input_text must be provided",
                    },
                )

            if has_meal and has_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "conflicting_input",
                        "message": "Only one of meal_id or input_text can be provided",
                    },
                )

            # If meal_id is provided, validate it exists and belongs to user
            if meal_id is not None:
                meal = await self._repository.get_meal_for_user(
                    meal_id=meal_id,
                    user_id=user_id,
                )

                if meal is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "code": "meal_not_found",
                            "message": "Meal not found or doesn't belong to user",
                        },
                    )

                # Check for active runs (queued or running)
                active_run = await self._repository.get_active_run(
                    meal_id=meal_id,
                    user_id=user_id,
                )

                if active_run is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "analysis_run_active",
                            "message": f"Active analysis run {active_run['id']} already exists for this meal",
                        },
                    )

                # Get next run_no for this meal
                run_no = await self._repository.get_next_run_no(
                    meal_id=meal_id,
                    user_id=user_id,
                )

                # Prepare raw_input (for now, store meal_id reference)
                raw_input = {
                    "meal_id": str(meal_id),
                    "source": "meal",
                }

            else:
                # Text-based analysis (no meal_id)
                # Process analysis FIRST, then create AI meal with results
                # This is the primary flow for AI-assisted meal logging

                # For text analysis, meal_id is None initially
                meal_id = None
                run_no = 1  # First run (meal will be created after analysis)

                # Prepare raw_input (store the text description)
                raw_input = {
                    "text": input_text,
                    "source": "text",
                }

                logger.info(
                    "Starting text-based analysis",
                    extra={
                        "user_id": str(user_id),
                        "input_text_preview": input_text[:50]
                        if len(input_text) > 50
                        else input_text,
                    },
                )

            # Insert analysis run record
            analysis_run = await self._repository.insert_run(
                user_id=user_id,
                meal_id=meal_id,
                run_no=run_no,
                status="queued",
                model=settings.analysis_model,
                threshold_used=Decimal(str(threshold)),
                raw_input=raw_input,
                retry_of_run_id=retry_of_run_id,
            )

            # Log successful creation
            logger.info(
                "analysis_runs.created",
                extra={
                    "run_id": str(analysis_run["id"]),
                    "user_id": str(user_id),
                    "meal_id": str(meal_id) if meal_id else None,
                    "run_no": run_no,
                    "model": settings.analysis_model,
                },
            )

            # MVP: Synchronously process the analysis
            if self._processor:
                logger.info(
                    "Starting synchronous analysis processing",
                    extra={"run_id": str(analysis_run["id"])},
                )

                # Process the analysis synchronously and return final result
                final_run = await self._processor.process(
                    run_id=analysis_run["id"],
                    user_id=user_id,
                    meal_id=meal_id,
                    raw_input=raw_input,
                    threshold=Decimal(str(threshold)),
                )

                # If this was an existing meal being analyzed, update it
                if final_run["status"] == "succeeded" and meal_id is not None:
                    run_id = (
                        final_run["id"]
                        if isinstance(final_run["id"], UUID)
                        else UUID(final_run["id"])
                    )

                    await self._update_ai_meal_with_results(
                        meal_id=meal_id,
                        user_id=user_id,
                        analysis_run_id=run_id,
                    )

                return final_run
            else:
                # Fallback: return queued run if processor not available
                logger.warning(
                    "Processor not available, returning queued run",
                    extra={"run_id": str(analysis_run["id"])},
                )
                return analysis_run

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to create analysis run: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "meal_id": str(meal_id) if meal_id else None,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def list_runs(
        self,
        *,
        user_id: UUID,
        meal_id: UUID | None,
        status_filter: str | None,
        created_from: Any | None,
        created_to: Any | None,
        page_size: int,
        page_after: str | None,
        sort: str,
    ) -> dict[str, Any]:
        """List analysis runs with filtering and cursor pagination.

        Args:
            user_id: User identifier for filtering
            meal_id: Optional meal filter
            status_filter: Optional status filter
            created_from: Optional start of date range
            created_to: Optional end of date range
            page_size: Number of items per page (1-50)
            page_after: Opaque cursor for next page
            sort: Sort field (created_at or -created_at)

        Returns:
            Dict with keys 'data' (list of runs) and 'page' (PageMeta)

        Raises:
            HTTPException:
                - 400: Invalid cursor format
                - 500: Database or unexpected errors
        """
        # Decode cursor if provided
        cursor_created_at = None
        cursor_id = None
        if page_after:
            try:
                cursor = AnalysisRunCursor.decode(page_after)
                cursor_created_at = cursor.created_at
                cursor_id = cursor.id
            except ValueError as exc:
                logger.warning(
                    "Invalid cursor provided",
                    extra={"user_id": str(user_id), "cursor": page_after},
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "invalid_cursor", "message": "Invalid pagination cursor"},
                ) from exc

        # Determine sort direction
        sort_desc = sort.startswith("-")

        # Fetch page_size + 1 to detect if there's a next page
        limit = page_size + 1

        try:
            # Fetch runs from repository
            runs = await self._repository.list_runs(
                user_id=user_id,
                meal_id=meal_id,
                status=status_filter,
                created_from=created_from,
                created_to=created_to,
                limit=limit,
                cursor_created_at=cursor_created_at,
                cursor_id=cursor_id,
                sort_desc=sort_desc,
            )

            # Check if there's a next page
            has_next_page = len(runs) > page_size
            if has_next_page:
                # Remove the extra item
                runs = runs[:page_size]

            # Generate cursor for next page
            next_cursor = None
            if has_next_page and runs:
                last_run = runs[-1]
                cursor_obj = AnalysisRunCursor(
                    created_at=last_run["created_at"],
                    id=last_run["id"],
                )
                next_cursor = cursor_obj.encode()

            # Build page metadata
            page_meta = PageMeta(
                size=len(runs),
                after=next_cursor,
            )

            logger.info(
                "Listed analysis runs",
                extra={
                    "user_id": str(user_id),
                    "count": len(runs),
                    "has_next": has_next_page,
                    "filters": {
                        "meal_id": str(meal_id) if meal_id else None,
                        "status": status_filter,
                    },
                },
            )

            return {
                "data": runs,
                "page": page_meta,
            }

        except RuntimeError as exc:
            logger.error(
                "Failed to list analysis runs",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "filters": {
                        "meal_id": str(meal_id) if meal_id else None,
                        "status": status_filter,
                    },
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unexpected error listing analysis runs",
                exc_info=True,
                extra={"user_id": str(user_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def retry_run(
        self,
        *,
        user_id: UUID,
        source_run_id: UUID,
        threshold: float | None,
        raw_input_override: dict | None,
    ) -> dict[str, Any]:
        """Retry an analysis run with optional threshold and input overrides.

        Validates that source run exists, belongs to user, is in terminal state,
        and no active run exists for the meal. Creates new run with incremented
        run_no and synchronously processes it (MVP mock).

        Args:
            user_id: UUID of the authenticated user
            source_run_id: UUID of the analysis run to retry
            threshold: Optional new confidence threshold (0-1)
            raw_input_override: Optional new raw input dict

        Returns:
            Dict with created analysis run metadata (detail response format)

        Raises:
            HTTPException:
                - 400: Source run not in terminal state, invalid overrides
                - 404: Source run not found or doesn't belong to user
                - 409: Active analysis run already exists for the meal
                - 500: Database or unexpected errors
        """
        try:
            # Fetch source run with raw_input
            source_run = await self._repository.get_run_with_raw_input(
                run_id=source_run_id,
                user_id=user_id,
            )

            if source_run is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "analysis_run_not_found",
                        "message": "Source analysis run not found or doesn't belong to user",
                    },
                )

            # Validate source run is in terminal state
            terminal_states = {"succeeded", "failed", "cancelled"}
            if source_run["status"] not in terminal_states:
                retry_msg = (
                    f"Cannot retry run in '{source_run['status']}' state. "
                    "Only terminal states (succeeded, failed, cancelled) "
                    "can be retried."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "invalid_retry_state",
                        "message": retry_msg,
                    },
                )

            # Extract meal_id from source run
            meal_id = source_run["meal_id"]

            # Check for active runs (queued or running) only if meal_id is present
            if meal_id is not None:
                active_run = await self._repository.get_active_run(
                    meal_id=meal_id,
                    user_id=user_id,
                )
            else:
                # Ad-hoc analysis (no meal_id), skip active run check
                active_run = None

            if active_run is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "analysis_run_active",
                        "message": f"Active analysis run {active_run['id']} already exists for this meal",
                    },
                )

            # Determine threshold: use override or source run's value
            threshold_used = threshold if threshold is not None else source_run["threshold_used"]
            if threshold_used is None:
                # Fallback to default if source run had no threshold
                threshold_used = Decimal("0.8")
            elif not isinstance(threshold_used, Decimal):
                threshold_used = Decimal(str(threshold_used))

            # Determine raw_input: use override or source run's value
            raw_input = (
                raw_input_override if raw_input_override is not None else source_run["raw_input"]
            )

            # Get next run_no
            run_no = await self._repository.get_next_run_no(
                meal_id=meal_id,
                user_id=user_id,
            )

            # Insert new analysis run record
            new_run = await self._repository.insert_run(
                user_id=user_id,
                meal_id=meal_id,
                run_no=run_no,
                status="queued",
                model=settings.analysis_model,
                threshold_used=threshold_used,
                raw_input=raw_input,
                retry_of_run_id=source_run_id,
            )

            # Log successful retry creation
            logger.info(
                "analysis_runs.retry_created",
                extra={
                    "run_id": str(new_run["id"]),
                    "source_run_id": str(source_run_id),
                    "user_id": str(user_id),
                    "meal_id": str(meal_id),
                    "run_no": run_no,
                    "threshold_used": str(threshold_used),
                },
            )

            # MVP: Synchronously process the retry analysis
            if self._processor:
                logger.info(
                    "Starting synchronous retry analysis processing",
                    extra={
                        "run_id": str(new_run["id"]),
                        "source_run_id": str(source_run_id),
                    },
                )

                # Process the analysis synchronously and return final result
                final_run = await self._processor.process(
                    run_id=new_run["id"],
                    user_id=user_id,
                    meal_id=meal_id,
                    raw_input=raw_input,
                    threshold=threshold_used,
                )

                return final_run
            else:
                # Fallback: fetch and return the queued run if processor not available
                logger.warning(
                    "Processor not available, returning queued run",
                    extra={"run_id": str(new_run["id"])},
                )
                final_run = await self._repository.get_by_id(
                    run_id=new_run["id"],
                    user_id=user_id,
                )
                return final_run

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                "Failed to retry analysis run: %s",
                exc,
                exc_info=True,
                extra={
                    "user_id": str(user_id),
                    "source_run_id": str(source_run_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def get_run_items(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Get items (ingredients) for an analysis run.

        Validates run ownership and fetches all items sorted by ordinal.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization

        Returns:
            Dict with run_id, model, and items list

        Raises:
            HTTPException 404: If run not found or not owned by user
            HTTPException 500: If database error occurs
        """
        if not self._items_repository:
            msg = "Items repository not configured"
            raise RuntimeError(msg)

        try:
            # Step 1: Verify run exists and belongs to user
            run = await self._repository.get_by_id(run_id=run_id, user_id=user_id)

            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "analysis_run_not_found",
                        "message": f"Analysis run {run_id} not found",
                    },
                )

            # Step 2: Fetch items for this run
            items = await self._items_repository.list_items(
                run_id=run_id,
                user_id=user_id,
            )

            # Step 3: Build response structure
            result = {
                "run_id": run_id,
                "model": run.get("model", settings.analysis_model),
                "items": items,
            }

            logger.info(
                "Retrieved analysis run items",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "items_count": len(items),
                },
            )

            return result

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.exception(
                "Failed to retrieve analysis run items",
                exc_info=True,
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def cancel_run(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Cancel an analysis run if it is not already in a terminal state.

        Validates run ownership and attempts to cancel. If the run is already
        in a terminal state (succeeded/failed/cancelled), returns 409 Conflict.

        Args:
            run_id: Analysis run identifier
            user_id: User identifier for authorization

        Returns:
            Dict with run details after cancellation

        Raises:
            HTTPException 404: If run not found or not owned by user
            HTTPException 409: If run is already in a terminal state
            HTTPException 500: If database error occurs
        """
        try:
            # Step 1: Verify run exists and get its current state
            run = await self._repository.get_by_id(run_id=run_id, user_id=user_id)

            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "analysis_run_not_found",
                        "message": f"Analysis run {run_id} not found",
                    },
                )

            # Step 2: Check if run is already in a terminal state
            current_status = run.get("status")
            if current_status in ("succeeded", "failed", "cancelled"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "analysis_run_already_finished",
                        "message": f"Cannot cancel run in '{current_status}' status",
                    },
                )

            # Step 3: Attempt to cancel the run using conditional update
            cancelled_run = await self._repository.cancel_run_if_active(
                run_id=run_id,
                user_id=user_id,
            )

            # Step 4: Handle race condition - run might have transitioned to terminal state
            # between our check and the update
            if not cancelled_run:
                # Re-fetch to get the actual current state
                run = await self._repository.get_by_id(run_id=run_id, user_id=user_id)
                if run and run.get("status") in ("succeeded", "failed", "cancelled"):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "analysis_run_already_finished",
                            "message": f"Run completed before cancellation with status '{run.get('status')}'",
                        },
                    )
                # Should not happen unless run was deleted
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "analysis_run_not_found",
                        "message": f"Analysis run {run_id} not found",
                    },
                )

            logger.info(
                "Analysis run cancelled",
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                    "previous_status": current_status,
                },
            )

            return cancelled_run

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.exception(
                "Failed to cancel analysis run",
                exc_info=True,
                extra={
                    "run_id": str(run_id),
                    "user_id": str(user_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error"},
            ) from exc

    async def _create_ai_meal_from_analysis(
        self,
        *,
        user_id: UUID,
        analysis_run_id: UUID,
        category: str,
        eaten_at: datetime,
    ) -> UUID:
        """Create a new AI meal with analysis results.

        Fetches all items from the analysis run, calculates total nutrition,
        and creates a new meal record with these values.

        Args:
            user_id: User identifier
            analysis_run_id: Analysis run identifier
            category: Meal category (e.g., 'sniadanie', 'obiad')
            eaten_at: When the meal was consumed

        Returns:
            UUID of the created meal

        Raises:
            RuntimeError: If unable to fetch items or create meal
        """
        try:
            # Fetch all items for this analysis run
            items = await self._items_repository.list_items(
                run_id=analysis_run_id,
                user_id=user_id,
            )

            # Calculate total nutrition from all items
            total_calories = sum(Decimal(str(item["calories"])) for item in items)
            total_protein = sum(Decimal(str(item["protein"])) for item in items)
            total_fat = sum(Decimal(str(item["fat"])) for item in items)
            total_carbs = sum(Decimal(str(item["carbs"])) for item in items)

            # Create the AI meal with calculated values
            meal_repo = MealRepository(self._repository._client)

            meal = await meal_repo.create_meal(
                user_id=user_id,
                category=category,
                eaten_at=eaten_at,
                source=MealSource.AI,
                calories=total_calories,
                protein=total_protein,
                fat=total_fat,
                carbs=total_carbs,
                analysis_run_id=analysis_run_id,
            )

            logger.info(
                "Created AI meal from analysis results",
                extra={
                    "meal_id": meal["id"],
                    "analysis_run_id": str(analysis_run_id),
                    "calories": float(total_calories),
                    "protein": float(total_protein),
                    "fat": float(total_fat),
                    "carbs": float(total_carbs),
                },
            )

            return UUID(meal["id"])

        except Exception as exc:
            logger.exception(
                "Failed to create AI meal from analysis: run=%s",
                analysis_run_id,
            )
            raise RuntimeError(f"Failed to create AI meal: {exc}") from exc

    async def _update_ai_meal_with_results(
        self,
        *,
        meal_id: UUID,
        user_id: UUID,
        analysis_run_id: UUID,
    ) -> None:
        """Update AI meal with analysis results (nutrition totals).

        Fetches all items from the analysis run, calculates total nutrition,
        and updates the meal record with these values.

        Args:
            meal_id: Meal identifier to update
            user_id: User identifier for authorization
            analysis_run_id: Analysis run identifier

        Raises:
            RuntimeError: If unable to fetch items or update meal
        """
        try:
            # Fetch all items for this analysis run
            items = await self._items_repository.list_items(
                run_id=analysis_run_id,
                user_id=user_id,
            )

            # Calculate total nutrition from all items
            total_calories = sum(Decimal(str(item["calories"])) for item in items)
            total_protein = sum(Decimal(str(item["protein"])) for item in items)
            total_fat = sum(Decimal(str(item["fat"])) for item in items)
            total_carbs = sum(Decimal(str(item["carbs"])) for item in items)

            # Update the meal with calculated values
            meal_repo = MealRepository(self._repository._client)

            await meal_repo.update_meal(
                meal_id=meal_id,
                user_id=user_id,
                source=MealSource.AI,
                calories=total_calories,
                protein=total_protein,
                fat=total_fat,
                carbs=total_carbs,
                analysis_run_id=analysis_run_id,
            )

            logger.info(
                "Updated AI meal with analysis results",
                extra={
                    "meal_id": str(meal_id),
                    "analysis_run_id": str(analysis_run_id),
                    "calories": float(total_calories),
                    "protein": float(total_protein),
                    "fat": float(total_fat),
                    "carbs": float(total_carbs),
                },
            )

        except Exception:
            logger.exception(
                "Failed to update AI meal with results: meal=%s run=%s",
                meal_id,
                analysis_run_id,
            )
            # Don't raise - analysis succeeded, meal update is secondary
            # The meal will have placeholder values but analysis is available

    @staticmethod
    def _quantize_two_decimal_places(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

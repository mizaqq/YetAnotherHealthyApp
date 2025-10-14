"""Analysis runs API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError

from app.api.v1.pagination import PageMeta, PaginatedResponse
from app.api.v1.schemas.analysis_runs import (
    AnalysisRunCancelResponse,
    AnalysisRunCreateRequest,
    AnalysisRunDetailResponse,
    AnalysisRunItemResponse,
    AnalysisRunItemsResponse,
    AnalysisRunListQuery,
    AnalysisRunQueuedResponse,
    AnalysisRunRetryRequest,
    AnalysisRunSummaryResponse,
)
from app.core.dependencies import (
    get_analysis_runs_service,
    get_current_user_id,
)
from app.services.analysis_runs_service import AnalysisRunsService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[AnalysisRunSummaryResponse],
    summary="List analysis runs",
    description="Retrieve a paginated list of analysis runs with optional filters.",
    responses={
        200: {
            "description": "Analysis runs retrieved successfully",
        },
        400: {
            "description": "Invalid request parameters",
        },
        401: {
            "description": "Missing or invalid authentication",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
async def list_analysis_runs(
    query: Annotated[AnalysisRunListQuery, Depends()],
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> PaginatedResponse[AnalysisRunSummaryResponse]:
    """List analysis runs for the authenticated user with filtering and pagination."""
    try:
        # Delegate to service layer
        result = await service.list_runs(
            user_id=user_id,
            meal_id=query.meal_id,
            status_filter=query.status,
            created_from=query.created_from,
            created_to=query.created_to,
            page_size=query.page_size,
            page_after=query.page_after,
            sort=query.sort,
        )

        # Convert dicts to response models
        data = [AnalysisRunSummaryResponse(**run) for run in result["data"]]
        page_meta = result["page"]

        return PaginatedResponse(data=data, page=page_meta)

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc


@router.get(
    "/{run_id}",
    response_model=AnalysisRunDetailResponse,
    summary="Get analysis run details",
    description=(
        "Retrieve detailed information about a specific AI analysis run, "
        "including metadata, metrics, costs, and error information."
    ),
    responses={
        200: {
            "description": "Analysis run details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "run_no": 2,
                        "status": "succeeded",
                        "latency_ms": 1500,
                        "tokens": 850,
                        "cost_minor_units": 15,
                        "cost_currency": "USD",
                        "threshold_used": 0.8,
                        "model": "openrouter/gpt-4o-mini",
                        "retry_of_run_id": None,
                        "error_code": None,
                        "error_message": None,
                        "created_at": "2025-10-12T07:40:00Z",
                        "completed_at": "2025-10-12T07:40:01.5Z",
                    }
                }
            },
        },
        400: {
            "description": "Invalid run_id format (not a valid UUID)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "invalid_run_id",
                            "message": "run_id must be a valid UUID",
                        }
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid authentication",
            "content": {
                "application/json": {"example": {"detail": "Missing authorization header"}}
            },
        },
        404: {
            "description": "Analysis run not found or doesn't belong to authenticated user",
            "content": {
                "application/json": {"example": {"detail": {"code": "analysis_run_not_found"}}}
            },
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": {"code": "internal_error"}}}},
        },
    },
)
async def get_analysis_run_detail(
    run_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> AnalysisRunDetailResponse:
    """Retrieve detailed analysis run information for the authenticated user.

    Returns comprehensive metadata about a single AI analysis execution, including:
    - Execution metrics (latency, tokens consumed)
    - Cost information (minor units and currency)
    - Status and error details
    - Model configuration (model identifier, threshold)
    - Retry information (if this run was a retry)

    This endpoint is useful for:
    - Debugging failed analysis runs
    - Monitoring AI usage and costs
    - Displaying analysis history to users
    - Understanding retry chains

    Path Parameters:
        run_id: UUID of the analysis run to retrieve

    Returns:
        AnalysisRunDetailResponse with complete analysis run metadata

    Raises:
        400: Invalid run_id format (not a valid UUID4)
        401: Missing or invalid authentication (JWT)
        404: Analysis run not found or doesn't belong to the authenticated user
        500: Internal server error (database or unexpected errors)

    Security:
        - Requires valid JWT authentication via Authorization header
        - Only returns analysis runs owned by the authenticated user
        - Row-level security enforced via user_id filtering
        - Sensitive fields (raw_input, raw_output) are excluded from response

    Performance:
        - Single database query with optimized column selection
        - Response can be cached client-side (consider Cache-Control headers)
        - Typical response time: < 100ms

    Example:
        ```
        GET /api/v1/analysis-runs/223e4567-e89b-12d3-a456-426614174001
        Authorization: Bearer <jwt_token>
        ```
    """
    # Path parameter is automatically validated as UUID by FastAPI
    # If validation fails, FastAPI returns 422 Unprocessable Entity
    # We catch this early to return 400 instead for better UX

    try:
        # Delegate to service layer for business logic
        analysis_run = await service.get_run_detail(
            run_id=run_id,
            user_id=user_id,
        )

        # Convert dict to response model
        return AnalysisRunDetailResponse(**analysis_run)

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors (shouldn't happen with proper repo normalization)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Data validation failed"},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc


@router.post(
    "",
    response_model=AnalysisRunQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create new analysis run",
    description=(
        "Queue a new AI analysis run for a meal or raw text description. "
        "In MVP, the analysis is processed synchronously within the request. "
        "Returns 202 Accepted with queued run metadata."
    ),
    responses={
        202: {
            "description": "Analysis run queued successfully",
            "headers": {
                "Location": {
                    "description": "URL to retrieve the analysis run details",
                    "schema": {"type": "string"},
                },
                "Retry-After": {
                    "description": "Suggested retry delay in seconds",
                    "schema": {"type": "integer"},
                },
            },
            "content": {
                "application/json": {
                    "example": {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "meal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "run_no": 1,
                        "status": "queued",
                        "threshold_used": 0.8,
                        "model": "openrouter/gpt-4o-mini",
                        "retry_of_run_id": None,
                        "latency_ms": None,
                        "created_at": "2025-10-12T07:29:30Z",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request (bad input, validation errors)",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_input": {
                            "summary": "Neither meal_id nor input_text provided",
                            "value": {
                                "detail": {
                                    "code": "missing_input",
                                    "message": "Either meal_id or input_text must be provided",
                                }
                            },
                        },
                        "conflicting_input": {
                            "summary": "Both meal_id and input_text provided",
                            "value": {
                                "detail": {
                                    "code": "conflicting_input",
                                    "message": "Only one of meal_id or input_text can be provided",
                                }
                            },
                        },
                        "text_not_supported": {
                            "summary": "Text analysis not yet implemented",
                            "value": {
                                "detail": {
                                    "code": "text_analysis_not_supported",
                                    "message": "Ad-hoc text analysis not yet supported in MVP",
                                }
                            },
                        },
                        "invalid_threshold": {
                            "summary": "Threshold out of range",
                            "value": {
                                "detail": {
                                    "code": "validation_error",
                                    "message": "threshold must be between 0 and 1",
                                }
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid authentication",
            "content": {
                "application/json": {"example": {"detail": "Missing authorization header"}}
            },
        },
        404: {
            "description": "Meal not found or doesn't belong to authenticated user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "meal_not_found",
                            "message": "Meal not found or doesn't belong to user",
                        }
                    }
                }
            },
        },
        409: {
            "description": "Active analysis run already exists for this meal",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "analysis_run_active",
                            "message": "Active analysis run already exists for this meal",
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": {"code": "internal_error"}}}},
        },
    },
)
async def create_analysis_run(
    payload: AnalysisRunCreateRequest,
    response: Response,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> AnalysisRunQueuedResponse:
    """Create a new analysis run for meal or text input.

    Validates the request, creates an analysis run record in the database,
    and (in MVP) synchronously processes the analysis. Returns 202 Accepted
    with metadata about the queued/running analysis.

    Request Body:
        - meal_id: Optional UUID of existing meal to analyze
        - input_text: Optional raw text description to analyze
        - threshold: Confidence threshold for matching (0-1, default 0.8)
        - Exactly one of meal_id or input_text must be provided

    Returns:
        AnalysisRunQueuedResponse with run metadata

    Response Headers:
        - Location: URL to GET the analysis run details
        - Retry-After: Suggested retry delay (5 seconds)

    Raises:
        400: Invalid request (validation errors, conflicting inputs)
        401: Missing or invalid authentication (JWT)
        404: Meal not found or doesn't belong to user
        409: Active analysis run already exists for this meal
        500: Internal server error (database or unexpected errors)

    Security:
        - Requires valid JWT authentication via Authorization header
        - Meal ownership validated via user_id filtering
        - Row-level security enforced in database queries
        - Input text sanitized and length-limited (1-2000 chars)

    Business Rules:
        - Only one active (queued/running) analysis per meal at a time
        - Sequential run_no assigned per meal
        - Text analysis not yet supported in MVP (returns 400)
        - Threshold defaults to 0.8 if not provided

    Performance:
        - Multiple database queries (validation, active check, insert)
        - Synchronous processing in MVP (blocking)
        - Consider rate limiting to prevent abuse

    Example:
        ```
        POST /api/v1/analysis-runs
        Authorization: Bearer <jwt_token>
        Content-Type: application/json

        {
          "meal_id": "123e4567-e89b-12d3-a456-426614174000",
          "threshold": 0.85
        }
        ```
    """
    try:
        # Delegate to service layer for business logic
        analysis_run = await service.create_run(
            user_id=user_id,
            meal_id=payload.meal_id,
            input_text=payload.input_text,
            threshold=payload.threshold,
        )

        # Set response headers
        run_id = analysis_run["id"]
        response.headers["Location"] = f"/api/v1/analysis-runs/{run_id}"
        response.headers["Retry-After"] = "5"

        # Convert dict to response model
        return AnalysisRunQueuedResponse(**analysis_run)

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors from response model
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error", "message": "Data validation failed"},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc


@router.post(
    "/{run_id}/retry",
    response_model=AnalysisRunDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry analysis run",
    description="Retry an existing analysis run with optional threshold and input overrides.",
    responses={
        200: {
            "description": "Analysis run retried successfully, returning final state",
        },
        400: {
            "description": "Invalid request (e.g., source run not in terminal state)",
        },
        401: {
            "description": "Missing or invalid authentication",
        },
        404: {
            "description": "Source analysis run not found",
        },
        409: {
            "description": "Active analysis run already exists for the meal",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
async def retry_analysis_run(
    run_id: UUID,
    request: AnalysisRunRetryRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> AnalysisRunDetailResponse:
    """Retry an analysis run with optional overrides.

    Creates a new analysis run based on the source run, optionally overriding
    the threshold and/or raw input. The source run must be in a terminal state
    (succeeded, failed, or cancelled).
    """
    try:
        # Delegate to service layer
        analysis_run = await service.retry_run(
            user_id=user_id,
            source_run_id=run_id,
            threshold=request.threshold,
            raw_input_override=request.raw_input,
        )

        # Convert dict to response model
        return AnalysisRunDetailResponse(**analysis_run)

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc


@router.get(
    "/{run_id}/items",
    response_model=AnalysisRunItemsResponse,
    summary="Get analysis run items",
    description="Retrieve all ingredients (items) generated during an analysis run with nutritional details.",
    responses={
        200: {
            "description": "Analysis run items retrieved successfully",
            "model": AnalysisRunItemsResponse,
        },
        400: {
            "description": "Invalid run_id format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "invalid_run_id",
                            "message": "run_id must be a valid UUID",
                        }
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid authentication",
            "content": {
                "application/json": {"example": {"detail": "Missing authorization header"}}
            },
        },
        404: {
            "description": "Analysis run not found or not owned by user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "analysis_run_not_found",
                            "message": "Analysis run {run_id} not found",
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": {"code": "internal_error"}}}},
        },
    },
)
async def get_analysis_run_items(
    run_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> AnalysisRunItemsResponse:
    """Get ingredients (items) for an analysis run.

    Fetches all items generated during the analysis run, sorted by ordinal.
    Returns empty list if no items found.

    Args:
        run_id: Analysis run identifier (UUID from path)
        user_id: Authenticated user ID (from JWT token)
        service: Analysis runs service instance (injected)

    Returns:
        AnalysisRunItemsResponse with run_id, model, and items list

    Raises:
        HTTPException 400: Invalid run_id format
        HTTPException 401: Missing or invalid authentication
        HTTPException 404: Analysis run not found or not owned by user
        HTTPException 500: Internal server error
    """
    try:
        # Delegate to service layer
        result = await service.get_run_items(
            run_id=run_id,
            user_id=user_id,
        )

        # Convert items dicts to response models
        items = [AnalysisRunItemResponse(**item) for item in result["items"]]

        # Build final response
        return AnalysisRunItemsResponse(
            run_id=result["run_id"],
            model=result["model"],
            items=items,
        )

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc


@router.post(
    "/{run_id}/cancel",
    response_model=AnalysisRunCancelResponse,
    summary="Cancel analysis run",
    description="Cancels a running or queued analysis run. Cannot cancel runs that are already completed, failed, or cancelled.",
    responses={
        200: {
            "description": "Analysis run cancelled successfully",
            "model": AnalysisRunCancelResponse,
        },
        400: {
            "description": "Invalid run_id format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "invalid_run_id",
                            "message": "run_id must be a valid UUID",
                        }
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid authentication",
            "content": {
                "application/json": {"example": {"detail": "Missing authorization header"}}
            },
        },
        404: {
            "description": "Analysis run not found or not owned by user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "analysis_run_not_found",
                            "message": "Analysis run {run_id} not found",
                        }
                    }
                }
            },
        },
        409: {
            "description": "Analysis run already in terminal state (cannot cancel)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "analysis_run_already_finished",
                            "message": "Cannot cancel run in 'succeeded' status",
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": {"code": "internal_error"}}}},
        },
    },
)
async def cancel_analysis_run(
    run_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[AnalysisRunsService, Depends(get_analysis_runs_service)],
) -> AnalysisRunCancelResponse:
    """Cancel an analysis run.

    Cancels a running or queued analysis run by setting its status to 'cancelled'
    with error_code='USER_CANCELLED'. Only the owner can cancel their runs.

    Runs that are already in a terminal state (succeeded, failed, cancelled)
    cannot be cancelled and will return 409 Conflict.

    Args:
        run_id: Analysis run identifier (UUID from path)
        user_id: Authenticated user ID (from JWT token)
        service: Analysis runs service instance (injected)

    Returns:
        AnalysisRunCancelResponse with final state after cancellation

    Raises:
        HTTPException 400: Invalid run_id format
        HTTPException 401: Missing or invalid authentication
        HTTPException 404: Analysis run not found or not owned by user
        HTTPException 409: Run already in terminal state
        HTTPException 500: Internal server error
    """
    try:
        # Delegate to service layer
        result = await service.cancel_run(
            run_id=run_id,
            user_id=user_id,
        )

        # Build response with only the fields defined in AnalysisRunCancelResponse
        return AnalysisRunCancelResponse(
            id=result["id"],
            status=result["status"],
            model=result.get("model", "unknown"),
            cancelled_at=result.get("completed_at"),  # completed_at is set to cancellation time
            error_code=result.get("error_code"),
            error_message=result.get("error_message"),
        )

    except HTTPException:
        # Re-raise HTTP exceptions from service layer as-is
        raise
    except ValidationError as exc:
        # Handle Pydantic validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "internal_error"},
        ) from exc

"""
Profile-related API endpoints.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import get_current_user_id, get_profile_service
from app.schemas.profile import (
    CompleteOnboardingCommand,
    ProfileOnboardingRequest,
    ProfileResponse,
    UpdateProfileCommand,
    UpdateProfileRequest,
)
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/onboarding",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete user onboarding",
    description=(
        "Create or finalize user profile during onboarding process. "
        "This operation is idempotent: first call creates/completes the profile, "
        "subsequent calls return 409 Conflict if onboarding was already completed."
    ),
    responses={
        201: {
            "description": "Profile created or updated successfully",
            "headers": {
                "Location": {
                    "description": "URL to retrieve the profile",
                    "schema": {"type": "string"},
                }
            },
        },
        400: {"description": "Invalid daily_calorie_goal value"},
        401: {"description": "Missing or invalid authentication token"},
        409: {"description": "Onboarding already completed"},
        500: {"description": "Internal server error"},
    },
)
async def complete_onboarding(
    request: ProfileOnboardingRequest,
    response: Response,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """
    Complete user onboarding by setting daily calorie goal.

    This endpoint handles three scenarios:
    1. No profile exists → creates new profile with onboarding completed
    2. Profile exists without onboarding_completed_at → updates and completes it
    3. Profile exists with onboarding_completed_at → returns 409 Conflict

    Args:
        request: ProfileOnboardingRequest with daily_calorie_goal
        response: FastAPI Response object to set headers
        user_id: Authenticated user's UUID (from JWT token)
        profile_service: Injected ProfileService instance

    Returns:
        ProfileResponse with the created/updated profile data

    Raises:
        HTTPException 400: Invalid input data
        HTTPException 401: Authentication failed
        HTTPException 409: Onboarding already completed
        HTTPException 500: Internal server error
    """
    logger.info(f"Starting onboarding for user {user_id}")

    # Create command with current timestamp
    command = CompleteOnboardingCommand(
        user_id=user_id,
        daily_calorie_goal=request.daily_calorie_goal,
        completed_at=datetime.now(UTC),
    )

    # Execute business logic
    profile = await profile_service.complete_onboarding(command)

    # Set Location header pointing to profile endpoint
    response.headers["Location"] = "/api/v1/profile"

    logger.info(f"Onboarding completed successfully for user {user_id}")
    return profile


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get user profile",
    description="Retrieve the authenticated user's profile information.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "Profile not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_profile(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """
    Get the authenticated user's profile.

    Args:
        user_id: Authenticated user's UUID (from JWT token)
        profile_service: Injected ProfileService instance

    Returns:
        ProfileResponse with the user's profile data

    Raises:
        HTTPException 401: Authentication failed
        HTTPException 404: Profile not found
        HTTPException 500: Internal server error
    """
    logger.info(f"Retrieving profile for user {user_id}")
    profile = await profile_service.get_profile(str(user_id))
    return profile


@router.patch(
    "",
    response_model=ProfileResponse,
    summary="Update user profile",
    description="Update the authenticated user's profile fields (e.g., daily calorie goal).",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Missing or invalid authentication token"},
        404: {"description": "Profile not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    """
    Update the authenticated user's profile.

    Allows partial updates to profile fields such as daily_calorie_goal
    and onboarding_completed_at.

    Args:
        request: UpdateProfileRequest with optional fields to update
        user_id: Authenticated user's UUID (from JWT token)
        profile_service: Injected ProfileService instance

    Returns:
        ProfileResponse with the updated profile data

    Raises:
        HTTPException 400: Invalid input data
        HTTPException 401: Authentication failed
        HTTPException 404: Profile not found
        HTTPException 500: Internal server error
    """
    logger.info(f"Updating profile for user {user_id}")

    # Create command object
    command = UpdateProfileCommand(
        user_id=user_id,
        daily_calorie_goal=request.daily_calorie_goal,
        onboarding_completed_at=request.onboarding_completed_at,
    )

    # Execute business logic
    profile = await profile_service.update_profile(command)

    logger.info(f"Profile updated successfully for user {user_id}")
    return profile

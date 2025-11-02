"""
Service layer for profile business logic.
"""

import logging

from fastapi import HTTPException, status

from app.db.repositories.profile_repository import ProfileRepository
from app.schemas.profile import CompleteOnboardingCommand, ProfileResponse, UpdateProfileCommand

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Orchestrates profile-related business operations.
    """

    def __init__(self, repository: ProfileRepository):
        self.repository = repository

    async def complete_onboarding(self, command: CompleteOnboardingCommand) -> ProfileResponse:
        """
        Complete user onboarding by creating or updating their profile.

        This operation is idempotent with the following behavior:
        - If no profile exists: creates a new profile with onboarding_completed_at set
        - If profile exists without onboarding_completed_at: updates it
        - If profile exists with onboarding_completed_at: raises 409 Conflict

        Args:
            command: CompleteOnboardingCommand with user_id, daily_calorie_goal, and completed_at

        Returns:
            ProfileResponse with the created or updated profile

        Raises:
            HTTPException 409: If onboarding was already completed
            HTTPException 500: For unexpected database errors
        """
        try:
            # Check if profile already exists
            existing_profile = self.repository.get_profile_for_update(command.user_id)

            # Scenario 3: Onboarding already completed
            if existing_profile and existing_profile.onboarding_completed_at is not None:
                logger.warning(f"Onboarding already completed for user {command.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Onboarding has already been completed",
                )

            # Scenario 1 & 2: Create new profile or update existing incomplete profile
            profile = self.repository.upsert_profile(
                user_id=command.user_id,
                daily_calorie_goal=command.daily_calorie_goal,
                onboarding_completed_at=command.completed_at,
            )

            logger.info(f"Onboarding completed for user {command.user_id}")
            return profile

        except HTTPException:
            # Re-raise HTTP exceptions (like 409 Conflict)
            raise
        except Exception as e:
            # Log unexpected errors without exposing internals
            logger.error(
                f"Unexpected error completing onboarding for user {command.user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing your request",
            ) from e

    async def get_profile(self, user_id: str) -> ProfileResponse:
        """
        Retrieve a user's profile.

        Args:
            user_id: The user's UUID as a string

        Returns:
            ProfileResponse with the user's profile data

        Raises:
            HTTPException 404: If profile not found
            HTTPException 500: For unexpected database errors
        """
        try:
            from uuid import UUID

            profile = self.repository.get_profile(UUID(user_id))

            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )

            return profile

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving profile for user {user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing your request",
            ) from e

    async def update_profile(self, command: UpdateProfileCommand) -> ProfileResponse:
        """
        Update user profile fields.

        Allows partial updates to daily_calorie_goal and onboarding_completed_at.

        Args:
            command: UpdateProfileCommand with user_id and optional fields to update

        Returns:
            ProfileResponse with the updated profile data

        Raises:
            HTTPException 404: If profile not found
            HTTPException 400: If update validation fails
            HTTPException 500: For unexpected database errors
        """
        try:
            # Check if profile exists
            existing_profile = self.repository.get_profile(command.user_id)

            if existing_profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )

            # Update profile with provided fields
            profile = self.repository.update_profile(
                user_id=command.user_id,
                daily_calorie_goal=command.daily_calorie_goal,
                onboarding_completed_at=command.onboarding_completed_at,
            )

            logger.info(f"Profile updated for user {command.user_id}")
            return profile

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating profile for user {command.user_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing your request",
            ) from e

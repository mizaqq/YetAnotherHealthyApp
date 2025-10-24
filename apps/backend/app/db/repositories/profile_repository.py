"""
Repository for profile data access operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from supabase import Client

from app.schemas.profile import ProfileResponse


class ProfileRepository:
    """
    Handles all database operations for user profiles.
    """

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def get_profile(self, user_id: UUID) -> ProfileResponse | None:
        """
        Retrieve a user profile by user_id.

        Args:
            user_id: The UUID of the user

        Returns:
            ProfileResponse if found, None otherwise

        Raises:
            Exception: For database errors
        """
        response = (
            self.client.table("profiles")
            .select("*")
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )

        if not response or response.data is None:
            return None

        return ProfileResponse(**response.data)

    def upsert_profile(
        self,
        user_id: UUID,
        daily_calorie_goal: Decimal,
        onboarding_completed_at: datetime,
        timezone: str = "UTC",
    ) -> ProfileResponse:
        """
        Insert or update a profile record.

        For new profiles: creates with all provided fields.
        For existing profiles: updates daily_calorie_goal and onboarding_completed_at.

        Args:
            user_id: The UUID of the user
            daily_calorie_goal: Daily calorie goal in kcal
            onboarding_completed_at: Timestamp when onboarding was completed
            timezone: User timezone (default: UTC)

        Returns:
            The created or updated ProfileResponse

        Raises:
            Exception: For database errors
        """
        # Prepare data for upsert
        profile_data: dict[str, Any] = {
            "user_id": str(user_id),
            "daily_calorie_goal": float(daily_calorie_goal),
            "timezone": timezone,
            "onboarding_completed_at": onboarding_completed_at.isoformat(),
        }

        # Upsert profile (on conflict update)
        response = (
            self.client.table("profiles")
            .upsert(
                profile_data,
                on_conflict="user_id",
            )
            .execute()
        )

        if not response or not response.data or len(response.data) == 0:
            raise Exception("Failed to upsert profile - no data returned")

        return ProfileResponse(**response.data[0])

    def get_profile_for_update(self, user_id: UUID) -> ProfileResponse | None:
        """
        Retrieve a profile for update operations.

        This method can be extended with SELECT FOR UPDATE logic
        if pessimistic locking is needed in the future.

        Args:
            user_id: The UUID of the user

        Returns:
            ProfileResponse if found, None otherwise
        """
        # For now, this is the same as get_profile
        # Can be extended with locking logic if needed
        return self.get_profile(user_id)

    def update_profile(
        self,
        user_id: UUID,
        daily_calorie_goal: Decimal | None = None,
        onboarding_completed_at: datetime | None = None,
    ) -> ProfileResponse:
        """
        Update specific fields of an existing profile.

        Args:
            user_id: The UUID of the user
            daily_calorie_goal: Optional new daily calorie goal
            onboarding_completed_at: Optional onboarding completion timestamp

        Returns:
            The updated ProfileResponse

        Raises:
            Exception: For database errors
        """
        # Build update data with only provided fields
        update_data: dict[str, Any] = {}

        if daily_calorie_goal is not None:
            update_data["daily_calorie_goal"] = float(daily_calorie_goal)

        if onboarding_completed_at is not None:
            update_data["onboarding_completed_at"] = onboarding_completed_at.isoformat()

        # If no fields to update, just return the current profile
        if not update_data:
            profile = self.get_profile(user_id)
            if profile is None:
                raise Exception(f"Profile not found for user {user_id}")
            return profile

        # Update profile
        response = (
            self.client.table("profiles").update(update_data).eq("user_id", str(user_id)).execute()
        )

        if not response or not response.data or len(response.data) == 0:
            raise Exception(f"Failed to update profile for user {user_id}")

        return ProfileResponse(**response.data[0])

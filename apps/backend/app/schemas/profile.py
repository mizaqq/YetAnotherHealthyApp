"""
Pydantic schemas for profile-related API operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProfileOnboardingRequest(BaseModel):
    """
    Request body for completing user onboarding.

    Validates daily calorie goal within acceptable range.
    """

    daily_calorie_goal: Annotated[
        Decimal,
        Field(
            ge=0,
            le=10000,
            max_digits=10,
            decimal_places=2,
            description="Daily calorie goal in kcal",
        ),
    ]

    @field_validator("daily_calorie_goal")
    @classmethod
    def normalize_decimal_places(cls, v: Decimal) -> Decimal:
        """Ensure exactly 2 decimal places."""
        return v.quantize(Decimal("0.01"))


class ProfileResponse(BaseModel):
    """
    Standard profile representation returned by API endpoints.
    """

    user_id: UUID
    daily_calorie_goal: Decimal
    timezone: str
    onboarding_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompleteOnboardingCommand(BaseModel):
    """
    Internal command object for completing onboarding.

    Used to pass validated data from endpoint to service layer.
    """

    user_id: UUID
    daily_calorie_goal: Decimal
    completed_at: datetime

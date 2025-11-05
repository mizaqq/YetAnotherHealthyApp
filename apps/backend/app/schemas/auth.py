"""
Pydantic schemas for authentication-related API operations.
"""

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterCommand(BaseModel):
    """
    Request body for user registration.

    Validates email format and password complexity requirements.
    Password must be at least 8 characters and contain both letters and digits.
    """

    email: EmailStr
    password: Annotated[
        str,
        Field(
            min_length=8,
            description="Password (minimum 8 characters, must contain letters and digits)",
        ),
    ]

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password contains at least one letter and one digit.

        Args:
            v: Password string to validate

        Returns:
            Original password if valid

        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ResetPasswordRequestCommand(BaseModel):
    """
    Request body for initiating password reset flow.

    Only requires email address. Response is always neutral to prevent
    email enumeration attacks.
    """

    email: EmailStr


class ResetPasswordConfirmCommand(BaseModel):
    """
    Request body for confirming password reset with new password.

    Requires valid recovery token in Authorization header.
    Password must meet same complexity requirements as registration.
    """

    password: Annotated[
        str,
        Field(
            min_length=8,
            description="New password (minimum 8 characters, must contain letters and digits)",
        ),
    ]

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password contains at least one letter and one digit.

        Args:
            v: Password string to validate

        Returns:
            Original password if valid

        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class MessageResponse(BaseModel):
    """
    Generic message response for authentication operations.

    Used for operations that don't return structured data,
    such as registration confirmation and password reset requests.
    """

    message: str

"""
Authentication-related API endpoints.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from supabase import Client

from app.core.dependencies import get_current_user_id, get_supabase_dependency
from app.schemas.auth import (
    MessageResponse,
    RegisterCommand,
    ResetPasswordConfirmCommand,
    ResetPasswordRequestCommand,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account with email and password. "
        "An email confirmation link will be sent to the provided email address. "
        "Users must confirm their email before they can log in."
    ),
    responses={
        201: {
            "description": "User created successfully, confirmation email sent",
            "content": {
                "application/json": {
                    "example": {
                        "message": (
                            "Registration successful. "
                            "Please check your email to confirm your account."
                        )
                    }
                }
            },
        },
        400: {"description": "Invalid email or password format"},
        409: {"description": "Email address already in use"},
        500: {"description": "Internal server error"},
    },
)
async def register(
    request: RegisterCommand,
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> MessageResponse:
    """
    Register a new user account.

    Creates a new user in Supabase Auth with email confirmation required.
    The user will receive an email with a confirmation link pointing to
    the frontend email confirmation page.

    Args:
        request: RegisterCommand with email and password
        client: Injected Supabase client

    Returns:
        MessageResponse indicating successful registration

    Raises:
        HTTPException 400: Invalid email or password format
        HTTPException 409: Email already in use
        HTTPException 500: Internal server error
    """
    try:
        # Create user with Supabase Admin API
        # email_confirm=False means email confirmation is required
        response = client.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
                "options": {"email_redirect_to": "http://localhost:5173/email-confirmation"},
            }
        )

        if not response or not response.user:
            logger.error("Failed to create user: no user returned from Supabase")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account",
            )

        logger.info(f"User registered successfully: {response.user.id}")
        return MessageResponse(
            message="Registration successful. Please check your email to confirm your account."
        )

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e).lower()

        # Check for duplicate email error
        if "user already registered" in error_message or "already exists" in error_message:
            logger.warning(f"Registration attempt with existing email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address already in use",
            ) from e

        # Log and return generic error for other cases
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        ) from e


@router.post(
    "/password/reset-request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description=(
        "Initiate password reset flow by sending a reset link to the provided email. "
        "For security reasons, this endpoint always returns success regardless of whether "
        "the email exists in the system."
    ),
    responses={
        202: {
            "description": "Request processed (always returned for security)",
            "content": {
                "application/json": {
                    "example": {
                        "message": (
                            "If the account exists, "
                            "a password reset link has been sent to your email."
                        )
                    }
                }
            },
        },
        400: {"description": "Invalid email format"},
        500: {"description": "Internal server error (logged, but returns 202)"},
    },
)
async def request_password_reset(
    request: ResetPasswordRequestCommand,
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> MessageResponse:
    """
    Request a password reset link.

    Sends a password reset email with a recovery link pointing to the
    frontend password reset confirmation page. Always returns success
    to prevent email enumeration attacks.

    Args:
        request: ResetPasswordRequestCommand with email
        client: Injected Supabase client

    Returns:
        MessageResponse with neutral success message

    Note:
        This endpoint always returns 202 Accepted, even if the email
        doesn't exist or an error occurs, to prevent attackers from
        determining which emails are registered.
    """
    try:
        # Send password reset email
        client.auth.reset_password_for_email(
            request.email,
            options={"redirect_to": "http://localhost:5173/reset-password/confirm"},
        )

        logger.info(f"Password reset requested for email: {request.email}")

    except Exception as e:
        # Log error but don't expose it to prevent email enumeration
        logger.warning(f"Error during password reset request (email: {request.email}): {e}")

    # Always return success message for security
    return MessageResponse(
        message="If the account exists, a password reset link has been sent to your email."
    )


@router.post(
    "/password/reset-confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm password reset",
    description=(
        "Complete password reset by providing a new password. "
        "Requires a valid recovery token in the Authorization header "
        "(obtained from the password reset email link)."
    ),
    responses={
        204: {"description": "Password reset successful"},
        400: {"description": "Invalid password format"},
        401: {"description": "Invalid or expired recovery token"},
        500: {"description": "Internal server error"},
    },
)
async def confirm_password_reset(
    request: ResetPasswordConfirmCommand,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> Response:
    """
    Confirm password reset with new password.

    Validates the recovery token from the Authorization header and
    updates the user's password if valid.

    Args:
        request: ResetPasswordConfirmCommand with new password
        user_id: User ID extracted from recovery token (validated by dependency)
        client: Injected Supabase client

    Returns:
        204 No Content response on success

    Raises:
        HTTPException 400: Invalid password format
        HTTPException 401: Invalid or expired recovery token
        HTTPException 500: Internal server error
    """
    try:
        # Update user password using admin API
        response = client.auth.admin.update_user_by_id(
            str(user_id),
            {"password": request.password},
        )

        if not response or not response.user:
            logger.error(f"Failed to update password for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password",
            )

        logger.info(f"Password reset successful for user {user_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during password reset confirmation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        ) from e

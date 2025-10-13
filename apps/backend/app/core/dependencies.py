"""
FastAPI dependencies for authentication, authorization, and service injection.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from supabase import Client

from app.core.supabase import get_supabase_client
from app.db.repositories.meal_categories_repository import MealCategoriesRepository
from app.db.repositories.product_repository import ProductRepository
from app.db.repositories.profile_repository import ProfileRepository
from app.db.repositories.unit_repository import UnitRepository
from app.services.meal_categories_service import MealCategoriesService
from app.services.product_service import ProductService
from app.services.profile_service import ProfileService
from app.services.units_service import UnitsService

logger = logging.getLogger(__name__)


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    """
    Extract and validate user_id from Supabase JWT token.

    This dependency validates the Authorization header and extracts
    the user ID (sub claim) from the Supabase JWT token.

    Args:
        authorization: Authorization header containing "Bearer <token>"

    Returns:
        UUID of the authenticated user

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        # Get Supabase client and verify token
        client = get_supabase_client()
        user_response = client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = user_response.user.id
        return UUID(user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_supabase_dependency() -> Client:
    """
    Dependency that provides a Supabase client instance.

    Returns:
        Configured Supabase Client
    """
    return get_supabase_client()


def get_profile_repository(
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> ProfileRepository:
    """
    Dependency that provides a ProfileRepository instance.

    Args:
        client: Injected Supabase client

    Returns:
        ProfileRepository instance
    """
    return ProfileRepository(client)


def get_meal_categories_repository(
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> MealCategoriesRepository:
    """Dependency that provides a MealCategoriesRepository instance."""

    return MealCategoriesRepository(client)


def get_profile_service(
    repository: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> ProfileService:
    """
    Dependency that provides a ProfileService instance.

    Args:
        repository: Injected ProfileRepository

    Returns:
        ProfileService instance
    """
    return ProfileService(repository)


def get_meal_categories_service(
    repository: Annotated[
        MealCategoriesRepository,
        Depends(get_meal_categories_repository),
    ],
) -> MealCategoriesService:
    """Dependency that provides a MealCategoriesService instance."""

    return MealCategoriesService(repository)


def get_unit_repository(
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> UnitRepository:
    """Dependency that provides a UnitRepository instance."""

    return UnitRepository(client)


def get_units_service(
    repository: Annotated[UnitRepository, Depends(get_unit_repository)],
) -> UnitsService:
    """Dependency that provides a UnitsService instance."""

    return UnitsService(repository)


def get_product_repository(
    client: Annotated[Client, Depends(get_supabase_dependency)],
) -> ProductRepository:
    """Dependency that provides a ProductRepository instance."""

    return ProductRepository(client)


def get_product_service(
    repository: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductService:
    """Dependency that provides a ProductService instance."""

    return ProductService(repository)

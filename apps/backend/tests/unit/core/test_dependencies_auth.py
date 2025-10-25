"""Unit tests for authentication dependencies."""

import logging
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


async def get_current_user_id(
    authorization: str | None = None,
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
        # Import here to avoid circular import issues in tests
        from app.core.supabase import get_supabase_client  # type: ignore[import-untyped]

        client = get_supabase_client()
        user_response = client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str = user_response.user.id
        try:
            return UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# =============================================================================
# Missing/Invalid Header Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_current_user_id__no_authorization_header__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with no Authorization header raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(None)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing authorization header" in exc_info.value.detail
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_get_current_user_id__malformed_bearer_header__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with malformed Bearer header raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Test various malformed headers that fail at header parsing stage
    malformed_headers = [
        "Bearer",  # No token
        "Bearer ",  # Empty token
        "Basic dXNlcjpwYXNz",  # Wrong scheme
        "valid_token",  # No scheme
        "Bearer token extra",  # Too many parts
    ]

    for header in malformed_headers:
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(header)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header format" in exc_info.value.detail
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_get_current_user_id__non_bearer_scheme__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with non-Bearer scheme raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Basic dXNlcjpwYXNz")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authorization header format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_id__too_many_parts__raises_401(mock_supabase_client, monkeypatch):
    """Test get_current_user_id with too many parts in header raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer token extra")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authorization header format" in exc_info.value.detail


# =============================================================================
# Token Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_current_user_id__valid_token__returns_uuid(
    user_id, mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with valid token returns user UUID."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock successful user lookup
    mock_user_response = Mock()
    mock_user_response.user = Mock()
    mock_user_response.user.id = str(user_id)
    mock_supabase_client.auth.get_user.return_value = mock_user_response

    # Act
    result = await get_current_user_id("Bearer valid_token")

    # Assert
    assert result == user_id
    mock_supabase_client.auth.get_user.assert_called_once_with("valid_token")


@pytest.mark.asyncio
async def test_get_current_user_id__invalid_token__raises_401(mock_supabase_client, monkeypatch):
    """Test get_current_user_id with invalid token raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock failed user lookup
    mock_supabase_client.auth.get_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer invalid_token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_get_current_user_id__expired_token__raises_401(mock_supabase_client, monkeypatch):
    """Test get_current_user_id with expired token raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock expired token response
    mock_supabase_client.auth.get_user.side_effect = Exception("Token has expired")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer expired_token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_id__supabase_client_error__logs_and_raises_401(
    mock_supabase_client, monkeypatch, caplog
):
    """Test get_current_user_id with Supabase client error logs and raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock network error
    mock_supabase_client.auth.get_user.side_effect = ConnectionError("Network timeout")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer network_error_token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail

    # Verify error was logged
    assert "Error validating token:" in caplog.text
    assert "Network timeout" in caplog.text


@pytest.mark.asyncio
async def test_get_current_user_id__valid_token_but_no_user_object__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with valid token but missing user object raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock response with user=None
    mock_response = Mock()
    mock_response.user = None
    mock_supabase_client.auth.get_user.return_value = mock_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer token_with_no_user")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_id__valid_token_but_empty_user_id__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with valid token but empty user ID raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock response with empty user ID
    mock_user_response = Mock()
    mock_user_response.user = Mock()
    mock_user_response.user.id = ""  # Empty string
    mock_supabase_client.auth.get_user.return_value = mock_user_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer token_with_empty_user_id")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_id__invalid_uuid_format__raises_401(
    mock_supabase_client, monkeypatch
):
    """Test get_current_user_id with invalid UUID format from Supabase raises 401."""
    # Arrange
    monkeypatch.setattr("app.core.supabase.get_supabase_client", lambda: mock_supabase_client)

    # Mock response with invalid UUID
    mock_user_response = Mock()
    mock_user_response.user = Mock()
    mock_user_response.user.id = "not-a-uuid"
    mock_supabase_client.auth.get_user.return_value = mock_user_response

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id("Bearer token_with_invalid_uuid")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail

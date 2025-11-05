"""Unit tests for pagination PageInfo and AnalysisRunCursor."""

import base64
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.api.v1.pagination import AnalysisRunCursor, PageMeta, PaginatedResponse

# =============================================================================
# PageMeta Tests
# =============================================================================


def test_page_meta__valid_construction():
    """Test PageMeta constructs correctly with valid values."""
    # Act
    page_meta = PageMeta(size=25, after="cursor_abc123")

    # Assert
    assert page_meta.size == 25
    assert page_meta.after == "cursor_abc123"


def test_page_meta__zero_size():
    """Test PageMeta accepts zero size."""
    # Act
    page_meta = PageMeta(size=0)

    # Assert
    assert page_meta.size == 0
    assert page_meta.after is None


def test_page_meta__negative_size__raises_validation_error():
    """Test PageMeta rejects negative size."""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        PageMeta(size=-1)

    assert "ge=0" in str(exc_info.value) or "size" in str(exc_info.value)


def test_page_meta__no_after_cursor():
    """Test PageMeta with no after cursor."""
    # Act
    page_meta = PageMeta(size=10)

    # Assert
    assert page_meta.size == 10
    assert page_meta.after is None


# =============================================================================
# AnalysisRunCursor Tests
# =============================================================================


def test_analysis_run_cursor__valid_construction(now: Any) -> None:
    """Test AnalysisRunCursor constructs correctly."""
    # Arrange
    run_id = uuid4()
    created_at = now

    # Act
    cursor = AnalysisRunCursor(created_at=created_at, id=run_id)

    # Assert
    assert cursor.created_at == created_at
    assert cursor.id == run_id


def test_analysis_run_cursor__encode_returns_base64_string(now: Any) -> None:
    """Test AnalysisRunCursor.encode returns valid base64 string."""
    # Arrange
    cursor = AnalysisRunCursor(created_at=now, id=uuid4())

    # Act
    encoded = cursor.encode()

    # Assert
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    # Verify it's valid base64
    decoded_bytes = base64.urlsafe_b64decode(encoded.encode())
    assert isinstance(decoded_bytes, bytes)


def test_analysis_run_cursor__encode_decode_symmetry(now: Any) -> None:
    """Test AnalysisRunCursor encode/decode maintains data integrity."""
    # Arrange
    original_cursor = AnalysisRunCursor(created_at=now, id=uuid4())

    # Act
    encoded = original_cursor.encode()
    decoded_cursor = AnalysisRunCursor.decode(encoded)

    # Assert
    assert decoded_cursor.created_at == original_cursor.created_at
    assert decoded_cursor.id == original_cursor.id


def test_analysis_run_cursor__decode_valid_cursor(now: Any) -> None:
    """Test AnalysisRunCursor.decode with valid cursor string."""
    # Arrange
    original_cursor = AnalysisRunCursor(created_at=now, id=uuid4())
    encoded = original_cursor.encode()

    # Act
    decoded_cursor = AnalysisRunCursor.decode(encoded)

    # Assert
    assert isinstance(decoded_cursor, AnalysisRunCursor)
    assert decoded_cursor.created_at == original_cursor.created_at
    assert decoded_cursor.id == original_cursor.id


def test_analysis_run_cursor__decode_invalid_base64__raises_value_error():
    """Test AnalysisRunCursor.decode with invalid base64 raises ValueError."""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisRunCursor.decode("invalid_base64!")

    assert "Invalid cursor format" in str(exc_info.value)


def test_analysis_run_cursor__decode_malformed_json__raises_value_error():
    """Test AnalysisRunCursor.decode with malformed JSON raises ValueError."""
    # Arrange
    malformed_json = json.dumps({"invalid": "data"})
    invalid_cursor = base64.urlsafe_b64encode(malformed_json.encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisRunCursor.decode(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_analysis_run_cursor__decode_missing_fields__raises_value_error():
    """Test AnalysisRunCursor.decode with missing required fields raises ValueError."""
    # Arrange
    incomplete_data = {"created_at": "2024-01-01T00:00:00"}
    # Missing id
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(incomplete_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisRunCursor.decode(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_analysis_run_cursor__decode_invalid_datetime__raises_value_error():
    """Test AnalysisRunCursor.decode with invalid datetime raises ValueError."""
    # Arrange
    invalid_datetime_data = {"created_at": "not-a-datetime", "id": str(uuid4())}
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(invalid_datetime_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisRunCursor.decode(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_analysis_run_cursor__decode_invalid_uuid__raises_value_error():
    """Test AnalysisRunCursor.decode with invalid UUID raises ValueError."""
    # Arrange
    invalid_uuid_data = {"created_at": "2024-01-01T00:00:00+00:00", "id": "not-a-uuid"}
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(invalid_uuid_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        AnalysisRunCursor.decode(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_analysis_run_cursor__decode_with_timezone__preserves_datetime(now: Any) -> None:
    """Test AnalysisRunCursor decode preserves timezone information."""
    # Arrange
    utc_cursor = AnalysisRunCursor(created_at=now, id=uuid4())
    encoded = utc_cursor.encode()

    # Act
    decoded = AnalysisRunCursor.decode(encoded)

    # Assert
    assert decoded.created_at == now
    assert decoded.created_at.tzinfo == UTC


# =============================================================================
# PaginatedResponse Tests
# =============================================================================


def test_paginated_response__generic_type():
    """Test PaginatedResponse works with generic types."""
    # Arrange
    data = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
    page_meta = PageMeta(size=2, after="next_cursor")

    # Act
    response = PaginatedResponse(data=data, page=page_meta)

    # Assert
    assert response.data == data
    assert response.page.size == 2
    assert response.page.after == "next_cursor"


def test_paginated_response__empty_data():
    """Test PaginatedResponse with empty data."""
    # Arrange
    data = []
    page_meta = PageMeta(size=0)

    # Act
    response = PaginatedResponse(data=data, page=page_meta)

    # Assert
    assert response.data == []
    assert response.page.size == 0
    assert response.page.after is None


def test_paginated_response__with_cursor():
    """Test PaginatedResponse with cursor for pagination."""
    # Arrange
    data = ["item1", "item2"]
    page_meta = PageMeta(
        size=2,
        after="eyJjcmVhdGVkX2F0IjoiMjAyNS0xMC0xMlQwNzoyOTozMFoiLCJpZCI6IjEyM2U0NTY3LWU4OWItMTJkMy1hNDU2LTQyNjYxNDE3NDAwMCJ9",
    )

    # Act
    response = PaginatedResponse(data=data, page=page_meta)

    # Assert
    assert len(response.data) == 2
    assert response.page.after is not None


# =============================================================================
# Integration Tests - Cursor Round Trip
# =============================================================================


def test_analysis_run_cursor__realistic_pagination_scenario(now: Any) -> None:
    """Test AnalysisRunCursor in a realistic pagination scenario."""
    # Simulate pagination through analysis runs

    # First page cursor (oldest run first)
    first_page_last_run = AnalysisRunCursor(created_at=now.replace(hour=10), id=uuid4())

    # Second page cursor (continuing from first page)
    second_page_last_run = AnalysisRunCursor(created_at=now.replace(hour=12), id=uuid4())

    # Act & Assert - Encode/decode both cursors
    first_encoded = first_page_last_run.encode()
    second_encoded = second_page_last_run.encode()

    first_decoded = AnalysisRunCursor.decode(first_encoded)
    second_decoded = AnalysisRunCursor.decode(second_encoded)

    # Verify data integrity
    assert first_decoded.created_at == first_page_last_run.created_at
    assert first_decoded.id == first_page_last_run.id

    assert second_decoded.created_at == second_page_last_run.created_at
    assert second_decoded.id == second_page_last_run.id

    # Verify chronological order (second cursor is newer)
    assert first_decoded.created_at < second_decoded.created_at


def test_cursor_encoding__url_safe_characters():
    """Test cursor encoding uses URL-safe base64 characters."""
    # Arrange
    cursor = AnalysisRunCursor(created_at=datetime(2024, 1, 1, tzinfo=UTC), id=uuid4())

    # Act
    encoded = cursor.encode()

    # Assert
    # URL-safe base64 may contain: A-Z, a-z, 0-9, -, _, =
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
    assert all(c in allowed_chars for c in encoded)

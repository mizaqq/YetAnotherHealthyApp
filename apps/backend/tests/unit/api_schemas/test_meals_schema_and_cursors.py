"""Unit tests for meals API schemas and cursor utilities."""

import base64
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.api.v1.schemas.meals import (
    MealCreatePayload,
    MealListQuery,
    MealSource,
    PageInfo,
    MealCursorData,
    MealListItem,
    MealListResponse,
    encode_meal_cursor,
    decode_meal_cursor,
)


# =============================================================================
# MealListQuery Validation Tests
# =============================================================================


def test_meal_list_query__default_values():
    """Test MealListQuery with no arguments uses correct defaults."""
    # Act
    query = MealListQuery()

    # Assert
    assert query.from_date is None
    assert query.to_date is None
    assert query.category is None
    assert query.source is None
    assert query.include_deleted is False
    assert query.page_size == 20
    assert query.page_after is None
    assert query.sort == "-eaten_at"


def test_meal_list_query__custom_page_size():
    """Test MealListQuery accepts custom page size within limits."""
    # Act & Assert - Valid sizes
    for size in [1, 50, 100]:
        query = MealListQuery(**{"page[size]": size})
        assert query.page_size == size


def test_meal_list_query__page_size_too_large__raises_validation_error():
    """Test MealListQuery rejects page size > 100."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealListQuery(**{"page[size]": 101})

    assert "page[size]" in str(exc_info.value)


def test_meal_list_query__page_size_too_small__raises_validation_error():
    """Test MealListQuery rejects page size < 1."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealListQuery(**{"page[size]": 0})

    assert "page[size]" in str(exc_info.value)


def test_meal_list_query__valid_sort_fields():
    """Test MealListQuery accepts valid sort field combinations."""
    # Act & Assert
    valid_sorts = ["eaten_at", "-eaten_at"]
    for sort in valid_sorts:
        query = MealListQuery(sort=sort)
        assert query.sort == sort


def test_meal_list_query__invalid_sort_field__raises_validation_error():
    """Test MealListQuery rejects invalid sort fields."""
    # Act & Assert
    invalid_sorts = ["invalid", "created_at", "-invalid", ""]
    for sort in invalid_sorts:
        with pytest.raises(ValidationError) as exc_info:
            MealListQuery(sort=sort)

        assert "sort" in str(exc_info.value)


def test_meal_list_query__date_filters():
    """Test MealListQuery accepts valid date filters."""
    # Arrange
    from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    to_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

    # Act
    query = MealListQuery(**{"from": from_date, "to": to_date})

    # Assert
    assert query.from_date == from_date
    assert query.to_date == to_date


def test_meal_list_query__to_date_before_from_date__raises_validation_error():
    """Test MealListQuery rejects 'to' date before 'from' date."""
    # Arrange
    from_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
    to_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealListQuery(**{"from": from_date, "to": to_date})

    assert "to" in str(exc_info.value)


def test_meal_list_query__category_filter():
    """Test MealListQuery accepts category filter."""
    # Act
    query = MealListQuery(category="śniadanie")

    # Assert
    assert query.category == "śniadanie"


def test_meal_list_query__source_filter():
    """Test MealListQuery accepts source filter."""
    # Act & Assert
    for source in [MealSource.AI, MealSource.MANUAL]:
        query = MealListQuery(source=source)
        assert query.source == source


def test_meal_list_query__include_deleted_filter():
    """Test MealListQuery accepts include_deleted filter."""
    # Act & Assert
    query = MealListQuery(include_deleted=True)
    assert query.include_deleted is True


# =============================================================================
# MealSource Enum Tests
# =============================================================================


def test_meal_source__valid_serialization():
    """Test MealSource enum serializes correctly."""
    # Act & Assert
    assert MealSource.AI.value == "ai"
    assert MealSource.EDITED.value == "edited"
    assert MealSource.MANUAL.value == "manual"


def test_meal_source__valid_deserialization():
    """Test MealSource enum deserializes correctly."""
    # Act & Assert
    assert MealSource("ai") == MealSource.AI
    assert MealSource("edited") == MealSource.EDITED
    assert MealSource("manual") == MealSource.MANUAL


def test_meal_source__invalid_value__raises_value_error():
    """Test MealSource rejects invalid values."""
    # Act & Assert
    with pytest.raises(ValueError):
        MealSource("invalid")


# =============================================================================
# Cursor Encoding/Decoding Tests
# =============================================================================


def test_encode_meal_cursor__returns_base64_string(now):
    """Test encode_meal_cursor returns valid base64 string."""
    # Arrange
    meal_id = uuid4()
    eaten_at = now

    # Act
    cursor = encode_meal_cursor(last_eaten_at=eaten_at, last_id=meal_id)

    # Assert
    assert isinstance(cursor, str)
    assert len(cursor) > 0

    # Verify it's valid base64
    decoded = base64.urlsafe_b64decode(cursor.encode())
    assert isinstance(decoded, bytes)


def test_decode_meal_cursor__symmetry_with_encode(now):
    """Test decode_meal_cursor reverses encode_meal_cursor correctly."""
    # Arrange
    original_id = uuid4()
    original_eaten_at = now

    # Act
    cursor = encode_meal_cursor(last_eaten_at=original_eaten_at, last_id=original_id)
    decoded = decode_meal_cursor(cursor)

    # Assert
    assert decoded.last_eaten_at == original_eaten_at
    assert decoded.last_id == original_id


def test_decode_meal_cursor__with_datetime_precision(now):
    """Test cursor encoding/decoding preserves datetime precision."""
    # Arrange
    meal_id = uuid4()
    eaten_at = now.replace(microsecond=123456)  # Include microseconds

    # Act
    cursor = encode_meal_cursor(last_eaten_at=eaten_at, last_id=meal_id)
    decoded = decode_meal_cursor(cursor)

    # Assert
    assert decoded.last_eaten_at == eaten_at
    assert decoded.last_id == meal_id


def test_decode_meal_cursor__invalid_base64__raises_value_error():
    """Test decode_meal_cursor with invalid base64 raises ValueError."""
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        decode_meal_cursor("invalid_base64!")

    assert "Invalid cursor format" in str(exc_info.value)


def test_decode_meal_cursor__malformed_json__raises_value_error():
    """Test decode_meal_cursor with malformed JSON raises ValueError."""
    # Arrange
    malformed_json = json.dumps({"invalid": "data"})
    invalid_cursor = base64.urlsafe_b64encode(malformed_json.encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        decode_meal_cursor(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_decode_meal_cursor__missing_fields__raises_value_error():
    """Test decode_meal_cursor with missing required fields raises ValueError."""
    # Arrange
    incomplete_data = {"last_eaten_at": "2024-01-01T00:00:00"}
    # Missing last_id
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(incomplete_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        decode_meal_cursor(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_decode_meal_cursor__invalid_uuid__raises_value_error():
    """Test decode_meal_cursor with invalid UUID raises ValueError."""
    # Arrange
    invalid_uuid_data = {"last_eaten_at": "2024-01-01T00:00:00", "last_id": "not-a-uuid"}
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(invalid_uuid_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        decode_meal_cursor(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


def test_decode_meal_cursor__invalid_datetime__raises_value_error():
    """Test decode_meal_cursor with invalid datetime raises ValueError."""
    # Arrange
    invalid_datetime_data = {"last_eaten_at": "not-a-datetime", "last_id": str(uuid4())}
    invalid_cursor = base64.urlsafe_b64encode(json.dumps(invalid_datetime_data).encode()).decode()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        decode_meal_cursor(invalid_cursor)

    assert "Invalid cursor format" in str(exc_info.value)


# =============================================================================
# MealCreatePayload Validation Tests
# =============================================================================


def test_meal_create_payload__ai_source_requires_macros_and_analysis_run_id(now):
    """Test MealCreatePayload with AI source requires all macro fields and analysis_run_id."""
    # Arrange
    valid_payload = {
        "category": "śniadanie",
        "eaten_at": now,
        "source": MealSource.AI,
        "calories": Decimal("500.00"),
        "protein": Decimal("25.00"),
        "fat": Decimal("20.00"),
        "carbs": Decimal("50.00"),
        "analysis_run_id": uuid4(),
    }

    # Act & Assert
    payload = MealCreatePayload(**valid_payload)
    assert payload.source == MealSource.AI
    assert payload.analysis_run_id is not None


def test_meal_create_payload__ai_source_missing_protein__raises_validation_error(now):
    """Test MealCreatePayload with AI source missing protein raises validation error."""
    # Arrange
    invalid_payload = {
        "category": "śniadanie",
        "eaten_at": now,
        "source": MealSource.AI,
        "calories": Decimal("500.00"),
        "fat": Decimal("20.00"),
        "carbs": Decimal("50.00"),
        "analysis_run_id": uuid4(),
        # Missing protein
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealCreatePayload(**invalid_payload)

    assert "protein" in str(exc_info.value)


def test_meal_create_payload__manual_source_forbids_macros_and_analysis_run_id(now):
    """Test MealCreatePayload with MANUAL source forbids macro fields and analysis_run_id."""
    # Arrange
    invalid_payload = {
        "category": "śniadanie",
        "eaten_at": now,
        "source": MealSource.MANUAL,
        "calories": Decimal("500.00"),
        "protein": Decimal("25.00"),  # Forbidden for MANUAL
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealCreatePayload(**invalid_payload)

    assert "manual" in str(exc_info.value).lower()


def test_meal_create_payload__normalize_category(now):
    """Test MealCreatePayload normalizes category to lowercase."""
    # Arrange
    payload_data = {
        "category": "ŚNIADANIE",  # Uppercase with Polish characters
        "eaten_at": now,
        "source": MealSource.MANUAL,
        "calories": Decimal("500.00"),
    }

    # Act
    payload = MealCreatePayload(**payload_data)

    # Assert
    assert payload.category == "śniadanie"


def test_meal_create_payload__eaten_at_requires_timezone(now):
    """Test MealCreatePayload requires timezone-aware eaten_at."""
    # Arrange
    payload_data = {
        "category": "śniadanie",
        "eaten_at": now.replace(tzinfo=None),  # Naive datetime
        "source": MealSource.MANUAL,
        "calories": Decimal("500.00"),
    }

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        MealCreatePayload(**payload_data)

    assert "timezone-aware" in str(exc_info.value)


def test_meal_create_payload__calories_validation():
    """Test MealCreatePayload validates calories constraints."""
    # Arrange
    now_utc = datetime.now(timezone.utc)

    # Act & Assert - Valid calories
    payload = MealCreatePayload(
        category="śniadanie",
        eaten_at=now_utc,
        source=MealSource.MANUAL,
        calories=Decimal("0.01"),  # Minimum valid
    )
    assert payload.calories == Decimal("0.01")

    # Invalid: negative calories
    with pytest.raises(ValidationError):
        MealCreatePayload(
            category="śniadanie",
            eaten_at=now_utc,
            source=MealSource.MANUAL,
            calories=Decimal("-1.00"),
        )


# =============================================================================
# MealListItem and MealListResponse Tests
# =============================================================================


def test_meal_list_item__decimal_serialization(now):
    """Test MealListItem serializes Decimal fields to float."""
    # Arrange
    meal_data = MealListItem(
        id=uuid4(),
        category="śniadanie",
        eaten_at=now,
        source=MealSource.AI,
        calories=Decimal("450.50"),
        protein=Decimal("25.50"),
        fat=Decimal("18.00"),
        carbs=Decimal("42.00"),
        accepted_analysis_run_id=uuid4(),
    )

    # Act
    json_data = meal_data.model_dump()

    # Assert
    assert isinstance(json_data["calories"], float)
    assert json_data["calories"] == 450.5
    assert isinstance(json_data["protein"], float)
    assert json_data["protein"] == 25.5


def test_page_info__valid_construction():
    """Test PageInfo constructs correctly."""
    # Act
    page_info = PageInfo(size=10, after="cursor123")

    # Assert
    assert page_info.size == 10
    assert page_info.after == "cursor123"


def test_meal_list_response__valid_construction(now):
    """Test MealListResponse constructs correctly."""
    # Arrange
    meals = [
        MealListItem(
            id=uuid4(),
            category="śniadanie",
            eaten_at=now,
            source=MealSource.AI,
            calories=Decimal("450.00"),
            accepted_analysis_run_id=None,
        )
    ]
    page_info = PageInfo(size=1, after=None)

    # Act
    response = MealListResponse(data=meals, page=page_info)

    # Assert
    assert len(response.data) == 1
    assert response.page.size == 1
    assert response.page.after is None


def test_meal_cursor_data__valid_construction(now):
    """Test MealCursorData constructs correctly."""
    # Arrange
    meal_id = uuid4()

    # Act
    cursor_data = MealCursorData(last_eaten_at=now, last_id=meal_id)

    # Assert
    assert cursor_data.last_eaten_at == now
    assert cursor_data.last_id == meal_id

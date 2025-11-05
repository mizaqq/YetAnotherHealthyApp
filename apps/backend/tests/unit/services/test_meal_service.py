"""Unit tests for MealService."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.meals import (
    MealCreatePayload,
    MealListItem,
    MealListQuery,
    MealSource,
    MealUpdatePayload,
    encode_meal_cursor,
)
from app.services.meal_service import MealService

# =============================================================================
# List Meals Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_meals__no_filters__returns_default_sorted_meals(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test listing meals without filters returns meals sorted by eaten_at desc."""
    # Arrange
    meals = [
        {
            "id": uuid4(),
            "category": meal_category,
            "eaten_at": now.replace(hour=8),
            "source": "ai",
            "calories": Decimal("300.00"),
            "protein": Decimal("20.00"),
            "fat": Decimal("10.00"),
            "carbs": Decimal("30.00"),
            "accepted_analysis_run_id": None,
        },
        {
            "id": uuid4(),
            "category": meal_category,
            "eaten_at": now.replace(hour=12),
            "source": "manual",
            "calories": Decimal("500.00"),
            "protein": None,
            "fat": None,
            "carbs": None,
            "accepted_analysis_run_id": None,
        },
        {
            "id": uuid4(),
            "category": meal_category,
            "eaten_at": now.replace(hour=18),
            "source": "ai",
            "calories": Decimal("600.00"),
            "protein": Decimal("35.00"),
            "fat": Decimal("20.00"),
            "carbs": Decimal("50.00"),
            "accepted_analysis_run_id": uuid4(),
        },
    ]
    mock_meal_repository.list_meals.return_value = meals

    service = MealService(mock_meal_repository)
    query = MealListQuery()

    # Act
    response = await service.list_meals(user_id=user_id, query=query)

    # Assert
    assert len(response.data) == 3
    assert response.page.size == 3
    assert response.page.after is None
    mock_meal_repository.list_meals.assert_called_once()
    call_kwargs = mock_meal_repository.list_meals.call_args.kwargs
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["sort_desc"] is True


@pytest.mark.asyncio
async def test_list_meals__with_date_range_filter__returns_filtered_meals(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test listing meals with date range filter."""
    # Arrange
    from_date = datetime(2025, 1, 10, 0, 0, 0, tzinfo=UTC)
    to_date = datetime(2025, 1, 20, 0, 0, 0, tzinfo=UTC)

    meals = []
    mock_meal_repository.list_meals.return_value = meals

    service = MealService(mock_meal_repository)
    query = MealListQuery(**{"from": from_date, "to": to_date})

    # Act
    response = await service.list_meals(user_id=user_id, query=query)

    # Assert
    assert len(response.data) == 0
    call_kwargs = mock_meal_repository.list_meals.call_args.kwargs
    assert call_kwargs["from_date"] == from_date
    assert call_kwargs["to_date"] == to_date


@pytest.mark.asyncio
async def test_list_meals__with_category_filter__returns_category_meals(
    user_id: UUID, meal_category: str, mock_meal_repository: Mock
):
    """Test listing meals filtered by category."""
    # Arrange
    mock_meal_repository.list_meals.return_value = []

    service = MealService(mock_meal_repository)
    query = MealListQuery(category=meal_category)

    # Act
    await service.list_meals(user_id=user_id, query=query)

    # Assert
    call_kwargs = mock_meal_repository.list_meals.call_args.kwargs
    assert call_kwargs["category"] == meal_category


@pytest.mark.asyncio
async def test_list_meals__with_source_filter__returns_source_meals(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test listing meals filtered by source."""
    # Arrange
    mock_meal_repository.list_meals.return_value = []

    service = MealService(mock_meal_repository)
    query = MealListQuery(source=MealSource.AI)

    # Act
    await service.list_meals(user_id=user_id, query=query)

    # Assert
    call_kwargs = mock_meal_repository.list_meals.call_args.kwargs
    assert call_kwargs["source"] == MealSource.AI


@pytest.mark.asyncio
async def test_list_meals__with_include_deleted__returns_all_meals(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test listing meals with include_deleted=True."""
    # Arrange
    mock_meal_repository.list_meals.return_value = []

    service = MealService(mock_meal_repository)
    query = MealListQuery(include_deleted=True)

    # Act
    await service.list_meals(user_id=user_id, query=query)

    # Assert
    call_kwargs = mock_meal_repository.list_meals.call_args.kwargs
    assert call_kwargs["include_deleted"] is True


# =============================================================================
# Pagination Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_meals__pagination_next_cursor__generated_correctly(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test pagination cursor generated correctly when more results available."""
    # Arrange
    page_size = 2
    meal_id_1 = uuid4()
    meal_id_2 = uuid4()
    meal_id_3 = uuid4()

    # Return page_size + 1 MealListItem objects to indicate more results
    meals = [
        MealListItem(
            id=meal_id_1,
            category=meal_category,
            eaten_at=now.replace(hour=18),
            source=MealSource.AI,
            calories=Decimal("600.00"),
            protein=Decimal("35.00"),
            fat=Decimal("20.00"),
            carbs=Decimal("50.00"),
            accepted_analysis_run_id=None,
        ),
        MealListItem(
            id=meal_id_2,
            category=meal_category,
            eaten_at=now.replace(hour=12),
            source=MealSource.AI,
            calories=Decimal("500.00"),
            protein=Decimal("30.00"),
            fat=Decimal("15.00"),
            carbs=Decimal("40.00"),
            accepted_analysis_run_id=None,
        ),
        MealListItem(
            id=meal_id_3,
            category=meal_category,
            eaten_at=now.replace(hour=8),
            source=MealSource.AI,
            calories=Decimal("300.00"),
            protein=Decimal("20.00"),
            fat=Decimal("10.00"),
            carbs=Decimal("30.00"),
            accepted_analysis_run_id=None,
        ),
    ]
    mock_meal_repository.list_meals.return_value = meals

    service = MealService(mock_meal_repository)
    query = MealListQuery(**{"page[size]": page_size})

    # Act
    response = await service.list_meals(user_id=user_id, query=query)

    # Assert
    assert response.page.size == 2  # Only page_size items returned
    assert len(response.data) == 2
    assert response.page.after is not None  # Cursor generated

    # Verify cursor points to last returned item
    last_item = response.data[-1]
    assert last_item.id == meal_id_2


@pytest.mark.asyncio
async def test_list_meals__pagination_last_page__no_next_cursor(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test last page has no next cursor."""
    # Arrange
    page_size = 2

    # Return exactly page_size meals
    meals = [
        {
            "id": uuid4(),
            "category": meal_category,
            "eaten_at": now.replace(hour=12),
            "source": "ai",
            "calories": Decimal("500.00"),
            "protein": Decimal("30.00"),
            "fat": Decimal("15.00"),
            "carbs": Decimal("40.00"),
            "accepted_analysis_run_id": None,
        },
        {
            "id": uuid4(),
            "category": meal_category,
            "eaten_at": now.replace(hour=8),
            "source": "ai",
            "calories": Decimal("300.00"),
            "protein": Decimal("20.00"),
            "fat": Decimal("10.00"),
            "carbs": Decimal("30.00"),
            "accepted_analysis_run_id": None,
        },
    ]
    mock_meal_repository.list_meals.return_value = meals

    service = MealService(mock_meal_repository)
    query = MealListQuery(**{"page[size]": page_size})

    # Act
    response = await service.list_meals(user_id=user_id, query=query)

    # Assert
    assert response.page.size == 2
    assert response.page.after is None  # No next page


@pytest.mark.asyncio
async def test_list_meals__invalid_cursor__raises_400(user_id: UUID, mock_meal_repository: Mock):
    """Test invalid cursor raises 400 error."""
    # Arrange
    service = MealService(mock_meal_repository)
    query = MealListQuery(**{"page[after]": "invalid_cursor_data"})

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.list_meals(user_id=user_id, query=query)

    assert exc_info.value.status_code == 400
    assert "Invalid pagination cursor format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_meals__cursor_decode_encode__symmetry(now: datetime):
    """Test cursor encoding and decoding preserves data."""
    # Arrange
    meal_id = uuid4()
    eaten_at = now

    # Act
    cursor = encode_meal_cursor(last_eaten_at=eaten_at, last_id=meal_id)

    # Assert
    assert isinstance(cursor, str)
    assert len(cursor) > 0

    # Verify it's valid base64
    from app.api.v1.schemas.meals import decode_meal_cursor

    decoded = decode_meal_cursor(cursor)
    assert decoded.last_eaten_at == eaten_at
    assert decoded.last_id == meal_id


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_meals__repository_exception__raises_500(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test repository exception raises 500 error."""
    # Arrange
    mock_meal_repository.list_meals.side_effect = Exception("Database error")

    service = MealService(mock_meal_repository)
    query = MealListQuery()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.list_meals(user_id=user_id, query=query)

    assert exc_info.value.status_code == 500
    assert "Unable to retrieve meals" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_meals__repository_http_exception__propagates(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test repository HTTPException propagates correctly."""
    # Arrange
    http_exc = HTTPException(status_code=400, detail="Bad request")
    mock_meal_repository.list_meals.side_effect = http_exc

    service = MealService(mock_meal_repository)
    query = MealListQuery()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.list_meals(user_id=user_id, query=query)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Bad request"


# =============================================================================
# Create Meal Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_meal__valid_ai_meal__creates_successfully(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test creating AI meal with valid data succeeds."""
    # Arrange
    analysis_run_id = uuid4()
    meal_id = uuid4()

    mock_meal_repository.category_exists.return_value = True
    mock_meal_repository.get_analysis_run_for_acceptance.return_value = {
        "id": analysis_run_id,
        "status": "succeeded",
    }
    mock_meal_repository.create_meal.return_value = {
        "id": meal_id,
        "user_id": user_id,
        "category": meal_category,
        "eaten_at": now,
        "source": "ai",
        "calories": Decimal("450.50"),
        "protein": Decimal("25.50"),
        "fat": Decimal("18.00"),
        "carbs": Decimal("42.00"),
        "analysis_run_id": analysis_run_id,
    }

    service = MealService(mock_meal_repository)
    payload = MealCreatePayload(
        category=meal_category,
        eaten_at=now,
        source=MealSource.AI,
        calories=Decimal("450.50"),
        protein=Decimal("25.50"),
        fat=Decimal("18.00"),
        carbs=Decimal("42.00"),
        analysis_run_id=analysis_run_id,
    )

    # Act
    result = await service.create_meal(user_id=user_id, payload=payload)

    # Assert
    assert result["id"] == meal_id
    assert result["source"] == "ai"
    mock_meal_repository.category_exists.assert_called_once_with(category_code=meal_category)
    mock_meal_repository.get_analysis_run_for_acceptance.assert_called_once()
    mock_meal_repository.create_meal.assert_called_once()


@pytest.mark.asyncio
async def test_create_meal__category_not_found__raises_404(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test creating meal with non-existent category raises 404."""
    # Arrange
    mock_meal_repository.category_exists.return_value = False

    service = MealService(mock_meal_repository)
    payload = MealCreatePayload(
        category=meal_category,
        eaten_at=now,
        source=MealSource.MANUAL,
        calories=Decimal("500.00"),
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_meal(user_id=user_id, payload=payload)

    assert exc_info.value.status_code == 404
    assert meal_category in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_meal__analysis_run_not_found__raises_404(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test creating AI meal with invalid analysis_run_id raises 404."""
    # Arrange
    analysis_run_id = uuid4()

    mock_meal_repository.category_exists.return_value = True
    mock_meal_repository.get_analysis_run_for_acceptance.return_value = None

    service = MealService(mock_meal_repository)
    payload = MealCreatePayload(
        category=meal_category,
        eaten_at=now,
        source=MealSource.AI,
        calories=Decimal("450.50"),
        protein=Decimal("25.50"),
        fat=Decimal("18.00"),
        carbs=Decimal("42.00"),
        analysis_run_id=analysis_run_id,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_meal(user_id=user_id, payload=payload)

    assert exc_info.value.status_code == 404
    assert "Analysis run" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_meal__manual_source__no_analysis_validation(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test creating manual meal skips analysis validation."""
    # Arrange
    meal_id = uuid4()

    mock_meal_repository.category_exists.return_value = True
    mock_meal_repository.create_meal.return_value = {
        "id": meal_id,
        "user_id": user_id,
        "category": meal_category,
        "eaten_at": now,
        "source": "manual",
        "calories": Decimal("500.00"),
        "protein": None,
        "fat": None,
        "carbs": None,
        "analysis_run_id": None,
    }

    service = MealService(mock_meal_repository)
    payload = MealCreatePayload(
        category=meal_category,
        eaten_at=now,
        source=MealSource.MANUAL,
        calories=Decimal("500.00"),
    )

    # Act
    result = await service.create_meal(user_id=user_id, payload=payload)

    # Assert
    assert result["source"] == "manual"
    mock_meal_repository.category_exists.assert_called_once()
    mock_meal_repository.get_analysis_run_for_acceptance.assert_not_called()
    mock_meal_repository.create_meal.assert_called_once()


@pytest.mark.asyncio
async def test_create_meal__repository_error__raises_500(
    user_id: UUID, now: datetime, meal_category: str, mock_meal_repository: Mock
):
    """Test repository error during create raises 500."""
    # Arrange
    mock_meal_repository.category_exists.return_value = True
    mock_meal_repository.create_meal.side_effect = Exception("Database error")

    service = MealService(mock_meal_repository)
    payload = MealCreatePayload(
        category=meal_category,
        eaten_at=now,
        source=MealSource.MANUAL,
        calories=Decimal("500.00"),
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_meal(user_id=user_id, payload=payload)

    assert exc_info.value.status_code == 500
    assert "Unable to create meal" in exc_info.value.detail


# =============================================================================
# Get Meal Detail Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_meal_detail__meal_exists__returns_detail(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test getting meal detail returns complete data."""
    # Arrange
    meal_id = sample_meal_data["id"]
    mock_meal_repository.get_meal_by_id.return_value = sample_meal_data

    service = MealService(mock_meal_repository)

    # Act
    result = await service.get_meal_detail(user_id=user_id, meal_id=meal_id)

    # Assert
    assert result["id"] == meal_id
    assert result["user_id"] == user_id
    assert result["category"] == sample_meal_data["category"]
    assert result["calories"] == sample_meal_data["calories"]
    mock_meal_repository.get_meal_by_id.assert_called_once_with(
        meal_id=meal_id,
        user_id=user_id,
        include_deleted=False,
    )


@pytest.mark.asyncio
async def test_get_meal_detail__with_analysis__includes_analysis_data(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test getting meal with analysis includes analysis data."""
    # Arrange
    meal_id = sample_meal_data["id"]
    analysis_run_id = sample_meal_data["accepted_analysis_run_id"]

    meal_with_analysis = {
        **sample_meal_data,
        "accepted_analysis_run_id": analysis_run_id,
    }

    analysis_run = {
        "id": analysis_run_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "gpt-4",
        "latency_ms": 1500,
        "tokens": 250,
        "cost_minor_units": 150,
        "cost_currency": "USD",
        "threshold_used": Decimal("0.8"),
        "retry_of_run_id": None,
        "error_code": None,
        "error_message": None,
        "created_at": sample_meal_data["created_at"],
        "completed_at": sample_meal_data["created_at"],
    }

    mock_meal_repository.get_meal_by_id.return_value = meal_with_analysis
    mock_meal_repository.get_analysis_run_details.return_value = analysis_run

    service = MealService(mock_meal_repository)

    # Act
    result = await service.get_meal_detail(user_id=user_id, meal_id=meal_id)

    # Assert
    assert result["analysis"] is not None
    assert result["analysis"]["id"] == analysis_run_id
    assert result["analysis"]["status"] == "succeeded"
    mock_meal_repository.get_analysis_run_details.assert_called_once_with(
        run_id=analysis_run_id,
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_get_meal_detail__with_analysis_items__includes_items(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test getting meal with analysis items includes items."""
    # Arrange
    meal_id = sample_meal_data["id"]
    analysis_run_id = sample_meal_data["accepted_analysis_run_id"]

    meal_with_analysis = {
        **sample_meal_data,
        "accepted_analysis_run_id": analysis_run_id,
    }

    analysis_run = {
        "id": analysis_run_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "gpt-4",
        "latency_ms": 1500,
        "tokens": 250,
        "cost_minor_units": 150,
        "cost_currency": "USD",
        "threshold_used": Decimal("0.8"),
        "retry_of_run_id": None,
        "error_code": None,
        "error_message": None,
        "created_at": sample_meal_data["created_at"],
        "completed_at": sample_meal_data["created_at"],
    }

    items = [
        {
            "id": uuid4(),
            "ordinal": 1,
            "ingredient_name": "eggs",
            "amount_grams": Decimal("100.00"),
            "calories": Decimal("155.00"),
            "protein": Decimal("13.00"),
            "fat": Decimal("11.00"),
            "carbs": Decimal("1.10"),
        }
    ]

    mock_meal_repository.get_meal_by_id.return_value = meal_with_analysis
    mock_meal_repository.get_analysis_run_details.return_value = analysis_run
    mock_meal_repository.get_analysis_run_items.return_value = items

    service = MealService(mock_meal_repository)

    # Act
    result = await service.get_meal_detail(
        user_id=user_id, meal_id=meal_id, include_analysis_items=True
    )

    # Assert
    assert result["analysis"]["items"] is not None
    assert len(result["analysis"]["items"]) == 1
    mock_meal_repository.get_analysis_run_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_meal_detail__meal_not_found__raises_404(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test getting non-existent meal raises 404."""
    # Arrange
    meal_id = uuid4()
    mock_meal_repository.get_meal_by_id.return_value = None

    service = MealService(mock_meal_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_meal_detail(user_id=user_id, meal_id=meal_id)

    assert exc_info.value.status_code == 404
    assert str(meal_id) in exc_info.value.detail


# =============================================================================
# Update Meal Tests
# =============================================================================


@pytest.mark.asyncio
async def test_update_meal__valid_fields__updates_successfully(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test updating meal with valid fields succeeds."""
    # Arrange
    meal_id = sample_meal_data["id"]

    updated_meal = {
        **sample_meal_data,
        "calories": Decimal("550.00"),
    }

    mock_meal_repository.get_meal_by_id.return_value = sample_meal_data
    mock_meal_repository.update_meal.return_value = updated_meal

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload(calories=Decimal("550.00"))

    # Act
    result = await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    # Assert
    assert result["calories"] == Decimal("550.00")
    mock_meal_repository.update_meal.assert_called_once()


@pytest.mark.asyncio
async def test_update_meal__no_fields_provided__raises_400(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test updating meal with no fields raises 400."""
    # Arrange
    meal_id = uuid4()

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    assert exc_info.value.status_code == 400
    assert "at least one field" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_meal__meal_not_found__raises_404(user_id: UUID, mock_meal_repository: Mock):
    """Test updating non-existent meal raises 404."""
    # Arrange
    meal_id = uuid4()
    mock_meal_repository.get_meal_by_id.return_value = None

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload(calories=Decimal("550.00"))

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_meal__change_to_manual_with_macros__raises_400(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test changing source to manual when macros exist raises 400."""
    # Arrange
    meal_id = sample_meal_data["id"]

    # Current meal has macros
    current_meal = {
        **sample_meal_data,
        "protein": Decimal("25.50"),
        "fat": Decimal("18.00"),
        "carbs": Decimal("42.00"),
    }

    mock_meal_repository.get_meal_by_id.return_value = current_meal

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload(source=MealSource.MANUAL)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    assert exc_info.value.status_code == 400
    assert "manual" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_meal__category_not_exists__raises_400(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test updating meal with non-existent category raises 400."""
    # Arrange
    meal_id = sample_meal_data["id"]

    mock_meal_repository.get_meal_by_id.return_value = sample_meal_data
    mock_meal_repository.category_exists.return_value = False

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload(category="non_existent")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    assert exc_info.value.status_code == 400
    assert "non_existent" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_meal__analysis_run_already_accepted__raises_409(
    user_id: UUID, sample_meal_data: dict, mock_meal_repository: Mock
):
    """Test updating with already-accepted analysis_run_id raises 409."""
    # Arrange
    meal_id = sample_meal_data["id"]
    other_meal_id = uuid4()
    analysis_run_id = uuid4()

    mock_meal_repository.get_meal_by_id.return_value = sample_meal_data
    mock_meal_repository.get_analysis_run_for_acceptance.return_value = {
        "id": analysis_run_id,
        "status": "succeeded",
        "accepted_in_meal_id": other_meal_id,  # Already accepted in different meal
    }

    service = MealService(mock_meal_repository)
    payload = MealUpdatePayload(analysis_run_id=analysis_run_id)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update_meal(user_id=user_id, meal_id=meal_id, payload=payload)

    assert exc_info.value.status_code == 409
    assert "already accepted" in exc_info.value.detail.lower()


# =============================================================================
# Soft Delete Tests
# =============================================================================


@pytest.mark.asyncio
async def test_soft_delete_meal__meal_exists__deletes_successfully(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test soft deleting existing meal succeeds."""
    # Arrange
    meal_id = uuid4()
    mock_meal_repository.soft_delete_meal.return_value = True

    service = MealService(mock_meal_repository)

    # Act
    await service.soft_delete_meal(user_id=user_id, meal_id=meal_id)

    # Assert
    mock_meal_repository.soft_delete_meal.assert_called_once_with(
        meal_id=meal_id,
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_soft_delete_meal__meal_not_found__raises_404(
    user_id: UUID, mock_meal_repository: Mock
):
    """Test soft deleting non-existent meal raises 404."""
    # Arrange
    meal_id = uuid4()
    mock_meal_repository.soft_delete_meal.return_value = False

    service = MealService(mock_meal_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.soft_delete_meal(user_id=user_id, meal_id=meal_id)

    assert exc_info.value.status_code == 404
    assert str(meal_id) in exc_info.value.detail

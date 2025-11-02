"""Unit test specific fixtures with mocked dependencies."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest


@pytest.fixture
def mock_meal_repository() -> Mock:
    """Mock for MealRepository (mixed sync/async methods)."""
    mock = Mock()
    # Sync method
    mock.list_meals.return_value = []
    # Async methods
    mock.create_meal = AsyncMock(return_value={})
    mock.get_meal_by_id = AsyncMock(return_value=None)
    mock.update_meal = AsyncMock(return_value=None)
    mock.soft_delete_meal = AsyncMock(return_value=False)
    mock.category_exists = AsyncMock(return_value=True)
    mock.get_analysis_run_for_acceptance = AsyncMock(return_value=None)
    mock.get_analysis_run_details = AsyncMock(return_value=None)
    mock.get_analysis_run_items = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_product_repository() -> Mock:
    """Mock for ProductRepository (sync)."""
    mock = Mock()
    mock.list_products.return_value = []
    mock.get_product_by_id.return_value = None
    return mock


@pytest.fixture
def mock_reports_repository() -> AsyncMock:
    """AsyncMock for ReportsRepository."""
    mock = AsyncMock()
    mock.get_daily_meal_aggregates.return_value = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
    }
    mock.get_daily_meals_list.return_value = []
    mock.get_meals_aggregated_by_date.return_value = {}
    return mock


@pytest.fixture
def mock_profile_repository() -> Mock:
    """Mock for ProfileRepository (sync)."""
    mock = Mock()
    mock.get_profile.return_value = None
    return mock


@pytest.fixture
def mock_analysis_runs_repository() -> AsyncMock:
    """AsyncMock for AnalysisRunsRepository."""
    mock = AsyncMock()
    mock.get_by_id.return_value = None
    mock.get_meal_for_user.return_value = None
    mock.get_active_run.return_value = None
    mock.get_next_run_no.return_value = 1
    mock.insert_run.return_value = {}
    mock.list_runs.return_value = []
    mock.get_run_with_raw_input.return_value = None
    mock.update_status.return_value = None
    mock.complete_run.return_value = {}
    mock.cancel_run_if_active.return_value = None
    return mock


@pytest.fixture
def mock_analysis_run_items_repository() -> AsyncMock:
    """AsyncMock for AnalysisRunItemsRepository."""
    mock = AsyncMock()
    mock.list_items.return_value = []
    mock.insert_item.return_value = None
    return mock


@pytest.fixture
def mock_openrouter_client() -> AsyncMock:
    """AsyncMock for OpenRouterClient."""
    mock = AsyncMock()
    mock.post.return_value = Mock()
    mock.stream_post.return_value = AsyncMock()
    return mock


@pytest.fixture
def mock_openrouter_service() -> AsyncMock:
    """AsyncMock for OpenRouterService."""
    mock = AsyncMock()
    mock.generate_chat_completion.return_value = Mock()
    mock.verify_ingredients_calories.return_value = []
    return mock


@pytest.fixture
def mock_supabase_client() -> Mock:
    """Mock for Supabase client."""
    mock = Mock()
    mock.auth = Mock()
    mock.auth.get_user.return_value = None
    return mock


# =============================================================================
# Common Test Data Fixtures
# =============================================================================


@pytest.fixture
def now() -> datetime:
    """Fixed timestamp for testing."""
    return datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def user_id() -> UUID:
    """Fixed user UUID for testing."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def meal_category() -> str:
    """Standard meal category code for testing."""
    return "śniadanie"


@pytest.fixture
def sample_meal_data(user_id: UUID, now: datetime, meal_category: str) -> dict[str, Any]:
    """Sample meal data dict for testing."""
    from decimal import Decimal

    meal_id = uuid4()
    analysis_run_id = uuid4()

    return {
        "id": meal_id,
        "user_id": user_id,
        "category": meal_category,
        "eaten_at": now,
        "source": "ai",
        "calories": Decimal("450.50"),
        "protein": Decimal("25.50"),
        "fat": Decimal("18.00"),
        "carbs": Decimal("42.00"),
        "accepted_analysis_run_id": analysis_run_id,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }

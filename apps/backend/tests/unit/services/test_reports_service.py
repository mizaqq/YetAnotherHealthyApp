"""Unit tests for ReportsService."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.reports import (
    DailySummaryMeal,
    DailySummaryProgress,
    DailySummaryResponse,
    DailySummaryTotals,
    ReportPointDTO,
    WeeklyTrendReportDTO,
)
from app.schemas.profile import ProfileResponse
from app.services.reports_service import ReportsService


# =============================================================================
# Get Daily Summary - Success Path Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_daily_summary__default_date_today_in_user_timezone__returns_summary(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary with default date (today in user's timezone) returns complete summary."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="Europe/Warsaw",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Mock repository returns
    aggregates = {
        "calories": Decimal("1850.00"),
        "protein": Decimal("120.50"),
        "fat": Decimal("85.25"),
        "carbs": Decimal("180.75"),
    }
    meals_data = [
        {
            "id": uuid4(),
            "category": "śniadanie",
            "calories": Decimal("450.00"),
            "eaten_at": now.replace(hour=8),
        },
        {
            "id": uuid4(),
            "category": "obiad",
            "calories": Decimal("800.00"),
            "eaten_at": now.replace(hour=13),
        },
    ]
    mock_reports_repository.get_daily_meal_aggregates.return_value = aggregates
    mock_reports_repository.get_daily_meals_list.return_value = meals_data

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_daily_summary(user_id=user_id)

    # Assert
    assert isinstance(result, DailySummaryResponse)
    # The date should be calculated based on current time in user's timezone
    # We can't predict the exact date without knowing current time, so just check it's a date
    assert isinstance(result.date, date)
    assert result.calorie_goal == Decimal("2000.00")

    # Check totals
    assert result.totals.calories == Decimal("1850.00")
    assert result.totals.protein == Decimal("120.50")
    assert result.totals.fat == Decimal("85.25")
    assert result.totals.carbs == Decimal("180.75")

    # Check progress (92.5% = 1850/2000 * 100)
    assert result.progress.calories_percentage == Decimal("92.5")

    # Check meals
    assert len(result.meals) == 2
    assert result.meals[0].category == "śniadanie"
    assert result.meals[1].category == "obiad"

    # Verify repository calls
    mock_profile_repository.get_profile.assert_called_once_with(user_id)
    mock_reports_repository.get_daily_meal_aggregates.assert_awaited_once()
    mock_reports_repository.get_daily_meals_list.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_daily_summary__specific_date_provided__returns_summary_for_that_date(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary with specific date returns summary for that date."""
    # Arrange
    target_date = date(2024, 12, 25)  # Christmas day
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("1800.00"),
        timezone="America/New_York",
        onboarding_completed_at=datetime(2024, 12, 20, tzinfo=timezone.utc),  # Before target date
        created_at=datetime(2024, 12, 20, tzinfo=timezone.utc),  # Before target date
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    aggregates = {
        "calories": Decimal("0.00"),
        "protein": Decimal("0.00"),
        "fat": Decimal("0.00"),
        "carbs": Decimal("0.00"),
    }
    meals_data = []  # No meals on Christmas day
    mock_reports_repository.get_daily_meal_aggregates.return_value = aggregates
    mock_reports_repository.get_daily_meals_list.return_value = meals_data

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_daily_summary(user_id=user_id, target_date=target_date)

    # Assert
    assert result.date == target_date
    assert result.calorie_goal == Decimal("1800.00")
    assert result.totals.calories == Decimal("0.00")
    assert result.progress.calories_percentage == Decimal("0.0")
    assert len(result.meals) == 0


@pytest.mark.asyncio
async def test_get_daily_summary__no_meals_for_date__returns_zero_totals_and_empty_meals(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary when no meals exist returns zero totals and empty meals list."""
    # Arrange
    target_date = now.date()
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2200.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # No meals - repository returns zeros
    aggregates = {
        "calories": Decimal("0.00"),
        "protein": Decimal("0.00"),
        "fat": Decimal("0.00"),
        "carbs": Decimal("0.00"),
    }
    meals_data = []
    mock_reports_repository.get_daily_meal_aggregates.return_value = aggregates
    mock_reports_repository.get_daily_meals_list.return_value = meals_data

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_daily_summary(user_id=user_id, target_date=target_date)

    # Assert
    assert result.totals.calories == Decimal("0.00")
    assert result.totals.protein == Decimal("0.00")
    assert result.totals.fat == Decimal("0.00")
    assert result.totals.carbs == Decimal("0.00")
    assert result.progress.calories_percentage == Decimal("0.0")
    assert len(result.meals) == 0


@pytest.mark.asyncio
async def test_get_daily_summary__profile_has_zero_calorie_goal__progress_percentage_zero(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary when profile has zero calorie goal returns zero progress percentage."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("0.00"),  # Zero goal (effectively no goal)
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    aggregates = {
        "calories": Decimal("500.00"),
        "protein": Decimal("25.00"),
        "fat": Decimal("20.00"),
        "carbs": Decimal("50.00"),
    }
    meals_data = [
        {
            "id": uuid4(),
            "category": "śniadanie",
            "calories": Decimal("500.00"),
            "eaten_at": now,
        }
    ]
    mock_reports_repository.get_daily_meal_aggregates.return_value = aggregates
    mock_reports_repository.get_daily_meals_list.return_value = meals_data

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_daily_summary(user_id=user_id)

    # Assert
    assert result.totals.calories == Decimal("500.00")
    assert result.progress.calories_percentage == Decimal("0.0")  # Zero because goal is zero
    assert len(result.meals) == 1


# =============================================================================
# Get Daily Summary - Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_daily_summary__profile_not_found__raises_404(
    user_id: UUID, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary when profile not found raises 404."""
    # Arrange
    mock_profile_repository.get_profile.return_value = None

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_daily_summary(user_id=user_id)

    assert exc_info.value.status_code == 404
    assert "User profile not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_daily_summary__date_before_profile_creation__raises_400(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary with date before profile creation raises 400."""
    # Arrange
    profile_creation_date = date(2024, 12, 15)
    target_date = date(2024, 12, 10)  # Before profile creation

    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=datetime.combine(profile_creation_date, time.min, tzinfo=timezone.utc),
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_daily_summary(user_id=user_id, target_date=target_date)

    assert exc_info.value.status_code == 400
    assert "cannot be before profile creation date" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_daily_summary__repository_error__raises_500(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary when repository fails raises 500."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Mock repository to raise exception
    mock_reports_repository.get_daily_meal_aggregates.side_effect = RuntimeError(
        "Database connection failed"
    )

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_daily_summary(user_id=user_id)

    assert exc_info.value.status_code == 500
    assert "Unable to generate daily summary" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_daily_summary__timezone_parsing_error__falls_back_to_utc(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get daily summary with invalid timezone falls back to UTC."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="Invalid/Timezone",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    aggregates = {
        "calories": Decimal("1000.00"),
        "protein": Decimal("50.00"),
        "fat": Decimal("40.00"),
        "carbs": Decimal("100.00"),
    }
    meals_data = []
    mock_reports_repository.get_daily_meal_aggregates.return_value = aggregates
    mock_reports_repository.get_daily_meals_list.return_value = meals_data

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_daily_summary(user_id=user_id)

    # Assert - should succeed with UTC fallback
    # Date will be current date, not the mocked now.date()
    assert isinstance(result.date, date)
    assert result.calorie_goal == Decimal("2000.00")
    assert result.totals.calories == Decimal("1000.00")


# =============================================================================
# Get Weekly Trend - Success Path Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_weekly_trend__default_end_date_today_utc__returns_7_day_trend(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend with default end date (today in UTC) returns 7 days of data."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Mock repository to return empty aggregates (no meals for current date range)
    mock_reports_repository.get_meals_aggregated_by_date.return_value = {}

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_weekly_trend(user_id=user_id)

    # Assert
    assert isinstance(result, WeeklyTrendReportDTO)
    # Dates will be calculated based on current time
    assert isinstance(result.start_date, date)
    assert isinstance(result.end_date, date)
    assert len(result.points) == 7

    # Check that all points have zero calories (no data) and correct goals
    for point in result.points:
        assert isinstance(point.date, date)
        assert point.calories == Decimal("0.00")
        assert point.goal == Decimal("2000.00")
        assert point.protein is None  # No data means None for macros
        assert point.fat is None
        assert point.carbs is None


@pytest.mark.asyncio
async def test_get_weekly_trend__specific_end_date_provided__returns_trend_for_that_period(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend with specific end date returns trend for that 7-day period."""
    # Arrange
    end_date = date(2024, 12, 25)
    start_date = date(2024, 12, 19)  # 7 days before (inclusive)

    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2200.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Only one day has data
    daily_aggregates = {
        date(2024, 12, 22): {
            "calories": Decimal("1500.00"),
            "protein": Decimal("100.00"),
            "fat": Decimal("60.00"),
            "carbs": Decimal("150.00"),
        },
    }
    mock_reports_repository.get_meals_aggregated_by_date.return_value = daily_aggregates

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_weekly_trend(user_id=user_id, end_date=end_date)

    # Assert
    assert result.start_date == start_date
    assert result.end_date == end_date
    assert len(result.points) == 7

    # Check that Dec 22 has data, others are zero
    dec22_index = (date(2024, 12, 22) - start_date).days
    assert result.points[dec22_index].date == date(2024, 12, 22)
    assert result.points[dec22_index].calories == Decimal("1500.00")

    # Check that other days have zero calories
    for i, point in enumerate(result.points):
        if i != dec22_index:
            assert point.calories == Decimal("0.00")


@pytest.mark.asyncio
async def test_get_weekly_trend__include_macros_false__returns_none_for_macro_fields(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend with include_macros=False returns None for protein/fat/carbs."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Use a specific end date that will include our test date
    end_date = date(2024, 12, 15)
    test_date = date(2024, 12, 15)
    daily_aggregates = {
        test_date: {
            "calories": Decimal("1800.00"),
            "protein": Decimal("120.00"),
            "fat": Decimal("80.00"),
            "carbs": Decimal("160.00"),
        },
    }
    mock_reports_repository.get_meals_aggregated_by_date.return_value = daily_aggregates

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_weekly_trend(
        user_id=user_id, end_date=end_date, include_macros=False
    )

    # Assert
    # Find the point for our test date (it should be the last point)
    assert result.end_date == end_date
    last_point = result.points[-1]  # Last point should be our test date

    assert last_point.date == test_date
    assert last_point.calories == Decimal("1800.00")
    assert last_point.protein is None  # Should be None when include_macros=False
    assert last_point.fat is None
    assert last_point.carbs is None


@pytest.mark.asyncio
async def test_get_weekly_trend__profile_zero_calorie_goal__uses_zero_goal(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend when profile has zero calorie goal uses zero as goal."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("0.00"),  # Zero goal set
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    end_date = date(2024, 12, 15)
    test_date = date(2024, 12, 15)
    daily_aggregates = {
        test_date: {
            "calories": Decimal("1200.00"),
            "protein": Decimal("80.00"),
            "fat": Decimal("50.00"),
            "carbs": Decimal("120.00"),
        },
    }
    mock_reports_repository.get_meals_aggregated_by_date.return_value = daily_aggregates

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act
    result = await service.get_weekly_trend(user_id=user_id, end_date=end_date)

    # Assert
    # Find the point for our test date (should be the last point)
    assert result.end_date == end_date
    last_point = result.points[-1]

    assert last_point.date == test_date
    assert last_point.calories == Decimal("1200.00")
    assert last_point.goal == Decimal("0.00")  # Zero goal when set to zero


# =============================================================================
# Get Weekly Trend - Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_weekly_trend__profile_not_found__raises_404(
    user_id: UUID, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend when profile not found raises 404."""
    # Arrange
    mock_profile_repository.get_profile.return_value = None

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_weekly_trend(user_id=user_id)

    assert exc_info.value.status_code == 404
    assert "User profile not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_weekly_trend__repository_error__raises_500(
    user_id: UUID, now: datetime, mock_reports_repository, mock_profile_repository
):
    """Test get weekly trend when repository fails raises 500."""
    # Arrange
    profile = ProfileResponse(
        user_id=user_id,
        daily_calorie_goal=Decimal("2000.00"),
        timezone="UTC",
        onboarding_completed_at=now,
        created_at=now,
        updated_at=now,
    )
    mock_profile_repository.get_profile.return_value = profile

    # Mock repository to raise exception
    mock_reports_repository.get_meals_aggregated_by_date.side_effect = RuntimeError(
        "Database query failed"
    )

    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_weekly_trend(user_id=user_id)

    assert exc_info.value.status_code == 500
    assert "Unable to generate weekly trend report" in exc_info.value.detail


# =============================================================================
# Helper Method Tests
# =============================================================================


def test_calculate_progress_percentage__normal_case__returns_correct_percentage(
    mock_reports_repository, mock_profile_repository
):
    """Test calculate progress percentage with normal values returns correct percentage."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    consumed = Decimal("1500.00")
    goal = Decimal("2000.00")

    # Act
    result = service._calculate_progress_percentage(consumed, goal)

    # Assert
    assert result == Decimal("75.0")  # 1500/2000 * 100 = 75.0


def test_calculate_progress_percentage__goal_is_zero__returns_zero_percentage(
    mock_reports_repository, mock_profile_repository
):
    """Test calculate progress percentage when goal is zero returns zero."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    consumed = Decimal("500.00")
    goal = Decimal("0.00")

    # Act
    result = service._calculate_progress_percentage(consumed, goal)

    # Assert
    assert result == Decimal("0.0")


def test_calculate_progress_percentage__goal_is_none__returns_zero_percentage(
    mock_reports_repository, mock_profile_repository
):
    """Test calculate progress percentage when goal is None returns zero."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    consumed = Decimal("500.00")
    goal = None

    # Act
    result = service._calculate_progress_percentage(consumed, goal)

    # Assert
    assert result == Decimal("0.0")


def test_calculate_progress_percentage__over_100_percent__returns_over_100(
    mock_reports_repository, mock_profile_repository
):
    """Test calculate progress percentage when consumed exceeds goal returns over 100."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    consumed = Decimal("2200.00")
    goal = Decimal("2000.00")

    # Act
    result = service._calculate_progress_percentage(consumed, goal)

    # Assert
    assert result == Decimal("110.0")  # 2200/2000 * 100 = 110.0


def test_get_timezone__valid_timezone__returns_zoneinfo_object(
    mock_reports_repository, mock_profile_repository
):
    """Test get timezone with valid timezone string returns ZoneInfo object."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    timezone_str = "Europe/Warsaw"

    # Act
    result = service._get_timezone(timezone_str)

    # Assert
    assert str(result) == "Europe/Warsaw"


def test_get_timezone__invalid_timezone__falls_back_to_utc(
    mock_reports_repository, mock_profile_repository
):
    """Test get timezone with invalid timezone string falls back to UTC."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    timezone_str = "Invalid/Timezone"

    # Act
    result = service._get_timezone(timezone_str)

    # Assert
    assert str(result) == "UTC"


def test_calculate_utc_boundaries__converts_date_to_utc_range(
    mock_reports_repository, mock_profile_repository
):
    """Test calculate UTC boundaries converts date in user timezone to UTC range."""
    # Arrange
    service = ReportsService(
        reports_repository=mock_reports_repository,
        profile_repository=mock_profile_repository,
    )

    # Use Warsaw timezone (UTC+1, with DST)
    from zoneinfo import ZoneInfo

    user_timezone = ZoneInfo("Europe/Warsaw")

    # December 15, 2024 (not DST)
    target_date = date(2024, 12, 15)

    # Act
    start_utc, end_utc = service._calculate_utc_boundaries(target_date, user_timezone)

    # Assert
    # Warsaw is UTC+1 in December
    expected_start = datetime(
        2024, 12, 14, 23, 0, 0, tzinfo=ZoneInfo("UTC")
    )  # 00:00 Warsaw = 23:00 UTC previous day
    expected_end = datetime(
        2024, 12, 15, 23, 0, 0, tzinfo=ZoneInfo("UTC")
    )  # 24:00 Warsaw = 23:00 UTC same day

    assert start_utc == expected_start
    assert end_utc == expected_end

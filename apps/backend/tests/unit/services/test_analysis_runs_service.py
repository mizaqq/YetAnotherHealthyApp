"""Unit tests for AnalysisRunsService."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.pagination import AnalysisRunCursor
from app.services.analysis_runs_service import AnalysisRunsService


# =============================================================================
# Get Run Detail Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_run_detail__run_exists__returns_run_data(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test getting run detail when run exists returns complete run data."""
    # Arrange
    run_id = uuid4()
    meal_id = uuid4()
    expected_run = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "anthropic/claude-3-5-sonnet",
        "threshold_used": Decimal("0.8"),
        "latency_ms": 1500,
        "tokens": 250,
        "cost_minor_units": 100,
        "cost_currency": "USD",
        "retry_of_run_id": None,
        "error_code": None,
        "error_message": None,
        "created_at": now,
        "completed_at": now,
    }
    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=expected_run)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.get_run_detail(run_id=run_id, user_id=user_id)

    # Assert
    assert result == expected_run
    mock_analysis_runs_repository.get_by_id.assert_awaited_once_with(run_id=run_id, user_id=user_id)


@pytest.mark.asyncio
async def test_get_run_detail__run_not_found__raises_404(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test getting run detail when run not found raises 404."""
    # Arrange
    run_id = uuid4()
    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=None)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_run_detail(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "analysis_run_not_found"
    mock_analysis_runs_repository.get_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_run_detail__repository_error__raises_500(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test getting run detail when repository fails raises 500."""
    # Arrange
    run_id = uuid4()
    mock_analysis_runs_repository.get_by_id = AsyncMock(
        side_effect=RuntimeError("Database connection failed")
    )

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_run_detail(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["code"] == "internal_error"


# =============================================================================
# Create Run - Input Validation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_run__neither_meal_nor_text__raises_400_missing_input(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test create run with neither meal_id nor input_text raises 400."""
    # Arrange
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_run(
            user_id=user_id,
            meal_id=None,
            input_text=None,
            threshold=0.8,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "missing_input"
    assert "Either meal_id or input_text must be provided" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_create_run__both_meal_and_text__raises_400_conflicting_input(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test create run with both meal_id and input_text raises 400."""
    # Arrange
    meal_id = uuid4()
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_run(
            user_id=user_id,
            meal_id=meal_id,
            input_text="scrambled eggs with toast",
            threshold=0.8,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "conflicting_input"
    assert "Only one of meal_id or input_text can be provided" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_create_run__meal_id_provided_but_meal_not_found__raises_404(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test create run with meal_id that doesn't exist raises 404."""
    # Arrange
    meal_id = uuid4()
    mock_analysis_runs_repository.get_meal_for_user = AsyncMock(return_value=None)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_run(
            user_id=user_id,
            meal_id=meal_id,
            input_text=None,
            threshold=0.8,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "meal_not_found"
    mock_analysis_runs_repository.get_meal_for_user.assert_awaited_once_with(
        meal_id=meal_id, user_id=user_id
    )


@pytest.mark.asyncio
async def test_create_run__active_run_exists__raises_409_conflict(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test create run when active run exists for meal raises 409."""
    # Arrange
    meal_id = uuid4()
    active_run_id = uuid4()

    mock_analysis_runs_repository.get_meal_for_user = AsyncMock(
        return_value={"id": meal_id, "user_id": user_id}
    )
    mock_analysis_runs_repository.get_active_run = AsyncMock(
        return_value={"id": active_run_id, "status": "running"}
    )

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create_run(
            user_id=user_id,
            meal_id=meal_id,
            input_text=None,
            threshold=0.8,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "analysis_run_active"
    assert str(active_run_id) in exc_info.value.detail["message"]
    mock_analysis_runs_repository.get_active_run.assert_awaited_once_with(
        meal_id=meal_id, user_id=user_id
    )


# =============================================================================
# Create Run - Success Paths Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_run__meal_id_provided_no_processor__returns_queued_run(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test create run with meal_id without processor returns queued run."""
    # Arrange
    meal_id = uuid4()
    run_id = uuid4()

    mock_analysis_runs_repository.get_meal_for_user = AsyncMock(
        return_value={"id": meal_id, "user_id": user_id}
    )
    mock_analysis_runs_repository.get_active_run = AsyncMock(return_value=None)
    mock_analysis_runs_repository.get_next_run_no = AsyncMock(return_value=2)
    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": run_id,
            "meal_id": meal_id,
            "run_no": 2,
            "status": "queued",
            "model": "anthropic/claude-3-5-sonnet",
            "threshold_used": Decimal("0.8"),
            "created_at": now,
        }
    )

    # Create service without processor (items_repository=None)
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.create_run(
        user_id=user_id,
        meal_id=meal_id,
        input_text=None,
        threshold=0.8,
    )

    # Assert
    assert result["id"] == run_id
    assert result["status"] == "queued"
    assert result["meal_id"] == meal_id
    assert result["run_no"] == 2

    mock_analysis_runs_repository.insert_run.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.insert_run.call_args.kwargs
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["meal_id"] == meal_id
    assert call_kwargs["run_no"] == 2
    assert call_kwargs["status"] == "queued"
    assert call_kwargs["threshold_used"] == Decimal("0.8")


@pytest.mark.asyncio
async def test_create_run__meal_id_provided_with_processor__processes_and_returns_succeeded(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_openrouter_service,
):
    """Test create run with meal_id and processor processes synchronously."""
    # Arrange
    meal_id = uuid4()
    run_id = uuid4()

    mock_analysis_runs_repository.get_meal_for_user = AsyncMock(
        return_value={"id": meal_id, "user_id": user_id}
    )
    mock_analysis_runs_repository.get_active_run = AsyncMock(return_value=None)
    mock_analysis_runs_repository.get_next_run_no = AsyncMock(return_value=1)
    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": run_id,
            "meal_id": meal_id,
            "run_no": 1,
            "status": "queued",
            "model": "anthropic/claude-3-5-sonnet",
            "threshold_used": Decimal("0.8"),
            "created_at": now,
        }
    )

    # Mock processor behavior
    mock_processor = AsyncMock()
    final_run = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "anthropic/claude-3-5-sonnet",
        "threshold_used": Decimal("0.8"),
        "latency_ms": 1200,
        "tokens": 180,
        "created_at": now,
        "completed_at": now,
    }
    mock_processor.process = AsyncMock(return_value=final_run)

    # Create service with processor
    service = AnalysisRunsService(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=Mock(),
        openrouter_service=mock_openrouter_service,
    )
    service._processor = mock_processor

    # Mock the _update_ai_meal_with_results method
    service._update_ai_meal_with_results = AsyncMock()

    # Act
    result = await service.create_run(
        user_id=user_id,
        meal_id=meal_id,
        input_text=None,
        threshold=0.8,
    )

    # Assert
    assert result["id"] == run_id
    assert result["status"] == "succeeded"
    mock_processor.process.assert_awaited_once()
    service._update_ai_meal_with_results.assert_awaited_once_with(
        meal_id=meal_id, user_id=user_id, analysis_run_id=run_id
    )


@pytest.mark.asyncio
async def test_create_run__text_provided_with_processor__processes_and_returns_succeeded(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_openrouter_service,
):
    """Test create run with text input and processor processes synchronously."""
    # Arrange
    run_id = uuid4()
    input_text = "2 scrambled eggs and whole wheat toast"

    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": run_id,
            "meal_id": None,
            "run_no": 1,
            "status": "queued",
            "model": "anthropic/claude-3-5-sonnet",
            "threshold_used": Decimal("0.8"),
            "created_at": now,
        }
    )

    # Mock processor behavior
    mock_processor = AsyncMock()
    final_run = {
        "id": run_id,
        "meal_id": None,
        "run_no": 1,
        "status": "succeeded",
        "model": "anthropic/claude-3-5-sonnet",
        "threshold_used": Decimal("0.8"),
        "latency_ms": 1500,
        "tokens": 220,
        "created_at": now,
        "completed_at": now,
    }
    mock_processor.process = AsyncMock(return_value=final_run)

    # Create service with processor
    service = AnalysisRunsService(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=Mock(),
        openrouter_service=mock_openrouter_service,
    )
    service._processor = mock_processor

    # Act
    result = await service.create_run(
        user_id=user_id,
        meal_id=None,
        input_text=input_text,
        threshold=0.8,
    )

    # Assert
    assert result["id"] == run_id
    assert result["status"] == "succeeded"

    # Verify insert_run was called with text-based raw_input
    mock_analysis_runs_repository.insert_run.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.insert_run.call_args.kwargs
    assert call_kwargs["meal_id"] is None
    assert call_kwargs["run_no"] == 1
    assert call_kwargs["raw_input"]["text"] == input_text
    assert call_kwargs["raw_input"]["source"] == "text"

    # Verify processor was called
    mock_processor.process.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_run__text_provided_no_processor__returns_queued_run(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test create run with text input without processor returns queued run."""
    # Arrange
    run_id = uuid4()
    input_text = "grilled chicken salad"

    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": run_id,
            "meal_id": None,
            "run_no": 1,
            "status": "queued",
            "model": "anthropic/claude-3-5-sonnet",
            "threshold_used": Decimal("0.8"),
            "created_at": now,
        }
    )

    # Create service without processor
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.create_run(
        user_id=user_id,
        meal_id=None,
        input_text=input_text,
        threshold=0.8,
    )

    # Assert
    assert result["id"] == run_id
    assert result["status"] == "queued"
    assert result["meal_id"] is None

    mock_analysis_runs_repository.insert_run.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.insert_run.call_args.kwargs
    assert call_kwargs["raw_input"]["text"] == input_text
    assert call_kwargs["raw_input"]["source"] == "text"


# =============================================================================
# List Runs Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_runs__no_filters__returns_all_user_runs(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test list runs without filters returns all user runs."""
    # Arrange
    runs = [
        {
            "id": uuid4(),
            "meal_id": uuid4(),
            "run_no": 1,
            "status": "succeeded",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "created_at": now,
            "completed_at": now,
        },
        {
            "id": uuid4(),
            "meal_id": uuid4(),
            "run_no": 1,
            "status": "failed",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "created_at": now,
            "completed_at": now,
        },
    ]
    mock_analysis_runs_repository.list_runs = AsyncMock(return_value=runs)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.list_runs(
        user_id=user_id,
        meal_id=None,
        status_filter=None,
        created_from=None,
        created_to=None,
        page_size=20,
        page_after=None,
        sort="-created_at",
    )

    # Assert
    assert len(result["data"]) == 2
    assert result["page"].size == 2
    assert result["page"].after is None

    mock_analysis_runs_repository.list_runs.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.list_runs.call_args.kwargs
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["limit"] == 21  # page_size + 1
    assert call_kwargs["sort_desc"] is True


@pytest.mark.asyncio
async def test_list_runs__with_pagination__returns_correct_page_with_cursor(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test list runs with pagination returns correct page and next cursor."""
    # Arrange
    page_size = 2
    # Return page_size + 1 items to indicate more pages exist
    runs = [
        {
            "id": uuid4(),
            "meal_id": uuid4(),
            "run_no": 1,
            "status": "succeeded",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "created_at": now,
            "completed_at": now,
        },
        {
            "id": uuid4(),
            "meal_id": uuid4(),
            "run_no": 1,
            "status": "running",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "created_at": now,
            "completed_at": None,
        },
        {
            "id": uuid4(),
            "meal_id": uuid4(),
            "run_no": 2,
            "status": "failed",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "created_at": now,
            "completed_at": now,
        },
    ]
    mock_analysis_runs_repository.list_runs = AsyncMock(return_value=runs)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.list_runs(
        user_id=user_id,
        meal_id=None,
        status_filter=None,
        created_from=None,
        created_to=None,
        page_size=page_size,
        page_after=None,
        sort="-created_at",
    )

    # Assert
    assert len(result["data"]) == page_size  # Should trim extra item
    assert result["page"].size == page_size
    assert result["page"].after is not None  # Should have next cursor

    # Verify cursor can be decoded
    cursor = AnalysisRunCursor.decode(result["page"].after)
    assert cursor.id == runs[1]["id"]  # Last item in returned page
    assert cursor.created_at == runs[1]["created_at"]


@pytest.mark.asyncio
async def test_list_runs__invalid_cursor__raises_400(user_id: UUID, mock_analysis_runs_repository):
    """Test list runs with invalid cursor raises 400."""
    # Arrange
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.list_runs(
            user_id=user_id,
            meal_id=None,
            status_filter=None,
            created_from=None,
            created_to=None,
            page_size=20,
            page_after="invalid_base64_cursor",
            sort="-created_at",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "invalid_cursor"


@pytest.mark.asyncio
async def test_list_runs__with_filters__passes_filters_to_repository(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test list runs with filters passes all filters to repository."""
    # Arrange
    meal_id = uuid4()
    created_from = now.replace(hour=0)
    created_to = now.replace(hour=23)

    mock_analysis_runs_repository.list_runs = AsyncMock(return_value=[])

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    await service.list_runs(
        user_id=user_id,
        meal_id=meal_id,
        status_filter="succeeded",
        created_from=created_from,
        created_to=created_to,
        page_size=10,
        page_after=None,
        sort="created_at",  # Ascending
    )

    # Assert
    mock_analysis_runs_repository.list_runs.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.list_runs.call_args.kwargs
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["meal_id"] == meal_id
    assert call_kwargs["status"] == "succeeded"
    assert call_kwargs["created_from"] == created_from
    assert call_kwargs["created_to"] == created_to
    assert call_kwargs["limit"] == 11
    assert call_kwargs["sort_desc"] is False  # No leading "-"


# =============================================================================
# Retry Run Tests
# =============================================================================


@pytest.mark.asyncio
async def test_retry_run__source_run_not_found__raises_404(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test retry run when source run not found raises 404."""
    # Arrange
    source_run_id = uuid4()
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=None)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.retry_run(
            user_id=user_id,
            source_run_id=source_run_id,
            threshold=None,
            raw_input_override=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "analysis_run_not_found"
    mock_analysis_runs_repository.get_run_with_raw_input.assert_awaited_once_with(
        run_id=source_run_id, user_id=user_id
    )


@pytest.mark.asyncio
async def test_retry_run__source_run_not_terminal__raises_400_invalid_state(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test retry run when source run is not in terminal state raises 400."""
    # Arrange
    source_run_id = uuid4()
    meal_id = uuid4()

    source_run = {
        "id": source_run_id,
        "meal_id": meal_id,
        "status": "running",  # Non-terminal state
        "threshold_used": Decimal("0.8"),
        "raw_input": {"meal_id": str(meal_id), "source": "meal"},
        "created_at": now,
    }
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=source_run)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.retry_run(
            user_id=user_id,
            source_run_id=source_run_id,
            threshold=None,
            raw_input_override=None,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "invalid_retry_state"
    assert "running" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_retry_run__active_run_exists_for_meal__raises_409_conflict(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test retry run when active run exists for meal raises 409."""
    # Arrange
    source_run_id = uuid4()
    meal_id = uuid4()
    active_run_id = uuid4()

    source_run = {
        "id": source_run_id,
        "meal_id": meal_id,
        "status": "failed",  # Terminal state
        "threshold_used": Decimal("0.8"),
        "raw_input": {"meal_id": str(meal_id), "source": "meal"},
        "created_at": now,
    }
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=source_run)
    mock_analysis_runs_repository.get_active_run = AsyncMock(
        return_value={"id": active_run_id, "status": "queued"}
    )

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.retry_run(
            user_id=user_id,
            source_run_id=source_run_id,
            threshold=None,
            raw_input_override=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "analysis_run_active"
    assert str(active_run_id) in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_retry_run__terminal_state_no_overrides__creates_new_run_with_same_params(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test retry run in terminal state without overrides uses original params."""
    # Arrange
    source_run_id = uuid4()
    meal_id = uuid4()
    new_run_id = uuid4()

    source_run = {
        "id": source_run_id,
        "meal_id": meal_id,
        "status": "failed",
        "threshold_used": Decimal("0.75"),
        "raw_input": {"meal_id": str(meal_id), "source": "meal"},
        "created_at": now,
    }
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=source_run)
    mock_analysis_runs_repository.get_active_run = AsyncMock(return_value=None)
    mock_analysis_runs_repository.get_next_run_no = AsyncMock(return_value=3)
    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": new_run_id,
            "meal_id": meal_id,
            "run_no": 3,
            "status": "queued",
            "threshold_used": Decimal("0.75"),
            "model": "anthropic/claude-3-5-sonnet",
            "retry_of_run_id": source_run_id,
            "created_at": now,
        }
    )
    mock_analysis_runs_repository.get_by_id = AsyncMock(
        return_value={
            "id": new_run_id,
            "meal_id": meal_id,
            "run_no": 3,
            "status": "queued",
            "threshold_used": Decimal("0.75"),
            "model": "anthropic/claude-3-5-sonnet",
            "retry_of_run_id": source_run_id,
            "created_at": now,
        }
    )

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.retry_run(
        user_id=user_id,
        source_run_id=source_run_id,
        threshold=None,  # No override
        raw_input_override=None,  # No override
    )

    # Assert
    assert result["id"] == new_run_id
    assert result["retry_of_run_id"] == source_run_id
    assert result["run_no"] == 3

    # Verify insert_run used original threshold and raw_input
    mock_analysis_runs_repository.insert_run.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.insert_run.call_args.kwargs
    assert call_kwargs["threshold_used"] == Decimal("0.75")
    assert call_kwargs["raw_input"] == source_run["raw_input"]
    assert call_kwargs["retry_of_run_id"] == source_run_id


@pytest.mark.asyncio
async def test_retry_run__terminal_state_with_threshold_override__uses_new_threshold(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test retry run with threshold override uses new threshold value."""
    # Arrange
    source_run_id = uuid4()
    meal_id = uuid4()
    new_run_id = uuid4()
    new_threshold = 0.9

    source_run = {
        "id": source_run_id,
        "meal_id": meal_id,
        "status": "succeeded",
        "threshold_used": Decimal("0.8"),
        "raw_input": {"meal_id": str(meal_id), "source": "meal"},
        "created_at": now,
    }
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=source_run)
    mock_analysis_runs_repository.get_active_run = AsyncMock(return_value=None)
    mock_analysis_runs_repository.get_next_run_no = AsyncMock(return_value=2)
    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": new_run_id,
            "meal_id": meal_id,
            "run_no": 2,
            "status": "queued",
            "threshold_used": Decimal("0.9"),
            "model": "anthropic/claude-3-5-sonnet",
            "retry_of_run_id": source_run_id,
            "created_at": now,
        }
    )
    mock_analysis_runs_repository.get_by_id = AsyncMock(
        return_value={
            "id": new_run_id,
            "meal_id": meal_id,
            "run_no": 2,
            "status": "queued",
            "threshold_used": Decimal("0.9"),
            "model": "anthropic/claude-3-5-sonnet",
            "retry_of_run_id": source_run_id,
            "created_at": now,
        }
    )

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.retry_run(
        user_id=user_id,
        source_run_id=source_run_id,
        threshold=new_threshold,
        raw_input_override=None,
    )

    # Assert
    assert result["threshold_used"] == Decimal("0.9")

    # Verify insert_run used new threshold
    mock_analysis_runs_repository.insert_run.assert_awaited_once()
    call_kwargs = mock_analysis_runs_repository.insert_run.call_args.kwargs
    assert call_kwargs["threshold_used"] == Decimal("0.9")


@pytest.mark.asyncio
async def test_retry_run__with_processor__processes_and_returns_final_run(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_openrouter_service,
):
    """Test retry run with processor processes synchronously and returns final result."""
    # Arrange
    source_run_id = uuid4()
    meal_id = uuid4()
    new_run_id = uuid4()

    source_run = {
        "id": source_run_id,
        "meal_id": meal_id,
        "status": "cancelled",
        "threshold_used": Decimal("0.8"),
        "raw_input": {"meal_id": str(meal_id), "source": "meal"},
        "created_at": now,
    }
    mock_analysis_runs_repository.get_run_with_raw_input = AsyncMock(return_value=source_run)
    mock_analysis_runs_repository.get_active_run = AsyncMock(return_value=None)
    mock_analysis_runs_repository.get_next_run_no = AsyncMock(return_value=2)
    mock_analysis_runs_repository.insert_run = AsyncMock(
        return_value={
            "id": new_run_id,
            "meal_id": meal_id,
            "run_no": 2,
            "status": "queued",
            "threshold_used": Decimal("0.8"),
            "model": "anthropic/claude-3-5-sonnet",
            "retry_of_run_id": source_run_id,
            "created_at": now,
        }
    )

    # Mock processor
    mock_processor = AsyncMock()
    final_run = {
        "id": new_run_id,
        "meal_id": meal_id,
        "run_no": 2,
        "status": "succeeded",
        "threshold_used": Decimal("0.8"),
        "model": "anthropic/claude-3-5-sonnet",
        "retry_of_run_id": source_run_id,
        "latency_ms": 1100,
        "tokens": 200,
        "created_at": now,
        "completed_at": now,
    }
    mock_processor.process = AsyncMock(return_value=final_run)

    service = AnalysisRunsService(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=Mock(),
        openrouter_service=mock_openrouter_service,
    )
    service._processor = mock_processor

    # Act
    result = await service.retry_run(
        user_id=user_id,
        source_run_id=source_run_id,
        threshold=None,
        raw_input_override=None,
    )

    # Assert
    assert result["id"] == new_run_id
    assert result["status"] == "succeeded"
    assert result["retry_of_run_id"] == source_run_id
    mock_processor.process.assert_awaited_once()


# =============================================================================
# Get Run Items Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_run_items__run_exists__returns_items(
    user_id: UUID, now: datetime, mock_analysis_runs_repository, mock_analysis_run_items_repository
):
    """Test get run items when run exists returns items list."""
    # Arrange
    run_id = uuid4()
    meal_id = uuid4()

    run_data = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "anthropic/claude-3-5-sonnet",
        "created_at": now,
    }
    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=run_data)

    items = [
        {
            "id": uuid4(),
            "ordinal": 1,
            "raw_name": "eggs",
            "quantity": Decimal("2"),
            "raw_unit": "g",
            "weight_grams": Decimal("100"),
            "calories": Decimal("143"),
            "protein": Decimal("12.6"),
            "fat": Decimal("9.5"),
            "carbs": Decimal("0.7"),
            "confidence": Decimal("0.95"),
        },
        {
            "id": uuid4(),
            "ordinal": 2,
            "raw_name": "toast",
            "quantity": Decimal("1"),
            "raw_unit": "slice",
            "weight_grams": Decimal("30"),
            "calories": Decimal("79"),
            "protein": Decimal("2.6"),
            "fat": Decimal("1.0"),
            "carbs": Decimal("14.7"),
            "confidence": Decimal("0.9"),
        },
    ]
    mock_analysis_run_items_repository.list_items = AsyncMock(return_value=items)

    service = AnalysisRunsService(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
    )

    # Act
    result = await service.get_run_items(run_id=run_id, user_id=user_id)

    # Assert
    assert result["run_id"] == run_id
    assert result["model"] == "anthropic/claude-3-5-sonnet"
    assert len(result["items"]) == 2
    assert result["items"][0]["ordinal"] == 1
    assert result["items"][1]["ordinal"] == 2

    mock_analysis_runs_repository.get_by_id.assert_awaited_once_with(run_id=run_id, user_id=user_id)
    mock_analysis_run_items_repository.list_items.assert_awaited_once_with(
        run_id=run_id, user_id=user_id
    )


@pytest.mark.asyncio
async def test_get_run_items__run_not_found__raises_404(
    user_id: UUID, mock_analysis_runs_repository, mock_analysis_run_items_repository
):
    """Test get run items when run not found raises 404."""
    # Arrange
    run_id = uuid4()
    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=None)

    service = AnalysisRunsService(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.get_run_items(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "analysis_run_not_found"


@pytest.mark.asyncio
async def test_get_run_items__items_repository_not_configured__raises_runtime_error(
    user_id: UUID, mock_analysis_runs_repository
):
    """Test get run items when items repository not configured raises RuntimeError."""
    # Arrange
    run_id = uuid4()

    # Create service without items_repository
    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        await service.get_run_items(run_id=run_id, user_id=user_id)

    assert "Items repository not configured" in str(exc_info.value)


# =============================================================================
# Cancel Run Tests
# =============================================================================


@pytest.mark.asyncio
async def test_cancel_run__active_run__cancels_successfully(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test cancel run when run is active cancels successfully."""
    # Arrange
    run_id = uuid4()
    meal_id = uuid4()

    active_run = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "running",
        "model": "anthropic/claude-3-5-sonnet",
        "created_at": now,
    }
    cancelled_run = {
        **active_run,
        "status": "cancelled",
        "completed_at": now,
    }

    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=active_run)
    mock_analysis_runs_repository.cancel_run_if_active = AsyncMock(return_value=cancelled_run)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act
    result = await service.cancel_run(run_id=run_id, user_id=user_id)

    # Assert
    assert result["id"] == run_id
    assert result["status"] == "cancelled"
    assert result["completed_at"] == now

    mock_analysis_runs_repository.cancel_run_if_active.assert_awaited_once_with(
        run_id=run_id, user_id=user_id
    )


@pytest.mark.asyncio
async def test_cancel_run__run_not_found__raises_404(user_id: UUID, mock_analysis_runs_repository):
    """Test cancel run when run not found raises 404."""
    # Arrange
    run_id = uuid4()
    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=None)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_run(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "analysis_run_not_found"


@pytest.mark.asyncio
async def test_cancel_run__already_terminal__raises_409_conflict(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test cancel run when run already in terminal state raises 409."""
    # Arrange
    run_id = uuid4()
    meal_id = uuid4()

    completed_run = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "succeeded",
        "model": "anthropic/claude-3-5-sonnet",
        "created_at": now,
        "completed_at": now,
    }

    mock_analysis_runs_repository.get_by_id = AsyncMock(return_value=completed_run)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_run(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "analysis_run_already_finished"
    assert "succeeded" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_cancel_run__race_condition__handles_gracefully(
    user_id: UUID, now: datetime, mock_analysis_runs_repository
):
    """Test cancel run handles race condition when run completes before cancel."""
    # Arrange
    run_id = uuid4()
    meal_id = uuid4()

    # First check: run is active
    running_run = {
        "id": run_id,
        "meal_id": meal_id,
        "run_no": 1,
        "status": "running",
        "model": "anthropic/claude-3-5-sonnet",
        "created_at": now,
    }

    # After attempted cancel: run completed (race condition)
    completed_run = {
        **running_run,
        "status": "succeeded",
        "completed_at": now,
    }

    # First call returns running, second call returns completed
    mock_analysis_runs_repository.get_by_id = AsyncMock(side_effect=[running_run, completed_run])
    # Cancel fails (returns None) because run already completed
    mock_analysis_runs_repository.cancel_run_if_active = AsyncMock(return_value=None)

    service = AnalysisRunsService(repository=mock_analysis_runs_repository)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel_run(run_id=run_id, user_id=user_id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "analysis_run_already_finished"
    assert "succeeded" in exc_info.value.detail["message"]

    # Verify both get_by_id calls were made
    assert mock_analysis_runs_repository.get_by_id.await_count == 2

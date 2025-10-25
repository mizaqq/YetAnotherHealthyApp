"""Unit tests for AnalysisRunProcessor."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from app.api.v1.schemas.products import MacroBreakdownDTO, ProductSource, ProductSummaryDTO
from app.schemas.openrouter import ChatRole, OpenRouterChatMessage
from app.services.analysis_processor import AnalysisRunProcessor
from app.services.openrouter_service import (
    AnalysisItem,
    IngredientVerificationResult,
    MacroDelta,
    MacroProfile,
    OpenRouterServiceError,
    ServiceDataError,
)


# =============================================================================
# Process - Success Path Tests
# =============================================================================


@pytest.mark.asyncio
async def test_process__valid_text_input__succeeds_and_creates_items(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process with valid text input succeeds and creates analysis items."""
    # Arrange
    run_id = uuid4()
    raw_input = {"text": "2 scrambled eggs and whole wheat toast", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter response
    mock_response = Mock()
    mock_response.model = "anthropic/claude-3-5-sonnet"
    mock_response.choices = [
        Mock(
            message=Mock(
                content=json.dumps(
                    {
                        "items": [
                            {
                                "ingredient_name": "egg, scrambled",
                                "amount_grams": 100,
                                "macros": {
                                    "calories": 143,
                                    "protein": 12.6,
                                    "fat": 9.5,
                                    "carbs": 0.7,
                                },
                            },
                            {
                                "ingredient_name": "bread, whole wheat",
                                "amount_grams": 60,
                                "confidence": 0.9,
                                "macros": {
                                    "calories": 158,
                                    "protein": 5.2,
                                    "fat": 2.0,
                                    "carbs": 29.4,
                                },
                            },
                        ]
                    }
                )
            )
        )
    ]
    mock_response.usage = Mock(prompt_tokens=50, completion_tokens=100, total_tokens=150)

    mock_openrouter_service.generate_chat_completion = AsyncMock(return_value=mock_response)
    mock_openrouter_service.verify_ingredients_calories = AsyncMock(return_value=[])

    # Mock repository methods
    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={
            "id": run_id,
            "status": "succeeded",
            "latency_ms": 1200,
            "tokens": 150,
            "model": "anthropic/claude-3-5-sonnet",
        }
    )
    mock_analysis_run_items_repository.insert_item = AsyncMock()

    # No product match in repository
    mock_product_repository.list_products.return_value = []

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert result["status"] == "succeeded"
    assert result["tokens"] == 150

    # Verify status was updated to "running"
    mock_analysis_runs_repository.update_status.assert_awaited_once_with(
        run_id=run_id, user_id=user_id, status="running"
    )

    # Verify items were created
    assert mock_analysis_run_items_repository.insert_item.await_count == 2

    # Verify OpenRouter was called
    mock_openrouter_service.generate_chat_completion.assert_awaited_once()

    # Verify complete_run was called
    mock_analysis_runs_repository.complete_run.assert_awaited_once()
    complete_call = mock_analysis_runs_repository.complete_run.call_args.kwargs
    assert complete_call["status"] == "succeeded"
    assert complete_call["tokens"] == 150


@pytest.mark.asyncio
async def test_process__with_product_matches__uses_database_macros(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process with product matches uses database macros instead of model macros."""
    # Arrange
    run_id = uuid4()
    product_id = uuid4()
    raw_input = {"text": "100g chicken breast", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter response
    mock_response = Mock()
    mock_response.model = "anthropic/claude-3-5-sonnet"
    mock_response.choices = [
        Mock(
            message=Mock(
                content=json.dumps(
                    {
                        "items": [
                            {
                                "ingredient_name": "chicken breast, raw",
                                "amount_grams": 100,
                                "macros": {
                                    "calories": 120,  # Model estimate
                                    "protein": 22,
                                    "fat": 2,
                                    "carbs": 0,
                                },
                            }
                        ]
                    }
                )
            )
        )
    ]
    mock_response.usage = Mock(prompt_tokens=30, completion_tokens=50, total_tokens=80)

    mock_openrouter_service.generate_chat_completion = AsyncMock(return_value=mock_response)
    mock_openrouter_service.verify_ingredients_calories = AsyncMock(return_value=[])

    # Mock product repository to return a match with database macros
    product_match = ProductSummaryDTO(
        id=product_id,
        name="Chicken breast, raw",
        source=ProductSource.USDA_SR_LEGACY,
        macros_per_100g=MacroBreakdownDTO(
            calories=Decimal("165"),  # Database value (more accurate)
            protein=Decimal("31"),
            carbs=Decimal("0"),
            fat=Decimal("3.6"),
        ),
        created_at=now,
    )
    mock_product_repository.list_products.return_value = [product_match]

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "succeeded"}
    )
    mock_analysis_run_items_repository.insert_item = AsyncMock()

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    # Verify item was created with database macros (scaled for 100g)
    mock_analysis_run_items_repository.insert_item.assert_awaited_once()
    insert_call = mock_analysis_run_items_repository.insert_item.call_args.kwargs

    # Database macros should be used (165 cal, not 120)
    assert insert_call["calories_kcal"] == Decimal("165")
    assert insert_call["protein_g"] == Decimal("31")
    assert insert_call["fat_g"] == Decimal("3.6")
    assert insert_call["carbs_g"] == Decimal("0")
    assert insert_call["matched_product_id"] == str(product_id)


@pytest.mark.asyncio
async def test_process__multiple_items__creates_with_correct_ordinals(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process with multiple items creates them with correct ordinal sequence."""
    # Arrange
    run_id = uuid4()
    raw_input = {"text": "breakfast: eggs, bacon, toast", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter response with 3 items
    mock_response = Mock()
    mock_response.model = "anthropic/claude-3-5-sonnet"
    mock_response.choices = [
        Mock(
            message=Mock(
                content=json.dumps(
                    {
                        "items": [
                            {
                                "ingredient_name": "egg, fried",
                                "amount_grams": 50,
                                "macros": {
                                    "calories": 71,
                                    "protein": 6.3,
                                    "fat": 4.7,
                                    "carbs": 0.4,
                                },
                            },
                            {
                                "ingredient_name": "bacon, cooked",
                                "amount_grams": 30,
                                "macros": {
                                    "calories": 161,
                                    "protein": 11.1,
                                    "fat": 12.3,
                                    "carbs": 0.9,
                                },
                            },
                            {
                                "ingredient_name": "bread, white",
                                "amount_grams": 60,
                                "macros": {
                                    "calories": 158,
                                    "protein": 5.2,
                                    "fat": 2.0,
                                    "carbs": 29.4,
                                },
                            },
                        ]
                    }
                )
            )
        )
    ]
    mock_response.usage = Mock(prompt_tokens=40, completion_tokens=120, total_tokens=160)

    mock_openrouter_service.generate_chat_completion = AsyncMock(return_value=mock_response)
    mock_openrouter_service.verify_ingredients_calories = AsyncMock(return_value=[])

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "succeeded"}
    )
    mock_analysis_run_items_repository.insert_item = AsyncMock()
    mock_product_repository.list_products.return_value = []

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert mock_analysis_run_items_repository.insert_item.await_count == 3

    # Verify ordinals are 1, 2, 3
    calls = mock_analysis_run_items_repository.insert_item.call_args_list
    assert calls[0].kwargs["ordinal"] == 1
    assert calls[0].kwargs["ingredient_name"] == "egg, fried"
    assert calls[1].kwargs["ordinal"] == 2
    assert calls[1].kwargs["ingredient_name"] == "bacon, cooked"
    assert calls[2].kwargs["ordinal"] == 3
    assert calls[2].kwargs["ingredient_name"] == "bread, white"


# =============================================================================
# Process - Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_process__no_text_input__raises_service_data_error_and_fails_run(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process without text input raises ServiceDataError and fails the run."""
    # Arrange
    run_id = uuid4()
    raw_input = {"source": "text"}  # Missing "text" field
    threshold = Decimal("0.8")

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "failed", "error_code": "external_data_error"}
    )

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert result["status"] == "failed"
    assert result["error_code"] == "external_data_error"

    # Verify complete_run was called with failure status
    mock_analysis_runs_repository.complete_run.assert_awaited_once()
    complete_call = mock_analysis_runs_repository.complete_run.call_args.kwargs
    assert complete_call["status"] == "failed"
    assert complete_call["error_code"] == "external_data_error"
    assert "Text input required" in complete_call["error_message"]


@pytest.mark.asyncio
async def test_process__openrouter_service_error__fails_run_with_error_code(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process when OpenRouter service fails propagates error code and fails run."""
    # Arrange
    run_id = uuid4()
    raw_input = {"text": "chicken and rice", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter to raise service error
    error = OpenRouterServiceError("API rate limit exceeded")
    error.error_code = "external_rate_limited"
    mock_openrouter_service.generate_chat_completion = AsyncMock(side_effect=error)

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "failed", "error_code": "external_rate_limited"}
    )

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert result["status"] == "failed"
    assert result["error_code"] == "external_rate_limited"

    mock_analysis_runs_repository.complete_run.assert_awaited_once()
    complete_call = mock_analysis_runs_repository.complete_run.call_args.kwargs
    assert complete_call["error_code"] == "external_rate_limited"


@pytest.mark.asyncio
async def test_process__service_data_error__fails_run_with_data_error_code(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process when data validation fails uses external_data_error code."""
    # Arrange
    run_id = uuid4()
    raw_input = {"text": "pasta carbonara", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter to return invalid response
    mock_response = Mock()
    mock_response.choices = []  # No choices - invalid response

    mock_openrouter_service.generate_chat_completion = AsyncMock(return_value=mock_response)

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "failed", "error_code": "external_data_error"}
    )

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert result["status"] == "failed"
    assert result["error_code"] == "external_data_error"


@pytest.mark.asyncio
async def test_process__unexpected_exception__fails_run_with_processing_error(
    user_id: UUID,
    now: datetime,
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test process when unexpected exception occurs uses PROCESSING_ERROR code."""
    # Arrange
    run_id = uuid4()
    raw_input = {"text": "salad", "source": "text"}
    threshold = Decimal("0.8")

    # Mock OpenRouter to raise unexpected error
    mock_openrouter_service.generate_chat_completion = AsyncMock(
        side_effect=ValueError("Unexpected error")
    )

    mock_analysis_runs_repository.update_status = AsyncMock()
    mock_analysis_runs_repository.complete_run = AsyncMock(
        return_value={"id": run_id, "status": "failed", "error_code": "PROCESSING_ERROR"}
    )

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor.process(
        run_id=run_id,
        user_id=user_id,
        meal_id=None,
        raw_input=raw_input,
        threshold=threshold,
    )

    # Assert
    assert result["status"] == "failed"
    assert result["error_code"] == "PROCESSING_ERROR"


# =============================================================================
# Parse Model Content Tests
# =============================================================================


def test_parse_model_content__nested_macros_format__parses_correctly(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing model content with nested macros object format."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = json.dumps(
        {
            "items": [
                {
                    "ingredient_name": "apple",
                    "amount_grams": 182,
                    "confidence": 0.95,
                    "macros": {
                        "calories": 95,
                        "protein": 0.5,
                        "carbs": 25.1,
                        "fat": 0.3,
                    },
                }
            ]
        }
    )
    threshold = Decimal("0.8")

    # Act
    items, payload = processor._parse_model_content(content, threshold)

    # Assert
    assert len(items) == 1
    assert items[0].ingredient_name == "apple"
    assert items[0].amount_grams == Decimal("182")
    assert items[0].confidence == Decimal("0.95")
    assert items[0].macros.calories == Decimal("95")
    assert items[0].macros.protein == Decimal("0.5")
    assert items[0].macros.carbs == Decimal("25.1")
    assert items[0].macros.fat == Decimal("0.3")


def test_parse_model_content__flat_macros_format__parses_correctly(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing model content with flat macros format (legacy)."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = json.dumps(
        {
            "items": [
                {
                    "ingredient_name": "banana",
                    "amount_grams": 118,
                    "calories": 105,
                    "protein": 1.3,
                    "carbs": 27.0,
                    "fat": 0.4,
                }
            ]
        }
    )
    threshold = Decimal("0.8")

    # Act
    items, payload = processor._parse_model_content(content, threshold)

    # Assert
    assert len(items) == 1
    assert items[0].ingredient_name == "banana"
    assert items[0].macros.calories == Decimal("105")
    assert items[0].macros.protein == Decimal("1.3")
    assert items[0].macros.carbs == Decimal("27.0")
    assert items[0].macros.fat == Decimal("0.4")


def test_parse_model_content__missing_confidence__uses_threshold(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing model content without confidence field uses threshold value."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = json.dumps(
        {
            "items": [
                {
                    "ingredient_name": "orange",
                    "amount_grams": 131,
                    "macros": {"calories": 62, "protein": 1.2, "carbs": 15.4, "fat": 0.2},
                    # No confidence field
                }
            ]
        }
    )
    threshold = Decimal("0.85")

    # Act
    items, payload = processor._parse_model_content(content, threshold)

    # Assert
    assert items[0].confidence == Decimal("0.85")


def test_parse_model_content__invalid_json__raises_service_data_error(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing invalid JSON raises ServiceDataError."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = "not valid json { broken"
    threshold = Decimal("0.8")

    # Act & Assert
    with pytest.raises(ServiceDataError) as exc_info:
        processor._parse_model_content(content, threshold)

    assert "not valid JSON" in str(exc_info.value)


def test_parse_model_content__missing_items_field__raises_service_data_error(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing response without items field raises ServiceDataError."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = json.dumps({"data": []})  # Wrong field name
    threshold = Decimal("0.8")

    # Act & Assert
    with pytest.raises(ServiceDataError) as exc_info:
        processor._parse_model_content(content, threshold)

    assert "missing 'items' list" in str(exc_info.value)


def test_parse_model_content__empty_items_list__raises_service_data_error(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test parsing response with empty items list raises ServiceDataError."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    content = json.dumps({"items": []})
    threshold = Decimal("0.8")

    # Act & Assert
    with pytest.raises(ServiceDataError) as exc_info:
        processor._parse_model_content(content, threshold)

    assert "empty items list" in str(exc_info.value)


# =============================================================================
# Lookup Product Tests
# =============================================================================


@pytest.mark.asyncio
async def test_lookup_product_by_name__match_found__returns_product_with_macros(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
    now: datetime,
):
    """Test product lookup with match found returns product data with macros."""
    # Arrange
    product_id = uuid4()
    ingredient_name = "egg, fried"

    product_match = ProductSummaryDTO(
        id=product_id,
        name="Egg, fried",
        source=ProductSource.USDA_SR_LEGACY,
        macros_per_100g=MacroBreakdownDTO(
            calories=Decimal("196"),
            protein=Decimal("13.6"),
            carbs=Decimal("0.8"),
            fat=Decimal("14.8"),
        ),
        created_at=now,
    )
    mock_product_repository.list_products.return_value = [product_match]

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor._lookup_product_by_name(ingredient_name)

    # Assert
    assert result is not None
    assert result["id"] == str(product_id)
    assert result["macros"]["calories"] == Decimal("196")
    assert result["macros"]["protein"] == Decimal("13.6")
    assert result["macros"]["carbs"] == Decimal("0.8")
    assert result["macros"]["fat"] == Decimal("14.8")

    # Verify search was performed with transformed query
    mock_product_repository.list_products.assert_called_once()
    call_kwargs = mock_product_repository.list_products.call_args[1]
    assert call_kwargs["search"] == "egg*fried"  # ", " replaced with "*"
    assert call_kwargs["include_macros"] is True


@pytest.mark.asyncio
async def test_lookup_product_by_name__no_match__returns_none(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test product lookup with no match returns None."""
    # Arrange
    ingredient_name = "exotic unknown ingredient"
    mock_product_repository.list_products.return_value = []

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor._lookup_product_by_name(ingredient_name)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_lookup_product_by_name__repository_error__returns_none(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test product lookup when repository fails returns None gracefully."""
    # Arrange
    ingredient_name = "chicken breast"
    mock_product_repository.list_products.side_effect = RuntimeError("Database connection failed")

    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    # Act
    result = await processor._lookup_product_by_name(ingredient_name)

    # Assert
    assert result is None  # Gracefully returns None on error


# =============================================================================
# Build Messages Tests
# =============================================================================


def test_build_messages__with_text__creates_proper_prompt(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test build messages with text input creates proper prompt structure."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    raw_input = {"text": "2 eggs and toast"}

    # Act
    messages = processor._build_messages(raw_input)

    # Assert
    assert len(messages) == 2
    assert messages[0].role == ChatRole.SYSTEM
    assert "dietetycznym asystentem" in messages[0].content
    assert messages[1].role == ChatRole.USER
    assert "2 eggs and toast" in messages[1].content
    assert "Opis posiłku:" in messages[1].content


def test_build_messages__without_text__uses_fallback(
    mock_analysis_runs_repository,
    mock_analysis_run_items_repository,
    mock_product_repository,
    mock_openrouter_service,
):
    """Test build messages without text uses fallback message."""
    # Arrange
    processor = AnalysisRunProcessor(
        repository=mock_analysis_runs_repository,
        items_repository=mock_analysis_run_items_repository,
        product_repository=mock_product_repository,
        openrouter_service=mock_openrouter_service,
    )

    raw_input = {}

    # Act
    messages = processor._build_messages(raw_input)

    # Assert
    assert len(messages) == 2
    assert messages[1].role == ChatRole.USER
    assert "Brak opisu tekstowego" in messages[1].content

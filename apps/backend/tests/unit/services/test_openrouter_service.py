"""Unit tests for OpenRouterService."""

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest

from app.api.v1.schemas.products import MacroBreakdownDTO, ProductSource, ProductSummaryDTO
from app.core.config import OpenRouterConfig, Settings
from app.schemas.openrouter import (
    ChatRole,
    JsonSchemaDefinition,
    JsonSchemaResponseFormat,
    OpenRouterChatMessage,
    OpenRouterChatResponse,
)
from app.services.openrouter_service import (
    AnalysisItem,
    AuthorizationError,
    InvalidRequestError,
    MacroProfile,
    OpenRouterService,
    RateLimitError,
    ServiceDataError,
    ServiceUnavailableError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_settings() -> Mock:
    """Mock Settings with OpenRouter configuration."""
    settings = Mock(spec=Settings)
    settings.openrouter = OpenRouterConfig(
        api_key="test-api-key",
        base_url="https://openrouter.ai/api/v1",
        default_model="anthropic/claude-3-5-sonnet",
        default_temperature=0.7,
        default_top_p=0.9,
        max_output_tokens=4000,
        max_input_tokens=8192,
    )
    return settings


@pytest.fixture
def openrouter_service(
    mock_settings: Mock, mock_openrouter_client: AsyncMock, mock_product_repository: Mock
) -> OpenRouterService:
    """OpenRouterService instance with mocked dependencies."""
    return OpenRouterService(
        settings=mock_settings,
        client=mock_openrouter_client,
        product_repository=mock_product_repository,
    )


# =============================================================================
# Generate Chat Completion - Success Tests
# =============================================================================


@pytest.mark.asyncio
async def test_generate_chat_completion__valid_request__returns_response(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test generate_chat_completion with valid request returns response."""
    # Arrange
    messages = [
        OpenRouterChatMessage(role=ChatRole.SYSTEM, content="You are a helpful assistant"),
        OpenRouterChatMessage(role=ChatRole.USER, content="Hello"),
    ]

    mock_response_data = {
        "id": "gen-123",
        "model": "anthropic/claude-3-5-sonnet",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hi there!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 5,
            "total_tokens": 20,
        },
    }

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.content = json.dumps(mock_response_data).encode()

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act
    result = await openrouter_service.generate_chat_completion(messages)

    # Assert
    assert isinstance(result, OpenRouterChatResponse)
    assert result.id == "gen-123"
    assert result.model == "anthropic/claude-3-5-sonnet"
    assert len(result.choices) == 1
    assert result.choices[0].message.content == "Hi there!"
    assert result.usage.total_tokens == 20

    mock_openrouter_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_chat_completion__custom_parameters__uses_overrides(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test generate_chat_completion with custom parameters uses provided values."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]
    custom_model = "openai/gpt-4"
    custom_temp = 0.5
    custom_top_p = 0.8
    custom_max_tokens = 2000

    mock_response_data = {
        "id": "gen-456",
        "model": custom_model,
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Response"},
                "finish_reason": "stop",
            }
        ],
    }

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act
    result = await openrouter_service.generate_chat_completion(
        messages,
        model=custom_model,
        temperature=custom_temp,
        top_p=custom_top_p,
        max_output_tokens=custom_max_tokens,
    )

    # Assert
    assert result.model == custom_model

    # Verify request payload included custom parameters
    call_kwargs = mock_openrouter_client.post.call_args.kwargs
    request_json = call_kwargs["json"]
    assert request_json["model"] == custom_model
    assert request_json["temperature"] == custom_temp
    assert request_json["top_p"] == custom_top_p
    assert request_json["max_output_tokens"] == custom_max_tokens


@pytest.mark.asyncio
async def test_generate_chat_completion__with_response_format__includes_json_schema(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test generate_chat_completion with response_format includes JSON schema."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Analyze this")]

    response_format = JsonSchemaResponseFormat(
        json_schema=JsonSchemaDefinition(
            name="meal_analysis",
            schema={"type": "object", "properties": {"items": {"type": "array"}}},
        )
    )

    mock_response_data = {
        "id": "gen-789",
        "model": "anthropic/claude-3-5-sonnet",
        "created": 1234567890,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": '{"items": []}'},
                "finish_reason": "stop",
            }
        ],
    }

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act
    await openrouter_service.generate_chat_completion(messages, response_format=response_format)

    # Assert
    call_kwargs = mock_openrouter_client.post.call_args.kwargs
    request_json = call_kwargs["json"]
    assert "response_format" in request_json
    assert request_json["response_format"]["type"] == "json_schema"
    assert request_json["response_format"]["json_schema"]["name"] == "meal_analysis"


# =============================================================================
# Generate Chat Completion - Error Mapping Tests
# =============================================================================


@pytest.mark.asyncio
async def test_generate_chat_completion__401_error__raises_authorization_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test 401 error maps to AuthorizationError."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 401
    mock_http_response.json.return_value = {"error": {"message": "Invalid API key"}}
    mock_http_response.text = "Unauthorized"
    mock_http_response.headers = {}
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Invalid API key" in str(exc_info.value)
    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "external_auth_error"


@pytest.mark.asyncio
async def test_generate_chat_completion__403_error__raises_authorization_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test 403 error maps to AuthorizationError."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 403
    mock_http_response.json.return_value = {"message": "Access forbidden"}
    mock_http_response.text = "Forbidden"
    mock_http_response.headers = {}
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(AuthorizationError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Access forbidden" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_chat_completion__429_error__raises_rate_limit_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test 429 error maps to RateLimitError with retry_after."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 429
    mock_http_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
    mock_http_response.text = "Too Many Requests"
    mock_http_response.headers = {"Retry-After": "60"}
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(RateLimitError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Rate limit exceeded" in str(exc_info.value)
    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "external_rate_limited"
    assert exc_info.value.retry_after == 60.0


@pytest.mark.asyncio
async def test_generate_chat_completion__400_error__raises_invalid_request_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test 400-499 errors map to InvalidRequestError."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 400
    mock_http_response.json.return_value = {"error": {"message": "Invalid request payload"}}
    mock_http_response.text = "Bad Request"
    mock_http_response.headers = {}
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(InvalidRequestError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Invalid request payload" in str(exc_info.value)
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "external_invalid_request"


@pytest.mark.asyncio
async def test_generate_chat_completion__500_error__raises_service_unavailable_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test 500+ errors map to ServiceUnavailableError."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 503
    mock_http_response.json.return_value = {"error": {"message": "Service unavailable"}}
    mock_http_response.text = "Service Unavailable"
    mock_http_response.headers = {}
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(ServiceUnavailableError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Service unavailable" in str(exc_info.value)
    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "external_service_unavailable"


@pytest.mark.asyncio
async def test_generate_chat_completion__invalid_json_response__raises_service_data_error(
    openrouter_service: OpenRouterService, mock_openrouter_client: AsyncMock
):
    """Test invalid JSON response raises ServiceDataError."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    mock_http_response = Mock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
    mock_http_response.content = b""

    mock_openrouter_client.post = AsyncMock(return_value=mock_http_response)

    # Act & Assert
    with pytest.raises(ServiceDataError) as exc_info:
        await openrouter_service.generate_chat_completion(messages)

    assert "Invalid JSON" in str(exc_info.value)
    assert exc_info.value.error_code == "external_data_error"


# =============================================================================
# Verify Ingredients - Success Tests
# =============================================================================


@pytest.mark.asyncio
async def test_verify_ingredients_calories__with_matching_product__returns_verification(
    openrouter_service: OpenRouterService, mock_product_repository: Mock, now: datetime
):
    """Test verify_ingredients with matching product returns verification result."""
    # Arrange
    product_id = uuid4()

    analysis_items = [
        AnalysisItem(
            ingredient_name="chicken breast",
            amount_grams=Decimal("100"),
            macros=MacroProfile(
                calories=Decimal("165"),
                protein=Decimal("31"),
                carbs=Decimal("0"),
                fat=Decimal("3.6"),
            ),
            product_id=product_id,
        )
    ]

    # Mock product repository
    product_dto = ProductSummaryDTO(
        id=product_id,
        name="Chicken breast, raw",
        source=ProductSource.USDA_SR_LEGACY,
        macros_per_100g=MacroBreakdownDTO(
            calories=Decimal("165"),
            protein=Decimal("31"),
            carbs=Decimal("0"),
            fat=Decimal("3.6"),
        ),
        created_at=now,
    )
    mock_product_repository.get_product_by_id.return_value = product_dto

    # Act
    results = await openrouter_service.verify_ingredients_calories(analysis_items)

    # Assert
    assert len(results) == 1
    assert results[0].ingredient_name == "chicken breast"
    assert results[0].product_id == product_id
    assert results[0].requires_manual_review is False
    assert len(results[0].issues) == 0

    # Verify macro delta was calculated
    assert results[0].macro_delta is not None
    assert results[0].macro_delta.calories_diff == Decimal("0.00")


@pytest.mark.asyncio
async def test_verify_ingredients_calories__no_product_id__requires_manual_review(
    openrouter_service: OpenRouterService, mock_product_repository: Mock
):
    """Test verify_ingredients without product_id requires manual review."""
    # Arrange
    analysis_items = [
        AnalysisItem(
            ingredient_name="unknown food",
            amount_grams=Decimal("100"),
            macros=MacroProfile(
                calories=Decimal("100"),
                protein=Decimal("5"),
                carbs=Decimal("10"),
                fat=Decimal("5"),
            ),
            product_id=None,  # No product reference
        )
    ]

    # Act
    results = await openrouter_service.verify_ingredients_calories(analysis_items)

    # Assert
    assert len(results) == 1
    assert results[0].requires_manual_review is True
    assert "missing_product_reference" in results[0].issues
    assert results[0].product_id is None
    assert results[0].macro_delta is None


@pytest.mark.asyncio
async def test_verify_ingredients_calories__product_not_found__requires_manual_review(
    openrouter_service: OpenRouterService, mock_product_repository: Mock
):
    """Test verify_ingredients with product not found requires manual review."""
    # Arrange
    product_id = uuid4()

    analysis_items = [
        AnalysisItem(
            ingredient_name="food item",
            amount_grams=Decimal("100"),
            macros=MacroProfile(
                calories=Decimal("150"),
                protein=Decimal("10"),
                carbs=Decimal("15"),
                fat=Decimal("8"),
            ),
            product_id=product_id,
        )
    ]

    # Product not found in DB
    mock_product_repository.get_product_by_id.return_value = None

    # Act
    results = await openrouter_service.verify_ingredients_calories(analysis_items)

    # Assert
    assert len(results) == 1
    assert results[0].requires_manual_review is True
    assert "product_not_found" in results[0].issues
    assert results[0].macro_delta is None


@pytest.mark.asyncio
async def test_verify_ingredients_calories__macro_delta_exceeds_tolerance__requires_review(
    openrouter_service: OpenRouterService, mock_product_repository: Mock, now: datetime
):
    """Test verify_ingredients with macro delta >15% requires manual review."""
    # Arrange
    product_id = uuid4()

    # AI reports 200 calories, DB has 165 (21% difference - exceeds 15%)
    analysis_items = [
        AnalysisItem(
            ingredient_name="chicken breast",
            amount_grams=Decimal("100"),
            macros=MacroProfile(
                calories=Decimal("200"),  # AI estimate
                protein=Decimal("31"),
                carbs=Decimal("0"),
                fat=Decimal("3.6"),
            ),
            product_id=product_id,
        )
    ]

    product_dto = ProductSummaryDTO(
        id=product_id,
        name="Chicken breast, raw",
        source=ProductSource.USDA_SR_LEGACY,
        macros_per_100g=MacroBreakdownDTO(
            calories=Decimal("165"),  # Actual value
            protein=Decimal("31"),
            carbs=Decimal("0"),
            fat=Decimal("3.6"),
        ),
        created_at=now,
    )
    mock_product_repository.get_product_by_id.return_value = product_dto

    # Act
    results = await openrouter_service.verify_ingredients_calories(analysis_items)

    # Assert
    assert len(results) == 1
    assert results[0].requires_manual_review is True
    assert "macro_delta_exceeded" in results[0].issues

    # Verify delta was calculated
    assert results[0].macro_delta is not None
    assert results[0].macro_delta.calories_diff == Decimal("35.00")  # 200 - 165
    assert abs(results[0].macro_delta.calories_pct) > Decimal("15")  # >15%


@pytest.mark.asyncio
async def test_verify_ingredients_calories__all_macros_within_tolerance__no_review(
    openrouter_service: OpenRouterService, mock_product_repository: Mock, now: datetime
):
    """Test verify_ingredients with all macros within 15% tolerance passes review."""
    # Arrange
    product_id = uuid4()

    # AI reports 170 calories, DB has 165 (3% difference - within 15%)
    analysis_items = [
        AnalysisItem(
            ingredient_name="chicken breast",
            amount_grams=Decimal("100"),
            macros=MacroProfile(
                calories=Decimal("170"),
                protein=Decimal("32"),  # Slight variance
                carbs=Decimal("0"),
                fat=Decimal("3.8"),  # Slight variance
            ),
            product_id=product_id,
        )
    ]

    product_dto = ProductSummaryDTO(
        id=product_id,
        name="Chicken breast, raw",
        source=ProductSource.USDA_SR_LEGACY,
        macros_per_100g=MacroBreakdownDTO(
            calories=Decimal("165"),
            protein=Decimal("31"),
            carbs=Decimal("0"),
            fat=Decimal("3.6"),
        ),
        created_at=now,
    )
    mock_product_repository.get_product_by_id.return_value = product_dto

    # Act
    results = await openrouter_service.verify_ingredients_calories(analysis_items)

    # Assert
    assert len(results) == 1
    assert results[0].requires_manual_review is False
    assert len(results[0].issues) == 0


# =============================================================================
# Internal Helper Tests
# =============================================================================


def test_build_payload__default_model_and_parameters(openrouter_service: OpenRouterService):
    """Test _build_payload with default model and parameters."""
    # Arrange
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content="Test")]

    # Act
    payload = openrouter_service._build_payload(
        messages,
        model=None,
        response_format=None,
        metadata=None,
        temperature=None,
        top_p=None,
        max_output_tokens=None,
    )

    # Assert
    assert payload.model == "anthropic/claude-3-5-sonnet"  # Default from config
    assert payload.temperature == 0.7  # Default from config
    assert payload.top_p == 0.9  # Default from config
    assert payload.max_output_tokens == 4000  # Default from config
    assert len(payload.messages) == 1


def test_build_payload__empty_messages__raises_invalid_request_error(
    openrouter_service: OpenRouterService,
):
    """Test _build_payload with empty messages raises InvalidRequestError."""
    # Arrange
    messages = []

    # Act & Assert
    with pytest.raises(InvalidRequestError) as exc_info:
        openrouter_service._build_payload(
            messages,
            model=None,
            response_format=None,
            metadata=None,
            temperature=None,
            top_p=None,
            max_output_tokens=None,
        )

    assert "At least one message is required" in str(exc_info.value)
    assert exc_info.value.details["field"] == "messages"


def test_enforce_input_limits__exceeds_max_chars__raises_invalid_request_error(
    openrouter_service: OpenRouterService,
):
    """Test _enforce_input_limits with input exceeding max chars raises error."""
    # Arrange - create message that exceeds limit
    # max_input_tokens = 8192, so max_chars = 8192 * 4 = 32768
    long_content = "a" * 35000  # Exceeds 32768
    messages = [OpenRouterChatMessage(role=ChatRole.USER, content=long_content)]

    # Act & Assert
    with pytest.raises(InvalidRequestError) as exc_info:
        openrouter_service._enforce_input_limits(messages)

    assert "Input payload too large" in str(exc_info.value)
    assert "max_chars" in exc_info.value.details
    assert exc_info.value.details["max_chars"] == 32768


def test_scale_macros__correctly_scales_per_100g_to_amount(openrouter_service: OpenRouterService):
    """Test _scale_macros correctly scales per-100g macros to amount."""
    # Arrange
    macros_per_100g = MacroBreakdownDTO(
        calories=Decimal("165"),
        protein=Decimal("31"),
        carbs=Decimal("0"),
        fat=Decimal("3.6"),
    )
    amount_grams = Decimal("200")  # Double the base amount

    # Act
    result = openrouter_service._scale_macros(macros_per_100g, amount_grams)

    # Assert
    assert result.calories == Decimal("330")  # 165 * 2
    assert result.protein == Decimal("62")  # 31 * 2
    assert result.carbs == Decimal("0")  # 0 * 2
    assert result.fat == Decimal("7.2")  # 3.6 * 2


def test_compare_macros__calculates_deltas_and_percentages(openrouter_service: OpenRouterService):
    """Test _compare_macros calculates correct deltas and percentages."""
    # Arrange
    expected = MacroProfile(
        calories=Decimal("100"),
        protein=Decimal("20"),
        carbs=Decimal("10"),
        fat=Decimal("5"),
    )
    actual = MacroProfile(
        calories=Decimal("120"),  # +20% difference
        protein=Decimal("22"),  # +10% difference
        carbs=Decimal("10"),  # No difference
        fat=Decimal("6"),  # +20% difference
    )

    # Act
    result = openrouter_service._compare_macros(expected, actual)

    # Assert
    assert result.calories_diff == Decimal("20.00")
    assert result.calories_pct == Decimal("20.00")  # (120-100)/100 * 100 = 20%

    assert result.protein_diff == Decimal("2.00")
    assert result.protein_pct == Decimal("10.00")  # (22-20)/20 * 100 = 10%

    assert result.carbs_diff == Decimal("0.00")
    assert result.carbs_pct == Decimal("0.00")

    assert result.fat_diff == Decimal("1.00")
    assert result.fat_pct == Decimal("20.00")  # (6-5)/5 * 100 = 20%


def test_requires_review__detects_tolerance_violations(openrouter_service: OpenRouterService):
    """Test _requires_review detects when any macro exceeds 15% tolerance."""
    # Arrange - create delta with one macro exceeding tolerance
    from app.services.openrouter_service import MacroDelta

    delta_exceeds = MacroDelta(
        calories_diff=Decimal("10"),
        protein_diff=Decimal("2"),
        carbs_diff=Decimal("1"),
        fat_diff=Decimal("1"),
        calories_pct=Decimal("10.0"),  # Within tolerance
        protein_pct=Decimal("20.0"),  # Exceeds 15%
        carbs_pct=Decimal("5.0"),  # Within tolerance
        fat_pct=Decimal("10.0"),  # Within tolerance
    )

    delta_within = MacroDelta(
        calories_diff=Decimal("10"),
        protein_diff=Decimal("2"),
        carbs_diff=Decimal("1"),
        fat_diff=Decimal("1"),
        calories_pct=Decimal("10.0"),  # Within tolerance
        protein_pct=Decimal("10.0"),  # Within tolerance
        carbs_pct=Decimal("5.0"),  # Within tolerance
        fat_pct=Decimal("10.0"),  # Within tolerance
    )

    # Act & Assert
    assert openrouter_service._requires_review(delta_exceeds) is True
    assert openrouter_service._requires_review(delta_within) is False


def test_extract_error_message__from_various_response_formats(
    openrouter_service: OpenRouterService,
):
    """Test _extract_error_message extracts messages from different formats."""
    # Arrange & Act & Assert

    # Format 1: error.message
    response1 = Mock(spec=httpx.Response)
    response1.json.return_value = {"error": {"message": "Error message 1"}}
    response1.text = "Fallback text"
    assert openrouter_service._extract_error_message(response1) == "Error message 1"

    # Format 2: message
    response2 = Mock(spec=httpx.Response)
    response2.json.return_value = {"message": "Error message 2"}
    response2.text = "Fallback text"
    assert openrouter_service._extract_error_message(response2) == "Error message 2"

    # Format 3: Invalid JSON - use text
    response3 = Mock(spec=httpx.Response)
    response3.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
    response3.text = "Plain text error"
    assert openrouter_service._extract_error_message(response3) == "Plain text error"

    # Format 4: No message field
    response4 = Mock(spec=httpx.Response)
    response4.json.return_value = {"status": "error"}
    response4.text = "Fallback text"
    assert openrouter_service._extract_error_message(response4) is None

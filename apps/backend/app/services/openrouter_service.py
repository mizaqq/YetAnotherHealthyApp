"""Orchestrates interactions with the OpenRouter API and product verification."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID, uuid4

import httpx

from app.core.config import OpenRouterConfig, Settings
from app.db.repositories.product_repository import ProductRepository
from app.schemas.openrouter import (
    JsonSchemaResponseFormat,
    OpenRouterChatMessage,
    OpenRouterChatRequest,
    OpenRouterChatResponse,
    OpenRouterStreamChunk,
)
from app.services.openrouter_client import (
    OpenRouterClient,
    OpenRouterClientError,
    RetryableOpenRouterError,
)

logger = logging.getLogger(__name__)


class MetricsRecorder(Protocol):  # pragma: no cover - interface contract
    """Abstract metrics collector used for observability."""

    def record(self, name: str, value: float, *, tags: dict[str, str] | None = None) -> None: ...


class Tracer(Protocol):  # pragma: no cover - interface contract
    """Abstract tracer used to create spans for external calls."""

    def start_as_current_span(self, name: str): ...


class OpenRouterServiceError(RuntimeError):
    """Base class for OpenRouter related failures."""

    status_code: int = 500
    error_code: str = "openrouter_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class AuthorizationError(OpenRouterServiceError):
    status_code = 500
    error_code = "external_auth_error"


class RateLimitError(OpenRouterServiceError):
    status_code = 429
    error_code = "external_rate_limited"

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        details = {"retry_after": retry_after} if retry_after is not None else None
        super().__init__(message, details=details)
        self.retry_after = retry_after


class InvalidRequestError(OpenRouterServiceError):
    status_code = 400
    error_code = "external_invalid_request"


class ServiceUnavailableError(OpenRouterServiceError):
    status_code = 503
    error_code = "external_service_unavailable"


class ServiceDataError(OpenRouterServiceError):
    status_code = 500
    error_code = "external_data_error"


@dataclass(slots=True)
class MacroProfile:
    """Represents macronutrients for a particular quantity."""

    calories: Decimal
    protein: Decimal
    carbs: Decimal
    fat: Decimal


@dataclass(slots=True)
class MacroDelta:
    """Captures absolute and percentage delta for macronutrients."""

    calories_diff: Decimal
    protein_diff: Decimal
    carbs_diff: Decimal
    fat_diff: Decimal
    calories_pct: Decimal | None
    protein_pct: Decimal | None
    carbs_pct: Decimal | None
    fat_pct: Decimal | None


@dataclass(slots=True)
class IngredientVerificationResult:
    """Result of comparing model output against product database."""

    ingredient_name: str
    product_id: UUID | None
    requires_manual_review: bool
    macro_delta: MacroDelta | None
    issues: list[str]


@dataclass(slots=True)
class AnalysisItem:
    """Normalized analysis item returned by AI layer."""

    ingredient_name: str
    amount_grams: Decimal
    macros: MacroProfile
    product_id: UUID | None = None
    confidence: Decimal | None = None


class OpenRouterService:
    """High level API for calling OpenRouter and validating responses."""

    _CHAT_PATH = "/chat/completions"
    _STREAM_BOUNDARY = "\n\n"
    _DEFAULT_INPUT_CHAR_LIMIT = 8192
    _MACRO_TOLERANCE_PERCENT = Decimal("15")

    def __init__(
        self,
        settings: Settings,
        client: OpenRouterClient,
        product_repository: ProductRepository,
        *,
        logger_: logging.Logger | None = None,
        metrics: MetricsRecorder | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self._settings = settings
        self._config: OpenRouterConfig = settings.openrouter
        self._client = client
        self._products = product_repository
        self._logger = logger_ or logging.getLogger("app.services.openrouter")
        self._metrics = metrics
        self._tracer = tracer
        self._default_params = {
            "temperature": self._config.default_temperature,
            "top_p": self._config.default_top_p,
            "max_output_tokens": self._config.max_output_tokens,
        }

    @property
    def default_params(self) -> dict[str, float | int]:
        """Expose immutable defaults used for chat completions."""

        return dict(self._default_params)

    async def generate_chat_completion(
        self,
        messages: Sequence[OpenRouterChatMessage | dict[str, Any]],
        *,
        model: str | None = None,
        response_format: JsonSchemaResponseFormat | dict[str, Any] | None = None,
        user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> OpenRouterChatResponse:
        """Call OpenRouter chat completion endpoint using validated payload."""

        request_payload = self._build_payload(
            messages,
            model=model,
            response_format=response_format,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
        )

        headers = self._build_headers(user_id=user_id)

        self._record_metric("openrouter.request", 1.0, tags={"model": request_payload.model})

        with self._maybe_trace("openrouter.chat_completion"):
            try:
                response = await self._client.post(
                    self._CHAT_PATH,
                    json=request_payload.model_dump(exclude_none=True),
                    headers=headers,
                )
                logging.info(response.content)
            except RetryableOpenRouterError as exc:  # pragma: no cover - network failure path
                self._logger.warning("OpenRouter transient error: %s", exc)
                raise ServiceUnavailableError("OpenRouter temporarily unavailable") from exc
            except OpenRouterClientError as exc:  # pragma: no cover - client failure path
                self._logger.error("OpenRouter client error: %s", exc, exc_info=True)
                raise ServiceUnavailableError("OpenRouter request failed") from exc

        if response.status_code >= 400:
            raise self._map_openrouter_error(response)

        parsed = self._parse_response(response)
        self._record_metric(
            "openrouter.tokens.total",
            float(parsed.usage.total_tokens) if parsed.usage else 0.0,
            tags={"model": parsed.model},
        )

        return parsed

    async def stream_chat_completion(
        self,
        messages: Sequence[OpenRouterChatMessage | dict[str, Any]],
        *,
        model: str | None = None,
        response_format: JsonSchemaResponseFormat | dict[str, Any] | None = None,
        user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[OpenRouterStreamChunk]:
        """Stream chat completion chunks as they arrive from OpenRouter."""

        request_payload = self._build_payload(
            messages,
            model=model,
            response_format=response_format,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
        )

        headers = self._build_headers(user_id=user_id)

        buffer = ""

        with self._maybe_trace("openrouter.chat_completion.stream"):
            try:
                stream = self._client.stream_post(
                    self._CHAT_PATH,
                    json=request_payload.model_dump(exclude_none=True),
                    headers=headers,
                )
                async for chunk in stream:
                    decoded = chunk.decode("utf-8", errors="ignore")
                    buffer += decoded
                    for parsed_chunk in self._parse_stream_buffer(buffer):
                        yield parsed_chunk
                    # Retain incomplete frame in buffer
                    buffer = self._retain_tail(buffer)
            except RetryableOpenRouterError as exc:  # pragma: no cover - network failure path
                self._logger.warning("OpenRouter transient streaming error: %s", exc)
                raise ServiceUnavailableError("OpenRouter temporarily unavailable") from exc
            except OpenRouterClientError as exc:  # pragma: no cover - client failure path
                self._logger.error("OpenRouter client stream error: %s", exc, exc_info=True)
                raise ServiceUnavailableError("OpenRouter request failed") from exc

    async def verify_ingredients_calories(
        self,
        analysis_items: Iterable[AnalysisItem],
    ) -> list[IngredientVerificationResult]:
        """Compare AI-provided macros with authoritative product data."""

        results: list[IngredientVerificationResult] = []
        for item in analysis_items:
            product = None
            issues: list[str] = []
            requires_review = False

            if item.product_id is None:
                issues.append("missing_product_reference")
                requires_review = True
            else:
                try:
                    product = self._products.get_product_by_id(item.product_id, include_portions=False)
                except Exception as exc:  # pragma: no cover - supabase error path
                    self._logger.error(
                        "Failed to fetch product for verification", exc_info=True, extra={"product_id": str(item.product_id)}
                    )
                    raise ServiceUnavailableError("Unable to validate ingredients against product database") from exc

                if product is None:
                    issues.append("product_not_found")
                    requires_review = True

            macro_delta: MacroDelta | None = None
            if product is not None:
                expected = self._scale_macros(product.macros_per_100g, item.amount_grams)
                macro_delta = self._compare_macros(expected, item.macros)
                if self._requires_review(macro_delta):
                    requires_review = True
                    issues.append("macro_delta_exceeded")

            results.append(
                IngredientVerificationResult(
                    ingredient_name=item.ingredient_name,
                    product_id=item.product_id,
                    requires_manual_review=requires_review,
                    macro_delta=macro_delta,
                    issues=issues,
                )
            )

        return results

    def _build_payload(
        self,
        messages: Sequence[OpenRouterChatMessage | dict[str, Any]],
        *,
        model: str | None,
        response_format: JsonSchemaResponseFormat | dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        temperature: float | None,
        top_p: float | None,
        max_output_tokens: int | None,
    ) -> OpenRouterChatRequest:
        normalized_messages = [self._coerce_message(message) for message in messages]
        if not normalized_messages:
            raise InvalidRequestError("At least one message is required", details={"field": "messages"})

        self._enforce_input_limits(normalized_messages)

        format_model: JsonSchemaResponseFormat | None
        if response_format is None:
            format_model = None
        elif isinstance(response_format, JsonSchemaResponseFormat):
            format_model = response_format
        elif isinstance(response_format, dict):
            format_model = JsonSchemaResponseFormat.model_validate(response_format)
        else:
            raise InvalidRequestError("Unsupported response_format type")

        payload = OpenRouterChatRequest(
            model=model or self._config.default_model,
            messages=normalized_messages,
            response_format=format_model,
            metadata=metadata,
            temperature=temperature or self._default_params["temperature"],
            top_p=top_p or self._default_params["top_p"],
            max_output_tokens=max_output_tokens or self._default_params["max_output_tokens"],
        )

        return payload

    def _coerce_message(self, message: OpenRouterChatMessage | dict[str, Any]) -> OpenRouterChatMessage:
        if isinstance(message, OpenRouterChatMessage):
            return message
        if not isinstance(message, dict):
            raise InvalidRequestError("Message must be a dict or OpenRouterChatMessage")
        return OpenRouterChatMessage.model_validate(message)

    def _enforce_input_limits(self, messages: Sequence[OpenRouterChatMessage]) -> None:
        char_limit = self._config.max_input_tokens
        if char_limit is None:
            max_chars = self._DEFAULT_INPUT_CHAR_LIMIT
        else:
            max_chars = int(char_limit * 4)

        total_chars = sum(len(message.content) for message in messages)
        if total_chars > max_chars:
            raise InvalidRequestError(
                "Input payload too large",
                details={"max_chars": max_chars, "current": total_chars},
            )

    def _build_headers(self, *, user_id: UUID | None) -> dict[str, str]:
        headers: dict[str, str] = {
            "X-Session-Id": str(uuid4()),
        }
        if user_id is not None:
            headers["X-User-Id"] = str(user_id)
        return headers

    def _parse_response(self, response: httpx.Response) -> OpenRouterChatResponse:
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            self._logger.error("Failed to decode OpenRouter response", exc_info=True)
            raise ServiceDataError("Invalid JSON returned by OpenRouter") from exc

        try:
            return OpenRouterChatResponse.model_validate(body)
        except Exception as exc:
            self._logger.error("Failed to validate OpenRouter response", exc_info=True, extra={"body": body})
            raise ServiceDataError("OpenRouter response validation failed") from exc

    def _parse_stream_buffer(self, buffer: str) -> Iterable[OpenRouterStreamChunk]:
        frames = buffer.split(self._STREAM_BOUNDARY)
        for frame in frames[:-1]:
            for line in frame.splitlines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    chunk_data = json.loads(payload)
                    yield OpenRouterStreamChunk.model_validate(chunk_data)
                except json.JSONDecodeError:
                    self._logger.warning("Dropped malformed stream chunk: %s", payload)
                except Exception as exc:  # pragma: no cover - invalid chunk path
                    self._logger.error("Stream chunk validation failed", exc_info=True, extra={"payload": payload})

    def _retain_tail(self, buffer: str) -> str:
        if buffer.endswith(self._STREAM_BOUNDARY):
            return ""
        tail = buffer.split(self._STREAM_BOUNDARY)[-1]
        return tail[-2048:]

    def _map_openrouter_error(self, response: httpx.Response) -> OpenRouterServiceError:
        retry_after = self._extract_retry_after(response)
        message = self._extract_error_message(response)
        status = response.status_code

        if status in (401, 403):
            return AuthorizationError(message or "OpenRouter authorization failed")
        if status == 429:
            return RateLimitError(message or "OpenRouter rate limited", retry_after=retry_after)
        if 400 <= status < 500:
            return InvalidRequestError(message or "OpenRouter rejected the request")
        return ServiceUnavailableError(message or "OpenRouter service error")

    def _extract_error_message(self, response: httpx.Response) -> str | None:
        try:
            body = response.json()
        except json.JSONDecodeError:
            return response.text[:200]

        if isinstance(body, dict):
            if "error" in body and isinstance(body["error"], dict):
                return str(body["error"].get("message"))
            if "message" in body:
                return str(body["message"])
        return None

    def _extract_retry_after(self, response: httpx.Response) -> float | None:
        header_value = response.headers.get("Retry-After")
        if not header_value:
            return None
        try:
            return float(header_value)
        except ValueError:
            return None

    def _record_metric(self, name: str, value: float, *, tags: dict[str, str] | None = None) -> None:
        if not self._metrics:  # pragma: no cover - telemetry optional
            return
        try:
            self._metrics.record(name, value, tags=tags)
        except Exception:  # pragma: no cover - defensive logging
            self._logger.warning("Failed to record metric", exc_info=True, extra={"metric": name})

    def _maybe_trace(self, span_name: str):
        if not self._tracer:  # pragma: no cover - tracing optional
            return _NullContext()
        return self._tracer.start_as_current_span(span_name)

    def _scale_macros(self, macros_per_100g: Any, amount_grams: Decimal) -> MacroProfile:
        """Convert per-100g macros to the requested amount."""

        if macros_per_100g is None:
            raise ServiceDataError("Product macros missing for verification")

        factor = amount_grams / Decimal("100")
        calories = Decimal(str(macros_per_100g.calories)) * factor
        protein = Decimal(str(macros_per_100g.protein)) * factor
        carbs = Decimal(str(macros_per_100g.carbs)) * factor
        fat = Decimal(str(macros_per_100g.fat)) * factor
        return MacroProfile(calories=calories, protein=protein, carbs=carbs, fat=fat)

    def _compare_macros(self, expected: MacroProfile, actual: MacroProfile) -> MacroDelta:
        def percent_delta(expected_value: Decimal, actual_value: Decimal) -> Decimal | None:
            if expected_value == 0:
                return None
            return ((actual_value - expected_value) / expected_value * Decimal("100")).quantize(Decimal("0.01"))

        calories_diff = (actual.calories - expected.calories).quantize(Decimal("0.01"))
        protein_diff = (actual.protein - expected.protein).quantize(Decimal("0.01"))
        carbs_diff = (actual.carbs - expected.carbs).quantize(Decimal("0.01"))
        fat_diff = (actual.fat - expected.fat).quantize(Decimal("0.01"))

        return MacroDelta(
            calories_diff=calories_diff,
            protein_diff=protein_diff,
            carbs_diff=carbs_diff,
            fat_diff=fat_diff,
            calories_pct=percent_delta(expected.calories, actual.calories),
            protein_pct=percent_delta(expected.protein, actual.protein),
            carbs_pct=percent_delta(expected.carbs, actual.carbs),
            fat_pct=percent_delta(expected.fat, actual.fat),
        )

    def _requires_review(self, delta: MacroDelta) -> bool:
        return any(
            pct is not None and abs(pct) > self._MACRO_TOLERANCE_PERCENT
            for pct in (
                delta.calories_pct,
                delta.protein_pct,
                delta.carbs_pct,
                delta.fat_pct,
            )
        )


class _NullContext:
    """Fallback context manager used when tracing is disabled."""

    def __enter__(self):  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover - trivial
        return False

    async def __aenter__(self):  # pragma: no cover - trivial
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover - trivial
        return False
"""HTTP client wrapper for communicating with the OpenRouter API."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import OpenRouterConfig

logger = logging.getLogger(__name__)


class OpenRouterClientError(RuntimeError):
    """Non-retryable failure reported by the OpenRouter client."""


class RetryableOpenRouterError(OpenRouterClientError):
    """Transient failure eligible for a retry."""

    def __init__(self, response: httpx.Response, body: str | None = None):
        message = f"Transient OpenRouter error: HTTP {response.status_code}"
        super().__init__(message)
        self.response = response
        self.body = body
        self.retry_after_seconds = _parse_retry_after(response)


class OpenRouterClient:
    """Thin wrapper around httpx.AsyncClient with retry semantics for OpenRouter."""

    _retry_status_codes = {429, 500, 502, 503, 504}

    def __init__(self, config: OpenRouterConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=str(config.base_url),
            headers=self._build_base_headers(config),
            timeout=config.request_timeout_seconds,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute a POST request with retry handling."""

        merged_headers = self._merge_headers(headers)
        retrying = self._retrying()
        async for attempt in retrying:
            with attempt:
                try:
                    response = await self._client.post(path, json=json, headers=merged_headers)
                    body_preview = (await response.aread())[:1000].decode("utf-8", errors="replace")
                    logger.info(
                        "OpenRouter response received",
                        extra={
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type"),
                            "body_preview": body_preview,
                        },
                    )
                except httpx.RequestError as exc:
                    logger.warning("OpenRouter network error: %s", exc, exc_info=True)
                    raise RetryableOpenRouterError(_fabricate_response(exc)) from exc

                if response.status_code in self._retry_status_codes:
                    body_text = await _consume_body(response)
                    logger.warning(
                        f"OpenRouter response body: {response.status_code} {response.content}"
                    )
                    logger.warning(
                        "OpenRouter returned retryable error",
                        extra={
                            "status_code": response.status_code,
                            "body": body_text[:500],
                            "retry_after": _parse_retry_after(response),
                        },
                    )
                    error = RetryableOpenRouterError(response, body=body_text)
                    if error.retry_after_seconds is not None:
                        await asyncio.sleep(error.retry_after_seconds)
                    raise error

                return response

        raise OpenRouterClientError("Exhausted retries calling OpenRouter")

    async def stream_post(
        self,
        path: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[bytes]:
        """Execute a streaming POST request with retry handling."""

        merged_headers = self._merge_headers(headers)
        retrying = self._retrying()
        async for attempt in retrying:
            with attempt:
                try:
                    async with self._client.stream(
                        "POST",
                        path,
                        json=json,
                        headers=merged_headers,
                    ) as response:
                        if response.status_code in self._retry_status_codes:
                            body_text = await _consume_body(response)
                            error = RetryableOpenRouterError(response, body=body_text)
                            if error.retry_after_seconds is not None:
                                await asyncio.sleep(error.retry_after_seconds)
                            raise error

                        async for chunk in response.aiter_bytes():
                            if chunk:
                                yield chunk
                        return
                except httpx.RequestError as exc:
                    logger.warning("OpenRouter network error during stream: %s", exc, exc_info=True)
                    raise RetryableOpenRouterError(_fabricate_response(exc)) from exc

        raise OpenRouterClientError("Exhausted retries streaming from OpenRouter")

    def _merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        merged = dict(self._client.headers)
        if headers:
            merged.update(headers)
        return merged

    def _retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            stop=stop_after_attempt(self._config.max_retries + 1),
            wait=_retry_wait(self._config),
            retry=retry_if_exception_type(RetryableOpenRouterError),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )

    @staticmethod
    def _build_base_headers(config: OpenRouterConfig) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {config.api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "X-Title": config.http_title or "YetAnotherHealthyApp Backend",
        }

        if config.http_referer:
            headers["HTTP-Referer"] = str(config.http_referer)

        return headers

    async def __aenter__(self) -> OpenRouterClient:  # pragma: no cover - convenience
        return self

    async def __aexit__(self, *exc_info: Any) -> None:  # pragma: no cover - convenience
        await self.aclose()


async def _consume_body(response: httpx.Response) -> str:
    body_bytes = await response.aread()
    return body_bytes.decode("utf-8", errors="replace")


def _retry_wait(config: OpenRouterConfig) -> wait_exponential:
    return wait_exponential(
        multiplier=config.retry_backoff_initial,
        max=config.retry_backoff_max,
        exp_base=2,
    )


def _parse_retry_after(response: httpx.Response) -> float | None:
    header_value = response.headers.get("retry-after")
    if not header_value:
        return None

    try:
        return float(header_value)
    except ValueError:
        return None


def _fabricate_response(exc: httpx.RequestError) -> httpx.Response:
    return httpx.Response(599, request=exc.request)


__all__ = [
    "OpenRouterClient",
    "OpenRouterClientError",
    "RetryableOpenRouterError",
]

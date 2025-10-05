"""Domain exceptions and HTTP error mapping."""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str, code: str, details: dict[str, Any] | None = None) -> None:
        """Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Optional additional context
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class RetrievalError(DomainException):
    """Error during food retrieval/search."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize retrieval error."""
        super().__init__(message, "RETRIEVAL_ERROR", details)


class LLMError(DomainException):
    """Error during LLM parsing/clarification."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize LLM error."""
        super().__init__(message, "LLM_ERROR", details)


class NormalizationError(DomainException):
    """Error during quantity normalization."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize normalization error."""
        super().__init__(message, "NORMALIZATION_ERROR", details)


class PersistenceError(DomainException):
    """Error during database operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize persistence error."""
        super().__init__(message, "PERSISTENCE_ERROR", details)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle domain exceptions and map to HTTP responses.

    Args:
        request: The incoming request
        exc: The domain exception

    Returns:
        JSON response with error details
    """
    # Map domain exceptions to HTTP status codes
    status_map = {
        "RETRIEVAL_ERROR": status.HTTP_502_BAD_GATEWAY,
        "LLM_ERROR": status.HTTP_502_BAD_GATEWAY,
        "NORMALIZATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "PERSISTENCE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
    }

    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details if exc.details else None,
            }
        },
    )

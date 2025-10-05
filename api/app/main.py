"""FastAPI main application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import foods, log, match, parse, summary
from app.core.exceptions import DomainException, domain_exception_handler
from app.core.logging import LoggingMiddleware, configure_logging
from app.core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events.

    Args:
        app: FastAPI application instance

    Yields:
        None during application lifetime
    """
    settings = get_settings()

    # Startup
    configure_logging(settings.env)

    yield

    # Shutdown
    # Close any open connections here in future


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    settings = get_settings()

    # OpenAPI tags metadata for better organization
    tags_metadata = [
        {
            "name": "parse",
            "description": "Parse natural language food descriptions into structured items.",
        },
        {
            "name": "match",
            "description": "Match parsed food items against the foods database using hybrid search.",
        },
        {
            "name": "log",
            "description": "Log consumed meals with computed macronutrients.",
        },
        {
            "name": "summary",
            "description": "Retrieve daily meal summaries with aggregated nutrition data.",
        },
        {
            "name": "foods",
            "description": "Search and browse the foods database.",
        },
        {
            "name": "health",
            "description": "Health check and service status endpoints.",
        },
    ]

    app = FastAPI(
        title="Calorie Intake Logger API",
        description="""
## Overview

Backend API for the Calorie Intake Logger PoC. This API enables users to:

- **Parse** natural language food descriptions (Polish) into structured items
- **Match** food items against a comprehensive nutritional database
- **Log** meals with automatic macro calculation
- **Retrieve** daily summaries with nutrition totals

## Architecture

The API follows a multi-stage pipeline:

1. **Parse**: LLM extracts structured food items from text
2. **Match**: Hybrid search (BM25 + k-NN) finds database matches
3. **Log**: Store meals with computed macronutrients
4. **Summary**: Aggregate daily nutrition data

## Authentication

Most endpoints require authentication via Bearer token (future implementation).

## Response Format

All responses include:
- `requestId`: Unique identifier for request tracing
- `durationMs`: Request processing time
- Standard error envelope for consistent error handling
        """,
        version="0.1.0",
        openapi_tags=tags_metadata,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        contact={
            "name": "API Support",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT",
        },
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware
    app.add_middleware(LoggingMiddleware)

    # Exception handlers
    app.add_exception_handler(DomainException, domain_exception_handler)

    # Include routers
    app.include_router(parse.router, prefix=settings.api_v1_prefix)
    app.include_router(match.router, prefix=settings.api_v1_prefix)
    app.include_router(log.router, prefix=settings.api_v1_prefix)
    app.include_router(summary.router, prefix=settings.api_v1_prefix)
    app.include_router(foods.router, prefix=settings.api_v1_prefix)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Status information
        """
        return {"status": "ok", "version": "0.1.0"}

    return app


# Create app instance
app = create_app()

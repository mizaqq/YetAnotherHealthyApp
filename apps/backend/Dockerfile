# ================================
# Stage 1: Builder
# ================================
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (syncs from lock file for reproducibility)
# --no-dev excludes development dependencies for production
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

# ================================
# Stage 2: Runtime
# ================================
FROM python:3.13-slim AS runtime

# Build arguments for metadata
ARG APP_VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF

# Metadata labels following OCI standards
LABEL org.opencontainers.image.title="YetAnotherHealthyApp Backend" \
      org.opencontainers.image.description="FastAPI backend for meal tracking and macro monitoring" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="YetAnotherHealthyApp" \
      maintainer="YetAnotherHealthyApp Team"

# Environment variables for production
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies only (curl for health checks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment and application from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

# Switch to non-root user
USER appuser

# Expose port 8000 (FastAPI default)
EXPOSE 8000

# Health check to verify application is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run uvicorn with production settings
# --host 0.0.0.0: Listen on all interfaces (required for Docker)
# --port 8000: Default FastAPI port
# --workers 1: Single worker (scale with container replicas instead)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


#!/bin/bash

# Docker Run Script for YetAnotherHealthyApp Backend
# Usage: ./docker-run.sh [IMAGE_NAME:TAG]

set -e

# Configuration
IMAGE="${1:-yetanotherhealthyapp-backend:latest}"
CONTAINER_NAME="yetanotherhealthyapp-backend"
HOST_PORT="8000"
CONTAINER_PORT="8000"

echo "================================================"
echo "Running YetAnotherHealthyApp Backend Container"
echo "================================================"
echo "Image: ${IMAGE}"
echo "Container Name: ${CONTAINER_NAME}"
echo "Port Mapping: ${HOST_PORT}:${CONTAINER_PORT}"
echo "================================================"

# Check if .env file exists for loading secrets
if [ -f .env.production ]; then
    echo "Loading environment from .env.production"
    ENV_FILE=".env.production"
elif [ -f .env ]; then
    echo "Loading environment from .env"
    ENV_FILE=".env"
else
    echo "WARNING: No .env file found. You must provide environment variables manually."
    ENV_FILE=""
fi

# Stop and remove existing container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and removing existing container..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Run the container
if [ -n "$ENV_FILE" ]; then
    # Run with env file
    docker run -d \
      --name "${CONTAINER_NAME}" \
      --env-file "${ENV_FILE}" \
      -e APP_ENV=production \
      -p "${HOST_PORT}:${CONTAINER_PORT}" \
      --memory="512m" \
      --cpus="1.0" \
      --restart=unless-stopped \
      "${IMAGE}"
else
    # Run with example environment variables (REPLACE WITH YOUR ACTUAL VALUES)
    echo ""
    echo "IMPORTANT: Replace the placeholder values below with your actual credentials!"
    echo ""
    docker run -d \
      --name "${CONTAINER_NAME}" \
      -e APP_ENV=production \
      -e SUPABASE_URL=https://your-project.supabase.co \
      -e SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key \
      -e OPENROUTER_API_KEY=your_actual_openrouter_key \
      -e CORS_ORIGINS='["https://your-frontend-domain.com"]' \
      -e LOG_LEVEL=INFO \
      -p "${HOST_PORT}:${CONTAINER_PORT}" \
      --memory="512m" \
      --cpus="1.0" \
      --restart=unless-stopped \
      "${IMAGE}"
fi

echo "================================================"
echo "Container started successfully!"
echo "================================================"
echo ""
echo "Container Status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "View logs:"
echo "  docker logs -f ${CONTAINER_NAME}"
echo ""
echo "Health check:"
echo "  curl http://localhost:${HOST_PORT}/api/v1/health"
echo ""
echo "Stop container:"
echo "  docker stop ${CONTAINER_NAME}"
echo ""
echo "Remove container:"
echo "  docker rm ${CONTAINER_NAME}"
echo "================================================"

# Wait a few seconds and test health endpoint
echo ""
echo "Waiting for application to start..."
sleep 5

if curl -sf http://localhost:${HOST_PORT}/api/v1/health > /dev/null 2>&1; then
    echo "✓ Health check passed! Application is running."
else
    echo "✗ Health check failed. Check logs with: docker logs ${CONTAINER_NAME}"
    exit 1
fi


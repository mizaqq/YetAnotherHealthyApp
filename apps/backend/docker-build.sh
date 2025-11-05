#!/bin/bash

# Docker Build Script for YetAnotherHealthyApp Backend
# Usage: ./docker-build.sh [IMAGE_NAME] [TAG]

set -e

# Configuration
IMAGE_NAME="${1:-yetanotherhealthyapp-backend}"
TAG="${2:-latest}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
APP_VERSION="0.1.0"

# Enable BuildKit for better performance and caching
export DOCKER_BUILDKIT=1

echo "================================================"
echo "Building Docker Image"
echo "================================================"
echo "Image Name: ${IMAGE_NAME}"
echo "Tag: ${TAG}"
echo "Build Date: ${BUILD_DATE}"
echo "VCS Ref: ${VCS_REF}"
echo "App Version: ${APP_VERSION}"
echo "================================================"

# Build the image
docker build \
  --build-arg APP_VERSION="${APP_VERSION}" \
  --build-arg BUILD_DATE="${BUILD_DATE}" \
  --build-arg VCS_REF="${VCS_REF}" \
  --tag "${IMAGE_NAME}:${TAG}" \
  --tag "${IMAGE_NAME}:${VCS_REF}" \
  --file Dockerfile \
  .

echo "================================================"
echo "Build completed successfully!"
echo "================================================"
echo "Image tags created:"
echo "  - ${IMAGE_NAME}:${TAG}"
echo "  - ${IMAGE_NAME}:${VCS_REF}"
echo ""
echo "To run the container, use:"
echo "  ./docker-run.sh ${IMAGE_NAME}:${TAG}"
echo ""
echo "Or manually with:"
echo "  docker run -p 8000:8000 \\"
echo "    -e APP_ENV=production \\"
echo "    -e SUPABASE_URL=your_url \\"
echo "    -e SUPABASE_SERVICE_ROLE_KEY=your_key \\"
echo "    -e OPENROUTER_API_KEY=your_key \\"
echo "    ${IMAGE_NAME}:${TAG}"
echo "================================================"


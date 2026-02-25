# Build script for Revenue Forecast Sync Docker image

#!/bin/bash

set -e

DOCKER_REGISTRY="docker.io/strakertech"
IMAGE_NAME="revenue-forecast-sync"
TAG="${1:-latest}"

echo "Building Revenue Forecast Sync Docker image..."
echo "Registry: $DOCKER_REGISTRY"
echo "Image: $IMAGE_NAME"
echo "Tag: $TAG"

# Build the image
docker build -t "$DOCKER_REGISTRY/$IMAGE_NAME:$TAG" .

echo "Build completed successfully!"
echo "Image: $DOCKER_REGISTRY/$IMAGE_NAME:$TAG"

# Optional: Push to registry (uncomment if needed)
# echo "Pushing to registry..."
# docker push "$DOCKER_REGISTRY/$IMAGE_NAME:$TAG"
# echo "Push completed!"

echo ""
echo "To test locally:"
echo "docker run --rm -v \$(pwd)/config.ini:/app/config.ini $DOCKER_REGISTRY/$IMAGE_NAME:$TAG"
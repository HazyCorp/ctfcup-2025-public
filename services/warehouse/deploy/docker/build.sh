#!/bin/bash
# Docker build script for warehouse service
# Builds Docker images for k3s (which uses Docker runtime)
# Usage: ./build.sh

set -e

SERVICE_NAME="warehouse"
SERVICE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=========================================="
echo "Building Docker images for $SERVICE_NAME"
echo "=========================================="

cd "$SERVICE_DIR"

# Build function
build_image() {
  local dockerfile="$1"
  local image_name="$2"
  
  if [ ! -f "$dockerfile" ]; then
    echo "WARNING: Dockerfile not found: $dockerfile"
    return 1
  fi
  
  echo ""
  echo "Building: $dockerfile -> $image_name:latest"
  
  # Build Docker image
  # k3s with --docker flag uses Docker as runtime, so images are automatically available
  sudo docker build -f "$dockerfile" -t "${image_name}:latest" .
  
  echo "  ✓ Image built successfully: ${image_name}:latest"
}

# Build all Docker images
build_image "deploy/docker/warehouse.Dockerfile" "warehouse-warehouse"
build_image "deploy/docker/auth-server.Dockerfile" "warehouse-auth-server"
build_image "deploy/docker/gateway-server.Dockerfile" "warehouse-gateway-server"
build_image "deploy/docker/ti-server.Dockerfile" "warehouse-ti-server"

# List built images
echo ""
echo "Built images:"
sudo docker images | grep -E "^warehouse" || echo "  (images listed above)"

echo ""
echo "=========================================="
echo "Docker images built successfully"
echo "=========================================="
echo ""
echo "Note: k3s uses Docker runtime (--docker flag), so images are"
echo "automatically available to Kubernetes without import."

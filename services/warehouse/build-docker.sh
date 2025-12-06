#!/bin/bash
set -e

# Docker build script
# Usage: ./build-docker.sh [version]

VERSION="${1:-latest}"

echo "================================================"
echo "Building Docker images"
echo "================================================"
echo "Version: $VERSION"
echo "================================================"


# Check docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: docker not found"
    exit 1
fi

echo ""
echo "Building images with docker..."
echo "================================================"

# Build options
BUILD_OPTS="--network=host"

# Build ti-server
echo "Building ti-server..."
docker build $BUILD_OPTS -f deploy/docker/ti-server.Dockerfile -t warehouse-ti-server:$VERSION .

# Build auth-server
echo "Building auth-server..."
docker build $BUILD_OPTS -f deploy/docker/auth-server.Dockerfile -t warehouse-auth-server:$VERSION .

# Build warehouse
echo "Building warehouse..."
docker build $BUILD_OPTS -f deploy/docker/warehouse.Dockerfile -t warehouse-warehouse:$VERSION .

# Build gateway-server
echo "Building gateway-server..."
docker build $BUILD_OPTS -f deploy/docker/gateway-server.Dockerfile -t warehouse-gateway-server:$VERSION .

echo ""
echo "================================================"
echo "All images built successfully!"
echo "================================================"

# Show built images
echo ""
echo "Built images:"
docker images | grep -E "(REPOSITORY|ti-server|auth-server|warehouse|gateway-server)" | grep -E "(REPOSITORY|$VERSION)"

echo ""
echo "[+] Done"
echo ""

#!/bin/bash
set -e

echo "════════════════════════════════════════════════"
echo "  🧹 Cleaning up Prototype Service"
echo "════════════════════════════════════════════════"
echo ""

echo "🗑️  Uninstalling Helm release..."
helm uninstall prototype -n prototype 2>/dev/null || echo "Release not found, skipping..."

echo "🗑️  Deleting namespace..."
kubectl delete namespace prototype 2>/dev/null || echo "Namespace not found, skipping..."

echo "🗑️  Deleting k3d cluster..."
k3d cluster delete prototype-cluster 2>/dev/null || echo "Cluster not found, skipping..."

echo "🗑️  Removing Docker images..."
docker rmi prototype:latest 2>/dev/null || echo "Image not found, skipping..."

echo ""
echo "✅ Cleanup complete!"
echo ""


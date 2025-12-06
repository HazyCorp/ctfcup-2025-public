#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════"
echo "  🚀 Deploying Prototype Service"
echo "════════════════════════════════════════════════"
echo ""

# Check if cluster exists
if k3d cluster list | grep -q "prototype-cluster"; then
    echo "✅ Cluster 'prototype-cluster' already exists"
else
    echo "📦 Creating k3d cluster with load balancer..."
    k3d cluster create --config k3d-config.yaml
    
    echo "⏳ Waiting for API server..."
    sleep 5
    until kubectl get nodes 2>/dev/null; do
        echo "Waiting for API server to be ready..."
        sleep 2
    done
    
    
    echo "⏳ Waiting for nodes to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s
    
    echo "⏳ Waiting for Traefik to be deployed..."
    sleep 10  # Give time for Traefik Helm chart to deploy
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=traefik -n kube-system --timeout=90s 2>/dev/null || \
        echo "⚠️  Traefik not ready yet, continuing anyway..."
fi

echo ""
echo "📦 Building Docker image..."
docker build -t prototype:latest -f deploy/docker/Dockerfile .

echo ""
echo "📦 Importing image to k3d..."
k3d image import prototype:latest -c prototype-cluster

echo ""
echo "🎯 Deploying with Helm..."
# Note: All dependencies are now managed through Kubernetes:
# 1. MinIO secret is created via pre-install hook (hook-weight: -10)
# 2. CSI credentials sync Job runs via post-install hook (hook-weight: 1)
# 3. Deployment's init container waits for PVC to be bound
# This ensures proper order without manual bash scripting!
helm upgrade --install prototype ./deploy/chart \
  --create-namespace \
  --namespace prototype \
  --wait \
  --timeout 10m

echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/prototype -n prototype

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Deployment Complete!"
echo "════════════════════════════════════════════════"
echo ""
echo "🌐 Service is available at:"
echo "   http://localhost:30081/"
echo ""
echo "🎯 NodePort service (без Ingress)"
echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n prototype"
echo "   kubectl get svc -n prototype"
echo ""
echo "💡 Tips:"
echo "   • Открыть в браузере: open http://localhost:30081/"
echo "   • Посмотреть логи: kubectl logs -l app.kubernetes.io/name=prototype -n prototype -f"
echo "   • Удалить кластер: k3d cluster delete prototype-cluster"
echo ""


#!/bin/bash
set -e

NAMESPACE="${1:-warehouse}"
RELEASE_NAME="${2:-warehouse}"

# Set KUBECONFIG for k3s
if [ -f "/etc/rancher/k3s/k3s.yaml" ]; then
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
elif [ -f "$HOME/.kube/config" ]; then
    export KUBECONFIG=$HOME/.kube/config
fi

echo "Uninstalling release..."
helm uninstall $RELEASE_NAME -n $NAMESPACE 2>/dev/null || echo "Release not found, skipping uninstall"

echo "Deleting PVCs..."
kubectl delete pvc -n $NAMESPACE --all 2>/dev/null || echo "No PVCs found"

echo "Waiting for resources to be deleted..."
sleep 5

echo "Install release..."
helm upgrade -i $RELEASE_NAME ./deploy/chart --create-namespace -n $NAMESPACE --wait --timeout 5m

echo "Release $RELEASE_NAME deployed successfully!"

echo ""
echo "Step 3/3: Checking status..."
echo "================================================"

# Wait for pods to start
sleep 5

# Show status
echo ""
echo "Pod status:"
kubectl get pods -n $NAMESPACE

echo ""
echo "Service status:"
kubectl get svc -n $NAMESPACE

echo ""
echo "================================================"
echo "Deployment completed successfully!"
echo "================================================"

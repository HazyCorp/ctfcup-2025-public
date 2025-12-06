#!/bin/bash
# Setup script for archive Helm chart on k3s
# Called via cloud-init during VM provisioning
# Images are pre-built in Packer
# Usage: ./setup.sh <team_number>

set -e

# Set kubeconfig for k3s
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHART_DIR="$SCRIPT_DIR"
RELEASE_NAME="archive"
NAMESPACE="default"
TEAM_NUMBER="${1:-0}"

log_info() {
    echo "[INFO] [team-${TEAM_NUMBER}] $1"
}

log_error() {
    echo "[ERROR] [team-${TEAM_NUMBER}] $1" >&2
}

# Wait for k3s to be ready
wait_for_k3s() {
    log_info "Waiting for k3s to be ready..."
    local retries=60
    local count=0
    
    while [ $count -lt $retries ]; do
        if kubectl cluster-info &> /dev/null; then
            log_info "k3s is ready"
            return 0
        fi
        count=$((count + 1))
        sleep 5
    done
    
    log_error "Timeout waiting for k3s"
    return 1
}

# Install or upgrade the Helm chart
install_chart() {
    log_info "Installing Helm chart: $RELEASE_NAME"
    cd "$CHART_DIR"
    
    helm upgrade --install "$RELEASE_NAME" . \
        --namespace "$NAMESPACE" \
        --create-namespace \
        --set teamNumber="$TEAM_NUMBER" \
        --wait \
        --timeout 10m
    
    log_info "Helm chart installed successfully"
}

# Cleanup chart folder after successful setup
cleanup_chart() {
    log_info "Cleaning up chart folder..."
    cd /
    rm -rf "$CHART_DIR"
    log_info "Chart folder deleted"
}

# Main
main() {
    log_info "Starting archive chart setup..."
    
    wait_for_k3s
    install_chart
    cleanup_chart
    
    log_info "Setup complete"
}

main "$@"

#!/bin/bash
set -e

# Agent as a Service - Zero-Downtime Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]
# Example: ./scripts/deploy.sh production v2.0.0

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="aaas"
DEPLOYMENT_NAME="aaas-deployment"
SERVICE_NAME="aaas-service"
HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_WAIT_TIME=300  # 5 minutes
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_warn "Namespace $NAMESPACE does not exist, creating..."
        kubectl create namespace $NAMESPACE
    fi

    log_info "Prerequisites check passed"
}

# Backup current deployment
backup_deployment() {
    log_info "Backing up current deployment..."

    local backup_file="backups/deployment-backup-$(date +%Y%m%d-%H%M%S).yaml"
    mkdir -p backups

    if kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE &> /dev/null; then
        kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o yaml > $backup_file
        log_info "Backup saved to $backup_file"
        echo $backup_file > .last-backup
    else
        log_warn "No existing deployment to backup"
    fi
}

# Apply Kubernetes manifests
apply_manifests() {
    log_info "Applying Kubernetes manifests for $ENVIRONMENT..."

    # Apply namespace
    kubectl apply -f k8s/deployment.yaml

    # Apply ingress if exists
    if [ -f "k8s/ingress.yaml" ]; then
        kubectl apply -f k8s/ingress.yaml
    fi

    # Update image version
    kubectl set image deployment/$DEPLOYMENT_NAME \
        aaas=ghcr.io/wilbtc/agent-as-service:$VERSION \
        -n $NAMESPACE

    log_info "Manifests applied successfully"
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready (timeout: ${MAX_WAIT_TIME}s)..."

    if kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=${MAX_WAIT_TIME}s; then
        log_info "Deployment is ready"
        return 0
    else
        log_error "Deployment failed to become ready within ${MAX_WAIT_TIME}s"
        return 1
    fi
}

# Health check
health_check() {
    log_info "Running health checks..."

    local max_attempts=10
    local attempt=1

    # Port forward to service for health check
    kubectl port-forward -n $NAMESPACE service/$SERVICE_NAME 8000:80 &
    local port_forward_pid=$!
    sleep 5  # Wait for port-forward to establish

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"

        if curl -f -s $HEALTH_ENDPOINT > /dev/null; then
            local health_response=$(curl -s $HEALTH_ENDPOINT)
            local status=$(echo $health_response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

            if [ "$status" = "healthy" ]; then
                log_info "Health check passed: $health_response"
                kill $port_forward_pid 2>/dev/null || true
                return 0
            fi
        fi

        log_warn "Health check failed, retrying in 10s..."
        sleep 10
        attempt=$((attempt + 1))
    done

    kill $port_forward_pid 2>/dev/null || true
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback deployment
rollback_deployment() {
    log_warn "Rolling back deployment..."

    if [ -f ".last-backup" ]; then
        local backup_file=$(cat .last-backup)
        if [ -f "$backup_file" ]; then
            kubectl apply -f $backup_file
            kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=120s
            log_info "Rollback completed successfully"
            return 0
        fi
    fi

    # Fallback to kubectl rollout undo
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=120s
    log_info "Rollback completed using kubectl undo"
}

# Get deployment info
get_deployment_info() {
    log_info "Deployment information:"
    echo ""
    kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE
    echo ""
    kubectl get pods -n $NAMESPACE -l app=aaas
    echo ""
    kubectl get service $SERVICE_NAME -n $NAMESPACE
}

# Main deployment flow
main() {
    log_info "Starting deployment to $ENVIRONMENT (version: $VERSION)"
    echo ""

    # Pre-deployment checks
    check_prerequisites

    # Backup current state
    backup_deployment

    # Apply new manifests
    apply_manifests

    # Wait for deployment
    if ! wait_for_deployment; then
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            log_error "Deployment failed, initiating rollback..."
            rollback_deployment
            exit 1
        else
            log_error "Deployment failed"
            exit 1
        fi
    fi

    # Health check
    if ! health_check; then
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            log_error "Health check failed, initiating rollback..."
            rollback_deployment
            exit 1
        else
            log_error "Health check failed"
            exit 1
        fi
    fi

    # Success
    echo ""
    log_info "Deployment completed successfully! 🎉"
    echo ""
    get_deployment_info

    # Cleanup old backups (keep last 10)
    find backups/ -name "deployment-backup-*.yaml" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
}

# Run main deployment
main

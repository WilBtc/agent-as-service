#!/bin/bash
set -e

# Agent as a Service - Rollback Script
# Usage: ./scripts/rollback.sh [revision]
# Example: ./scripts/rollback.sh 2  (rollback to 2 revisions ago)

REVISION=${1:-1}
NAMESPACE="aaas"
DEPLOYMENT_NAME="aaas-deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Show rollout history
show_history() {
    log_info "Deployment history:"
    echo ""
    kubectl rollout history deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    echo ""
}

# Perform rollback
rollback() {
    log_warn "Rolling back deployment by $REVISION revision(s)..."

    if [ "$REVISION" -eq 1 ]; then
        # Simple undo
        kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    else
        # Get specific revision
        local target_revision=$(kubectl rollout history deployment/$DEPLOYMENT_NAME -n $NAMESPACE --revision=$REVISION)
        if [ -z "$target_revision" ]; then
            log_error "Revision $REVISION not found"
            exit 1
        fi
        kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE --to-revision=$REVISION
    fi

    # Wait for rollback to complete
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=120s

    log_info "Rollback completed successfully"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    # Port forward for health check
    kubectl port-forward -n $NAMESPACE service/aaas-service 8000:80 &
    local port_forward_pid=$!
    sleep 5

    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/health > /dev/null; then
            local health_response=$(curl -s http://localhost:8000/health)
            log_info "Health check passed: $health_response"
            kill $port_forward_pid 2>/dev/null || true
            return 0
        fi

        log_warn "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 5
        attempt=$((attempt + 1))
    done

    kill $port_forward_pid 2>/dev/null || true
    log_error "Health check failed after rollback"
    return 1
}

# Main
main() {
    log_warn "Starting rollback process..."
    echo ""

    show_history

    read -p "Are you sure you want to rollback? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    rollback

    if verify_rollback; then
        echo ""
        log_info "Rollback verified successfully! ✓"
        echo ""
        kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE
        kubectl get pods -n $NAMESPACE -l app=aaas
    else
        log_error "Rollback verification failed"
        exit 1
    fi
}

main

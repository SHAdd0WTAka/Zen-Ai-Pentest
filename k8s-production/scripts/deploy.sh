#!/bin/bash
# ============================================================================
# Zen-AI-Pentest Deployment Script
# Supports blue-green and canary deployment strategies
# ============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="zen-ai-pentest"
ENVIRONMENT="${ENVIRONMENT:-prod}"
DEPLOYMENT_STRATEGY="${DEPLOYMENT_STRATEGY:-rolling}"  # rolling, blue-green, canary
VERSION="${VERSION:-latest}"
TIMEOUT="${TIMEOUT:-600}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMMAND

Zen-AI-Pentest Deployment Script

Commands:
    deploy          Deploy the application
    rollback        Rollback to previous version
    status          Check deployment status
    validate        Validate Kubernetes manifests
    cleanup         Clean up old resources

Options:
    -e, --environment   Environment (dev, staging, prod) [default: prod]
    -s, --strategy      Deployment strategy (rolling, blue-green, canary) [default: rolling]
    -v, --version       Version to deploy [default: latest]
    -t, --timeout       Deployment timeout in seconds [default: 600]
    -n, --namespace     Kubernetes namespace [default: zen-ai-pentest]
    -h, --help          Show this help message

Examples:
    $0 deploy -e prod -v v1.0.0
    $0 deploy -e staging -s canary -v v1.1.0
    $0 rollback -e prod
    $0 status -e prod
EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--strategy)
                DEPLOYMENT_STRATEGY="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_error "kustomize is not installed"
        exit 1
    fi

    # Check helm (optional)
    if ! command -v helm &> /dev/null; then
        log_warning "helm is not installed (optional)"
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Validate manifests
validate_manifests() {
    log_info "Validating Kubernetes manifests..."

    local overlay_path="$PROJECT_ROOT/kubernetes/overlays/$ENVIRONMENT"

    if [[ ! -d "$overlay_path" ]]; then
        log_error "Overlay not found: $overlay_path"
        exit 1
    fi

    # Validate with kustomize
    if ! kustomize build "$overlay_path" > /dev/null 2>&1; then
        log_error "Kustomize build failed"
        exit 1
    fi

    # Validate with kubectl
    if ! kustomize build "$overlay_path" | kubectl apply --dry-run=client -f - > /dev/null 2>&1; then
        log_error "kubectl validation failed"
        exit 1
    fi

    log_success "Manifests validation passed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi

    # Check resource quotas
    local current_pods
    current_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    log_info "Current pods in namespace: $current_pods"

    # Check node capacity
    local node_count
    node_count=$(kubectl get nodes --no-headers | wc -l)
    log_info "Available nodes: $node_count"

    log_success "Pre-deployment checks passed"
}

# Rolling deployment
rolling_deploy() {
    log_info "Starting rolling deployment..."

    local overlay_path="$PROJECT_ROOT/kubernetes/overlays/$ENVIRONMENT"

    # Apply manifests
    log_info "Applying manifests from $overlay_path"
    kustomize build "$overlay_path" | kubectl apply -f -

    # Wait for rollout
    log_info "Waiting for deployments to complete..."

    local deployments
    deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    for deployment in $deployments; do
        log_info "Waiting for deployment: $deployment"
        if ! kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
            log_error "Rollout failed for: $deployment"
            return 1
        fi
    done

    log_success "Rolling deployment completed"
}

# Blue-green deployment
blue_green_deploy() {
    log_info "Starting blue-green deployment..."

    local blue_version
    blue_version=$(kubectl get deployment api-gateway -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
    local green_version="$VERSION"

    log_info "Current (blue) version: $blue_version"
    log_info "New (green) version: $green_version"

    # Deploy green version with different labels
    local overlay_path="$PROJECT_ROOT/kubernetes/overlays/$ENVIRONMENT"

    log_info "Deploying green version..."
    kustomize build "$overlay_path" | \
        sed "s/version: v1.0.0/version: $green_version/g" | \
        sed "s/app: zen-ai-pentest/app: zen-ai-pentest-green/g" | \
        kubectl apply -f -

    # Wait for green deployment
    log_info "Waiting for green deployment to be ready..."
    kubectl rollout status deployment/api-gateway-green -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    # Run smoke tests
    log_info "Running smoke tests on green deployment..."
    if ! run_smoke_tests "green"; then
        log_error "Smoke tests failed, rolling back..."
        kubectl delete deployment -l app=zen-ai-pentest-green -n "$NAMESPACE"
        return 1
    fi

    # Switch traffic to green
    log_info "Switching traffic to green deployment..."
    kubectl patch service api-gateway -n "$NAMESPACE" -p \
        '{"spec":{"selector":{"app":"zen-ai-pentest-green"}}}'

    # Wait and verify
    sleep 30

    # Delete blue deployment
    log_info "Deleting blue deployment..."
    kubectl delete deployment -l app=zen-ai-pentest,version!="$green_version" -n "$NAMESPACE"

    log_success "Blue-green deployment completed"
}

# Canary deployment
canary_deploy() {
    log_info "Starting canary deployment..."

    local overlay_path="$PROJECT_ROOT/kubernetes/overlays/$ENVIRONMENT"
    local canary_percentage="${CANARY_PERCENTAGE:-10}"

    log_info "Canary percentage: $canary_percentage%"

    # Deploy canary version
    log_info "Deploying canary version..."
    kustomize build "$overlay_path" | \
        sed "s/replicas: 3/replicas: 1/g" | \
        sed "s/app: zen-ai-pentest/app: zen-ai-pentest-canary/g" | \
        kubectl apply -f -

    # Wait for canary
    log_info "Waiting for canary deployment..."
    kubectl rollout status deployment/api-gateway-canary -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    # Configure canary ingress
    log_info "Configuring canary ingress..."
    kubectl annotate ingress api-gateway-ingress \
        nginx.ingress.kubernetes.io/canary="true" \
        nginx.ingress.kubernetes.io/canary-weight="$canary_percentage" \
        -n "$NAMESPACE"

    # Monitor metrics
    log_info "Monitoring canary metrics for 5 minutes..."
    sleep 300

    # Check error rate
    local error_rate
    error_rate=$(kubectl exec -it deployment/prometheus -n zen-monitoring -- \
        curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' 2>/dev/null | \
        jq -r '.data.result[0].value[1]' || echo "0")

    log_info "Canary error rate: $error_rate"

    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        log_error "Canary error rate too high, rolling back..."
        rollback_canary
        return 1
    fi

    # Promote canary to full deployment
    log_info "Promoting canary to full deployment..."
    kubectl annotate ingress api-gateway-ingress \
        nginx.ingress.kubernetes.io/canary- \
        nginx.ingress.kubernetes.io/canary-weight- \
        -n "$NAMESPACE"

    # Apply full deployment
    rolling_deploy

    # Delete canary
    kubectl delete deployment -l app=zen-ai-pentest-canary -n "$NAMESPACE"

    log_success "Canary deployment completed"
}

# Rollback canary
rollback_canary() {
    log_info "Rolling back canary..."

    kubectl annotate ingress api-gateway-ingress \
        nginx.ingress.kubernetes.io/canary- \
        nginx.ingress.kubernetes.io/canary-weight- \
        -n "$NAMESPACE"

    kubectl delete deployment -l app=zen-ai-pentest-canary -n "$NAMESPACE"
}

# Run smoke tests
run_smoke_tests() {
    local version="$1"
    log_info "Running smoke tests for version: $version"

    # Health check
    local health_status
    health_status=$(kubectl get pods -l app="zen-ai-pentest-$version" -n "$NAMESPACE" -o jsonpath='{.items[0].status.phase}')

    if [[ "$health_status" != "Running" ]]; then
        log_error "Health check failed"
        return 1
    fi

    # API check
    local api_status
    api_status=$(kubectl exec -it deployment/api-gateway-"$version" -n "$NAMESPACE" -- \
        curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")

    if [[ "$api_status" != "200" ]]; then
        log_error "API health check failed: $api_status"
        return 1
    fi

    log_success "Smoke tests passed"
    return 0
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."

    local deployments
    deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    for deployment in $deployments; do
        log_info "Rolling back: $deployment"
        kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE"
    done

    # Wait for rollback
    for deployment in $deployments; do
        kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${TIMEOUT}s"
    done

    log_success "Rollback completed"
}

# Check deployment status
status() {
    log_info "Checking deployment status..."

    echo ""
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    echo "=== Services ==="
    kubectl get services -n "$NAMESPACE"

    echo ""
    echo "=== Deployments ==="
    kubectl get deployments -n "$NAMESPACE"

    echo ""
    echo "=== Horizontal Pod Autoscalers ==="
    kubectl get hpa -n "$NAMESPACE"

    echo ""
    echo "=== Resource Quotas ==="
    kubectl get resourcequota -n "$NAMESPACE"

    echo ""
    echo "=== Events ==="
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -20
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."

    # Delete old ReplicaSets
    kubectl get replicasets -n "$NAMESPACE" --no-headers | \
        awk '$2==0 {print $1}' | \
        xargs -r kubectl delete replicasets -n "$NAMESPACE"

    # Delete old pods
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Succeeded,status.phase=Failed --no-headers | \
        awk '{print $1}' | \
        xargs -r kubectl delete pods -n "$NAMESPACE"

    log_success "Cleanup completed"
}

# Main function
main() {
    parse_args "$@"

    if [[ -z "${COMMAND:-}" ]]; then
        log_error "No command specified"
        usage
        exit 1
    fi

    case "$COMMAND" in
        deploy)
            check_prerequisites
            validate_manifests
            pre_deployment_checks

            case "$DEPLOYMENT_STRATEGY" in
                rolling)
                    rolling_deploy
                    ;;
                blue-green)
                    blue_green_deploy
                    ;;
                canary)
                    canary_deploy
                    ;;
                *)
                    log_error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
                    exit 1
                    ;;
            esac
            ;;
        rollback)
            check_prerequisites
            rollback
            ;;
        status)
            check_prerequisites
            status
            ;;
        validate)
            check_prerequisites
            validate_manifests
            ;;
        cleanup)
            check_prerequisites
            cleanup
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

main "$@"

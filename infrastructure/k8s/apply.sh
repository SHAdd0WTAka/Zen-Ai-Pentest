#!/bin/bash
#===============================================================================
# Zen-AI-Pentest Kubernetes Deployment Script
#===============================================================================

set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

NAMESPACE="zen-pentest"
ENVIRONMENT="production"
ACTION="apply"

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Environment (staging|production)
    -n, --namespace NS       Kubernetes namespace (default: zen-pentest)
    -a, --action ACTION      Action: apply|delete|status (default: apply)
    -h, --help               Show this help message

EXAMPLES:
    $0                           # Deploy to production
    $0 -e staging                # Deploy to staging
    $0 -a delete                 # Delete all resources
    $0 -a status                 # Check deployment status
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    if ! command -v kustomize &>/dev/null; then
        log_warning "kustomize not found. Trying kubectl kustomize..."
        if ! kubectl kustomize --help &>/dev/null; then
            log_error "kustomize support not available in kubectl"
            exit 1
        fi
    fi

    if ! kubectl cluster-info &>/dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

generate_secrets() {
    log_info "Generating secrets..."

    # Generate random passwords if not set
    if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
        export POSTGRES_PASSWORD=$(openssl rand -hex 32)
        log_info "Generated POSTGRES_PASSWORD"
    fi

    if [[ -z "${SECRET_KEY:-}" ]]; then
        export SECRET_KEY=$(openssl rand -hex 64)
        log_info "Generated SECRET_KEY"
    fi

    if [[ -z "${JWT_SECRET:-}" ]]; then
        export JWT_SECRET=$(openssl rand -hex 64)
        log_info "Generated JWT_SECRET"
    fi

    if [[ -z "${ENCRYPTION_KEY:-}" ]]; then
        export ENCRYPTION_KEY=$(openssl rand -hex 32)
        log_info "Generated ENCRYPTION_KEY"
    fi

    if [[ -z "${ADMIN_PASSWORD:-}" ]]; then
        export ADMIN_PASSWORD=$(openssl rand -hex 16)
        log_info "Generated ADMIN_PASSWORD: $ADMIN_PASSWORD"
        echo "Admin Password: $ADMIN_PASSWORD" > admin-password.txt
        chmod 600 admin-password.txt
    fi
}

apply_manifests() {
    log_info "Applying Kubernetes manifests..."

    cd "$(dirname "$0")"

    # Create namespace first
    kubectl apply -f namespace.yaml

    # Apply with kustomize
    if command -v kustomize &>/dev/null; then
        kustomize build . | kubectl apply -f -
    else
        kubectl apply -k .
    fi

    log_success "Manifests applied successfully"
}

wait_for_deployment() {
    log_info "Waiting for deployments to be ready..."

    kubectl wait --for=condition=available --timeout=300s \
        deployment/zen-pentest-api -n "$NAMESPACE" || true

    kubectl wait --for=condition=available --timeout=300s \
        deployment/zen-pentest-worker -n "$NAMESPACE" || true

    kubectl wait --for=condition=available --timeout=300s \
        deployment/zen-pentest-frontend -n "$NAMESPACE" || true

    log_success "Deployments are ready"
}

delete_resources() {
    log_warning "Deleting all resources..."

    cd "$(dirname "$0")"

    if command -v kustomize &>/dev/null; then
        kustomize build . | kubectl delete -f - --ignore-not-found=true
    else
        kubectl delete -k . --ignore-not-found=true
    fi

    # Delete namespace
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true

    log_success "Resources deleted"
}

show_status() {
    log_info "Deployment Status"
    log_info "================="

    echo -e "\n${YELLOW}Pods:${NC}"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo -e "\n${YELLOW}Services:${NC}"
    kubectl get svc -n "$NAMESPACE"

    echo -e "\n${YELLOW}Deployments:${NC}"
    kubectl get deployments -n "$NAMESPACE"

    echo -e "\n${YELLOW}Ingress:${NC}"
    kubectl get ingress -n "$NAMESPACE"

    echo -e "\n${YELLOW}Persistent Volume Claims:${NC}"
    kubectl get pvc -n "$NAMESPACE"

    echo -e "\n${YELLOW}Events (last 10):${NC}"
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
}

show_endpoints() {
    log_info "Service Endpoints"
    log_info "================="

    local ingress_ip
    ingress_ip=$(kubectl get ingress zen-pentest-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

    echo -e "\n${GREEN}Application URLs:${NC}"
    echo "  Web UI:     https://zenpentest.io (IP: $ingress_ip)"
    echo "  API:        https://api.zenpentest.io"
    echo "  API Docs:   https://api.zenpentest.io/docs"

    echo -e "\n${GREEN}Port-forward (for local access):${NC}"
    echo "  kubectl port-forward svc/zen-pentest-api 8000:8000 -n $NAMESPACE"
    echo "  kubectl port-forward svc/zen-pentest-frontend 3000:3000 -n $NAMESPACE"
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -a|--action)
                ACTION="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    case "$ACTION" in
        apply)
            check_prerequisites
            generate_secrets
            apply_manifests
            wait_for_deployment
            show_status
            show_endpoints
            ;;
        delete)
            delete_resources
            ;;
        status)
            show_status
            show_endpoints
            ;;
        *)
            log_error "Unknown action: $ACTION"
            usage
            exit 1
            ;;
    esac
}

main "$@"

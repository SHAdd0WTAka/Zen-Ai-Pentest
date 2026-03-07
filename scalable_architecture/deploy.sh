#!/bin/bash
# =============================================================================
# Zen-AI-Pentest Deployment Script
# Supports 100+ Concurrent Agents
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
MIN_DOCKER_VERSION="24.0"
MIN_COMPOSE_VERSION="2.20"

# =============================================================================
# Helper Functions
# =============================================================================

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

# =============================================================================
# Pre-flight Checks
# =============================================================================

check_docker() {
    log_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    if [ "$(printf '%s\n' "$MIN_DOCKER_VERSION" "$DOCKER_VERSION" | sort -V | head -n1)" != "$MIN_DOCKER_VERSION" ]; then
        log_error "Docker version $DOCKER_VERSION is too old. Minimum required: $MIN_DOCKER_VERSION"
        exit 1
    fi

    log_success "Docker version $DOCKER_VERSION is compatible"
}

check_docker_compose() {
    log_info "Checking Docker Compose installation..."

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if using 'docker compose' (v2) or 'docker-compose' (v1)
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short | grep -oP '\d+\.\d+' | head -1)
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_VERSION=$(docker-compose --version | grep -oP '\d+\.\d+' | head -1)
        COMPOSE_CMD="docker-compose"
    fi

    if [ "$(printf '%s\n' "$MIN_COMPOSE_VERSION" "$COMPOSE_VERSION" | sort -V | head -n1)" != "$MIN_COMPOSE_VERSION" ]; then
        log_warning "Docker Compose version $COMPOSE_VERSION may have compatibility issues. Recommended: $MIN_COMPOSE_VERSION+"
    fi

    log_success "Docker Compose version $COMPOSE_VERSION is available"
}

check_env_file() {
    log_info "Checking environment configuration..."

    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env file not found. Creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "Please edit .env file with your configuration before continuing"
            exit 1
        else
            log_error ".env.example not found. Cannot create configuration."
            exit 1
        fi
    fi

    # Source the env file for checks
    set -a
    source "$ENV_FILE"
    set +a

    # Check critical settings
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "change-me-in-production" ]; then
        log_error "JWT_SECRET is not set or using default value. Please set a secure secret in .env"
        exit 1
    fi

    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "zen_secure_password" ]; then
        log_error "POSTGRES_PASSWORD is not set or using default value. Please set a secure password in .env"
        exit 1
    fi

    log_success "Environment configuration is valid"
}

check_system_resources() {
    log_info "Checking system resources..."

    # Check available memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 16 ]; then
        log_warning "System has only ${TOTAL_MEM}GB RAM. Recommended: 32GB+ for 100 agents"
    else
        log_success "System has ${TOTAL_MEM}GB RAM"
    fi

    # Check available disk space
    DISK_AVAIL=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_AVAIL" -lt 50 ]; then
        log_warning "Only ${DISK_AVAIL}GB disk space available. Recommended: 100GB+"
    else
        log_success "Disk space: ${DISK_AVAIL}GB available"
    fi

    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 8 ]; then
        log_warning "System has only $CPU_CORES CPU cores. Recommended: 16+ for 100 agents"
    else
        log_success "System has $CPU_CORES CPU cores"
    fi
}

# =============================================================================
# Deployment Functions
# =============================================================================

deploy_infrastructure() {
    log_info "Deploying core infrastructure (Redis, PostgreSQL)..."

    $COMPOSE_CMD up -d redis postgres

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10

    # Check Redis
    if ! $COMPOSE_CMD exec -T redis redis-cli ping | grep -q "PONG"; then
        log_error "Redis is not responding"
        exit 1
    fi
    log_success "Redis is ready"

    # Check PostgreSQL
    if ! $COMPOSE_CMD exec -T postgres pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
        log_error "PostgreSQL is not ready"
        exit 1
    fi
    log_success "PostgreSQL is ready"
}

deploy_application() {
    log_info "Deploying application services..."

    # Build and start all services
    $COMPOSE_CMD up -d --build

    log_success "Application services deployed"
}

wait_for_health() {
    log_info "Waiting for services to be healthy..."

    MAX_RETRIES=30
    RETRY_INTERVAL=5

    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API Gateway is healthy"
            return 0
        fi
        log_info "Waiting for API Gateway... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done

    log_error "API Gateway failed to become healthy"
    return 1
}

scale_agents() {
    log_info "Scaling agents to initial capacity..."

    # Get MIN_AGENTS from env
    MIN_AGENTS=${MIN_AGENTS:-5}

    log_info "Starting with $MIN_AGENTS baseline agents"

    # Agents are started via docker-compose
    log_success "Agent pool initialized"
}

# =============================================================================
# Verification Functions
# =============================================================================

verify_deployment() {
    log_info "Verifying deployment..."

    # Check all services are running
    RUNNING_SERVICES=$($COMPOSE_CMD ps --filter "status=running" --format "{{.Name}}" | wc -l)
    log_info "Running services: $RUNNING_SERVICES"

    # Check API health
    API_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "{}")
    log_info "API Health: $API_HEALTH"

    # Check Redis
    REDIS_INFO=$($COMPOSE_CMD exec -T redis redis-cli info clients | grep connected_clients)
    log_info "Redis: $REDIS_INFO"

    log_success "Deployment verification complete"
}

# =============================================================================
# Utility Functions
# =============================================================================

show_status() {
    log_info "Current deployment status:"
    $COMPOSE_CMD ps
}

show_logs() {
    log_info "Showing logs (Ctrl+C to exit)..."
    $COMPOSE_CMD logs -f
}

cleanup() {
    log_warning "Cleaning up deployment..."
    $COMPOSE_CMD down
    log_success "Cleanup complete"
}

full_cleanup() {
    log_warning "Performing full cleanup (removes volumes)..."
    $COMPOSE_CMD down -v
    docker system prune -f
    log_success "Full cleanup complete"
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

deploy() {
    echo "========================================"
    echo "  Zen-AI-Pentest Deployment"
    echo "  Supporting 100+ Concurrent Agents"
    echo "========================================"
    echo ""

    check_docker
    check_docker_compose
    check_env_file
    check_system_resources

    echo ""
    log_info "Starting deployment..."
    echo ""

    deploy_infrastructure
    deploy_application
    wait_for_health
    scale_agents

    echo ""
    verify_deployment

    echo ""
    echo "========================================"
    log_success "Deployment completed successfully!"
    echo "========================================"
    echo ""
    echo "Access points:"
    echo "  API Gateway:    http://localhost:8000"
    echo "  Flower:         http://localhost:5555"
    echo "  Prometheus:     http://localhost:9090"
    echo "  Grafana:        http://localhost:3000"
    echo "  Jaeger:         http://localhost:16686"
    echo ""
    echo "Useful commands:"
    echo "  ./deploy.sh status    - Show service status"
    echo "  ./deploy.sh logs      - Show logs"
    echo "  ./deploy.sh cleanup   - Stop all services"
    echo ""
}

# =============================================================================
# Command Handler
# =============================================================================

case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    cleanup)
        cleanup
        ;;
    full-cleanup)
        full_cleanup
        ;;
    scale)
        if [ -z "$2" ]; then
            log_error "Usage: ./deploy.sh scale <number_of_agents>"
            exit 1
        fi
        log_info "Scaling agents to $2..."
        $COMPOSE_CMD up -d --scale agent-template="$2"
        log_success "Scaled to $2 agents"
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|cleanup|full-cleanup|scale <n>}"
        exit 1
        ;;
esac

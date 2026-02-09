#!/bin/bash
# =============================================================================
# Zen AI Pentest - Docker Setup Script
# =============================================================================
# Automates the Docker setup process for Zen AI Pentest
# Usage: ./scripts/docker-setup.sh [dev|prod|full]
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
MODE="${1:-dev}"

# Functions
print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         Zen AI Pentest - Docker Setup                      ║"
    echo "║                                                            ║"
    echo "║  Mode: $MODE                                               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Get versions
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker version: $DOCKER_VERSION"
    
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
        print_success "Docker Compose v2: $COMPOSE_VERSION"
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        print_success "Docker Compose: $COMPOSE_VERSION"
        COMPOSE_CMD="docker-compose"
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            print_success "Created $ENV_FILE from example"
        else
            print_warning ".env.example not found, creating minimal .env"
            cat > "$ENV_FILE" << EOF
ZEN_AI_ENV=$MODE
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
EOF
        fi
        print_warning "Please review and customize $ENV_FILE"
    else
        print_success "$ENV_FILE already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs evidence reports sessions data custom_modules
    mkdir -p secrets
    mkdir -p config
    
    # Set permissions
    chmod 700 secrets
    
    print_success "Directory structure created"
}

generate_secrets() {
    print_status "Generating secrets..."
    
    if [ ! -f "secrets/db_password.txt" ]; then
        openssl rand -base64 32 > secrets/db_password.txt
        chmod 600 secrets/db_password.txt
        print_success "Generated database password"
    fi
    
    if [ ! -f "secrets/redis_password.txt" ]; then
        openssl rand -base64 32 > secrets/redis_password.txt
        chmod 600 secrets/redis_password.txt
        print_success "Generated Redis password"
    fi
}

build_images() {
    print_status "Building Docker images..."
    
    case $MODE in
        dev)
            $COMPOSE_CMD -f $COMPOSE_FILE build --target development zen-ai-pentest
            ;;
        prod)
            $COMPOSE_CMD -f $COMPOSE_FILE build --target production zen-ai-pentest
            ;;
        full)
            $COMPOSE_CMD -f $COMPOSE_FILE build
            ;;
        *)
            print_error "Unknown mode: $MODE"
            exit 1
            ;;
    esac
    
    print_success "Images built successfully"
}

start_services() {
    print_status "Starting services..."
    
    case $MODE in
        dev)
            $COMPOSE_CMD -f $COMPOSE_FILE up -d zen-ai-pentest postgres redis
            ;;
        prod)
            $COMPOSE_CMD -f $COMPOSE_FILE up -d
            ;;
        full)
            $COMPOSE_CMD -f $COMPOSE_FILE --profile monitoring --profile proxy up -d
            ;;
    esac
    
    print_success "Services started"
}

wait_for_health() {
    print_status "Waiting for services to be healthy..."
    
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if $COMPOSE_CMD -f $COMPOSE_FILE ps | grep -q "healthy"; then
            print_success "All services are healthy"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 2
    done
    
    print_warning "Timeout waiting for services, check logs with: docker-compose logs"
    return 1
}

print_summary() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   Setup Complete!                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo "Services:"
    $COMPOSE_CMD -f $COMPOSE_FILE ps
    
    echo ""
    echo "Access Points:"
    echo "  - API:           http://localhost:8080"
    echo "  - API Docs:      http://localhost:8080/docs"
    echo "  - Health Check:  http://localhost:8080/health"
    
    if [ "$MODE" = "full" ]; then
        echo "  - Kibana:        http://localhost:5601"
        echo "  - Traefik:       http://localhost:8080/dashboard/"
    fi
    
    echo ""
    echo "Useful Commands:"
    echo "  View logs:       $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    echo "  Stop services:   $COMPOSE_CMD -f $COMPOSE_FILE down"
    echo "  Scale workers:   $COMPOSE_CMD -f $COMPOSE_FILE up -d --scale worker=3"
    echo ""
    echo "Documentation: https://github.com/SHAdd0WTAka/zen-ai-pentest/docs/DOCKER_SETUP.md"
}

# Main execution
main() {
    print_banner
    check_prerequisites
    setup_environment
    generate_secrets
    build_images
    start_services
    wait_for_health
    print_summary
}

main

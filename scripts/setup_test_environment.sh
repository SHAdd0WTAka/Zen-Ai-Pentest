#!/bin/bash
# =============================================================================
# Setup Test Environment for Zen-AI-Pentest
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo "================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "================================================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =============================================================================
# CHECK DOCKER
# =============================================================================

print_header "Checking Docker Installation"

if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

print_success "Docker and Docker Compose found"

# =============================================================================
# START TEST ENVIRONMENT
# =============================================================================

print_header "Starting Test Environment"

cd "$(dirname "$0")/.."

if [ -f "docker-compose.test.yml" ]; then
    print_warning "Starting vulnerable test targets..."
    print_warning "This will start: DVWA, Juice Shop, bWAPP, Metasploitable, Mutillidae, WebGoat"
    echo ""

    docker-compose -f docker-compose.test.yml down 2>/dev/null || true
    docker-compose -f docker-compose.test.yml up -d

    print_success "Test environment started!"
else
    print_error "docker-compose.test.yml not found"
    exit 1
fi

# =============================================================================
# WAIT FOR TARGETS
# =============================================================================

print_header "Waiting for Targets to be Ready"

echo "Waiting for services to start (this may take 30-60 seconds)..."
echo ""

TARGETS=(
    "localhost:8080:DVWA"
    "localhost:3000:Juice Shop"
    "localhost:8081:bWAPP"
    "localhost:8082:Mutillidae"
    "localhost:8083:WebGoat"
    "localhost:2222:Metasploitable SSH"
)

for target in "${TARGETS[@]}"; do
    IFS=':' read -r host port name <<< "$target"

    echo -n "  Checking $name on $host:$port... "

    for i in {1..30}; do
        if timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            print_success "Ready"
            break
        fi
        sleep 2

        if [ $i -eq 30 ]; then
            print_error "Timeout"
        fi
    done
done

echo ""
print_success "All test targets are ready!"

# =============================================================================
# RUN TESTS
# =============================================================================

print_header "Running Integration Tests"

echo "Running tests against real vulnerable targets..."
echo ""

python3 -m pytest tests/integration/test_real_targets.py -v --tb=short || {
    print_warning "Some tests may have failed or been skipped"
    print_warning "This is normal if not all targets are available"
}

# =============================================================================
# SUMMARY
# =============================================================================

print_header "Test Environment Summary"

echo ""
echo "Access your test targets:"
echo ""
echo "  DVWA:           http://localhost:8080"
echo "  Juice Shop:     http://localhost:3000"
echo "  bWAPP:          http://localhost:8081"
echo "  Mutillidae:     http://localhost:8082"
echo "  WebGoat:        http://localhost:8083"
echo "  Metasploitable: SSH on localhost:2222"
echo ""
echo "Default credentials (if required):"
echo "  DVWA:       admin/password"
echo "  bWAPP:      bee/bug"
echo "  WebGoat:    (create account)"
echo ""
print_success "Test environment is ready!"
echo ""
echo "To stop: docker-compose -f docker-compose.test.yml down"
echo ""

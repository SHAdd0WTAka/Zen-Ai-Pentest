#!/bin/bash
# API Test Skript

API_URL="${API_URL:-http://127.0.0.1:5000}"
API_KEY="${API_KEY:-}"

echo "🧪 Testing Kimi Personas API"
echo "URL: $API_URL"
echo "═══════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local desc=$4
    
    echo -n "Testing $desc... "
    
    if [ -n "$data" ]; then
        if [ -n "$API_KEY" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" \
                -X "$method" \
                -H "Content-Type: application/json" \
                -H "X-API-Key: $API_KEY" \
                -d "$data" \
                "$API_URL$endpoint")
        else
            response=$(curl -s -o /dev/null -w "%{http_code}" \
                -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_URL$endpoint")
        fi
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    fi
    
    if [ "$response" -ge 200 ] && [ "$response" -lt 300 ]; then
        echo -e "${GREEN}✓ HTTP $response${NC}"
    else
        echo -e "${RED}✗ HTTP $response${NC}"
    fi
}

# Tests
test_endpoint "GET" "/api/v1/health" "" "Health Check"
test_endpoint "GET" "/api/v1/personas" "" "List Personas"
test_endpoint "GET" "/api/v1/personas/recon" "" "Get Recon Persona"
test_endpoint "GET" "/api/v1/personas/categories" "" "List Categories"
test_endpoint "GET" "/api/v1/personas/redteam/prompt" "" "Get System Prompt"

# Chat test (requires auth)
if [ -n "$API_KEY" ]; then
    test_endpoint "POST" "/api/v1/chat" \
        '{"persona":"recon","message":"test"}' \
        "Chat Endpoint"
else
    echo "Skipping auth tests (no API_KEY set)"
fi

echo "═══════════════════════════════════════════════════════════════"
echo "Tests complete!"

#!/bin/bash

# Apply Branch Protection Script
# Usage: ./apply-branch-protection.sh <github_token> [branch_name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OWNER="SHAdd0WTAka"
REPO="zen-ai-pentest"
TOKEN="${1:-}"
BRANCH="${2:-master}"

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Error: GitHub Token required${NC}"
    echo ""
    echo "Usage:"
    echo "  ./apply-branch-protection.sh <github_token> [branch_name]"
    echo ""
    echo "Example:"
    echo "  ./apply-branch-protection.sh ghp_xxxxxxxxxxxx master"
    echo ""
    echo "Get your token at: https://github.com/settings/tokens"
    echo "Required scopes: repo (full control of private repositories)"
    exit 1
fi

echo -e "${BLUE}🔒 Applying Branch Protection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Repository: $OWNER/$REPO"
echo "Branch: $BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# API Endpoint
API_URL="https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection"

# Protection Configuration
PAYLOAD=$(cat <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "test (ubuntu-latest, 3.11)",
      "test (ubuntu-latest, 3.12)",
      "test (windows-latest, 3.11)",
      "Analyze Python Code",
      "dependency-review"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
)

echo -e "${YELLOW}📡 Sending request to GitHub API...${NC}"
echo ""

# Make API Request
RESPONSE=$(curl -s -X PUT \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$API_URL" 2>&1)

# Check if successful
if echo "$RESPONSE" | grep -q '"url"'; then
    echo -e "${GREEN}✅ Branch protection applied successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Configuration:${NC}"
    echo "  • Require PR reviews: YES (1 approval)"
    echo "  • Require CODEOWNERS: YES"
    echo "  • Dismiss stale reviews: YES"
    echo "  • Require status checks: YES"
    echo "  • Force pushes: BLOCKED"
    echo "  • Branch deletion: BLOCKED"
    echo "  • Admin enforcement: YES"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🔒 PROTECTION ACTIVE${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Test it:"
    echo "  git checkout $BRANCH"
    echo "  git push origin $BRANCH"
    echo "  # Should fail with: direct push blocked"
    exit 0
else
    echo -e "${RED}❌ Failed to apply branch protection${NC}"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | head -20
    echo ""
    
    if echo "$RESPONSE" | grep -q "Not Found"; then
        echo -e "${YELLOW}⚠️  Branch '$BRANCH' might not exist${NC}"
        echo "Available branches:"
        curl -s -H "Authorization: token $TOKEN" \
            "https://api.github.com/repos/$OWNER/$REPO/branches" | grep -o '"name": "[^"]*"' | head -10
    fi
    
    if echo "$RESPONSE" | grep -q "Upgrade to GitHub Pro"; then
        echo -e "${YELLOW}⚠️  Note: Some features require GitHub Pro/Team/Enterprise${NC}"
    fi
    
    exit 1
fi

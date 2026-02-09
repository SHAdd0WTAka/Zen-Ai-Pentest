#!/bin/bash
# Zen-AI-Pentest Notification Setup Script
# Usage: ./setup-notifications.sh [slack|discord|both]

set -e

REPO="SHAdd0WTAka/Zen-Ai-Pentest"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

echo "=========================================="
echo "🎉 Zen-AI-Pentest Notification Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) not found!"
        echo "Install from: https://cli.github.com/"
        exit 1
    fi
    print_success "GitHub CLI found"
}

authenticate() {
    if [ -z "$GITHUB_TOKEN" ]; then
        print_status "Checking GitHub authentication..."
        if ! gh auth status &> /dev/null; then
            print_warning "Not authenticated. Running 'gh auth login'..."
            gh auth login
        fi
    else
        print_status "Using provided GitHub token..."
        echo "$GITHUB_TOKEN" | gh auth login --with-token
    fi
    print_success "Authenticated with GitHub"
}

setup_slack() {
    echo ""
    echo "=========================================="
    echo "📱 Slack Setup"
    echo "=========================================="
    echo ""
    
    print_status "Opening Slack API Apps page..."
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://api.slack.com/apps" &
    elif command -v open &> /dev/null; then
        open "https://api.slack.com/apps" &
    elif command -v start &> /dev/null; then
        start "https://api.slack.com/apps" &
    fi
    
    echo ""
    echo "Follow these steps:"
    echo "1. Click 'Create New App' → 'From scratch'"
    echo "2. App Name: Zen-AI-Pentest"
    echo "3. Select your workspace"
    echo "4. Go to 'Incoming Webhooks' → Turn ON"
    echo "5. Click 'Add New Webhook to Workspace'"
    echo "6. Select a channel and click 'Allow'"
    echo "7. Copy the webhook URL"
    echo ""
    
    read -p "Paste your Slack webhook URL (or press Enter to skip): " slack_url
    
    if [ -n "$slack_url" ]; then
        print_status "Adding Slack secret to GitHub..."
        gh secret set SLACK_WEBHOOK_URL --body "$slack_url" --repo "$REPO"
        print_success "Slack webhook configured!"
    else
        print_warning "Skipped Slack setup"
    fi
}

setup_discord() {
    echo ""
    echo "=========================================="
    echo "💬 Discord Setup"
    echo "=========================================="
    echo ""
    
    print_status "Please open Discord and follow these steps:"
    echo ""
    echo "1. Right-click your server → 'Server Settings'"
    echo "2. Click 'Integrations' → 'Webhooks'"
    echo "3. Click 'New Webhook'"
    echo "4. Name: Zen-AI-Bot"
    echo "5. Select channel (e.g., #general)"
    echo "6. Click 'Copy Webhook URL'"
    echo ""
    
    read -p "Paste your Discord webhook URL (or press Enter to skip): " discord_url
    
    if [ -n "$discord_url" ]; then
        print_status "Adding Discord secret to GitHub..."
        gh secret set DISCORD_WEBHOOK_URL --body "$discord_url" --repo "$REPO"
        print_success "Discord webhook configured!"
    else
        print_warning "Skipped Discord setup"
    fi
}

test_notifications() {
    echo ""
    echo "=========================================="
    echo "🧪 Testing Notifications"
    echo "=========================================="
    echo ""
    
    print_status "Triggering test workflow..."
    gh workflow run test-notifications.yml --repo "$REPO"
    
    print_success "Test workflow triggered!"
    print_status "Check your Slack/Discord in a few seconds..."
}

show_summary() {
    echo ""
    echo "=========================================="
    echo "📊 Setup Summary"
    echo "=========================================="
    echo ""
    
    # Check configured secrets
    echo "Configured Secrets:"
    gh secret list --repo "$REPO" | grep -E "(SLACK|DISCORD)" || echo "No notification secrets configured yet"
    
    echo ""
    echo "What happens now:"
    echo "✅ Health Score alerts (< 50)"
    echo "✅ Workflow failure notifications"
    echo "✅ New release announcements"
    echo "✅ Issue & PR activity updates"
    echo ""
    echo "Next steps:"
    echo "1. Add webhooks anytime via GitHub Settings:"
    echo "   https://github.com/$REPO/settings/secrets/actions"
    echo "2. Or run this script again"
    echo "3. Test with: gh workflow run test-notifications.yml"
    echo ""
    print_success "Setup complete! 🚀"
}

# Main execution
main() {
    local type="${1:-both}"
    
    check_gh_cli
    authenticate
    
    case "$type" in
        slack)
            setup_slack
            ;;
        discord)
            setup_discord
            ;;
        both)
            setup_slack
            setup_discord
            ;;
        *)
            print_error "Usage: $0 [slack|discord|both]"
            exit 1
            ;;
    esac
    
    show_summary
}

main "$@"

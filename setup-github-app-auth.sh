#!/bin/bash
#==============================================================================
# GitHub App Authentication Setup Script
# Configures automatic token generation for GitHub App authentication
#==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_ID="2872904"
PRIVATE_KEY_NAME="zen-ai-pentest-kimi-assistant.2026-02-23.private-key.pem"
HELPER_SCRIPT="/home/atakan/zen-ai-pentest/github-app-credential-helper.py"

#==============================================================================
# Helper Functions
#==============================================================================

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

#==============================================================================
# Validation Functions
#==============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if private key exists
    local private_key_path="$HOME/Downloads/$PRIVATE_KEY_NAME"
    if [[ ! -f "$private_key_path" ]]; then
        print_error "Private key not found at: $private_key_path"
        echo "Please ensure the private key file is in ~/Downloads/"
        exit 1
    fi
    print_success "Private key found"
    
    # Check if credential helper script exists
    if [[ ! -f "$HELPER_SCRIPT" ]]; then
        print_error "Credential helper script not found: $HELPER_SCRIPT"
        exit 1
    fi
    print_success "Credential helper script found"
    
    # Check Python dependencies
    if ! python3 -c "import jwt" 2>/dev/null; then
        print_warning "PyJWT not installed. Installing..."
        pip3 install pyjwt cryptography --user -q
        print_success "Dependencies installed"
    else
        print_success "Python dependencies OK"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    print_success "Git is installed"
}

validate_repo() {
    local repo_path="$1"
    
    if [[ ! -d "$repo_path/.git" ]]; then
        print_error "Not a git repository: $repo_path"
        exit 1
    fi
    print_success "Valid git repository: $repo_path"
}

#==============================================================================
# Setup Functions
#==============================================================================

configure_credential_helper() {
    local repo_path="$1"
    
    print_header "Configuring Git Credential Helper"
    
    cd "$repo_path"
    
    # Remove any existing credential helpers
    git config --local --unset-all credential.helper 2>/dev/null || true
    
    # Set our credential helper
    git config --local credential.helper "$HELPER_SCRIPT"
    
    print_success "Credential helper configured"
    
    # Verify configuration
    local configured_helper
    configured_helper=$(git config --local credential.helper)
    print_info "Configured helper: $configured_helper"
}

clean_remote_url() {
    local repo_path="$1"
    
    print_header "Cleaning Remote URL"
    
    cd "$repo_path"
    
    # Get current remote URL
    local current_url
    current_url=$(git remote get-url origin 2>/dev/null || echo "")
    
    if [[ -z "$current_url" ]]; then
        print_warning "No remote 'origin' configured"
        return
    fi
    
    print_info "Current URL: $current_url"
    
    # Remove any embedded tokens from URL
    local clean_url
    if [[ "$current_url" =~ ^https://[^@]+@github.com ]]; then
        # Extract repo path
        clean_url=$(echo "$current_url" | sed -E 's|https://[^@]+@|https://|')
        git remote set-url origin "$clean_url"
        print_success "Removed token from remote URL"
        print_info "Clean URL: $clean_url"
    elif [[ "$current_url" =~ ^git@github.com ]]; then
        print_warning "SSH URL detected. Consider switching to HTTPS for App Auth"
        print_info "Current: $current_url"
        print_info "To switch: git remote set-url origin https://github.com/user/repo.git"
    else
        print_success "URL is already clean (no embedded token)"
    fi
}

test_authentication() {
    local repo_path="$1"
    
    print_header "Testing Authentication"
    
    cd "$repo_path"
    
    # Check if we can fetch
    print_info "Testing git fetch..."
    if git fetch --dry-run 2>&1 | grep -q "Authentication failed"; then
        print_error "Authentication test failed"
        return 1
    fi
    
    print_success "Authentication test passed"
    
    # Create a test commit and push
    print_info "Creating test commit..."
    local test_file=".github-app-auth-test"
    echo "GitHub App Auth enabled on $(date)" > "$test_file"
    
    git add "$test_file" 2>/dev/null || true
    
    if git commit -m "chore: GitHub App authentication test" --quiet 2>/dev/null; then
        print_success "Test commit created"
        
        print_info "Pushing to remote..."
        if git push --quiet 2>&1; then
            print_success "Push successful! GitHub App Auth is working"
            
            # Clean up test file
            git rm --quiet "$test_file" 2>/dev/null || rm -f "$test_file"
            git commit -m "chore: Remove auth test file" --quiet 2>/dev/null || true
            git push --quiet 2>/dev/null || true
        else
            print_error "Push failed"
            git reset --soft HEAD~1 --quiet
            rm -f "$test_file"
            return 1
        fi
    else
        print_warning "Nothing to commit (test file may already exist)"
        rm -f "$test_file"
    fi
}

show_status() {
    local repo_path="$1"
    
    print_header "Configuration Status"
    
    cd "$repo_path"
    
    echo ""
    echo -e "${BLUE}Repository:${NC} $repo_path"
    echo -e "${BLUE}Remote URL:${NC} $(git remote get-url origin 2>/dev/null || echo 'Not set')"
    echo -e "${BLUE}Credential Helper:${NC} $(git config --local credential.helper 2>/dev/null || echo 'Not set')"
    echo ""
    
    # Check for token in URL
    local url
    url=$(git remote get-url origin 2>/dev/null || echo "")
    if [[ "$url" =~ ^https://[^@]+@github.com ]]; then
        print_warning "⚠️  WARNING: Token embedded in remote URL!"
        echo "   Run: git remote set-url origin <clean-url>"
    fi
}

#==============================================================================
# Main
#==============================================================================

main() {
    print_header "GitHub App Authentication Setup"
    print_info "App ID: $APP_ID"
    print_info "Helper: $HELPER_SCRIPT"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    echo ""
    
    # Determine repository path
    local repo_path
    if [[ $# -eq 1 ]]; then
        repo_path="$1"
    else
        repo_path=$(pwd)
        print_info "No path specified, using current directory: $repo_path"
    fi
    
    # Convert to absolute path
    repo_path=$(cd "$repo_path" && pwd)
    
    # Validate repository
    validate_repo "$repo_path"
    echo ""
    
    # Configure
    configure_credential_helper "$repo_path"
    echo ""
    
    clean_remote_url "$repo_path"
    echo ""
    
    # Test
    if test_authentication "$repo_path"; then
        echo ""
        print_header "Setup Complete! 🎉"
        show_status "$repo_path"
        echo ""
        print_info "Your repository is now configured for automatic GitHub App authentication"
        print_info "The credential helper will generate fresh tokens for each git operation"
        echo ""
        print_info "To verify: cd \"$repo_path\" && git push"
    else
        echo ""
        print_error "Setup failed. Please check the error messages above."
        exit 1
    fi
}

# Show help
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "GitHub App Authentication Setup"
    echo ""
    echo "Usage: $0 [repository-path]"
    echo ""
    echo "Examples:"
    echo "  $0                           # Use current directory"
    echo "  $0 ~/zen-ai-pentest          # Setup specific repo"
    echo "  $0 '~/Documents/Obsidian Vault'  # Path with spaces"
    echo ""
    echo "This script will:"
    echo "  1. Check prerequisites (private key, dependencies)"
    echo "  2. Configure git credential helper"
    echo "  3. Clean remote URL (remove embedded tokens)"
    echo "  4. Test authentication with a push"
    echo ""
    exit 0
fi

main "$@"

#!/bin/bash
# =============================================================================
# Zen-AI-Pentest - Fehlende Tools installieren
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo "============================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "============================================================================="
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
# FEHLENDE TOOLS INSTALLIEREN
# =============================================================================

clear
print_header "🔧 Fehlende Tools installieren"
echo ""

export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin:$HOME/.local/bin

# 1. ZAP (OWASP Zed Attack Proxy)
print_header "1/9: OWASP ZAP"
if command -v zaproxy &> /dev/null || command -v zap.sh &> /dev/null; then
    print_success "ZAP bereits installiert"
else
    sudo apt-get update -qq
    sudo apt-get install -y -qq zaproxy 2>/dev/null && \
        print_success "OWASP ZAP installiert" || \
        print_error "ZAP Installation fehlgeschlagen"
fi

# 2. Subfinder
print_header "2/9: Subfinder"
if command -v subfinder &> /dev/null; then
    print_success "Subfinder bereits installiert"
else
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null && \
        print_success "Subfinder installiert" || \
        print_error "Subfinder Installation fehlgeschlagen"
fi

# 3. Ignorant (Email OSINT)
print_header "3/9: Ignorant"
pip install -q ignorant 2>/dev/null && \
    print_success "Ignorant installiert" || \
    print_error "Ignorant Installation fehlgeschlagen"

# 4. BloodHound
print_header "4/9: BloodHound"
if command -v bloodhound &> /dev/null; then
    print_success "BloodHound bereits installiert"
else
    sudo apt-get install -y -qq bloodhound 2>/dev/null && \
        print_success "BloodHound installiert" || \
        print_error "BloodHound Installation fehlgeschlagen"
fi

# 5. CrackMapExec
print_header "5/9: CrackMapExec"
if command -v crackmapexec &> /dev/null; then
    print_success "CrackMapExec bereits installiert"
else
    pip install -q crackmapexec 2>/dev/null && \
        print_success "CrackMapExec installiert" || \
        print_error "CrackMapExec Installation fehlgeschlagen"
fi

# 6. Responder
print_header "6/9: Responder"
if [ -d "$HOME/tools/Responder" ]; then
    print_success "Responder bereits installiert"
else
    mkdir -p $HOME/tools
    git clone --depth 1 https://github.com/lgandx/Responder.git $HOME/tools/Responder 2>/dev/null && \
        print_success "Responder installiert" || \
        print_error "Responder Installation fehlgeschlagen"
fi

# 7. Semgrep
print_header "7/9: Semgrep"
if command -v semgrep &> /dev/null; then
    print_success "Semgrep bereits installiert"
else
    pip install -q semgrep 2>/dev/null && \
        print_success "Semgrep installiert" || \
        print_error "Semgrep Installation fehlgeschlagen"
fi

# 8. TruffleHog
print_header "8/9: TruffleHog"
if command -v trufflehog &> /dev/null; then
    print_success "TruffleHog bereits installiert"
else
    pip install -q truffleHog 2>/dev/null && \
        print_success "TruffleHog installiert" || \
        print_error "TruffleHog Installation fehlgeschlagen"
fi

# 9. Trivy
print_header "9/9: Trivy"
if command -v trivy &> /dev/null; then
    print_success "Trivy bereits installiert"
else
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin 2>/dev/null && \
        print_success "Trivy installiert" || \
        print_error "Trivy Installation fehlgeschlagen"
fi

# =============================================================================
# ZUSAMMENFASSUNG
# =============================================================================

print_header "✅ Installation abgeschlossen!"
echo ""
echo "Führe 'python check_tools.py' aus, um den Status zu prüfen."
echo ""

#!/bin/bash
# =============================================================================
# Zen-AI-Pentest - Komplett-Installation aller Tools
# =============================================================================

set -e  # Bei Fehler abbrechen

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TOTAL_STEPS=10
CURRENT_STEP=0

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

step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo -e "${BLUE}[${CURRENT_STEP}/${TOTAL_STEPS}]${NC} $1"
    echo "-----------------------------------------------------------------------------"
}

# =============================================================================
# START
# =============================================================================

clear
print_header "🚀 Zen-AI-Pentest - Komplett-Installation"
echo "Dieses Skript installiert alle 38 Tools und Integrationen"
echo ""
echo "Benötigt: sudo-Rechte für System-Pakete"
echo "Dauer: ca. 10-30 Minuten (je nach Internet-Verbindung)"
echo ""
read -p "Fortfahren? (j/n): " confirm
if [[ $confirm != [jJ] ]]; then
    echo "Abgebrochen."
    exit 0
fi

# =============================================================================
# 1. SYSTEM UPDATE & GRUNDPakete
# =============================================================================
step "System-Update & Grundpakete"

sudo apt-get update -qq
sudo apt-get install -y -qq \
    git curl wget python3 python3-pip python3-venv \
    golang-go nmap masscan nikto sqlmap whatweb \
    tshark tcpdump wireshark-common \
    libpcap-dev libssl-dev \
    build-essential gcc make \
    unzip zip jq \
    2>&1 | grep -v "^Selecting\|^Preparing\|^Unpacking\|^Setting up" || true

print_success "System-Pakete installiert"

# =============================================================================
# 2. PYTHON PACKAGES
# =============================================================================
step "Python Packages (pip)"

# Scapy für Packet Manipulation
pip install -q scapy 2>/dev/null || print_warning "Scapy konnte nicht installiert werden"

# Zusätzliche Python-Tools
pip install -q \
    requests beautifulsoup4 lxml \
    dnspython ipwhois shodan censys \
    pyjwt cryptography bcrypt \
    2>/dev/null || print_warning "Einige Python-Pakete konnten nicht installiert werden"

print_success "Python Packages installiert"

# =============================================================================
# 3. GO-TOOLS (FFuF, Subfinder, HTTPX, etc.)
# =============================================================================
step "Go-Tools (FFuF, Subfinder, HTTPX, Amass)"

export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin:$HOME/.local/bin

# FFuF - Fast Web Fuzzer
go install github.com/ffuf/ffuf@latest 2>/dev/null && \
    print_success "FFuF installiert" || print_warning "FFuF Installation fehlgeschlagen"

# Subfinder - Subdomain Discovery
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null && \
    print_success "Subfinder installiert" || print_warning "Subfinder Installation fehlgeschlagen"

# HTTPX - Fast HTTP Prober
go install github.com/projectdiscovery/httpx/cmd/httpx@latest 2>/dev/null && \
    print_success "HTTPX installiert" || print_warning "HTTPX Installation fehlgeschlagen"

# Nuclei - Vulnerability Scanner
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null && \
    print_success "Nuclei installiert" || print_warning "Nuclei Installation fehlgeschlagen"

# Amass - Attack Surface Mapping
go install github.com/owasp-amass/amass/v4/...@master 2>/dev/null && \
    print_success "Amass installiert" || print_warning "Amass Installation fehlgeschlagen"

print_success "Go-Tools installation abgeschlossen"

# =============================================================================
# 4. GOBUSTER
# =============================================================================
step "Gobuster (Directory/Subdomain Buster)"

if command -v gobuster &> /dev/null; then
    print_success "Gobuster bereits installiert"
else
    sudo apt-get install -y -qq gobuster 2>/dev/null && \
        print_success "Gobuster installiert" || \
        print_warning "Gobuster konnte nicht installiert werden"
fi

# =============================================================================
# 5. WAFW00F
# =============================================================================
step "WAFW00F (Web Application Firewall Detector)"

if command -v wafw00f &> /dev/null; then
    print_success "WAFW00F bereits installiert"
else
    sudo apt-get install -y -qq wafw00f 2>/dev/null && \
        print_success "WAFW00F installiert" || \
        print_warning "WAFW00F konnte nicht installiert werden"
fi

# =============================================================================
# 6. BURP SUITE COMMUNITY
# =============================================================================
step "Burp Suite Community"

if command -v burpsuite &> /dev/null || [ -f /usr/share/burpsuite/burpsuite.jar ]; then
    print_success "Burp Suite bereits installiert"
else
    sudo apt-get install -y -qq burpsuite 2>/dev/null && \
        print_success "Burp Suite Community installiert" || \
        print_warning "Burp Suite konnte nicht installiert werden (manuell von portswigger.net downloaden)"
fi

# =============================================================================
# 7. ZAP (OWASP Zed Attack Proxy)
# =============================================================================
step "OWASP ZAP"

if command -v zaproxy &> /dev/null || command -v zap.sh &> /dev/null; then
    print_success "ZAP bereits installiert"
else
    sudo apt-get install -y -qq zaproxy 2>/dev/null && \
        print_success "OWASP ZAP installiert" || \
        print_warning "ZAP konnte nicht installiert werden"
fi

# =============================================================================
# 8. METASPLOIT FRAMEWORK
# =============================================================================
step "Metasploit Framework"

if command -v msfconsole &> /dev/null; then
    print_success "Metasploit bereits installiert"
else
    print_warning "Metasploit wird installiert... (kann einige Minuten dauern)"
    curl -s https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > /tmp/msfinstall
    chmod 755 /tmp/msfinstall
    /tmp/msfinstall 2>&1 | tail -5 || print_warning "Metasploit Installation fehlgeschlagen"
fi

# =============================================================================
# 9. ADDITIONALE OSINT TOOLS
# =============================================================================
step "OSINT Tools (Sherlock, Scout, Ignorant)"

# Sherlock - Username Enumeration
if [ ! -d "$HOME/tools/sherlock" ]; then
    mkdir -p $HOME/tools
    git clone --depth 1 https://github.com/sherlock-project/sherlock.git $HOME/tools/sherlock 2>/dev/null && \
        pip install -q -r $HOME/tools/sherlock/requirements.txt 2>/dev/null && \
        print_success "Sherlock installiert" || print_warning "Sherlock Installation fehlgeschlagen"
else
    print_success "Sherlock bereits vorhanden"
fi

# Ignorant - Email OSINT
pip install -q ignorant 2>/dev/null && \
    print_success "Ignorant installiert" || print_warning "Ignorant Installation fehlgeschlagen"

# Scout - OSINT Framework (Python Version)
pip install -q scout-osint 2>/dev/null && \
    print_success "Scout OSINT installiert" || print_warning "Scout Installation fehlgeschlagen"

# =============================================================================
# 10. ACTIVE DIRECTORY TOOLS
# =============================================================================
step "Active Directory Tools"

# BloodHound
sudo apt-get install -y -qq bloodhound 2>/dev/null && \
    print_success "BloodHound installiert" || print_warning "BloodHound konnte nicht installiert werden"

# CrackMapExec
pip install -q crackmapexec 2>/dev/null && \
    print_success "CrackMapExec installiert" || print_warning "CrackMapExec Installation fehlgeschlagen"

# Responder (für LLMNR/NBT-NS Poisoning)
if [ ! -d "$HOME/tools/Responder" ]; then
    git clone --depth 1 https://github.com/lgandx/Responder.git $HOME/tools/Responder 2>/dev/null && \
        print_success "Responder installiert" || print_warning "Responder Installation fehlgeschlagen"
else
    print_success "Responder bereits vorhanden"
fi

# =============================================================================
# 11. WIRELESS TOOLS
# =============================================================================
step "Wireless Tools (Aircrack-ng)"

sudo apt-get install -y -qq aircrack-ng 2>/dev/null && \
    print_success "Aircrack-ng installiert" || print_warning "Aircrack-ng konnte nicht installiert werden"

# =============================================================================
# 12. CODE ANALYSIS TOOLS
# =============================================================================
step "Code Analysis & Secret Scanning"

# Semgrep
pip install -q semgrep 2>/dev/null && \
    print_success "Semgrep installiert" || print_warning "Semgrep Installation fehlgeschlagen"

# TruffleHog
pip install -q truffleHog 2>/dev/null && \
    print_success "TruffleHog installiert" || print_warning "TruffleHog Installation fehlgeschlagen"

# =============================================================================
# 13. CONTAINER SECURITY
# =============================================================================
step "Container Security (Trivy)"

if command -v trivy &> /dev/null; then
    print_success "Trivy bereits installiert"
else
    # Trivy Installation
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin 2>/dev/null && \
        print_success "Trivy installiert" || print_warning "Trivy Installation fehlgeschlagen"
fi

# =============================================================================
# 14. HYDRA - BRUTE FORCE
# =============================================================================
step "Hydra (Login Cracker)"

sudo apt-get install -y -qq hydra 2>/dev/null && \
    print_success "Hydra installiert" || print_warning "Hydra konnte nicht installiert werden"

# =============================================================================
# 15. WORDLISTS
# =============================================================================
step "Wordlists"

sudo apt-get install -y -qq wordlists seclists 2>/dev/null && \
    print_success "Wordlists (rockyou, SecLists) installiert" || \
    print_warning "Wordlists konnten nicht installiert werden"

# Rockyou entpacken falls vorhanden
if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then
    sudo gzip -d /usr/share/wordlists/rockyou.txt.gz 2>/dev/null || true
    print_success "Rockyou Wordlist entpackt"
fi

# =============================================================================
# FINALISIERUNG
# =============================================================================

echo ""
echo "============================================================================="
echo -e "${GREEN}🎉 INSTALLATION ABGESCHLOSSEN!${NC}"
echo "============================================================================="
echo ""
echo "📋 Installierte Tools:"
echo ""

# Verfügbare Tools auflisten
echo "🌐 Netzwerk:"
command -v nmap &> /dev/null && echo "   ✅ Nmap"
command -v masscan &> /dev/null && echo "   ✅ Masscan"
python3 -c "import scapy" 2>/dev/null && echo "   ✅ Scapy"
command -v tshark &> /dev/null && echo "   ✅ Tshark"

echo ""
echo "🕸️  Web Security:"
command -v burpsuite &> /dev/null && echo "   ✅ Burp Suite"
command -v sqlmap &> /dev/null && echo "   ✅ SQLMap"
command -v nikto &> /dev/null && echo "   ✅ Nikto"
command -v zaproxy &> /dev/null && echo "   ✅ OWASP ZAP"
command -v ffuf &> /dev/null && echo "   ✅ FFuF"
command -v gobuster &> /dev/null && echo "   ✅ Gobuster"
command -v wafw00f &> /dev/null && echo "   ✅ WAFW00F"
command -v whatweb &> /dev/null && echo "   ✅ WhatWeb"

echo ""
echo "🔍 Reconnaissance:"
command -v subfinder &> /dev/null && echo "   ✅ Subfinder"
command -v httpx &> /dev/null && echo "   ✅ HTTPX"
command -v nuclei &> /dev/null && echo "   ✅ Nuclei"
command -v amass &> /dev/null && echo "   ✅ Amass"

echo ""
echo "💥 Exploitation:"
command -v msfconsole &> /dev/null && echo "   ✅ Metasploit"

echo ""
echo "🕵️  OSINT:"
[ -d "$HOME/tools/sherlock" ] && echo "   ✅ Sherlock"
python3 -c "import ignorant" 2>/dev/null && echo "   ✅ Ignorant"

echo ""
echo "🏢 Active Directory:"
command -v bloodhound &> /dev/null && echo "   ✅ BloodHound"
command -v crackmapexec &> /dev/null && echo "   ✅ CrackMapExec"
[ -d "$HOME/tools/Responder" ] && echo "   ✅ Responder"

echo ""
echo "🔓 Brute Force:"
command -v hydra &> /dev/null && echo "   ✅ Hydra"

echo ""
echo "📝 Code Analysis:"
command -v semgrep &> /dev/null && echo "   ✅ Semgrep"
command -v trufflehog &> /dev/null && echo "   ✅ TruffleHog"

echo ""
echo "🐳 Container:"
command -v trivy &> /dev/null && echo "   ✅ Trivy"

echo ""
echo "============================================================================="
echo "⚠️  WICHTIGE HINWEISE:"
echo "============================================================================="
echo ""
echo "1. Einige Tools benötigen ROOT-Rechte:"
echo "   - Masscan, Scapy (raw sockets)"
echo "   - Aircrack-ng (wireless)"
echo ""
echo "2. PATH aktualisieren:"
echo "   export PATH=\$PATH:\$HOME/go/bin:\$HOME/.local/bin"
echo ""
echo "3. Metasploit initialisieren (erster Start):"
echo "   sudo msfdb init"
echo ""
echo "4. Nuclei Templates aktualisieren:"
echo "   nuclei -update-templates"
echo ""
echo "5. Führe die Tests aus mit:"
echo "   cd zen-ai-pentest"
echo "   source venv/bin/activate"
echo "   python check_tools.py"
echo ""
echo "============================================================================="

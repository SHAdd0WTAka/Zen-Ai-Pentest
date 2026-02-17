#!/bin/bash
#
# Pentest Tools Installation Script
# Installs required and optional pentest tools
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
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

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            echo $ID
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
log_info "Detected OS: $OS"

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is not recommended for security."
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Install package based on OS
install_package() {
    local package=$1
    
    case $OS in
        ubuntu|debian)
            sudo apt-get update -qq
            sudo apt-get install -y -qq $package
            ;;
        fedora|centos|rhel)
            sudo dnf install -y $package
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm $package
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install $package
            else
                log_error "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
}

# Install Nmap
install_nmap() {
    log_info "Installing Nmap..."
    
    if command -v nmap &> /dev/null; then
        log_success "Nmap already installed: $(nmap -V | head -1)"
        return
    fi
    
    install_package nmap
    log_success "Nmap installed successfully"
}

# Install SQLMap
install_sqlmap() {
    log_info "Installing SQLMap..."
    
    if command -v sqlmap &> /dev/null; then
        log_success "SQLMap already installed: $(sqlmap --version)"
        return
    fi
    
    # Try package manager first
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        install_package sqlmap
    else
        # Install from GitHub
        log_info "Installing SQLMap from GitHub..."
        
        SQLMAP_DIR="/opt/sqlmap"
        if [ -d "$SQLMAP_DIR" ]; then
            sudo rm -rf "$SQLMAP_DIR"
        fi
        
        sudo git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git "$SQLMAP_DIR"
        sudo ln -sf "$SQLMAP_DIR/sqlmap.py" /usr/local/bin/sqlmap
        sudo chmod +x /usr/local/bin/sqlmap
    fi
    
    log_success "SQLMap installed successfully"
}

# Install Nuclei
install_nuclei() {
    log_info "Installing Nuclei..."
    
    if command -v nuclei &> /dev/null; then
        log_success "Nuclei already installed: $(nuclei -version 2>/dev/null | grep Version | awk '{print $3}')"
        return
    fi
    
    # Install using official installer
    log_info "Downloading Nuclei..."
    
    if command -v go &> /dev/null; then
        # Install via go
        go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    else
        # Download binary
        local arch=$(uname -m)
        local os="linux"
        [[ "$OSTYPE" == "darwin"* ]] && os="macos"
        
        local download_url="https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_${os}_${arch}.zip"
        
        cd /tmp
        curl -sL "$download_url" -o nuclei.zip
        unzip -q nuclei.zip
        sudo mv nuclei /usr/local/bin/
        rm nuclei.zip
        cd -
    fi
    
    # Download templates
    nuclei -update-templates
    
    log_success "Nuclei installed successfully"
}

# Install GoBuster
install_gobuster() {
    log_info "Installing GoBuster..."
    
    if command -v gobuster &> /dev/null; then
        log_success "GoBuster already installed"
        return
    fi
    
    if command -v go &> /dev/null; then
        go install github.com/OJ/gobuster/v3@latest
    else
        install_package gobuster
    fi
    
    log_success "GoBuster installed successfully"
}

# Install Subfinder
install_subfinder() {
    log_info "Installing Subfinder..."
    
    if command -v subfinder &> /dev/null; then
        log_success "Subfinder already installed"
        return
    fi
    
    if command -v go &> /dev/null; then
        go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    else
        log_warning "Go not installed, skipping Subfinder"
    fi
    
    log_success "Subfinder installed successfully"
}

# Install Amass
install_amass() {
    log_info "Installing Amass..."
    
    if command -v amass &> /dev/null; then
        log_success "Amass already installed"
        return
    fi
    
    if command -v snap &> /dev/null; then
        sudo snap install amass
    elif command -v go &> /dev/null; then
        go install -v github.com/owasp-amass/amass/v4/...@master
    else
        log_warning "Neither snap nor go available, skipping Amass"
    fi
    
    log_success "Amass installed successfully"
}

# Install FFUF
install_ffuf() {
    log_info "Installing FFUF..."
    
    if command -v ffuf &> /dev/null; then
        log_success "FFUF already installed"
        return
    fi
    
    if command -v go &> /dev/null; then
        go install github.com/ffuf/ffuf/v2@latest
    else
        log_warning "Go not installed, skipping FFUF"
    fi
    
    log_success "FFUF installed successfully"
}

# Install Nikto
install_nikto() {
    log_info "Installing Nikto..."
    
    if command -v nikto &> /dev/null; then
        log_success "Nikto already installed"
        return
    fi
    
    install_package nikto
    
    log_success "Nikto installed successfully"
}

# Install WhatWeb
install_whatweb() {
    log_info "Installing WhatWeb..."
    
    if command -v whatweb &> /dev/null; then
        log_success "WhatWeb already installed"
        return
    fi
    
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        install_package whatweb
    else
        log_warning "WhatWeb installation not automated for $OS"
    fi
    
    log_success "WhatWeb installed successfully"
}

# Install WAFW00F
install_wafw00f() {
    log_info "Installing WAFW00F..."
    
    if command -v wafw00f &> /dev/null; then
        log_success "WAFW00F already installed"
        return
    fi
    
    if command -v pip3 &> /dev/null; then
        pip3 install wafw00f
    else
        log_warning "pip3 not found, skipping WAFW00F"
    fi
    
    log_success "WAFW00F installed successfully"
}

# Check Go installation
check_go() {
    if ! command -v go &> /dev/null; then
        log_info "Go not found. Installing Go..."
        
        case $OS in
            ubuntu|debian)
                sudo apt-get update -qq
                sudo apt-get install -y -qq golang-go
                ;;
            fedora|centos|rhel)
                sudo dnf install -y golang
                ;;
            macos)
                brew install go
                ;;
            *)
                log_warning "Please install Go manually for your OS"
                ;;
        esac
    fi
    
    if command -v go &> /dev/null; then
        log_success "Go installed: $(go version)"
    fi
}

# Install wordlists
install_wordlists() {
    log_info "Installing wordlists..."
    
    local wordlist_dir="/usr/share/wordlists"
    sudo mkdir -p "$wordlist_dir"
    
    # SecLists
    if [ ! -d "$wordlist_dir/SecLists" ]; then
        log_info "Downloading SecLists..."
        cd /tmp
        git clone --depth 1 https://github.com/danielmiessler/SecLists.git
        sudo mv SecLists "$wordlist_dir/"
        rm -rf /tmp/SecLists
        log_success "SecLists installed"
    fi
    
    # Dirb wordlists
    if [ ! -d "$wordlist_dir/dirb" ]; then
        install_package dirb
    fi
}

# Main installation
main() {
    echo "==============================================="
    echo "  Zen-AI-Pentest Tool Installer"
    echo "==============================================="
    echo
    
    check_root
    
    # Parse arguments
    INSTALL_ALL=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                INSTALL_ALL=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --all    Install all tools (required + optional)"
                echo "  --help   Show this help message"
                echo
                echo "Without --all, only required tools are installed."
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log_info "Starting installation..."
    log_info "This may take a while..."
    echo
    
    # Required tools
    install_nmap
    install_sqlmap
    
    # Optional tools (if --all)
    if [[ "$INSTALL_ALL" == true ]]; then
        log_info "Installing optional tools..."
        
        check_go
        
        install_nuclei
        install_gobuster
        install_subfinder
        install_amass
        install_ffuf
        install_nikto
        install_whatweb
        install_wafw00f
        install_wordlists
    else
        log_info "Skipping optional tools (use --all to install everything)"
    fi
    
    echo
    echo "==============================================="
    log_success "Installation complete!"
    echo "==============================================="
    echo
    
    # Final check
    echo "Running tool check..."
    echo
    
    if command -v python3 &> /dev/null; then
        python3 -m tools.integrations.tool_checker || true
    fi
    
    echo
    log_info "Required tools installed:"
    echo "  - nmap: $(nmap -V 2>/dev/null | head -1 || echo 'Not found')"
    echo "  - sqlmap: $(sqlmap --version 2>/dev/null || echo 'Not found')"
    echo
    log_info "You can now run: python tests/run_tests.py"
}

# Run main
main "$@"

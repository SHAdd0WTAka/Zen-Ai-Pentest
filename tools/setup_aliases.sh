#!/bin/bash
# Zen-Ai-Pentest Aliase & Functions
# Füge das zu deiner ~/.bashrc hinzu: source ~/Zen-Ai-Pentest/tools/setup_aliases.sh

ZEN_DIR="$HOME/Zen-Ai-Pentest"

# --- Kimi Helper Aliase ---
alias kimi-helper="python3 $ZEN_DIR/tools/kimi_helper.py"
alias khi="python3 $ZEN_DIR/tools/kimi_helper.py"
alias kh="python3 $ZEN_DIR/tools/kimi_helper.py"

# Schnelle Persona-Aufrufe
alias k-recon="python3 $ZEN_DIR/tools/kimi_helper.py -p recon"
alias k-exploit="python3 $ZEN_DIR/tools/kimi_helper.py -p exploit"
alias k-report="python3 $ZEN_DIR/tools/kimi_helper.py -p report"
alias k-audit="python3 $ZEN_DIR/tools/kimi_helper.py -p audit"
alias k-social="python3 $ZEN_DIR/tools/kimi_helper.py -p social"
alias k-network="python3 $ZEN_DIR/tools/kimi_helper.py -p network"
alias k-mobile="python3 $ZEN_DIR/tools/kimi_helper.py -p mobile"
alias k-redteam="python3 $ZEN_DIR/tools/kimi_helper.py -p redteam"
alias k-ics="python3 $ZEN_DIR/tools/kimi_helper.py -p ics"
alias k-cloud="python3 $ZEN_DIR/tools/kimi_helper.py -p cloud"
alias k-crypto="python3 $ZEN_DIR/tools/kimi_helper.py -p crypto"

# Interaktiver Modus
alias k-chat="python3 $ZEN_DIR/tools/kimi_helper.py -i"

# --- Zen-Ai Pentest Aliase ---
alias zen="cd $ZEN_DIR && source .env 2>/dev/null || true"
alias zen-scan="python3 $ZEN_DIR/zen-ai-pentest.py"
alias zen-autonomous="python3 $ZEN_DIR/run_autonomous.py"

# --- Kimi Personas API Aliase ---
alias kimi-api-start="$ZEN_DIR/api/start_server.sh"
alias kimi-api-server="python3 $ZEN_DIR/api/kimi_personas_api.py"
alias kimi-api-logs="tail -f $ZEN_DIR/logs/api.log 2>/dev/null || echo 'Keine Logs vorhanden'"

# Kimi API CLI Client
alias kimi-cli="python3 $ZEN_DIR/api/cli_client.py"
alias kapi="python3 $ZEN_DIR/api/cli_client.py"
alias kapi-health="python3 $ZEN_DIR/api/cli_client.py health"
alias kapi-list="python3 $ZEN_DIR/api/cli_client.py list"
alias kapi-admin="python3 $ZEN_DIR/api/cli_client.py admin"

# Screenshot Manager
alias kscreenshot="python3 $ZEN_DIR/api/add_screenshot.py"
alias kss="python3 $ZEN_DIR/api/add_screenshot.py"
alias kss-list="python3 $ZEN_DIR/api/add_screenshot.py list"
alias kss-add="python3 $ZEN_DIR/api/add_screenshot.py add"
alias kss-downloads="python3 $ZEN_DIR/api/add_screenshot.py downloads"
alias kss-open="python3 $ZEN_DIR/api/add_screenshot.py open"

# --- Hilfsfunktionen ---

# Kimi mit Datei-Inhalt als Prompt
k-file() {
    local persona="${1:-recon}"
    local file="$2"
    if [[ -z "$file" ]]; then
        echo "Usage: k-file <persona> <file>"
        echo "Example: k-file exploit /tmp/request.txt"
        return 1
    fi
    python3 $ZEN_DIR/tools/kimi_helper.py -p "$persona" -f "$file"
}

# Schneller Target-Scan mit Kimi Recon
k-target() {
    local target="$1"
    if [[ -z "$target" ]]; then
        echo "Usage: k-target <domain/ip>"
        echo "Example: k-target example.com"
        return 1
    fi
    python3 $ZEN_DIR/tools/kimi_helper.py -p recon "Analysiere $target - Subdomains, Ports, Technologien. Gib konkrete nmap/gobuster Befehle."
}

# Code-Review mit Kimi Audit
k-review() {
    local file="$1"
    if [[ -z "$file" ]]; then
        echo "Usage: k-review <python-file>"
        echo "Example: k-review vulnerable.py"
        return 1
    fi
    if [[ ! -f "$file" ]]; then
        echo "❌ File not found: $file"
        return 1
    fi
    python3 $ZEN_DIR/tools/kimi_helper.py -p audit -f "$file"
}

# Zeige verfügbare Kimi Personas
k-personas() {
    python3 $ZEN_DIR/tools/kimi_helper.py --list
}

echo "🛡️ Zen-Ai-Pentest Aliase geladen!"
echo "Core:     k-recon, k-exploit, k-report, k-audit"
echo "Extended: k-social, k-network, k-mobile, k-redteam, k-ics, k-cloud, k-crypto"
echo "Utils:    k-chat, k-target, k-review"

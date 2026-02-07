#!/bin/bash
# Setup-Script für zen-kimi Aliase

echo "🚀 Richte zen-kimi Aliase ein..."

# Ermittle das korrekte Home-Verzeichnis
ZEN_DIR="$HOME/Zen-Ai-Pentest"

# Prüfe ob Zen-Ai-Pentest existiert
if [ ! -d "$ZEN_DIR" ]; then
    echo "⚠️  Zen-Ai-Pentest nicht in $ZEN_DIR gefunden"
    echo "Suche nach alternatives Verzeichnis..."
    
    # Versuche zu finden
    FOUND=$(find ~ -name "kimi_cli_integration.py" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        ZEN_DIR=$(dirname $(dirname "$FOUND"))
        echo "✅ Gefunden: $ZEN_DIR"
    else
        echo "❌ Zen-Ai-Pentest Verzeichnis nicht gefunden!"
        echo "Bitte gib den Pfad manuell an:"
        read -r ZEN_DIR
    fi
fi

# Füge Aliase zur Shell-Konfiguration hinzu
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.bashrc"
    touch "$SHELL_RC"
fi

echo "📝 Füge Aliase zu $SHELL_RC hinzu..."

# Backup erstellen
cp "$SHELL_RC" "$SHELL_RC.backup.$(date +%Y%m%d)"

# Aliase hinzufügen (vermeide Duplikate)
grep -q "# Zen-Ai-Pentest Aliase" "$SHELL_RC" || cat >> "$SHELL_RC" << EOF

# ============================================
# Zen-Ai-Pentest Aliase
# ============================================
alias zen-kimi="python3 $ZEN_DIR/tools/kimi_cli_integration.py"
alias zlogin="python3 $ZEN_DIR/tools/kimi_cli_integration.py --login"
alias zcheck="python3 $ZEN_DIR/tools/kimi_cli_integration.py --check"

# Schnell-Zugriff auf Personas
alias zrecon="zen-kimi -p recon"
alias zexploit="zen-kimi -p exploit"
alias zreport="zen-kimi -p report"
alias zaudit="zen-kimi -p audit"
alias znetwork="zen-kimi -p network"
alias zred="zen-kimi -p redteam"
# ============================================
EOF

echo "✅ Aliase hinzugefügt zu: $SHELL_RC"
echo ""
echo "🔄 Lade Shell-Konfiguration neu..."
source "$SHELL_RC"

echo ""
echo "🎉 Setup abgeschlossen!"
echo ""
echo "Verfügbare Befehle:"
echo "  zen-kimi -p <persona> [prompt]  # Kimi mit Persona starten"
echo "  zlogin                          # Bei kimi einloggen"
echo "  zcheck                          # Status prüfen"
echo ""
echo "Schnell-Personas:"
echo "  zrecon 'Finde Subdomains von example.com'"
echo "  zexploit 'Schreibe einen SQLi POC'"
echo "  zreport 'CVSS-Bewertung für CVE-2024-1234'"
echo "  zaudit 'Reviewe diesen Python-Code'"
echo ""

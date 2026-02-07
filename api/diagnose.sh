#!/bin/bash
# Diagnose-Skript für Kimi Personas API

echo "🔧 Zen-Ai Kimi Personas - Diagnose"
echo "═══════════════════════════════════════════════════════════════"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# 1. Prüfe Python
echo -e "\n📋 [1/10] Python Version..."
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VER"
else
    echo -e "${RED}✗ Python3 nicht gefunden${NC}"
    ERRORS=$((ERRORS+1))
fi

# 2. Prüfe Dependencies
echo -e "\n📦 [2/10] Dependencies..."
for pkg in flask flask_cors flask_sock rich requests; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $pkg"
    else
        echo -e "${RED}✗ $pkg fehlt${NC}"
        ERRORS=$((ERRORS+1))
    fi
done

# 3. Prüfe Verzeichnisstruktur
echo -e "\n📁 [3/10] Verzeichnisstruktur..."
ZEN_DIR="$HOME/Zen-Ai-Pentest"
for dir in "$ZEN_DIR/tools" "$ZEN_DIR/api" "$ZEN_DIR/api/templates"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir"
    else
        echo -e "${RED}✗ $dir fehlt${NC}"
        ERRORS=$((ERRORS+1))
    fi
done

# 4. Prüfe Dateien
echo -e "\n📄 [4/10] Wichtige Dateien..."
for file in "$ZEN_DIR/tools/kimi_helper.py" "$ZEN_DIR/api/kimi_personas_api.py" "$ZEN_DIR/api/templates/index.html"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $(basename $file)"
    else
        echo -e "${RED}✗ $(basename $file) fehlt${NC}"
        ERRORS=$((ERRORS+1))
    fi
done

# 5. Prüfe Personas
echo -e "\n🎭 [5/10] Persona-Dateien..."
PERSONA_DIR="$HOME/.config/kimi/personas"
if [ -d "$PERSONA_DIR" ]; then
    PERSONA_COUNT=$(ls -1 "$PERSONA_DIR"/*.md 2>/dev/null | wc -l)
    if [ "$PERSONA_COUNT" -eq 11 ]; then
        echo -e "${GREEN}✓${NC} Alle 11 Personas vorhanden"
    else
        echo -e "${YELLOW}⚠${NC} Nur $PERSONA_COUNT Personas gefunden (erwarte 11)"
        echo "  Erstelle fehlende Personas..."
        python3 "$ZEN_DIR/tools/update_personas.py"
    fi
else
    echo -e "${RED}✗ Persona-Verzeichnis fehlt${NC}"
    mkdir -p "$PERSONA_DIR"
    python3 "$ZEN_DIR/tools/update_personas.py"
fi

# 6. Prüfe laufende Prozesse
echo -e "\n🔄 [6/10] Laufende Server..."
API_PID=$(pgrep -f "kimi_personas_api.py" | head -1)
if [ -n "$API_PID" ]; then
    echo -e "${GREEN}✓${NC} API Server läuft (PID: $API_PID)"
    echo "  Port: $(lsof -Pan -p $API_PID -i | grep LISTEN | awk '{print $9}' | head -1)"
else
    echo -e "${YELLOW}⚠${NC} API Server nicht aktiv"
    echo "  Starte mit: python3 $ZEN_DIR/api/kimi_personas_api.py --no-auth"
fi

# 7. Prüfe Ports
echo -e "\n🔌 [7/10] Port 5000..."
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Port 5000 belegt"
else
    echo -e "${YELLOW}⚠${NC} Port 5000 frei (Server nicht aktiv)"
fi

# 8. Teste API Verbindung
echo -e "\n🌐 [8/10] API Verbindungstest..."
if curl -s http://127.0.0.1:5000/api/v1/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API erreichbar auf http://127.0.0.1:5000"
    HEALTH=$(curl -s http://127.0.0.1:5000/api/v1/health)
    echo "  Response: $HEALTH"
else
    echo -e "${RED}✗${NC} API nicht erreichbar"
    echo "  Mögliche Ursachen:"
    echo "    - Server nicht gestartet"
    echo "    - Firewall blockiert Port 5000"
    echo "    - Falscher Host/Port"
    ERRORS=$((ERRORS+1))
fi

# 9. Prüfe Firewall
echo -e "\n🧱 [9/10] Firewall..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | grep -i "status" | awk '{print $2}')
    if [ "$UFW_STATUS" = "active" ]; then
        echo -e "${YELLOW}⚠${NC} UFW aktiv - prüfe Regeln"
        ufw status | grep 5000 || echo "  Port 5000 nicht explizit erlaubt"
    else
        echo -e "${GREEN}✓${NC} UFW inaktiv"
    fi
elif command -v iptables &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} iptables vorhanden (Status unklar)"
else
    echo -e "${GREEN}✓${NC} Keine Firewall erkannt"
fi

# 10. Prüfe Konfiguration
echo -e "\n⚙️  [10/10] Konfiguration..."
CONFIG_FILE="$ZEN_DIR/config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✓${NC} config.json vorhanden"
    if python3 -c "import json; f=open('$CONFIG_FILE'); d=json.load(f); print('  API Key:', '✓' if d.get('backends',{}).get('kimi_api_key') else '✗')" 2>/dev/null; then
        true
    else
        echo "  API Key: nicht konfiguriert (optional mit --no-auth)"
    fi
else
    echo -e "${YELLOW}⚠${NC} config.json nicht gefunden"
fi

# Zusammenfassung
echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Alle Checks bestanden!${NC}"
    echo ""
    echo "Starte den Server mit:"
    echo "  python3 $ZEN_DIR/api/kimi_personas_api.py --no-auth"
    echo ""
    echo "Oder:"
    echo "  cd $ZEN_DIR/api && python3 kimi_personas_api.py --no-auth"
else
    echo -e "${RED}❌ $ERRORS Problem(e) gefunden${NC}"
    echo ""
    echo "Installiere fehlende Dependencies:"
    echo "  pip3 install flask flask-cors flask-sock rich requests"
    echo ""
    echo "Erstelle fehlende Personas:"
    echo "  python3 $ZEN_DIR/tools/update_personas.py"
fi
echo "═══════════════════════════════════════════════════════════════"

# Auto-Fix Angebot
if [ $ERRORS -gt 0 ]; then
    echo ""
    read -p "Auto-Fix versuchen? (j/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        echo "🔧 Führe Auto-Fix durch..."
        pip3 install flask flask-cors flask-sock rich requests -q
        python3 "$ZEN_DIR/tools/update_personas.py"
        echo -e "${GREEN}✓${NC} Auto-Fix abgeschlossen"
        echo "Starte jetzt: python3 $ZEN_DIR/api/kimi_personas_api.py --no-auth"
    fi
fi

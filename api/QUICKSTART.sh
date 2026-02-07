#!/bin/bash
# Zen-Ai Kimi Personas Quickstart

set -e

echo "🚀 Zen-Ai Kimi Personas Quickstart"
echo "═══════════════════════════════════════════════════════════════"

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

ZEN_DIR="$HOME/Zen-Ai-Pentest"

# 1. Dependencies prüfen/installieren
echo -e "${BLUE}📦 Prüfe Dependencies...${NC}"

if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installiere Flask..."
    pip3 install flask flask-cors flask-sock -q
fi

if ! python3 -c "import rich" 2>/dev/null; then
    echo "Installiere Rich..."
    pip3 install rich requests -q
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"

# 2. Aliase laden
echo -e "${BLUE}🔧 Lade Aliase...${NC}"
source "$ZEN_DIR/tools/setup_aliases.sh"
echo -e "${GREEN}✓ Aliase geladen${NC}"

# 3. Personas erstellen
echo -e "${BLUE}🎭 Erstelle Personas...${NC}"
python3 "$ZEN_DIR/tools/update_personas.py" > /dev/null
echo -e "${GREEN}✓ 11 Personas bereit${NC}"

# 4. Teste CLI
echo -e "${BLUE}🧪 Teste CLI...${NC}"
if khi --list > /dev/null 2>&1; then
    echo -e "${GREEN}✓ CLI funktioniert${NC}"
else
    echo "⚠️ CLI hat Probleme, versuche trotzdem API..."
fi

# 5. Starte API Server im Hintergrund
echo -e "${BLUE}🌐 Starte API Server...${NC}"
python3 "$ZEN_DIR/api/kimi_personas_api.py" --no-auth &
SERVER_PID=$!
sleep 2

# 6. Teste API
echo -e "${BLUE}🧪 Teste API...${NC}"
if curl -s http://127.0.0.1:5000/api/v1/health > /dev/null; then
    echo -e "${GREEN}✓ API läuft auf http://127.0.0.1:5000${NC}"
else
    echo "⚠️ API nicht erreichbar"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Setup abgeschlossen!${NC}"
echo ""
echo "Verfügbare Befehle:"
echo "  khi --list              # Personas anzeigen"
echo "  k-recon 'message'       # Recon Anfrage"
echo "  k-exploit 'message'     # Exploit Anfrage"
echo "  k-cloud 'message'       # Cloud Anfrage"
echo "  kimi-api-start          # API Server starten"
echo "  kapi health             # API Status prüfen"
echo ""
echo "Web UI: http://127.0.0.1:5000"
echo ""
echo "Drücke ENTER zum Server stoppen..."
read

kill $SERVER_PID 2>/dev/null || true
echo "👋 Auf Wiedersehen!"

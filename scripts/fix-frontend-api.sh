#!/bin/bash
# Fix ZEN-ALPHA Frontend API Connection
# Dieses Skript diagnostiziert und behebt das API-Verbindungsproblem

echo "🔧 ZEN-ALPHA API Connection Fix"
echo "================================"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Aktuelle API URL aus der client.ts extrahieren
echo "📋 Schritt 1: Aktuelle Konfiguration prüfen..."
CURRENT_API=$(grep "API_BASE_URL" web_ui/frontend/src/api/client.ts | head -1 | sed 's/.*|| '\''\(.*\)'\''.*/\1/')
echo "   Aktuelle API URL: ${YELLOW}$CURRENT_API${NC}"
echo ""

# Prüfe ob ngrok URL
echo "📋 Schritt 2: API Erreichbarkeit testen..."
if curl -s --max-time 5 "$CURRENT_API/health" > /dev/null 2>&1; then
    echo "   ${GREEN}✓ API ist erreichbar!${NC}"
    curl -s "$CURRENT_API/health" | head -1
elif curl -s --max-time 5 "$CURRENT_API" -o /tmp/api_check.html 2>/dev/null; then
    if grep -q "DOCTYPE" /tmp/api_check.html 2>/dev/null; then
        echo "   ${RED}✗ API liefert HTML statt JSON (ngrok offline oder 404)${NC}"
        echo ""
        echo "   ${YELLOW}MÖGLICHE LÖSUNGEN:${NC}"
        echo ""
        echo "   Option 1: Lokales Backend starten + ngrok"
        echo "   ----------------------------------------"
        echo "   Terminal 1: python -m api.main"
        echo "   Terminal 2: ngrok http 8000"
        echo "   Dann die neue ngrok URL in GitHub Secrets setzen:"
        echo "   CF_API_URL = https://xxxx.ngrok-free.app"
        echo ""
        echo "   Option 2: Direkt auf lokale API umstellen (nur für lokale Entwicklung)"
        echo "   --------------------------------------------------------------------"
        echo "   Möchtest du auf http://localhost:8000 umstellen? (nur lokal)"
        echo ""
        read -p "   Auf localhost:8000 umstellen? (j/N): " choice
        if [ "$choice" = "j" ] || [ "$choice" = "J" ]; then
            sed -i "s|const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://[^']*'|const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'|" web_ui/frontend/src/api/client.ts
            echo "   ${GREEN}✓ Auf localhost:8000 umgestellt${NC}"
            echo "   ${YELLOW}⚠️  WICHTIG: Backend muss lokal laufen!${NC}"
            echo ""
            echo "   Starte Backend mit:"
            echo "   uvicorn api.main:app --host 0.0.0.0 --port 8000"
        fi
        echo ""
        echo "   Option 3: Neuen ngrok Tunnel erstellen"
        echo "   --------------------------------------"
        if command -v ngrok &> /dev/null; then
            echo "   ngrok ist installiert. Starte tunnel..."
            echo "   ${YELLOW}Führe aus:${NC} ngrok http 8000"
        else
            echo "   ngrok nicht installiert. Download: https://ngrok.com/download"
        fi
    fi
else
    echo "   ${RED}✗ API ist nicht erreichbar (Connection refused)${NC}"
fi

echo ""
echo "📋 Schritt 3: Lokales Backend Status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ${GREEN}✓ Lokales Backend läuft auf Port 8000${NC}"
else
    echo "   ${RED}✗ Kein lokales Backend auf Port 8000 gefunden${NC}"
    echo ""
    echo "   Backend starten mit:"
    echo "   ${YELLOW}uvicorn api.main:app --host 0.0.0.0 --port 8000${NC}"
fi

echo ""
echo "📋 Zusammenfassung der Optionen:"
echo "================================="
echo ""
echo "1. ${GREEN}Lokale Entwicklung:${NC}"
echo "   - Backend: uvicorn api.main:app --reload"
echo "   - Frontend: cd web_ui/frontend && npm run dev"
echo ""
echo "2. ${GREEN}Mit ngrok (für Cloudflare Pages):${NC}"
echo "   - Backend: uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo "   - Tunnel: ngrok http 8000"
echo "   - GitHub Secret CF_API_URL aktualisieren"
echo "   - Workflow neu ausführen"
echo ""
echo "3. ${GREEN}Schnellfix für lokale Nutzung:${NC}"
echo "   - client.ts auf localhost:8000 umstellen (siehe oben)"
echo ""

#!/bin/bash
# Push Kimi Personas System to GitHub

echo "🚀 Zen-Ai Pentest - GitHub Push Helper"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd ~/Zen-Ai-Pentest

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Prüfe Git
echo "📋 Prüfe Git Status..."
if [ ! -d .git ]; then
    echo -e "${RED}❌ Kein Git Repository gefunden!${NC}"
    echo "Bitte stelle sicher, dass du im Zen-Ai-Pentest Verzeichnis bist."
    exit 1
fi

# Zeige aktuellen Branch
BRANCH=$(git branch --show-current)
echo -e "Aktueller Branch: ${YELLOW}$BRANCH${NC}"
echo ""

# Zeige neue Dateien
echo "📁 Neue Dateien die hinzugefügt werden:"
git status --short | grep "^??" | head -20

echo ""
echo "Modifizierte Dateien:"
git status --short | grep "^ M" | head -20

echo ""
read -p "Alle neuen Dateien hinzufügen? (j/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Jj]$ ]]; then
    echo ""
    echo "📦 Füge Dateien hinzu..."

    # Tools
    git add tools/kimi_helper.py
    git add tools/update_personas.py
    git add tools/setup_aliases.sh

    # API
    git add api/kimi_personas_api.py
    git add api/cli_client.py
    git add api/add_screenshot.py
    git add api/templates/index.html
    git add api/manage.sh
    git add api/status.sh
    git add api/diagnose.sh
    git add api/QUICK_TEST.sh
    git add api/QUICKSTART.sh
    git add api/test_api.sh
    git add api/start_server.sh
    git add api/postman_collection.json
    git add api/docker-compose.yml
    git add api/Dockerfile
    git add api/requirements-api.txt
    git add api/README.md

    # Docs
    git add KIMI_PERSONAS_INTEGRATION.md
    git add KIMI_PERSONAS_SETUP.md
    git add DEMO.md

    # Screenshots Verzeichnis
    mkdir -p screenshots
    git add screenshots/

    echo -e "${GREEN}✅ Dateien hinzugefügt${NC}"
    echo ""

    # Commit
    echo "📝 Erstelle Commit..."
    git commit -m "feat: Add Kimi Personas System with 11 Pentest AI assistants

- Add 11 specialized pentest personas:
  * Core: recon, exploit, report, audit
  * Extended: social, network, mobile, redteam, ics, cloud, crypto

- Add CLI tool (kimi_helper.py) with interactive mode
  * One-shot and interactive chat modes
  * 11 persona-specific commands (k-recon, k-exploit, etc.)

- Add Flask REST API with WebSocket support
  * 12+ API endpoints
  * Request logging and admin dashboard
  * Screenshot upload and analysis

- Add Web UI with modern design
  * 3 tabs: Chat, Screenshots, Documentation
  * Drag & drop screenshot upload
  * Real-time screenshot analysis

- Add API CLI client for programmatic access
- Add screenshot management tools
- Add Docker support with docker-compose
- Add Postman collection for API testing
- Add comprehensive documentation

Features:
- WebSocket chat for real-time communication
- Request logging with audit trail
- Admin dashboard with statistics
- Screenshot gallery and analysis
- Batch processing support
- Auto-diagnose and management tools

Closes #42"

    echo -e "${GREEN}✅ Commit erstellt${NC}"
    echo ""

    # Push
    echo "🚀 Pushe zu GitHub..."
    git push origin $BRANCH

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ ERFOLGREICH GEPUSHT!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Repository: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest"
        echo ""
        echo "Neue Features:"
        echo "  • 11 Pentest Personas"
        echo "  • CLI Tool (tools/kimi_helper.py)"
        echo "  • REST API (api/kimi_personas_api.py)"
        echo "  • Web UI (http://127.0.0.1:5000)"
        echo "  • Screenshot Analysis"
        echo ""
        echo "Nächste Schritte:"
        echo "  1. Prüfe GitHub: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest"
        echo "  2. Starte Server: bash api/manage.sh start"
        echo "  3. Öffne Web UI: http://127.0.0.1:5000"
    else
        echo -e "${RED}❌ Push fehlgeschlagen${NC}"
        echo "Mögliche Ursachen:"
        echo "  - Keine Internetverbindung"
        echo "  - Authentifizierungsproblem"
        echo "  - Merge Konflikt"
    fi
else
    echo "Abgebrochen."
    exit 0
fi

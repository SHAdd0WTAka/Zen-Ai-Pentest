#!/bin/bash
# Push zu GitHub mit Personal Access Token

echo "🚀 Push zu GitHub mit Token"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd ~/Zen-Ai-Pentest

# Prüfe ob Token als Environment Variable gesetzt ist
if [ -n "$GITHUB_TOKEN" ]; then
    TOKEN="$GITHUB_TOKEN"
    echo "✅ Token aus Umgebungsvariable gefunden"
else
    echo "📝 GitHub Token wird benötigt"
    echo ""
    echo "So erstellst du einen Token:"
    echo "1. Öffne: https://github.com/settings/tokens/new"
    echo "2. Gib einen Namen ein: Zen-Ai-Pentest"
    echo "3. Wähle Scope: ☑️ repo (Full control)"
    echo "4. Klicke: Generate token"
    echo "5. Kopiere den Token (wird nur einmal angezeigt!)"
    echo ""

    # Token interaktiv abfragen
    echo "Token eingeben (wird nicht angezeigt):"
    read -s TOKEN
    echo ""
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Kein Token angegeben"
    exit 1
fi

echo "🔄 Pushe zu GitHub..."

# Push mit Token
git push https://${TOKEN}@github.com/SHAdd0WTAka/Zen-Ai-Pentest.git master

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ERFOLGREICH GEPUSHT!"
    echo ""
    echo "🔗 Repository: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest"
    echo ""
    echo "Neue Features im Repo:"
    echo "  • 11 Pentest Personas"
    echo "  • CLI Tool (kimi_helper.py)"
    echo "  • Flask REST API"
    echo "  • Web UI mit Screenshots"
    echo "  • Docker Support"
else
    echo ""
    echo "❌ Push fehlgeschlagen"
    echo "Mögliche Ursachen:"
    echo "  - Falscher Token"
    echo "  - Keine Berechtigungen (Scope: repo)"
    echo "  - Netzwerkproblem"
fi

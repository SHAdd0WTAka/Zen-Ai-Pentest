#!/bin/bash
# Dieses Skript trägt den Discord Token in GitHub Secrets ein

echo "🤖 Discord Token Setup für GitHub"
echo "================================"
echo ""
echo "Token aus .env Datei lesen..."
echo ""

# Token aus .env laden
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Token gefunden: ${DISCORD_BOT_TOKEN:0:20}..."
else
    echo "❌ .env Datei nicht gefunden!"
    exit 1
fi

echo ""
echo "GitHub CLI wird verwendet, um Secret zu setzen..."
echo ""

# Mit gh CLI den Secret setzen (falls gh installiert ist)
if command -v gh &> /dev/null; then
    echo "$DISCORD_BOT_TOKEN" | gh secret set DISCORD_BOT_TOKEN --repo SHAdd0WTAka/Zen-Ai-Pentest
    echo "✅ Secret gesetzt!"
else
    echo "⚠️  GitHub CLI nicht installiert."
    echo ""
    echo "Manuelle Schritte:"
    echo "1. Gehe zu: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
    echo "2. Klicke 'New repository secret'"
    echo "3. Name: DISCORD_BOT_TOKEN"
    echo "4. Value: Kopiere diesen Token:"
    echo ""
    echo "$DISCORD_BOT_TOKEN"
    echo ""
    echo "5. Klicke 'Add secret'"
fi

echo ""
echo "🎉 Fertig! Der Bot ist jetzt vollständig eingerichtet."

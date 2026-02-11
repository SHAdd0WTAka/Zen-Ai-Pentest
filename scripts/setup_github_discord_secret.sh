#!/bin/bash
# Setup Discord Webhook als GitHub Secret

echo "🔐 Discord Webhook Secret Setup"
echo "==============================="
echo ""

# Der Discord Webhook URL (von dir bereitgestellt)
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1470872093473378448/itojPo72PMHvdyoxagYPAQjndVlMRwpgokDlPDxZIR_QoWGCLePsv5q4PYE4DenYo39-"

echo "Discord Webhook: ${DISCORD_WEBHOOK:0:50}..."
echo ""

# Mit gh CLI das Secret setzen
if command -v gh &> /dev/null; then
    echo "$DISCORD_WEBHOOK" | gh secret set DISCORD_WEBHOOK_URL --repo SHAdd0WTAka/Zen-Ai-Pentest
    echo "✅ Secret 'DISCORD_WEBHOOK_URL' wurde in GitHub hinterlegt!"
    echo ""
    echo "Du kannst das Secret hier überprüfen:"
    echo "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
else
    echo "⚠️  GitHub CLI nicht installiert."
    echo ""
    echo "Manuelle Schritte:"
    echo "1. Gehe zu: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
    echo "2. Klicke 'New repository secret'"
    echo "3. Name: DISCORD_WEBHOOK_URL"
    echo "4. Value: Kopiere die komplette URL:"
    echo ""
    echo "$DISCORD_WEBHOOK"
    echo ""
    echo "5. Klicke 'Add secret'"
fi

echo ""
echo "🎉 Fertig! Der Webhook ist jetzt sicher hinterlegt."

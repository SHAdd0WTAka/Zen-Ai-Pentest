#!/bin/bash
# Fix Frontend API URL Script

echo "═══════════════════════════════════════════════════════════"
echo "  FRONTEND API URL FIX"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Current API URL
API_URL="https://unleniently-hauriant-laurel.ngrok-free.dev"
echo "🎯 API URL: $API_URL"

# Fix permissions and patch
cd /home/atakan/zen-ai-pentest/web_ui/frontend/dist/assets

echo "📁 Changing file permissions..."
sudo chown $(whoami):$(whoami) index-DRK4O_6o.js

echo "🔧 Patching JS file..."
# Use sed to replace URLs
sed -i 's|begins-export-skill-pie\.trycloudflare\.com|unleniently-hauriant-laurel.ngrok-free.dev|g' index-DRK4O_6o.js
sed -i 's|brands-briefing-franklin-luggage\.trycloudflare\.com|unleniently-hauriant-laurel.ngrok-free.dev|g' index-DRK4O_6o.js

echo "✅ Verifying..."
COUNT=$(grep -c "unleniently-hauriant-laurel" index-DRK4O_6o.js)
echo "   Found $COUNT occurrences of new URL"

echo ""
echo "🚀 Deploying..."
cd /home/atakan/zen-ai-pentest/web_ui/frontend
npx wrangler pages deploy dist --project-name=zen-alpha-pentest --branch=main --commit-dirty=true

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🔗 Frontend: https://zen-alpha-pentest.pages.dev"
echo "🔗 API:      https://unleniently-hauriant-laurel.ngrok-free.dev"
echo ""
echo "⚠️  Wichtig: Diese ngrok-URL ist TEMPORÄR (max 2 Stunden)."
echo "   Für permanente URL: ngrok http 8000 --url=deine-statische-domain"
echo ""

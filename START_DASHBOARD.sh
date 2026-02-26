#!/bin/bash
echo "🚀 Zen AI Pentest Dashboard"
echo ""

cd /home/atakan/zen-ai-pentest/web_ui/frontend

echo "📦 Prüfe Dependencies..."
if [ ! -d "node_modules" ]; then
    echo "   Installiere npm packages (dauert 1-2 Minuten)..."
    npm install
fi

echo ""
echo "🌐 Starte Dashboard..."
echo ""
echo "   URLs:"
echo "   • http://localhost:5173/         ← Landing Page"
echo "   • http://localhost:5173/dashboard ← Agent Dashboard"
echo ""
echo "⏳ Starte Server..."
echo ""

npm run dev

#!/bin/bash
# Schneller Test nach Verbindungsproblemen

echo "🧪 Zen-Ai Kimi Personas - Schnelltest"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Prüfe ob Server läuft
if ! curl -s http://127.0.0.1:5000/api/v1/health >/dev/null 2>&1; then
    echo "⚠️  Server nicht erreichbar!"
    echo ""
    echo "Starte Server automatisch..."
    cd ~/Zen-Ai-Pentest/api
    nohup python3 kimi_personas_api.py --no-auth > /tmp/kimi_api.log 2>&1 &
    sleep 3
fi

# Teste API
echo "🔌 Teste API Verbindung..."
HEALTH=$(curl -s http://127.0.0.1:5000/api/v1/health 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Verbindung erfolgreich!"
    echo ""
    echo "API Status:"
    echo "$HEALTH" | python3 -m json.tool
    echo ""

    echo "Verfügbare Personas:"
    curl -s http://127.0.0.1:5000/api/v1/personas 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  • {k}: {v[\"name\"]}') for k,v in d['personas'].items()]"

    echo ""
    echo "Web UI: http://127.0.0.1:5000"
    echo ""
    echo "Test-URLs:"
    echo "  curl http://127.0.0.1:5000/api/v1/health"
    echo "  curl http://127.0.0.1:5000/api/v1/personas"
    echo "  curl http://127.0.0.1:5000/admin"

else
    echo "❌ Verbindung fehlgeschlagen!"
    echo ""
    echo "Mögliche Lösungen:"
    echo "1. Firewall prüfen: sudo ufw allow 5000"
    echo "2. Anderen Port nutzen: python3 api/kimi_personas_api.py -p 8080"
    echo "3. Logs prüfen: tail -f /tmp/kimi_api.log"
    echo "4. Diagnose: bash ~/Zen-Ai-Pentest/api/diagnose.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"

#!/bin/bash
# Zeigt Status des Kimi Personas API Servers

echo "🛡️ Zen-Ai Kimi Personas - Status"
echo "═══════════════════════════════════════════════════════════════"

API_PID=$(pgrep -f "kimi_personas_api.py" | head -1)

if [ -n "$API_PID" ]; then
    echo -e "\033[0;32m✅ Server läuft\033[0m"
    echo "   PID: $API_PID"
    echo "   URL: http://127.0.0.1:5000"
    echo "   Web UI: http://127.0.0.1:5000/"
    echo ""
    
    # API Health Check
    HEALTH=$(curl -s http://127.0.0.1:5000/api/v1/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   API Status: $(echo $HEALTH | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")"
        echo "   Personas: $(echo $HEALTH | python3 -c "import sys,json; print(json.load(sys.stdin)['personas_available'])")"
        echo "   Version: $(echo $HEALTH | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")"
    fi
    
    # Admin Stats
    STATS=$(curl -s http://127.0.0.1:5000/admin 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   Uptime: $(echo $STATS | python3 -c "import sys,json; print(json.load(sys.stdin)['uptime_formatted'])")"
        echo "   Requests: $(echo $STATS | python3 -c "import sys,json; print(json.load(sys.stdin)['stats']['total_requests'])")"
    fi
    
    echo ""
    echo "Verfügbare Befehle:"
    echo "  curl http://127.0.0.1:5000/api/v1/health"
    echo "  curl http://127.0.0.1:5000/api/v1/personas"
    echo "  curl http://127.0.0.1:5000/admin"
    echo ""
    echo "Server stoppen:"
    echo "  kill $API_PID"
    
else
    echo -e "\033[0;31m❌ Server nicht aktiv\033[0m"
    echo ""
    echo "Starten mit:"
    echo "  python3 ~/Zen-Ai-Pentest/api/kimi_personas_api.py --no-auth"
    echo ""
    echo "Oder im Hintergrund:"
    echo "  cd ~/Zen-Ai-Pentest/api && nohup python3 kimi_personas_api.py --no-auth > /tmp/kimi_api.log 2>&1 &"
fi

echo "═══════════════════════════════════════════════════════════════"

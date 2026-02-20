#!/bin/bash
# Kimi Personas API Server Management

ZEN_DIR="$HOME/Zen-Ai-Pentest"
API_SCRIPT="$ZEN_DIR/api/kimi_personas_api.py"
LOG_FILE="/tmp/kimi_api.log"
PID_FILE="/tmp/kimi_api.pid"

show_help() {
    echo "🛡️ Kimi Personas API Manager"
    echo ""
    echo "Verwendung: $0 {start|stop|restart|status|logs|test}"
    echo ""
    echo "Befehle:"
    echo "  start    - Server starten"
    echo "  stop     - Server stoppen"
    echo "  restart  - Server neu starten"
    echo "  status   - Status anzeigen"
    echo "  logs     - Logs anzeigen"
    echo "  test     - API Verbindung testen"
    echo "  diagnose - Vollständige Diagnose"
    echo ""
}

start_server() {
    if pgrep -f "kimi_personas_api.py" > /dev/null; then
        echo "⚠️  Server läuft bereits!"
        status
        return 1
    fi

    echo "🚀 Starte Server..."
    cd "$ZEN_DIR/api"
    nohup python3 "$API_SCRIPT" --no-auth > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if pgrep -f "kimi_personas_api.py" > /dev/null; then
        echo "✅ Server gestartet!"
        echo "   URL: http://127.0.0.1:5000"
        echo "   Web UI: http://127.0.0.1:5000/"
        return 0
    else
        echo "❌ Fehler beim Starten!"
        echo "Logs: $LOG_FILE"
        return 1
    fi
}

stop_server() {
    PID=$(pgrep -f "kimi_personas_api.py" | head -1)
    if [ -z "$PID" ]; then
        echo "⚠️  Server nicht aktiv"
        return 1
    fi

    echo "🛑 Stoppe Server (PID: $PID)..."
    kill $PID 2>/dev/null
    sleep 1

    if pgrep -f "kimi_personas_api.py" > /dev/null; then
        echo "⚠️  Erzwinge Beendigung..."
        kill -9 $PID 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo "✅ Server gestoppt"
}

restart_server() {
    stop_server
    sleep 1
    start_server
}

status() {
    bash "$ZEN_DIR/api/status.sh"
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Letzte 50 Zeilen Logs:"
        echo "═══════════════════════════════════════════════════════════════"
        tail -50 "$LOG_FILE"
    else
        echo "⚠️  Keine Logs gefunden"
    fi
}

test_api() {
    echo "🧪 Teste API Verbindung..."
    echo ""

    # Health
    echo -n "Health Check... "
    if curl -s http://127.0.0.1:5000/api/v1/health >/dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "❌ FEHLER"
        return 1
    fi

    # Personas
    echo -n "Personas Liste... "
    COUNT=$(curl -s http://127.0.0.1:5000/api/v1/personas 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['count'])")
    if [ "$COUNT" = "11" ]; then
        echo "✅ OK (11 Personas)"
    else
        echo "❌ FEHLER (nur $COUNT Personas)"
    fi

    # Admin
    echo -n "Admin Dashboard... "
    if curl -s http://127.0.0.1:5000/admin >/dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "❌ FEHLER"
    fi

    echo ""
    echo "Alle Tests abgeschlossen!"
}

run_diagnose() {
    bash "$ZEN_DIR/api/diagnose.sh"
}

# Hauptprogramm
case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_api
        ;;
    diagnose)
        run_diagnose
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac

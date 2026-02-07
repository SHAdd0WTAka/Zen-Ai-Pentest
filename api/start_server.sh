#!/bin/bash
# Kimi Personas API Server Starter

cd "$(dirname "$0")"

# Default Werte
HOST="${KIMI_API_HOST:-127.0.0.1}"
PORT="${KIMI_API_PORT:-5000}"
DEBUG="${KIMI_API_DEBUG:-false}"

echo "🚀 Starting Kimi Personas API Server..."
echo "═══════════════════════════════════════════════════════════════"

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    exit 1
fi

# Prüfe Dependencies
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installiere Dependencies..."
    pip3 install -r requirements-api.txt
fi

# Prüfe Personas
echo "🔍 Prüfe Personas..."
python3 -c "
import sys
sys.path.insert(0, '..')
from tools.kimi_helper import create_default_personas
create_default_personas()
"

# Start Server
echo ""
echo "🌐 Konfiguration:"
echo "   Host:  $HOST"
echo "   Port:  $PORT"
echo "   Debug: $DEBUG"
echo ""

if [ "$DEBUG" = "true" ]; then
    python3 kimi_personas_api.py -H "$HOST" -p "$PORT" -d
else
    python3 kimi_personas_api.py -H "$HOST" -p "$PORT"
fi

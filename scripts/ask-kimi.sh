#!/bin/bash
# Kimi CLI mit Personas/Skills

PERSONA_DIR="${KIMI_PERSONA_DIR:-$HOME/.config/kimi/personas}"
MODE="${1:-recon}"
shift 1 || true

# Lade System Prompt
if [[ -f "$PERSONA_DIR/$MODE.md" ]]; then
    SYSTEM_PROMPT=$(cat "$PERSONA_DIR/$MODE.md")
    echo "[Mode: $MODE aktiviert]" >&2
else
    echo "[Warnung: Persona $MODE nicht gefunden, nutze Standard]" >&2
    SYSTEM_PROMPT="Du bist ein hilfreicher Assistent."
fi

# Kombiniere System Prompt mit User Input
FULL_PROMPT="$SYSTEM_PROMPT

---
User Anfrage:
$@"

# An kimi-cli senden
if command -v kimi &> /dev/null; then
    echo "$FULL_PROMPT" | kimi ask -
else
    echo "Fehler: kimi-cli nicht gefunden. Bitte installieren: pip install kimi-cli" >&2
    exit 1
fi

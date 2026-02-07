#!/bin/bash
# Kimi CLI mit Personas/Skills

PERSONA_DIR="$HOME/.config/kimi/personas"
MODE="${1:-recon}"
shift 1

# Lade System Prompt
if [[ -f "$PERSONA_DIR/$MODE.md" ]]; then
    SYSTEM_PROMPT=$(cat "$PERSONA_DIR/$MODE.md")
    echo "[🧠 Mode: $MODE aktiviert]"
else
    echo "[⚠️ Persona $MODE nicht gefunden, nutze Standard]"
    SYSTEM_PROMPT="Du bist ein hilfreicher Assistent."
fi

# Kombiniere System Prompt mit User Input
FULL_PROMPT="$SYSTEM_PROMPT

User Anfrage:
$@"

# An kimi-cli senden (über stdin oder temp file)
echo "$FULL_PROMPT" | kimi ask -

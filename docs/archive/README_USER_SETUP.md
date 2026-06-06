# Zen-AI Pentest - Benutzer-Setup

> **Wichtig:** Jeder Benutzer muss seine eigenen API Keys konfigurieren!
> Die `.env` Datei enthält KEINE echten Keys und sollte niemals committed werden.

## Schnellstart für neue Benutzer

### 1. Konfiguration prüfen

```bash
python scripts/check_config.py
```

Zeigt den aktuellen Status aller Backends.

### 2. API Key einrichten

Wähle eines der unterstützten Backends:

#### Option A: Kimi (Moonshot AI) - Empfohlen
```bash
# Hol deinen Key bei: https://platform.moonshot.cn/
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "sk-dein-echter-key"
```

#### Option B: OpenRouter (Multi-Provider)
```bash
# Hol deinen Key bei: https://openrouter.ai/keys
python scripts/setup_wizard.py -b openrouter -m openrouter/auto -k "sk-or-..."
```

#### Option C: OpenAI
```bash
# Hol deinen Key bei: https://platform.openai.com/api-keys
python scripts/setup_wizard.py -b openai -m gpt-4o -k "sk-..."
```

### 3. Konfiguration testen

```bash
python scripts/check_config.py
```

Sollte anzeigen: `[green]Konfiguriert`

### 4. Kimi Helper nutzen

```bash
# One-Shot Anfrage
python tools/kimi_helper.py -p recon "Analysiere example.com"

# Interaktiver Modus
python tools/kimi_helper.py -i
```

## Multi-Backend Setup

Du kannst mehrere Backends gleichzeitig konfigurieren:

```bash
# Kimi als Standard
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "sk-kimi-key"

# OpenAI als Backup (manuelle .env editieren)
# Füge zur .env hinzu:
# export OPENAI_API_KEY="sk-openai-key"

# Dann wechseln mit:
python scripts/switch_model.py -b openai -m gpt-4o
```

## Wichtige Hinweise

### .env wird NIEMALS committed

```gitignore
# In .gitignore
.env
.env.backup
```

### Keys sind persönlich
- Teile deine API Keys **niemals**
- Jeder Entwickler verwendet seinen eigenen Key
- Bei der Arbeit im Team: Jeder führt `setup_wizard.py` einmal aus

### Kosten beachten
- Kimi: Günstig, gute Rate-Limits
- OpenRouter: Pay-per-use, viele Modelle
- OpenAI: GPT-4 teuer, GPT-3.5 günstig

## Troubleshooting

### "Kein gültiger API Key gefunden"
```bash
# Lösung: Setup durchführen
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "DEIN_KEY"
```

### "401 Unauthorized"
```bash
# Key ist ungültig oder abgelaufen
# Neuen Key generieren und neu konfigurieren
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "NEUER_KEY"
```

### Mehrere Backends wechseln
```bash
# Liste verfügbarer Backends
python scripts/switch_model.py --list

# Wechsle Backend
python scripts/switch_model.py -b openai

# Wechsle Modell
python scripts/switch_model.py -m gpt-4o-mini
```

## Backend-Vergleich

| Feature | Kimi | OpenRouter | OpenAI |
|---------|------|------------|--------|
| Preis | ⭐ Sehr günstig | Mittel | Teuer (GPT-4) |
| Speed | Schnell | Mittel | Schnell |
| Code-Qualität | ⭐ Sehr gut | Gut | ⭐ Sehr gut |
| Verfügbarkeit | China | Global | Global |
| Rate-Limits | Großzügig | Variiert | Streng |

## Support

Bei Problemen mit der Einrichtung:
1. `python scripts/check_config.py` ausführen
2. Fehlermeldung lesen
3. API Key auf Gültigkeit prüfen (Dashboard des Providers)
4. Neu konfigurieren mit `setup_wizard.py`

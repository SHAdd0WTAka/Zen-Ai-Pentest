# CI/CD Monitoring & Self-Healing

## Overview

Zen AI Pentest includes **self-monitoring GitHub Actions** that:
- Überwachen alle Workflows alle 20 Minuten
- Senden Benachrichtigungen bei Fehlern (Discord/Slack)
- Reparieren automatisch Code-Style-Probleme
- Retries für fehlgeschlagene Runs

## Workflows

### 1. Watcher (`watcher.yml`)

Läuft alle 20 Minuten und überprüft:
- ✅ Alle Workflows healthy?
- ❌ Failed runs in letzten 30 Minuten?
- ⚠️ Workflows, die länger als 15 Minuten laufen?

**Features:**
- Detaillierte GitHub Summary
- Discord-Benachrichtigung bei Fehlern
- Auto-Retry für failed workflows (bei manuellem Trigger)

### 2. Webhook Notifications (`webhook-notify.yml`)

Reagiert auf Workflow-Completion und sendet:
- Discord Embeds mit Status
- Slack Attachments
- JSON Payloads an custom Webhooks

### 3. Auto-Fix (`auto-fix.yml`)

Repariert automatisch:
- Line endings (CRLF → LF)
- Python formatting (black)
- Import sorting (isort)
- Basic linting issues (autopep8)

**Commits mit `[skip ci]`** um Endlosschleifen zu vermeiden.

## Setup

### Discord Notifications

```powershell
# Run setup script
.\scripts\setup-discord-webhook.ps1

# Oder manuell:
# 1. Discord Server → Integrations → Webhooks → New Webhook
# 2. GitHub Repo → Settings → Secrets → New repository secret
#    Name: DISCORD_WEBHOOK
#    Value: https://discord.com/api/webhooks/...
```

### Slack Notifications

```bash
# Slack App mit Incoming Webhooks erstellen
# GitHub Secret hinzufügen:
#   Name: SLACK_WEBHOOK
#   Value: https://hooks.slack.com/services/...
```

## Konfiguration

### Watcher-Intervall ändern

`.github/workflows/watcher.yml`:
```yaml
on:
  schedule:
    - cron: '*/20 * * * *'  # Alle 20 Minuten
    # Alternativen:
    # - cron: '0 * * * *'     # Jede Stunde
    # - cron: '*/5 * * * *'   # Alle 5 Minuten
```

### Benachrichtigungs-Filter

Nur bei Fehlern benachrichtigen:
```yaml
jobs:
  notify:
    if: github.event.workflow_run.conclusion == 'failure'
```

### Auto-Fix deaktivieren

Bestimmte Fixes überspringen:
```yaml
- name: Fix line endings
  if: false  # Deaktiviert
```

## WebSocket Alternative (für Echtzeit)

Für Echtzeit-Monitoring kannst du einen WebSocket-Server einrichten:

```python
# webhook_server.py
import asyncio
import websockets
import json

connected = set()

async def handler(websocket):
    connected.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            # Broadcast an alle verbundenen Clients
            for conn in connected:
                await conn.send(json.dumps({
                    "type": "workflow_update",
                    "data": data
                }))
    finally:
        connected.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
```

GitHub Actions sendet dann an diesen Server:
```yaml
- name: Send to WebSocket
  run: |
    curl -X POST http://your-server:8765/webhook \
      -d '{"status": "${{ github.event.workflow_run.conclusion }}"}'
```

## Troubleshooting

### Webhook nicht erreichbar

```yaml
- name: Test Webhook
  run: |
    curl -I ${{ secrets.DISCORD_WEBHOOK }}
  continue-on-error: true
```

### Secret nicht gesetzt

```yaml
- name: Check Secret
  run: |
    if [ -z "${{ secrets.DISCORD_WEBHOOK }}" ]; then
      echo "::warning::DISCORD_WEBHOOK not set"
      exit 0
    fi
```

### Rate Limits

GitHub API hat Rate Limits:
- 1000 Requests/Stunde für Actions
- Watcher reduziert auf alle 20 Minuten = max 72 Requests/Tag

## Dashboard

Einfaches Status-Dashboard lokal hosten:

```html
<!-- status-dashboard.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Zen AI Pentest - CI Status</title>
  <script>
    const ws = new WebSocket('ws://localhost:8765');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      document.getElementById('status').innerHTML += 
        `<p>${new Date().toLocaleTimeString()}: ${data.status}</p>`;
    };
  </script>
</head>
<body>
  <h1>CI/CD Status</h1>
  <div id="status"></div>
</body>
</html>
```

## Zusammenfassung

| Feature | Workflow | Trigger |
|---------|----------|---------|
| Health Check | `watcher.yml` | Alle 20 Minuten |
| Notifications | `webhook-notify.yml` | On completion |
| Auto-Fix | `auto-fix.yml` | On failure / Manual |
| Retry | In `watcher.yml` | Manual only |

---

*Automated monitoring keeps your CI/CD healthy!*

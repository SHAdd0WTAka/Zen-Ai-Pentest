# Slack & Discord Webhook Setup Guide

> Konfiguration für Zen-AI-Pentest Repository Notifications

---

## 🎯 Übersicht

Die Health-Check und Notification Workflows können Benachrichtigungen an Slack und Discord senden:

- **Health Score < 50** (Critical)
- **Workflow Failures**
- **Security Alerts**
- **New Releases**

---

## 📱 Slack Webhook Einrichtung

### Schritt 1: Slack App Erstellen

1. Gehe zu: https://api.slack.com/apps
2. Klicke **"Create New App"**
3. Wähle **"From scratch"**
4. **App Name:** `Zen-AI-Pentest Bot`
5. **Workspace:** Deinen Workspace auswählen
6. Klicke **"Create App"**

### Schritt 2: Webhook Aktivieren

1. Im linken Menü: **"Incoming Webhooks"**
2. Schalte um auf **"On"**
3. Scrolle runter zu **"Webhook URLs for Your Workspace"**
4. Klicke **"Add New Webhook to Workspace"**
5. Wähle den Channel (z.B. `#github-notifications`)
6. Klicke **"Allow"**

### Schritt 3: Webhook URL Kopieren

Die URL sieht so aus:
```
https://hooks.slack.com/services/T.../B.../...
```

**→ Diese URL brauchst du für GitHub Secrets!**

---

## 💬 Discord Webhook Einrichtung

### Schritt 1: Server-Einstellungen

1. Öffne Discord
2. Klicke auf deinen **Server-Namen** (oben links)
3. Wähle **"Server Settings"**
4. Gehe zu **"Integrations"**
5. Klicke **"Webhooks"**
6. Klicke **"New Webhook"**

### Schritt 2: Webhook Konfigurieren

1. **Name:** `Zen-AI-Pentest`
2. **Channel:** Wähle einen Text-Channel (z.B. `#github`)
3. Optional: Lade ein Avatar-Bild hoch
4. Klicke **"Copy Webhook URL"**

### Schritt 3: Webhook URL

Die URL sieht so aus:
```
https://discord.com/api/webhooks/.../...
```

**→ Diese URL brauchst du für GitHub Secrets!**

---

## 🔐 GitHub Secrets Hinzufügen

### Option 1: Manuelle Einrichtung

1. Gehe zu: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions`
2. Klicke **"New repository secret"**
3. Füge folgende Secrets hinzu:

#### Slack Secret
- **Name:** `SLACK_WEBHOOK_URL`
- **Value:** `https://hooks.slack.com/services/...`

#### Discord Secret
- **Name:** `DISCORD_WEBHOOK_URL`
- **Value:** `https://discord.com/api/webhooks/.../...`

### Option 2: Via API (mit Token)

```bash
# Slack Secret
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/SHAdd0WTAka/Zen-Ai-Pentest/actions/secrets/SLACK_WEBHOOK_URL \
  -d '{
    "encrypted_value": "YOUR_ENCRYPTED_WEBHOOK_URL",
    "key_id": "YOUR_KEY_ID"
  }'

# Discord Secret
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/SHAdd0WTAka/Zen-Ai-Pentest/actions/secrets/DISCORD_WEBHOOK_URL \
  -d '{
    "encrypted_value": "YOUR_ENCRYPTED_WEBHOOK_URL",
    "key_id": "YOUR_KEY_ID"
  }'
```

---

## 🧪 Testen

### Slack Test
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🧪 Test von Zen-AI-Pentest"}' \
  YOUR_SLACK_WEBHOOK_URL
```

### Discord Test
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"content":"🧪 Test von Zen-AI-Pentest"}' \
  YOUR_DISCORD_WEBHOOK_URL
```

---

## 📋 Verfügbare Notifications

### Slack
- ✅ Repository Health Score Alerts
- ✅ Workflow Failure Notifications
- ✅ Security Vulnerability Alerts
- ✅ Release Notifications

### Discord
- ✅ Repository Health Score Alerts
- ✅ Workflow Failure Notifications
- ✅ Security Vulnerability Alerts
- ✅ New Contributor Welcome

---

## 🔗 Schnell-Links

| Service | URL |
|---------|-----|
| GitHub Secrets | https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions |
| Slack API | https://api.slack.com/apps |
| Discord Webhooks | Server Settings → Integrations |

---

## ❓ Troubleshooting

### Slack: "invalid_auth"
- Webhook URL ist falsch kopiert
- App wurde deaktiviert

### Discord: "404 Not Found"
- Webhook wurde gelöscht
- Falsche URL

### GitHub: "Secret not found"
- Name muss exakt sein: `SLACK_WEBHOOK_URL` oder `DISCORD_WEBHOOK_URL`
- Groß-/Kleinschreibung beachten

---

**Brauchst du Hilfe bei der Einrichtung?** 🚀

# Discord Server Setup Guide

## 🎮 Server: https://discord.gg/zJZUJwK9AC

## Einrichtung

### 1. Discord Developer Portal
- URL: https://discord.com/developers/applications/1470531751595086017
- Application ID: `1470531751595086017`

### 2. Localhost Testing mit ngrok
```bash
# ngrok installieren
npm install -g ngrok

# Tunnel auf Port 8080 starten
ngrok http 8080

# Ausgabe kopieren: https://xxxx.ngrok-free.app
```

### 3. Discord App konfigurieren
- **Interactions Endpoint URL**: `https://[ngrok-url]/api/discord`
- **OAuth2 Redirects**: `https://[ngrok-url]/auth/callback`

### 4. Bot Token
Für GitHub Notifications:
1. Developer Portal → Bot → Add Bot
2. Token kopieren
3. In GitHub Secrets als `DISCORD_WEBHOOK_URL` speichern

## Server Struktur (Vorschlag)

```
📁 Zen-AI-Pentest
├── 📢 announcements
├── 🔔 ci-cd-notifications
├── 💬 general
├── 🆘 support
├── 💡 feature-requests
├── 🐛 bug-reports
└── 📊 statistics
```

## Webhook Integration

Aktueller Webhook für Tests:
```
https://discord.com/api/webhooks/1467204465177399337/_HuBAnK--fKhE3qT2eP_kUrV_kGvQBYZ2TOLyHAdnQO0741XS77JfTfTvCICpGnQfViB
```

**⚠️ Für Produktion neuen Webhook im Discord-Server erstellen!**

## Bot Features

- ✅ CI/CD Build Notifications
- ✅ Release Announcements
- ✅ Issue/PR Updates
- ✅ Security Alerts
- ⏳ Custom Commands (coming soon)

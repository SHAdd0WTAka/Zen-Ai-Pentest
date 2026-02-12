# Telegram Integration Setup

## Einrichtung von Telegram Notifications für Zen-AI-Pentest

---

## 🎯 Übersicht

Das Telegram-Integrationssystem sendet automatische Benachrichtigungen für:
- ✅ Workflow-Ergebnisse (CI/CD)
- 📋 Issues (erstellt/geschlossen)
- 🔀 Pull Requests (geöffnet/gemergt)
- 🚀 Releases (veröffentlicht)
- 🧪 Manuelle Test-Nachrichten

---

## 📱 Schritt-für-Schritt Einrichtung

### Schritt 1: Telegram Bot erstellen

1. Öffne Telegram und suche nach **"@BotFather"**
2. Starte den Bot mit **"/start"**
3. Sende **"/newbot"**
4. Gib einen Namen ein: `Zen-AI-Pentest Bot`
5. Gib einen Username ein: `zen_ai_pentest_bot` (muss mit _bot enden)
6. **WICHTIG**: Kopiere den **Token** (z.B. `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Schritt 2: Chat ID ermitteln

#### Option A: Persönlicher Chat (Direktnachrichten)

1. Suche deinen Bot und starte ihn
2. Sende eine Nachricht an den Bot
3. Öffne im Browser:
   ```
   https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates
   ```
4. Suche nach `"chat":{"id":123456789` - das ist deine Chat ID

#### Option B: Gruppenchat (Empfohlen für Teams)

1. Füge den Bot zu einer Gruppe hinzu
2. Mache den Bot zum Admin (optional, für mehr Funktionen)
3. Sende eine Nachricht in die Gruppe
4. Öffne: `https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates`
5. Die Chat ID für Gruppen beginnt mit `-` (z.B. `-123456789`)

### Schritt 3: Secrets in GitHub hinterlegen

1. Gehe zu: **Repository Settings** → **Environments** → **production**
2. Klicke **"Add environment secret"**
3. Füge zwei Secrets hinzu:

| Secret Name | Wert |
|-------------|------|
| `TELEGRAM_BOT_TOKEN` | Dein Bot Token von BotFather |
| `TELEGRAM_CHAT_ID` | Deine Chat ID (z.B. `123456789` oder `-123456789` für Gruppen) |

---

## 🚀 Testen

### Automatischer Test

1. Gehe zu: **Actions** → **Telegram Notifications**
2. Klicke **"Run workflow"**
3. Gib eine Testnachricht ein (optional)
4. Klicke **"Run workflow"**
5. Du bekommst eine E-Mail zur Genehmigung (Required Reviewer)
6. Genehmige den Workflow
7. Check deinen Telegram-Chat!

### Manueller Test (lokal)

```bash
# Mit curl
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=Test message from Zen-AI-Pentest" \
  -d "parse_mode=HTML"
```

---

## 📊 Benachrichtigungs-Typen

| Event | Auslöser | Nachricht |
|-------|----------|-----------|
| **Workflow Success** | CI/CD Pipeline erfolgreich | ✅ Workflow SUCCESS |
| **Workflow Failed** | CI/CD Pipeline fehlgeschlagen | ❌ Workflow FAILED |
| **Issue Opened** | Neues Issue erstellt | 📋 Issue opened |
| **Issue Closed** | Issue geschlossen | ✅ Issue closed |
| **PR Opened** | Pull Request erstellt | 🔀 PR opened |
| **PR Merged** | PR gemergt | ✅ PR MERGED |
| **Release** | Neue Version veröffentlicht | 🚀 New Release |

---

## 🔒 Sicherheit

- ✅ Secrets sind verschlüsselt in GitHub Environments
- ✅ Keine Tokens im Code oder Chat
- ✅ Required Reviewer für alle Ausführungen
- ✅ Maskierung in Logs

---

## 🐛 Fehlerbehebung

### "Chat not found"
- Prüfe ob die Chat ID korrekt ist
- Für Gruppen: Muss mit `-` beginnen
- Bot muss im Chat sein (bei Gruppen)

### "Bot was blocked"
- Starte den Bot im Chat mit `/start`
- Prüfe ob du den Bot nicht blockiert hast

### "Wrong HTTP code"
- Token ist ungültig/abgelaufen
- Neuen Token bei @BotFather generieren

### Keine Nachrichten erhalten
- Secrets in GitHub prüfen (Environment: production)
- Workflow wurde genehmigt?
- Chat ID korrekt?

---

## 📞 Support

Bei Problemen:
1. BotFather: @BotFather
2. GitHub Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues
3. Discord: https://discord.gg/BSmCqjhY

---

**Letzte Aktualisierung**: 2026-02-11

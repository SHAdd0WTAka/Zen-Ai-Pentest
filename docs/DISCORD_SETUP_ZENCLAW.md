# 🔌 Discord Integration für ZenClaw

> Sichere Webhook-Einrichtung für den Guardian Bot

## 🎯 Übersicht

ZenClaw sendet automatisch Benachrichtigungen an Discord bei:
- 🚀 Pushes zum main Branch
- 🐛 Neuen/resolved Issues
- ✅/❌ Workflow Status (CI/CD)
- 🧪 Manuelle Test-Nachrichten

## 🛡️ Sicherheitshinweis

**WICHTIG:** Der Discord Webhook URL ist ein **Secret**!
- ❌ Niemals im Code speichern
- ❌ Niemals im Chat posten
- ❌ Niemals loggen
- ✅ Nur in GitHub Secrets hinterlegen

## 📋 Schritt-für-Schritt Anleitung

### Schritt 1: Discord Webhook erstellen (Manuell)

1. **Discord öffnen**
   - Server: "Zen-Ai" auswählen

2. **Server Settings**
   - Klicke auf Servernamen (Dropdown)
   - Wähle "Servereinstellungen"

3. **Integrations**
   - Linkes Menü: "Integrationen"
   - Klicke: "Webhooks"
   - Klicke: "Neuer Webhook"

4. **Webhook konfigurieren**
   - **Name:** `ZenClaw Guardian`
   - **Kanal:** Wähle `#zenclaw-logs` (oder erstelle ihn)
   - **Avatar:** Lade ZenClaw Logo hoch (optional)
   - Klicke: "Webhook-URL kopieren"

5. **URL kopieren**
   - Sieht aus wie: `https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz`
   - **Diese URL ist GEHEIM!**

### Schritt 2: Secret in GitHub hinzufügen

1. **Gehe zu GitHub Repository**
   - URL: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions`

2. **Neues Secret erstellen**
   - Klicke: "New repository secret"
   - **Name:** `DISCORD_WEBHOOK_URL`
   - **Value:** Füge die kopierte Discord URL ein
   - Klicke: "Add secret"

3. **Verifizierung**
   - Secret sollte jetzt in der Liste erscheinen
   - Wert ist maskiert (zeigt nur `***`)

### Schritt 3: Testen

1. **Manueller Test**
   - Gehe zu: Actions → ZenClaw Discord Integration
   - Klicke: "Run workflow"
   - Gib Test-Nachricht ein
   - Klicke: "Run workflow"

2. **Automatischer Test**
   - Mache einen Test-Commit
   - Warte auf Benachrichtigung in Discord

## 🎨 Discord Embed Format

ZenClaw sendet farbcodierte Nachrichten:

| Event | Farbe | Bedeutung |
|-------|-------|-----------|
| 🚀 Push | 🟢 Grün | Neue Code-Änderung |
| 🐛 Issue Open | 🔴 Rot | Problem aufgetreten |
| ✅ Issue Close | 🟢 Grün | Problem gelöst |
| ✅ Workflow OK | 🟢 Grün | CI/CD erfolgreich |
| ❌ Workflow Fail | 🔴 Rot | CI/CD fehlgeschlagen |
| 🧪 Test | 🔵 Blau | Manuelle Nachricht |

## 🔧 Fehlerbehebung

### "Discord notification failed"
- Webhook URL korrekt in Secrets?
- Kanal existiert noch?
- ZenClaw hat Schreibberechtigung?

### Keine Nachrichten trotz korrekter Konfiguration
- Workflow überhaupt gelaufen? (Actions Tab prüfen)
- Event-Filter prüfen (nur main branch?)
- Secret-Name exakt `DISCORD_WEBHOOK_URL`?

## 📝 Beispiel Payload

```json
{
  "embeds": [{
    "title": "🚀 Push to main",
    "description": "Commit: feat: Add new feature",
    "color": 3066993,
    "timestamp": "2026-02-16T04:00:00Z",
    "footer": {
      "text": "ZenClaw Guardian | push"
    },
    "fields": [
      {
        "name": "Repository",
        "value": "SHAdd0WTAka/Zen-Ai-Pentest",
        "inline": true
      },
      {
        "name": "Actor",
        "value": "SHAdd0WTAka",
        "inline": true
      }
    ]
  }]
}
```

## 🔐 Sicherheits-Checkliste

- [ ] Webhook URL nur in GitHub Secrets
- [ ] Keine Logs mit Webhook URL
- [ ] Kanal-Berechtigungen geprüft
- [ ] Test erfolgreich durchgeführt
- [ ] ZenClaw als Mod/Admin hinzugefügt

## 📞 Support

Bei Problemen:
1. `@Kimi` im GitHub Chat fragen
2. ZenClaw Status prüfen: `!status`
3. Webhook testen via curl (lokal)

---

**Erstellt:** 2026-02-16  
**Version:** 1.0  
**Autor:** Kimi AI (Lead Architect)

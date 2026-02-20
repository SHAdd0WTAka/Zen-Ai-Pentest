# 🔐 Discord Security Quickstart

Schnelle Einrichtung der Discord-Server-Sicherheit.

---

## 🎯 Ziel

- ✅ Nur Server-Mitglieder können Inhalte sehen
- ✅ Normale Mitglieder können **keine** Server-Settings ändern
- ✅ Automatische Member-Rollen-Vergabe

---

## ⚡ Schnell-Setup (30 Sekunden)

### Option A: Mit Bot (Empfohlen)

```bash
# 1. Bot-Token setzen
export DISCORD_BOT_TOKEN="dein_bot_token"

# 2. Bot starten
python scripts/discord_security_bot.py

# 3. Im Discord eingeben:
/zen-security-setup
```

### Option B: Python Script

```bash
export DISCORD_BOT_TOKEN="dein_bot_token"
python scripts/setup_discord_permissions.py
```

### Option C: Manuell

Siehe [DISCORD_SERVER_SETUP.md](DISCORD_SERVER_SETUP.md)

---

## 📋 Befehle

| Befehl | Beschreibung | Wer kann es? |
|--------|--------------|--------------|
| `/zen-security-setup` | Konfiguriert Server komplett | Nur Admins |
| `/zen-security-check` | Prüft aktuelle Sicherheit | Nur Admins |
| `/zen-add-member @user` | Weist Member-Rolle zu | Mods & Admins |

---

## 🔒 Was wird konfiguriert?

```
Vorher:
├─ @everyone (alle Internet-User)
│  └─ ✅ Kann alles sehen (UNGESICHERT!)

Nachher:
├─ @everyone (alle Internet-User)
│  └─ ❌ Kann NICHTS sehen
├─ Member (Server-Mitglieder)
│  ├─ ✅ Chat lesen/schreiben
│  ├─ ✅ Voice-Chat
│  └─ ❌ Keine Admin-Rechte
├─ Moderator
│  ├─ ✅ Alles wie Member
│  ├─ ✅ Kick/Timeout
│  └─ ❌ Keine Server-Settings
└─ Admin
   └─ ✅ Voller Zugriff
```

---

## 🚨 WICHTIG

1. **Bot braucht Rechte:**
   - Server verwalten
   - Rollen verwalten
   - Kanäle verwalten

2. **Rollen-Hierarchie:**
   ```
   Admin
   Moderator
   Member
   Bot (muss über Member sein!)
   @everyone
   ```

3. **Testen:** Probiere es erst auf einem Test-Server!

---

## 🆘 Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Bot hat nicht genügend Rechte" | Bot-Rolle höher in Hierarchie verschieben |
| "Member sehen nichts" | Prüfe ob Member-Rolle existiert |
| "Niemand kann schreiben" | Channel-Berechtigungen für Member aktivieren |

---

## 📞 Hilfe

- Detaillierte Anleitung: [DISCORD_SERVER_SETUP.md](DISCORD_SERVER_SETUP.md)
- Discord Support: https://support.discord.com

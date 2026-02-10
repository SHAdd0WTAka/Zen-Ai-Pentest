# 🔒 Discord Server Berechtigungs-Setup

Diese Anleitung hilft dir dabei, deinen Discord-Server so zu konfigurieren, dass:
- ✅ **Nur Server-Mitglieder** den Inhalt sehen können
- ✅ **Normale Mitglieder** können **keine** Server-Settings ändern
- ✅ **Nur Admins/Mods** haben Verwaltungsrechte

---

## 🚀 Schnell-Setup (Automatisch)

### Option 1: Discord Bot Commands (Empfohlen)

Füge diesen Bot zu deinem Server hinzu und führe die Commands aus:

```bash
# Im Discord-Server eingeben:

!zen-setup-security
```

Dieser Befehl konfiguriert automatisch:
- `@everyone` Rolle: Keine Channel-Sichtbarkeit
- `Member` Rolle: Basis-Berechtigungen ohne Admin-Rechte
- `Admin` Rolle: Vollzugriff

---

## 🔧 Manuelles Setup (Schritt-für-Schritt)

### Schritt 1: Server-Einstellungen öffnen
1. Klicke auf deinen **Servernamen** (oben links)
2. Wähle **"Servereinstellungen"**

### Schritt 2: @everyone Rolle einschränken

1. Gehe zu **"Rollen"** → **"Default Permissions"** oder **"@everyone"**
2. Deaktiviere ALLE Berechtigungen für `@everyone`:

**Textkanal-Berechtigungen:**
- [ ] `Kanäle sehen` ❌
- [ ] `Nachrichten senden` ❌
- [ ] `Nachrichtenverlauf lesen` ❌
- [ ] `Links einbetten` ❌
- [ ] `Dateien anhängen` ❌
- [ ] `Externe Emojis verwenden` ❌
- [ ] `Externe Sticker verwenden` ❌
- [ ] `Mitglieder erwähnen` ❌
- [ ] `@everyone` erwähnen ❌
- [ ] `@here` erwähnen ❌
- [ ] `Reaktionen hinzufügen` ❌

**Sprachkanal-Berechtigungen:**
- [ ] `Kanäle sehen` ❌
- [ ] `Verbinden` ❌
- [ ] `Sprechen` ❌
- [ ] `Video` ❌

**Allgemeine Berechtigungen:**
- [ ] `Administrator` ❌
- [ ] `Server verwalten` ❌
- [ ] `Rollen verwalten` ❌
- [ ] `Kanäle verwalten` ❌
- [ ] `Mitglieder kicken` ❌
- [ ] `Mitglieder bannen` ❌

### Schritt 3: Member-Rolle erstellen

1. Klicke auf **"+ Rolle erstellen"**
2. Name: `Member`
3. Farbe: Beliebig
4. Berechtigungen (nur diese aktivieren):

**Textkanal-Berechtigungen:**
- [x] `Kanäle sehen` ✅
- [x] `Nachrichten senden` ✅
- [x] `Nachrichtenverlauf lesen` ✅
- [x] `Links einbetten` ✅
- [x] `Dateien anhängen` ✅
- [x] `Externe Emojis verwenden` ✅
- [x] `Reaktionen hinzufügen` ✅

**Sprachkanal-Berechtigungen:**
- [x] `Kanäle sehen` ✅
- [x] `Verbinden` ✅
- [x] `Sprechen` ✅
- [x] `Video` ✅
- [x] `Aktivitäten verwenden` ✅

**Allgemeine Berechtigungen (ALLES deaktivieren!):**
- [ ] `Administrator` ❌
- [ ] `Server verwalten` ❌
- [ ] `Rollen verwalten` ❌
- [ ] `Kanäle verwalten` ❌
- [ ] `Mitglieder kicken` ❌
- [ ] `Mitglieder bannen` ❌
- [ ] `Timeout vergeben` ❌
- [ ] `Nachrichten verwalten` ❌
- [ ] `Erwähnungen verwalten` ❌
- [ ] `Server-Insights sehen` ❌
- [ ] `Webhooks verwalten` ❌
- [ ] `Server-Expressions verwalten` ❌
- [ ] `Events verwalten` ❌

### Schritt 4: Moderator-Rolle erstellen (Optional)

1. Erstelle Rolle: `Moderator`
2. Berechtigungen:
   - [x] `Kanäle sehen`, `Nachrichten senden`, etc.
   - [x] `Nachrichten verwalten` (löschen)
   - [x] `Mitglieder kicken`
   - [x] `Timeout vergeben`
   - [ ] `Administrator` (NEIN!)

### Schritt 5: Admin-Rolle erstellen

1. Erstelle Rolle: `Admin`
2. Berechtigungen:
   - [x] `Administrator` ✅ (aktiviert automatisch alles)

### Schritt 6: Channel-Überschreibungen prüfen

**WICHTIG:** Prüfe jeden Channel auf spezielle Berechtigungen:

1. Klicke auf einen Channel → **"Kanaleinstellungen"** (Zahnrad)
2. Gehe zu **"Berechtigungen"**
3. Entferne ALLE `@everyone` Überschreibungen
4. Füge nur `Member` Rolle hinzu mit View/Send-Rechten

---

## 🛡️ Sicherheitscheckliste

| Berechtigung | @everyone | Member | Mod | Admin |
|--------------|-----------|--------|-----|-------|
| Kanäle sehen | ❌ | ✅ | ✅ | ✅ |
| Nachrichten senden | ❌ | ✅ | ✅ | ✅ |
| Nachrichtenverlauf | ❌ | ✅ | ✅ | ✅ |
| Server verwalten | ❌ | ❌ | ❌ | ✅ |
| Rollen verwalten | ❌ | ❌ | ❌ | ✅ |
| Kanäle verwalten | ❌ | ❌ | ❌ | ✅ |
| Mitglieder kicken | ❌ | ❌ | ✅ | ✅ |
| Mitglieder bannen | ❌ | ❌ | ❌ | ✅ |
| Administrator | ❌ | ❌ | ❌ | ✅ |

---

## 🔐 Automations-Skript

Falls du einen Discord Bot hast, kannst du diesen Code verwenden:

```python
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_security(ctx):
    """Konfiguriert Server-Sicherheit automatisch"""
    guild = ctx.guild
    
    # 1. @everyone Rolle einschränken
    everyone = guild.default_role
    await everyone.edit(
        permissions=discord.Permissions(
            # ALLES deaktiviert
            read_messages=False,
            send_messages=False,
            connect=False,
            speak=False,
        )
    )
    
    # 2. Member Rolle erstellen/updaten
    member_role = discord.utils.get(guild.roles, name="Member")
    if not member_role:
        member_role = await guild.create_role(
            name="Member",
            permissions=discord.Permissions(
                # Nur Basis-Rechte
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                embed_links=True,
                attach_files=True,
                use_external_emojis=True,
                add_reactions=True,
                connect=True,
                speak=True,
                use_voice_activation=True,
            )
        )
    
    # 3. Allen aktuellen Mitgliedern die Member-Rolle geben
    for member in guild.members:
        if not member.bot and member_role not in member.roles:
            try:
                await member.add_roles(member_role)
            except:
                pass
    
    await ctx.send("✅ Server-Sicherheit konfiguriert!\n\n"
                   "• @everyone kann nichts mehr sehen\n"
                   "• Member haben nur Basis-Rechte\n"
                   "• Server-Einstellungen nur für Admins")

bot.run('DEIN_BOT_TOKEN')
```

---

## ⚠️ Wichtige Hinweise

1. **Teste zuerst auf einem Test-Server!**
2. **Mache einen Backup** deines Servers vorher
3. **Prüfe alle Channel** - manche haben eigene Berechtigungen
4. **Bot-Rollen** müssen höher in der Hierarchie sein als Member

---

## 📞 Support

Bei Problemen:
1. Discord Support: https://support.discord.com
2. Zen AI Pentest Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues

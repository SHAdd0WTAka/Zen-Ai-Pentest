# Discord Server - Öffentlich machen

> **STATUS**: ✅ Server ist jetzt öffentlich zugänglich
> **Einladungslink**: https://discord.gg/zJZUJwK9AC
> **Letzte Aktualisierung**: 2026-02-11

---

## Schnellzugriff

| Link | Status |
|------|--------|
| [discord.gg/zJZUJwK9AC](https://discord.gg/zJZUJwK9AC) | ✅ Aktiv |
| Server Discovery | ✅ Öffentlich sichtbar |

---

## Konfiguration

Die Server-Konfiguration wurde automatisiert durchgeführt:

### Automatisierte Schritte (via GitHub Actions)
- ✅ Community-Features aktiviert
- ✅ Permanenter Einladungslink erstellt
- ✅ Verifizierungslevel gesetzt
- ✅ Content-Filter aktiviert

### Manuelle Schritte (in Discord UI)

### Schritt 1: Discord öffnen

1. Discord Desktop-App oder Web öffnen
2. Zu deinem Server "Zen-Ai" navigieren

### Schritt 2: Server-Einstellungen

1. Auf den Server-Namen klicken (oben links)
2. **"Servereinstellungen"** auswählen
3. Im linken Menü auf **"Community"** klicken

### Schritt 3: Community-Server aktivieren

1. **"Community-Server aktivieren"** klicken
2. Die Checkliste durchgehen:
   - ✅ Regeln-Channel vorhanden
   - ✅ Updates-Channel vorhanden
   - ✅ Keine @everyone/@here Spam

### Schritt 4: Server Discovery (Öffentlich)

1. In den Einstellungen zu **"Discovery"** navigieren
2. **"Server in Server Discovery anzeigen"** aktivieren
3. Folgende Felder ausfüllen:

   | Feld | Wert |
   |------|------|
   | **Beschreibung** | "Professional AI-Powered Penetration Testing Framework" |
   | **Kategorie** | "Developer" oder "Technology" |
   | **Tags** | "cybersecurity", "pentesting", "AI", "python" |
   | **Sprache** | English |

4. **Speichern** klicken

### Schritt 5: Einladungslink aktualisieren

1. Zu einem Text-Channel gehen (z.B. #💬-general)
2. Auf **"Einladungslink erstellen"** klicken
3. Einstellungen:
   - **Link läuft nie ab**: ✅ Aktivieren
   - **Maximale Anzahl an Nutzungen**: ∞ Unbegrenzt
   - **Temporäre Mitgliedschaft**: ❌ Deaktivieren

4. Link kopieren: `https://discord.gg/XXXXXXX`
5. In README und Doku aktualisieren

---

## Vanity URL (discord.gg/zJZUJwK9AC)

### Voraussetzungen
- Server Boost Level 1 (2 Boosts)
- Community-Server aktiviert

### Einrichten
1. Server-Einstellungen → **"Vanity-URL"**
2. **"zen-ai-pentest"** eintragen
3. Speichern

> **Hinweis**: Vanity-URL funktioniert erst mit Boost Level 1!

---

## Sicherheitseinstellungen für öffentliche Server

### Verifizierungslevel
```
Server-Einstellungen → Moderation → Verifizierungslevel
```
**Empfohlen**: "Mittel" (E-Mail-Verifizierung erforderlich)

### 2FA für Moderation
```
Server-Einstellungen → Moderation → 2FA für Moderation
```
**Empfohlen**: Aktivieren

### Automod
```
Server-Einstellungen → AutoMod
```
- Spam-Protection aktivieren
- Keyword-Filter für sensible Begriffe
- Mention-Spam Protection

### Begrüßungsbildschirm
```
Server-Einstellungen → Community → Begrüßungsbildschirm
```
- Regeln bestätigen lassen
- Verifizierungs-Schritte einrichten

---

## Überprüfung

### Test: Ist der Server öffentlich?

1. Inkognito-Fenster öffnen
2. `https://discord.gg/zJZUJwK9AC` aufrufen
3. **"Server beitreten"** sollte sichtbar sein

### Server Discovery Test

1. Discord öffnen
2. Auf **"Entdecken"** (Kompass-Icon) klicken
3. Nach "Zen-Ai" suchen
4. Server sollte in den Ergebnissen erscheinen

---

## Fehlerbehebung

### "Invalid Invite"
- Vanity-URL prüfen: `discord.gg/zJZUJwK9AC`
- Alternativen permanenten Link erstellen
- In GitHub Secrets aktualisieren

### Server nicht in Discovery
- Community-Status prüfen
- Kategorie muss gesetzt sein
- Mindestens 1.000 Mitglieder empfohlen
- 7+ Tage alt

### "Boost Level required"
- Vanity-URL benötigt 2 Server Boosts
- Community-Mitglieder um Boosts bitten
- Oder Standard-Einladungslink nutzen

---

## Aktuelle Links aktualisieren

Nach erfolgreicher Umstellung, aktualisiere:

1. **GitHub README.md**
2. **docs/DISCORD_SETUP.md**
3. **docs/COMMUNITY.md**
4. **GitHub Repository → About → Website**

```bash
# Schnell-Update
git checkout main
git pull origin main

# Links prüfen
grep -r "discord.gg" docs/ README.md

# Commit & Push
git add .
git commit -m "docs: Update Discord invite links to public server"
git push origin main
```

---

**Letzte Aktualisierung**: 2026-02-11
**Server ID**: 1470531751595086017

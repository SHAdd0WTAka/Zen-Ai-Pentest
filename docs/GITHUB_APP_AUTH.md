# GitHub App Authentication Setup

Diese Dokumentation beschreibt die Einrichtung und Verwendung der GitHub App-Authentifizierung für das Zen-AI-Pentest-Projekt.

> 📖 **Ausführliche Architektur-Dokumentation:**  
> Für detaillierte Informationen über Sicherheit, Datenfluss und Token-Lebenszyklus, siehe:  
> **[SECRETS_ARCHITECTURE.md](./SECRETS_ARCHITECTURE.md)**
>
> 🔒 **Wichtig:** Deine Secrets werden niemals an externe Server gesendet. Alle Operationen sind **lokal**.

## ⚡ Quick Start (3 Schritte)

```bash
# 1. Setup ausführen
bash mcp/obsidian/setup.sh

# 2. Secrets eintragen (siehe unten)
code ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml

# 3. VS Codium neu laden
# Ctrl+Shift+P → Developer: Reload Window
```

**Das war's!** Ab sofort werden Tokens automatisch bei jedem `git push` generiert.

## Übersicht

Die GitHub App-Authentifizierung bietet **sichere, automatische Token-Generierung** für Git-Operationen, ohne langlaufende Personal Access Tokens (PATs) zu speichern.

### Vorteile

| Feature | GitHub App | PAT (Classic) |
|---------|------------|---------------|
| **Token-Lebensdauer** | 1 Stunde (automatisch erneuert) | Unbefristet |
| **Sicherheit** | ✅ Kurzlebig, automatisch | ⚠️ Langlaufend |
| **Setup** | Einmalig, dann automatisch | Manuelle Verwaltung |
| **Scope** | Repository-spezifisch | Global |

## Architektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Git Command   │────▶│ Credential Helper│────▶│  GitHub API     │
│   (git push)    │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                           │
                              ▼                           ▼
                        ┌──────────────┐          ┌──────────────┐
                        │ Private Key  │          │  Fresh Token │
                        │ (lokal)      │          │  (1h valid)  │
                        └──────────────┘          └──────────────┘
```

## Komponenten

### 1. Credential Helper

**Datei:** `github-app-credential-helper.py`

Wird automatisch von Git aufgerufen und generiert frische Tokens:
- Liest den Private Key aus `~/Downloads/`
- Erzeugt JWT mit 10-Minuten-Gültigkeit
- Tauscht JWT gegen Installation Token
- Gibt Token im korrekten Format zurück

### 2. Setup-Script

**Datei:** `setup-github-app-auth.sh`

Einrichtung für ein Repository:
```bash
# Ein Repository konfigurieren
~/zen-ai-pentest/setup-github-app-auth.sh /path/to/repo

# Aktuelles Verzeichnis verwenden
~/zen-ai-pentest/setup-github-app-auth.sh
```

### 3. Token Generator

**Datei:** `generate_installation_token.py`

Manuelle Token-Generierung für Debugging oder API-Aufrufe:
```bash
cd ~/zen-ai-pentest && python3 generate_installation_token.py
```

## Einrichtung

### Voraussetzungen

1. **GitHub App installiert:** Zen-AI-Pentest-Kimi-Assistant (ID: 2872904)
2. **Private Key vorhanden:** `~/Downloads/zen-ai-pentest-kimi-assistant.*.pem`
3. **Python-Abhängigkeiten:** PyJWT, Cryptography

### Schritt-für-Schritt

1. **Repository auswählen:**
   ```bash
   cd ~/zen-ai-pentest
   # oder
   cd "~/Documents/Obsidian Vault"
   ```

2. **Setup-Script ausführen:**
   ```bash
   ~/zen-ai-pentest/setup-github-app-auth.sh
   ```

3. **Testen:**
   ```bash
   git push
   # Sollte ohne Token-Eingabe funktionieren
   ```

## Fehlerbehebung

### "Resource not accessible by integration"

Die GitHub App hat keine Berechtigung für das Repository. Lösung:
1. GitHub → Settings → Applications → Zen-AI-Pentest-Kimi-Assistant
2. "Configure" → Repository-Zugriff hinzufügen

### "Could not find host github.com"

Netzwerkproblem. Prüfen:
```bash
ping github.com
curl -I https://api.github.com
```

### Token wird nicht aktualisiert

Credential Helper nicht korrekt konfiguriert:
```bash
# Prüfen
git config --local credential.helper

# Sollte zeigen:
# /home/atakan/zen-ai-pentest/github-app-credential-helper.py

# Falls nicht, neu konfigurieren
~/zen-ai-pentest/setup-github-app-auth.sh
```

## Sicherheitshinweise

### Private Key Schutz

- 🔒 **Niemals committen:** Der Private Key ist in `.gitignore` eingetragen
- 🔒 **Lokale Speicherung:** Nur in `~/Downloads/` oder sicherem Verzeichnis
- 🔒 **Backup:** Bei Verlust muss ein neuer Key in GitHub generiert werden

### Token-Lebensdauer & Auto-Refresh

- ⏱️ **Installation Token:** 1 Stunde (von GitHub festgelegt)
- ⏱️ **JWT:** 10 Minuten (von uns generiert)
- 🔄 **Auto-Refresh:** Bei jedem `git push` wird automatisch ein neuer Token generiert

#### Wie funktioniert der Auto-Refresh?

```
13:00 Uhr: git push → Token #1 generiert (gültig bis 14:00)
13:30 Uhr: git push → Token #2 generiert (gültig bis 14:30), Token #1 läuft in 30min ab
14:00 Uhr: Token #1 ist ungültig (egal, du hast #2)
14:15 Uhr: git push → Token #3 generiert (gültig bis 15:15)
```

**Du musst dich um nichts kümmern** - bei jedem Push wird automatisch ein frischer Token erzeugt!

## Technische Details

### Git Credential Helper Flow

```
1. git push
2. Git erkennt HTTPS-URL ohne Credentials
3. Git ruft credential.helper auf
4. Helper generiert JWT:
   - Header: { "alg": "RS256", "typ": "JWT" }
   - Payload: { "iat": <now>, "exp": <now+600>, "iss": "2872904" }
   - Signiert mit Private Key (RSA)
5. Helper tauscht JWT gegen Installation Token
6. Helper gibt aus: "username=x-access-token password=ghs_..."
7. Git verwendet Token für HTTPS-Auth
8. Token wird nicht gespeichert (cache timeout = 0)
```

### URL-Format

Wichtig: GitHub App Tokens müssen im speziellen Format übergeben werden:

```
# ❌ Falsch
https://ghs_xxx@github.com/owner/repo.git

# ✅ Richtig
https://x-access-token:ghs_xxx@github.com/owner/repo.git
```

Der Credential Helper übernimmt dies automatisch.

## Migration von PAT

Bestehende Repositories mit PAT:

```bash
# 1. Alten Token aus Remote URL entfernen
git remote set-url origin https://github.com/owner/repo.git

# 2. GitHub App Auth aktivieren
~/zen-ai-pentest/setup-github-app-auth.sh

# 3. PAT löschen (optional, empfohlen)
# GitHub → Settings → Developer settings → Personal access tokens
```

## Weitere Ressourcen

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [Git Credential Helper](https://git-scm.com/docs/gitcredentials)
- [JWT.io](https://jwt.io/) - JWT debugging

---

**Letzte Aktualisierung:** 2026-02-24  
**App ID:** 2872904  
**Installation ID:** 110359081

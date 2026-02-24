# GitHub App Authentication

Detaillierte Dokumentation der GitHub App-basierten Authentifizierung.

## Übersicht

Die GitHub App-Authentifizierung bietet:
- ✅ Automatische Token-Generierung
- ✅ Keine langlaufenden PATs
- ✅ 1-Stunden Token-Lebensdauer
- ✅ Sichere Private Key-basierte Auth

## Architektur

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Git Push   │────▶│ Credential Helper│────▶│  GitHub API     │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │                           │
                    ┌──────────────┐          ┌──────────────┐
                    │ Private Key  │          │  Fresh Token │
                    │ (lokal)      │          │  (1h valid)  │
                    └──────────────┘          └──────────────┘
```

## Einrichtung

### 1. Voraussetzungen prüfen

```bash
# Private Key muss existieren
ls ~/Downloads/zen-ai-pentest-kimi-assistant.*.pem
```

### 2. Repository konfigurieren

```bash
# Für ein Repository
~/zen-ai-pentest/setup-github-app-auth.sh /pfad/zum/repo

# Für aktuelles Verzeichnis
~/zen-ai-pentest/setup-github-app-auth.sh
```

### 3. Testen

```bash
cd /pfad/zum/repo
git push
# Sollte ohne Token-Eingabe funktionieren!
```

## Dateien

| Datei | Zweck |
|-------|-------|
| `github-app-credential-helper.py` | Core-Logik für Token-Generierung |
| `setup-github-app-auth.sh` | Setup-Script für Repos |
| `generate_installation_token.py` | Manuelle Token-Generierung |

## Manuelle Token-Generierung

```bash
cd ~/zen-ai-pentest
python3 generate_installation_token.py
```

## Fehlerbehebung

### "Resource not accessible by integration"

Die App hat keine Berechtigung für das Repository:

1. GitHub → Settings → Applications
2. "Zen-AI-Pentest-Kimi-Assistant" → Configure
3. Repository-Zugriff hinzufügen

### Token läuft nicht ab

Prüfe Credential Helper:
```bash
git config --local credential.helper
# Sollte zeigen:
# /home/atakan/zen-ai-pentest/github-app-credential-helper.py
```

### Timeout bei Push

Network-Problem oder GitHub API nicht erreichbar:
```bash
# Teste Connectivity
ping github.com
curl -I https://api.github.com
```

## Migration von PAT

### 1. Alten Token entfernen

```bash
# Aus Remote URL entfernen
git remote set-url origin https://github.com/user/repo.git
```

### 2. GitHub App Auth aktivieren

```bash
~/zen-ai-pentest/setup-github-app-auth.sh .
```

### 3. Alten PAT löschen

GitHub → Settings → Developer settings → Personal access tokens

## Technische Details

### JWT Payload

```python
{
    "iat": <now - 60>,      # Issued at
    "exp": <now + 600>,     # Expires (10 min)
    "iss": "2872904"        # App ID
}
```

### URL-Format

Wichtig: Korrektes Format für GitHub App Tokens:

```
# ❌ Falsch
https://ghs_xxx@github.com/...

# ✅ Richtig
https://x-access-token:ghs_xxx@github.com/...
```

## Sicherheitshinweise

- 🔒 Private Key niemals committen
- 🔒 Private Key niemals teilen
- 🔒 Bei Verlust: Neuen Key in GitHub generieren
- 🔒 Token ist nur 1h gültig (automatisch)

## Referenzen

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [Git Credential Helper](https://git-scm.com/docs/gitcredentials)
- [JWT.io](https://jwt.io/)

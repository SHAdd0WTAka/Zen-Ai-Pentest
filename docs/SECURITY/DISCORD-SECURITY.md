# Discord Notification Security

## Secret Masking & Leak Prevention

Dieses Dokument beschreibt die Sicherheitsmaßnahmen für Discord-Notifications.

---

## Overview

Unsere Discord-Integration implementiert mehrere Schutzschichten gegen Credential-Leaks:

### 1. Pre-Commit Secret Scanning
```yaml
# .pre-commit-config.yaml
- Gitleaks: Scannt auf bekannte Secret-Patterns
- TruffleHog: Deep-Scan mit Verifikation
- detect-private-key: Erkennt private Keys
```
**Wann**: Vor jedem Commit
**Ziel**: Secrets gar nicht erst ins Repository lassen

### 2. CI/CD Secret Masking
```yaml
# discord-github-notify.yml
- Maskiert alle potenziellen Secrets in Notifications
- Ersetzt durch: **********
- Ueberprueft Commit-Messages, PR-Titel, Issue-Titel
```
**Wann**: Vor Discord-Notification
**Ziel**: Keine Secrets in Discord-Chat

### 3. GitHub Secret Protection
```yaml
# GitHub Actions
- Secrets werden in Logs automatisch maskiert
- DISCORD_WEBHOOK_URL nur via ${{ secrets.XXX }}
- Keine Ausgabe von Secrets in Workflow-Logs
```

---

## Maskierte Patterns

Folgende Patterns werden automatisch erkannt und maskiert:

| Pattern | Beispiel | Maskiert |
|---------|----------|----------|
| OpenAI API Key | `sk-abc123...` | `**********` |
| GitHub Token | `ghp_xxxxxxxx...` | `**********` |
| GitHub PAT | `github_pat_xxx...` | `**********` |
| Discord Token | `xxx.yyy.zzz` | `**********` |
| Discord Webhook | `.../webhooks/xxx/yyy` | `**********` |
| Telegram Token | `123456:ABC-DEF...` | `**********` |
| AWS Access Key | `AKIAIOSFODNN7EXAMPLE` | `**********` |
| AWS Secret | `wJalrXUtnFEMI/K7MDENG...` | `**********` |
| Private Keys | `-----BEGIN PRIVATE KEY-----` | `**********` |
| Database URLs | `postgresql://user:pass@...` | `**********` |
| JWT Tokens | `eyJhbGciOiJIUzI1NiIs...` | `**********` |
| Passwords | `password=secret123` | `**********` |
| API Keys | `api_key=abc123...` | `**********` |
| Bearer Tokens | `Bearer eyJhbG...` | `**********` |
| High Entropy | `aBc123XyZ789...` (32+ chars) | `**********` |

---

## Wenn Secrets erkannt werden

### Szenario 1: Pre-Commit Hook findet Secret

```bash
# Git Push wird BLOCKIERT
Gitleaks.................................................................Failed
- hook id: gitleaks
- exit code: 1

🛑 Secret detected in file: config.py
   api_key = "sk-abc123..."

✅ SOFORTIGE AKTION:
   1. Secret aus Code entfernen
   2. In .env Datei verschieben
   3. Git History bereinigen (falls gepusht)
```

**Was tun:**
1. Secret aus Code entfernen
2. `.env` oder GitHub Secrets verwenden
3. Falls gepusht: Git History bereinigen

### Szenario 2: Discord-Notification maskiert Secret

```
🚀 Code Pushed
Branch: feature/new-api
Author: developer
Commit: "Add OpenAI integration **********"

🔒 Security Notice: Potential sensitive data detected and masked
```

**Was tun:**
1. Commit-Message pruefen
2. Falls Secret enthalten: Commit amend + force push
3. Secret rotieren (neuen Token generieren)

---

## Best Practices

### 1. Niemals Secrets in Commit-Messages

```bash
# ❌ FALSCH
git commit -m "Add API key: sk-abc123..."

# ✅ RICHTIG
git commit -m "Add OpenAI integration"
# Key wird in GitHub Secrets gespeichert
```

### 2. Environment Variables nutzen

```python
# ❌ FALSCH
api_key = "sk-abc123..."

# ✅ RICHTIG
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 3. .env.example statt echte Keys

```bash
# .env.example
OPENAI_API_KEY=your-key-here
DISCORD_WEBHOOK_URL=your-webhook-url
```

### 4. GitHub Secrets fuer CI/CD

```yaml
# .github/workflows/example.yml
env:
  API_KEY: ${{ secrets.OPENAI_API_KEY }}  # ✅ Sicher

# ❌ NIE so:
env:
  API_KEY: "sk-abc123..."  # GEHT INS LOG!
```

---

## Manuelle Ueberpruefung

### Secret-Scan lokal ausfuehren

```bash
# Gitleaks
gitleaks detect --source . --verbose

# TruffleHog
trufflehog git file://. --only-verified

# Bandit (Python security)
bandit -r . -ll
```

---

## Incident Response

### Secret wurde geleakt - Sofortmassnahmen

1. **Secret ROTIEREN** (sofort)
   - Neuen Token generieren
   - Alten deaktivieren

2. **Repository bereinigen**
   ```bash
   # Secret aus History entfernen
   git filter-repo --path config.py --invert-paths
   ```

3. **GitHub kontaktieren**
   - Settings → Security → Secret scanning alerts
   - GitHub Support bei kompromittiertem Account

4. **Discord Webhook neu erstellen**
   - Alten Webhook loeschen
   - Neuen generieren
   - In GitHub Secrets aktualisieren

---

## Support

Bei Sicherheitsvorfällen:
1. DM @SHAdd0WTAka auf Discord
2. GitHub Security Advisory erstellen
3. NIE Secrets in Issues/PRs posten!

---

**Letzte Aktualisierung**: 2026-02-11
**Version**: 1.0
**Owner**: @SHAdd0WTAka

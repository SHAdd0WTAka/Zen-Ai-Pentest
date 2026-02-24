# Security Setup Guide

Diese Seite dokumentiert alle Security-Features und deren Einrichtung.

## 🔐 GitHub App Authentication

Automatische Token-Generierung für sichere Git-Operationen ohne langlaufende PATs.

### Einrichtung

```bash
# Repository konfigurieren
~/zen-ai-pentest/setup-github-app-auth.sh /pfad/zum/repo
```

### Funktionsweise

1. Git ruft Credential Helper auf
2. Helper generiert JWT (signiert mit Private Key)
3. JWT wird gegen Installation Token getauscht
4. Token wird für HTTPS-Auth verwendet

### Token-Lebensdauer

- **JWT:** 10 Minuten
- **Installation Token:** 1 Stunde
- **Auto-Refresh:** Bei jedem Push

## 🛡️ Snyk Integration

### Voraussetzungen

1. Snyk Account: https://app.snyk.io/account
2. Token generieren: "Personal access tokens"
3. In GitHub Secrets hinterlegen: `SNYK_TOKEN`

### Scan-Typen

| Scan | Auslöser | Beschreibung |
|------|----------|--------------|
| Dependencies | Push, PR | Python CVE-Check |
| Code (SAST) | Push, PR | Statische Analyse |
| Container | Schedule | Docker Image |
| IaC | Schedule | Kubernetes Manifeste |

### Workflow-Status

Überprüfe Scans: https://github.com/SHAdd0WTAka/zen-ai-pentest/actions/workflows/snyk-security.yml

## 🔍 CodeQL

Automatische Code-Analyse bei jedem Push.

### Geänderte Alerts

- ✅ Clear-text logging (HIGH) - Gefixt
- ✅ Script Injection (CRITICAL) - Gefixt
- ✅ URL Sanitization (HIGH) - Gefixt

### Status

CodeQL läuft automatisch auf dem `main` Branch.

## 📝 Pre-commit Hooks

Automatische Code-Qualitäts-Checks vor jedem Commit.

### Installation

```bash
cd ~/zen-ai-pentest
source .venv/bin/activate
pip install pre-commit
pre-commit install
```

### Aktive Hooks

- `black` - Code-Formatierung
- `isort` - Import-Sortierung
- `flake8` - Linting
- `detect-secrets` - Secret-Erkennung
- `bandit` - Security-Linter

### Befehle

```bash
# Manuelle Prüfung
pre-commit run --all-files

# Skip (Notfall)
git commit -m "hotfix" --no-verify
```

## 🔑 Secret Management

### Option 1: Obsidian Vault (Empfohlen)

```bash
# Setup
bash mcp/obsidian/setup.sh

# Secrets bearbeiten
code ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml
```

**Vorteile:**
- Verschlüsselt at rest
- MCP-Integration
- Nie im Git

### Option 2: .env File

```bash
cp .env.example .env
nano .env
```

**Wichtig:** `.env` in `.gitignore` eintragen!

## 📊 Security Dashboards

| Tool | URL |
|------|-----|
| GitHub Security | https://github.com/SHAdd0WTAka/zen-ai-pentest/security |
| Snyk | https://app.snyk.io/org/shadd0wtaka/projects |
| CodeQL | Im Security Tab |

## 🚨 Incident Response

Falls Secrets committed wurden:

1. **Token sofort rotieren**
   ```bash
   # GitHub Settings -> Developer settings -> Tokens
   # Alten Token löschen, neuen generieren
   ```

2. **History bereinigen (falls nötig)**
   ```bash
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch .env" \
   --prune-empty --tag-name-filter cat -- --all
   ```

3. **Snyk/Dependabot Alerts prüfen**

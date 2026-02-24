# Troubleshooting

Häufige Probleme und deren Lösungen.

## Installation

### "ModuleNotFoundError"

**Problem:** Python-Modul nicht gefunden

**Lösung:**
```bash
cd ~/zen-ai-pentest
source .venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"

**Problem:** Keine Ausführungsrechte

**Lösung:**
```bash
chmod +x setup.sh
chmod +x mcp/obsidian/setup.sh
```

## GitHub App Auth

### "Authentication failed"

**Problem:** Token wird nicht akzeptiert

**Lösung:**
1. Private Key prüfen:
   ```bash
   ls ~/Downloads/zen-ai-pentest-kimi-assistant.*.pem
   ```

2. Credential Helper prüfen:
   ```bash
   git config --local credential.helper
   ```

3. Neu einrichten:
   ```bash
   ~/zen-ai-pentest/setup-github-app-auth.sh .
   ```

### "Resource not accessible"

**Problem:** App hat keine Berechtigung

**Lösung:**
1. GitHub → Settings → Applications
2. "Zen-AI-Pentest-Kimi-Assistant" → Configure
3. Repository-Zugriff hinzufügen

## Datenbank

### "Connection refused"

**Problem:** PostgreSQL läuft nicht

**Lösung:**
```bash
# Starten
sudo systemctl start postgresql

# Status prüfen
sudo systemctl status postgresql
```

### "Database does not exist"

**Problem:** Datenbank nicht erstellt

**Lösung:**
```bash
sudo -u postgres createdb zen_pentest
```

## Pre-commit Hooks

### "Hook failed"

**Problem:** Formatierung nicht korrekt

**Lösung:**
```bash
# Auto-fix
pre-commit run --all-files

# Oder skip (Notfall)
git commit -m "msg" --no-verify
```

### "detect-secrets failed"

**Problem:** Secrets gefunden

**Lösung:**
1. Secrets entfernen
2. `.secrets.baseline` aktualisieren:
   ```bash
   detect-secrets scan > .secrets.baseline
   ```

## Snyk

### "SNYK_TOKEN not set"

**Problem:** Token fehlt

**Lösung:**
```bash
# In GitHub Secrets hinterlegen:
# https://github.com/SHAdd0WTAka/zen-ai-pentest/settings/secrets/actions
# Name: SNYK_TOKEN
# Value: snyk_...
```

### "Invalid token"

**Problem:** Token abgelaufen

**Lösung:**
1. https://app.snyk.io/account
2. Neuen Token generieren
3. In GitHub Secrets aktualisieren

## API

### "401 Unauthorized"

**Problem:** JWT abgelaufen

**Lösung:**
```bash
# Neuen Token holen
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### "422 Validation Error"

**Problem:** Falsches Request-Format

**Lösung:**
```bash
# API-Doku prüfen
http://localhost:8000/docs
```

## Tools

### "Command not found"

**Problem:** Tool nicht installiert

**Lösung:**
```bash
# Nmap
sudo apt-get install nmap

# Nuclei
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

# SQLMap
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
```

### "Timeout"

**Problem:** Tool braucht zu lange

**Lösung:**
```python
# Timeout erhöhen
agent = ReActAgent(timeout=600)  # 10 Minuten
```

## Performance

### "Memory error"

**Problem:** Zu wenig RAM

**Lösung:**
```bash
# Swap erhöhen
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### "Too many open files"

**Problem:** File Descriptor Limit

**Lösung:**
```bash
ulimit -n 4096
```

## Logs

### Wo finde ich Logs?

```bash
# Application Logs
tail -f ~/.local/share/zen-ai-pentest/logs/app.log

# Error Logs
tail -f ~/.local/share/zen-ai-pentest/logs/error.log

# GitHub Actions Logs
# Siehe: https://github.com/SHAdd0WTAka/zen-ai-pentest/actions
```

## Support

Falls das Problem weiterhin besteht:

1. **GitHub Issues:** https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
2. **Discord:** https://discord.gg/BSmCqjhY
3. **Logs mitschicken:** Immer relevante Logs beifügen

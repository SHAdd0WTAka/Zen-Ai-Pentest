# Configuration Guide

Zen-AI-Pentest unterstützt zwei Konfigurations-Approaches.

## Vergleich

| Feature | Obsidian Vault | .env File |
|---------|---------------|-----------|
| **Sicherheit** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Setup** | Mittel | Einfach |
| **Best für** | Production | Development |
| **Verschlüsselung** | Ja | Nein |
| **MCP-Integration** | Ja | Nein |

## Option 1: Obsidian Vault (Empfohlen)

### Setup

```bash
# 1. Setup-Script ausführen
bash mcp/obsidian/setup.sh

# 2. Secrets bearbeiten
code ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml

# 3. VS Codium neu laden
Ctrl+Shift+P → Developer: Reload Window
```

### Vault-Struktur

```yaml
# ~/Documents/Obsidian Vault/Secrets/secrets.yaml
kimi:
  api_key: "sk-your-kimi-api-key"

openai:
  api_key: "sk-your-openai-key"

database:
  url: "postgresql://user:pass@localhost:5432/zen_pentest"

notifications:
  slack_webhook: "https://hooks.slack.com/..."
  discord_webhook: "https://discord.com/api/webhooks/..."

cloud:
  aws_access_key_id: "AKIA..."
  aws_secret_access_key: "..."
```

### MCP Integration

`.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "obsidian-secrets": {
      "command": "python3",
      "args": ["mcp/obsidian/server.py"]
    }
  }
}
```

## Option 2: Environment Variables

### Quick Setup

```bash
# 1. Example kopieren
cp .env.example .env

# 2. Bearbeiten
nano .env

# 3. Laden
source .env
```

### Beispiel .env

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/zen_pentest

# Security
SECRET_KEY=your-secret-key-here
JWT_EXPIRATION=3600

# AI Providers
KIMI_API_KEY=your-kimi-api-key
DEFAULT_BACKEND=kimi
DEFAULT_MODEL=kimi-k2.5

# Alternative Backends
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_HOST=smtp.gmail.com

# Cloud
AWS_ACCESS_KEY_ID=AKIA...
AZURE_SUBSCRIPTION_ID=...
```

### .gitignore

Wichtig! Füge hinzu:

```gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets.yaml
secrets.json
```

## Umschalten zwischen Optionen

```bash
# Force Vault
export USE_VAULT=true

# Force .env
export USE_ENV_FILE=true
```

## Alle Optionen

Siehe `.env.example` für vollständige Liste aller Konfigurationsoptionen.

## Troubleshooting

### "Secret not found"

1. Vault-Pfad prüfen:
   ```bash
   ls ~/Documents/Obsidian\ Vault/Secrets/
   ```

2. Dateiberechtigungen:
   ```bash
   chmod 600 ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml
   ```

### "Database connection failed"

1. PostgreSQL läuft?
   ```bash
   sudo systemctl status postgresql
   ```

2. Datenbank existiert?
   ```bash
   sudo -u postgres psql -l
   ```

### "API Key invalid"

- Key im Vault/.env prüfen
- Key bei Provider rotieren

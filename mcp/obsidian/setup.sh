#!/bin/bash
# Setup Obsidian Vault for Secrets

VAULT_DIR="$HOME/Documents/Obsidian Vault/Secrets"

echo "🔐 Setting up Obsidian Secrets Vault..."

# Create directory
mkdir -p "$VAULT_DIR"

# Create template secrets.yaml
cat > "$VAULT_DIR/secrets.yaml" << 'SECRETS'
# =============================================================================
# Obsidian Secrets Vault
# WARNING: Keep this file private! Do not commit to Git!
# =============================================================================

# Kubernetes / Database
DB_PASSWORD: "your-secure-db-password-here"
REDIS_PASSWORD: "your-secure-redis-password-here"

# API Keys
OPENAI_API_KEY: "sk-your-openai-key"
KIMI_API_KEY: "your-kimi-api-key"
ANTHROPIC_API_KEY: "sk-ant-your-anthropic-key"

# JWT / Encryption
JWT_SECRET: "your-jwt-secret-min-32-chars"
SECRET_KEY: "your-secret-key-min-32-chars"
ENCRYPTION_KEY: "your-encryption-key-32-chars"

# Cloud Providers
AWS_ACCESS_KEY_ID: "AKIA..."
AWS_SECRET_ACCESS_KEY: "your-aws-secret"
AZURE_CLIENT_SECRET: "your-azure-secret"
GCP_SERVICE_ACCOUNT_KEY: "your-gcp-key"

# Notifications
SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/..."
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/..."
EMAIL_SMTP_PASSWORD: "your-smtp-password"

# GitHub
GITHUB_TOKEN: "ghp_your_github_token"
SECRETS

# Create .gitignore
cat > "$VAULT_DIR/.gitignore" << 'GITIGNORE'
# Ignore all files in this directory
*
# Except this .gitignore
!.gitignore
# And the template (without real values)
!secrets.yaml.template
GITIGNORE

# Create README
cat > "$VAULT_DIR/README.md" << 'README'
# 🔐 Secrets Vault

This directory contains sensitive credentials.

## Security
- Never commit real secrets to Git
- Use this only for local development
- For production, use proper secret management (AWS Secrets Manager, Vault, etc.)

## Usage
The MCP server reads secrets from `secrets.yaml`.
README

echo "✅ Obsidian Vault created at: $VAULT_DIR"
echo "📝 Edit $VAULT_DIR/secrets.yaml with your real credentials"
echo "🔒 The directory is gitignored automatically"

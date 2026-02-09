# GitHub Actions Secrets

This document describes all secrets used by the Zen AI Pentest workflows.

## Table of Contents

- [Required Secrets](#required-secrets)
- [Optional Secrets](#optional-secrets)
- [Secret Setup Instructions](#secret-setup-instructions)
- [Workflow-Specific Secret Usage](#workflow-specific-secret-usage)

---

## Required Secrets

These secrets are required for the CI/CD pipeline to function properly.

### `CODECOV_TOKEN`

**Purpose:** Upload code coverage reports to Codecov

**Used by:**
- `ci.yml` - Coverage upload after tests
- `coverage.yml` - Dedicated coverage workflow

**How to obtain:**
1. Go to [codecov.io](https://codecov.io)
2. Sign up/login with your GitHub account
3. Add your repository
4. Copy the repository upload token

**Setup:**
```bash
# In repository: Settings → Secrets and variables → Actions → New repository secret
Name: CODECOV_TOKEN
Value: <your-codecov-token>
```

---

## Optional Secrets

### Notification Secrets

#### `SLACK_WEBHOOK_URL`

**Purpose:** Send notifications to Slack channel

**Used by:**
- `release.yml` - Release notifications
- `notifications.yml` (if enabled) - Build status, security alerts

**How to obtain:**
1. In Slack, go to your workspace settings
2. Create an Incoming Webhook
3. Select the target channel
4. Copy the Webhook URL

**Setup:**
```bash
Name: SLACK_WEBHOOK_URL
Value: https://hooks.slack.com/services/T00/B00/xxxxxxxxx
```

**Security Note:** Keep this URL secret. Anyone with access can post to your channel.

---

#### `DISCORD_WEBHOOK_URL`

**Purpose:** Send notifications to Discord channel

**Used by:**
- `release.yml` - Release notifications
- Various notification workflows

**How to obtain:**
1. In Discord, go to Server Settings → Integrations
2. Create a Webhook
3. Select the target channel
4. Copy the Webhook URL

**Setup:**
```bash
Name: DISCORD_WEBHOOK_URL
Value: https://discord.com/api/webhooks/0000000000/xxxxxxxxxxxxxxxxxx
```

---

#### `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`

**Purpose:** Send notifications via Telegram

**Used by:**
- `telegram-notifications.yml` (manual trigger only)

**How to obtain:**
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Copy the bot token
3. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

**Setup:**
```bash
Name: TELEGRAM_BOT_TOKEN
Value: 123456:ABCdefGHIjklMNOpqr

Name: TELEGRAM_CHAT_ID
Value: 123456
```

---

### API Keys

#### `OPENROUTER_API_KEY`

**Purpose:** Access AI models for benchmark tests

**Used by:**
- `benchmark.yml` - Performance testing with AI components

**How to obtain:**
1. Go to [openrouter.ai](https://openrouter.ai)
2. Create an account
3. Generate an API key

**Setup:**
```bash
Name: OPENROUTER_API_KEY
Value: sk-or-v1-xxxxxxxxxxxxxxxx
```

---

### Security Secrets

#### `GITLEAKS_LICENSE`

**Purpose:** License for GitLeaks secret scanning (optional, for enhanced features)

**Used by:**
- `security.yml` - Secret detection

**How to obtain:**
1. Go to [gitleaks.io](https://gitleaks.io)
2. Purchase or request a license

---

### Admin/Automation Secrets

#### `ADMIN_BOT_APP_ID` & `ADMIN_BOT_PRIVATE_KEY`

**Purpose:** GitHub App credentials for privileged operations

**Used by:**
- `auto-merge-dependabot.yml` - Branch protection bypass for Dependabot merges

**How to obtain:**
1. Create a GitHub App in your organization/personal settings
2. Grant it `contents:write` and `administration:write` permissions
3. Generate and download a private key
4. Note the App ID

**Setup:**
```bash
Name: ADMIN_BOT_APP_ID
Value: 123456

Name: ADMIN_BOT_PRIVATE_KEY
Value: -----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...
-----END RSA PRIVATE KEY-----
```

**Note:** These are only needed if using the advanced auto-merge workflow.

---

## Secret Setup Instructions

### Setting Secrets via GitHub UI

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name and value
5. Click **Add secret**

### Setting Secrets via GitHub CLI

```bash
# Install gh CLI if not already installed
# https://cli.github.com/

# Set a secret
ggh secret set CODECOV_TOKEN --body "your-token-here"

# Set from file
ggh secret set ADMIN_BOT_PRIVATE_KEY < private-key.pem

# List secrets
ggh secret list
```

### Setting Secrets via API

```bash
# Requires a personal access token with repo scope
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_PAT" \
  https://api.github.com/repos/OWNER/REPO/actions/secrets/SECRET_NAME \
  -d '{
    "encrypted_value": "ENCRYPTED_VALUE",
    "key_id": "KEY_ID"
  }'
```

---

## Workflow-Specific Secret Usage

### ci.yml

| Secret | Required | Purpose |
|--------|----------|---------|
| `CODECOV_TOKEN` | No | Upload coverage reports |
| `GITHUB_TOKEN` | Auto | Artifact upload, status checks |

### security.yml

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto | SARIF upload to Security tab |
| `GITLEAKS_LICENSE` | No | Enhanced GitLeaks features |

### release.yml

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto | Create releases, push packages |
| `SLACK_WEBHOOK_URL` | No | Slack release notifications |
| `DISCORD_WEBHOOK_URL` | No | Discord release notifications |

**Note:** PyPI publishing uses [trusted publishing](https://docs.pypi.org/trusted-publishers/) and does not require a token secret.

### benchmark.yml

| Secret | Required | Purpose |
|--------|----------|---------|
| `OPENROUTER_API_KEY` | No | AI model access for benchmarks |

### dependabot-auto-merge.yml

| Secret | Required | Purpose |
|--------|----------|---------|
| `GITHUB_TOKEN` | Auto | PR approval and merge |

### auto-merge-dependabot.yml (Optional)

| Secret | Required | Purpose |
|--------|----------|---------|
| `ADMIN_BOT_APP_ID` | Yes | GitHub App ID |
| `ADMIN_BOT_PRIVATE_KEY` | Yes | GitHub App private key |

---

## Security Best Practices

### 1. Principle of Least Privilege

Only add secrets that are actually needed. Review workflow permissions:

```yaml
permissions:
  contents: read  # Instead of write, if only reading
```

### 2. Rotate Secrets Regularly

Set calendar reminders to rotate secrets:
- API keys: Every 90 days
- Tokens: Every 180 days
- Certificates: Before expiry

### 3. Audit Secret Access

Monitor when secrets are used:
- Check workflow run logs
- Review GitHub Audit Log (for organizations)
- Set up alerts for failed authentication

### 4. Use GitHub Environments for Sensitive Workflows

For releases and deployments, use environments with protection rules:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://pypi.org/p/zen-ai-pentest
```

### 5. Never Log Secrets

GitHub automatically masks secrets in logs, but be careful with:
- Custom encoding/decoding
- Splitting secrets into parts
- Using secrets in URLs

### 6. Use Short-Lived Tokens Where Possible

Prefer:
- GitHub App tokens over PATs
- OIDC tokens for cloud providers
- Trusted publishing for PyPI

---

## Troubleshooting Secrets

### Secret not being recognized

1. Check the secret name is exactly correct (case-sensitive)
2. Verify the secret is set at the right level (repo vs org)
3. For fork PRs, secrets are not available for security reasons

### "Secret not found" errors

- Secrets are only available to workflows triggered by the repository
- Fork PRs don't have access to secrets
- Use `pull_request_target` carefully if needed

### Rotating a secret

1. Generate new secret value
2. Update in GitHub Settings
3. Test the workflow
4. Revoke old secret at the provider
5. Monitor for any issues

---

## Secret Reference Quick Guide

| Secret | Category | Priority | Setup Difficulty |
|--------|----------|----------|------------------|
| `CODECOV_TOKEN` | CI/CD | High | Easy |
| `SLACK_WEBHOOK_URL` | Notification | Low | Easy |
| `DISCORD_WEBHOOK_URL` | Notification | Low | Easy |
| `TELEGRAM_BOT_TOKEN` | Notification | Low | Medium |
| `OPENROUTER_API_KEY` | API | Low | Easy |
| `GITLEAKS_LICENSE` | Security | Low | Medium |
| `ADMIN_BOT_APP_ID` | Automation | Optional | Hard |
| `ADMIN_BOT_PRIVATE_KEY` | Automation | Optional | Hard |

---

## Contact

For issues with secrets or to request new secret additions, please:
1. Open an issue with the `infrastructure` label
2. Do not include secret values in any communications
3. Rotate any potentially compromised secrets immediately

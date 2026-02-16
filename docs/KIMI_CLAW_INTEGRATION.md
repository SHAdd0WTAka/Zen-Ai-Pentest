# 🤖 Kimi Claw Gateway Integration

> **Unified notification system for Zen-AI-Pentest**

Kimi Claw acts as the central hub for all repository notifications, replacing multiple separate workflows with a single intelligent gateway.

## 🎯 What is Kimi Claw?

Instead of managing:
- ❌ Discord notification workflows
- ❌ Telegram bot scripts  
- ❌ Slack webhook configurations
- ❌ Email notification setups

Use **one unified system**:
- ✅ Kimi Claw receives all GitHub events
- ✅ Intelligently distributes to your preferred channels
- ✅ AI-powered message summarization
- ✅ Smart severity-based routing

## 🚀 Features

### Event Coverage

| Event Type | Notification | Severity |
|------------|--------------|----------|
| Push | Commit summary with author | info |
| Pull Request (opened) | New PR with title & author | info |
| Pull Request (merged) | Merge confirmation | success |
| Pull Request (closed) | Close notification | warning |
| Issues (opened) | Bug/feature alert | warning |
| Issues (closed) | Resolution confirmation | success |
| Workflow Success | CI/CD passed | success |
| Workflow Failure | CI/CD failed with link | error |

### Smart Capabilities

- **Severity Levels**: Auto-detects importance (info → warning → error → success)
- **Emoji Indicators**: Visual parsing at a glance
- **Direct Links**: Click through to commits, PRs, issues
- **Fallback Channels**: Discord/Telegram backup if Claw unavailable
- **Custom Messages**: Manual trigger with custom text

## 📋 Setup

### Prerequisites

1. Kimi Claw account (https://claw.moonshot.cn)
2. API Token from your Claw dashboard

### Step 1: Add GitHub Secrets

Navigate to: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions`

Add these secrets:

```
Secret Name: KIMI_CLAW_TOKEN
Value: claw_your_token_here
```

Optional configuration:
```
KIMI_CLAW_DISCORD_ENABLED=true
KIMI_CLAW_TELEGRAM_ENABLED=true
KIMI_CLAW_SLACK_ENABLED=false
```

### Step 2: Verify Installation

```bash
# Trigger a test notification
gh workflow run kimi-claw-gateway.yml \
  -R SHAdd0WTAka/Zen-Ai-Pentest \
  -f message="Test notification from CLI"
```

Or use GitHub web interface:
1. Go to Actions → Kimi Claw Gateway
2. Click "Run workflow"
3. Enter test message
4. Click "Run"

## 🔧 Configuration

### Customize Events

Edit `.github/workflows/kimi-claw-gateway.yml`:

```yaml
on:
  push:
    branches: [main, develop]  # Add branches
  issues:
    types: [opened]             # Only notify on new issues
  # Remove events you don't want
```

### Message Templates

Modify the `Prepare Event Data` step to customize messages:

```bash
case "$EVENT_TYPE" in
  push)
    MESSAGE="🚀 ${{ github.actor }} pushed: $COMMIT_MSG"
    ;;
esac
```

### Channel Routing

Control which channels receive which severity:

```yaml
"channels": {
  "discord": $SEVERITY != "info",     # Skip info on Discord
  "telegram": true,                    # All to Telegram
  "slack": $SEVERITY == "error"        # Only errors to Slack
}
```

## 🧪 Testing

### Manual Test
```bash
# Local test with curl
curl -X POST "$KIMI_CLAW_API_URL/notify" \
  -H "Authorization: Bearer $KIMI_CLAW_TOKEN" \
  -d '{
    "event": "test",
    "repository": "zen-ai-pentest",
    "message": "Hello from Kimi Claw!",
    "severity": "info"
  }'
```

### Automated Test
The workflow includes fallback mechanisms:
- If Kimi Claw fails → Sends to Discord
- If Discord fails → Sends to Telegram
- If all fail → Logs to GitHub Actions summary

## 📊 Monitoring

Check notification delivery:

1. **GitHub Actions**: View workflow runs
2. **Kimi Claw Dashboard**: See message history
3. **Discord/Telegram**: Verify receipt

## 🎨 Hemisphere Sync

This integration embodies the Hemisphere Sync philosophy:

- **Left Brain (Kimi)**: Logic, structured workflows, automation
- **Right Brain (Observer^^)**: Creative notification design, context-aware messaging
- **Kimi Claw**: The bridge that unifies both worlds

## 🔗 Related

- [Main Workflow](../.github/workflows/kimi-claw-gateway.yml)
- [Setup Script](../.kimi/setup_kimi_claw.py)
- [Discord Integration](./DISCORD_SETUP.md)
- [Telegram Integration](./TELEGRAM_SETUP.md)

---

**Status**: ✅ Prototype ready for testing

# 🔔 Zen-AI-Pentest Notification System

> Intelligent notifications for your repository health

## ✨ Features

### 📱 Supported Platforms
- **Slack** - Professional team notifications
- **Discord** - Community & personal notifications

### 🎯 Notification Types

| Event | Priority | Description |
|-------|----------|-------------|
| 🚨 **Health Score Critical** | HIGH | Repository health drops below 50/100 |
| ❌ **Workflow Failure** | HIGH | CI/CD pipeline fails |
| 🔒 **Security Alert** | HIGH | New vulnerability detected |
| 📦 **New Release** | MEDIUM | Version published |
| 📝 **Issue Activity** | LOW | Issue opened/closed/reopened |
| 🔀 **Pull Request** | LOW | PR opened/closed/merged |

---

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Run setup script
./scripts/setup-notifications.sh
```

The script will:
1. Guide you through Slack/Discord webhook creation
2. Automatically add secrets to GitHub
3. Test the connection

### Option 2: Manual Setup

#### Slack
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Enable "Incoming Webhooks"
4. Add webhook to your workspace
5. Copy webhook URL
6. Add to GitHub Secrets: `SLACK_WEBHOOK_URL`

#### Discord
1. Open Discord → Server Settings → Integrations → Webhooks
2. Create new webhook
3. Copy webhook URL
4. Add to GitHub Secrets: `DISCORD_WEBHOOK_URL`

---

## 🎨 Message Examples

### Slack Notifications
```
🔔 Zen-AI-Pentest Notification

Event: workflow_run
Status: Workflow failed!
Repository: SHAdd0WTAka/Zen-Ai-Pentest
Branch: master
Priority: high

[View on GitHub]
```

### Discord Notifications
```
🔔 **Zen-AI-Pentest Alert**

**Event:** workflow_run
**Status:** Workflow failed!
**Repository:** SHAdd0WTAka/Zen-Ai-Pentest
**Branch:** master
**Priority:** high

[View Details]
```

---

## 🔧 Workflows Using Notifications

| Workflow | File | Triggers |
|----------|------|----------|
| Smart Notifications | `.github/workflows/smart-notifications.yml` | All workflow runs, releases, issues, PRs |
| Repository Health | `.github/workflows/repository-health-check.yml` | Schedule, push, PR |
| Auto-Fix | `.github/workflows/auto-fix-repository.yml` | Schedule, push |
| Test Notifications | `.github/workflows/test-notifications.yml` | Manual |

---

## 🧪 Testing

### Test via GitHub Actions
1. Go to **Actions** tab
2. Select **"Test Notifications"**
3. Click **"Run workflow"**
4. Choose test type (slack/discord/both)
5. Check your notifications!

### Test locally
```bash
# Set environment variables
export SLACK_WEBHOOK_URL="your-slack-url"
export DISCORD_WEBHOOK_URL="your-discord-url"

# Run test script
python scripts/test_webhooks.py
```

---

## 📋 Troubleshooting

### Notifications not working?

1. **Check Secrets:**
   ```bash
   gh secret list --repo SHAdd0WTAka/Zen-Ai-Pentest
   ```

2. **Verify Webhook URLs:**
   - Slack: Must start with `https://hooks.slack.com/services/`
   - Discord: Must start with `https://discord.com/api/webhooks/`

3. **Check Workflow Status:**
   - Go to Actions tab
   - Look for failed workflows
   - Check logs for error messages

### Common Issues

| Issue | Solution |
|-------|----------|
| "Secret not found" | Add webhook URL to GitHub Secrets |
| "Invalid webhook URL" | Regenerate webhook and update secret |
| "No notifications received" | Check channel permissions |
| "Workflow skipped" | Ensure secrets are configured |

---

## 🔗 Links

- [Slack API](https://api.slack.com/apps)
- [GitHub Secrets](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions)
- [Repository Actions](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions)

---

**Questions?** Open an issue or check the [troubleshooting guide](#troubleshooting)! 🚀

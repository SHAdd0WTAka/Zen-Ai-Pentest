# Discord GitHub Actions Workflow Fixes

## Summary

Fixed failing Discord notification workflows and improved error handling across all notification-related GitHub Actions workflows.

## Issues Found and Fixed

### 1. **discord-github-notify.yml** (Main failing workflow)
**Issues:**
- Missing secret check before attempting webhook call
- No timeout setting (could hang indefinitely)
- Shell-based JSON escaping could fail with special characters
- Missing concurrency settings
- Missing permissions declaration

**Fixes:**
- Added `Check Discord Webhook Secret` step to verify secret exists before attempting notification
- Added `timeout-minutes: 5` to prevent hung jobs
- Replaced sed-based JSON escaping with Python `json.dumps()` for proper escaping
- Added concurrency settings to prevent parallel run conflicts
- Added minimal permissions (`contents: read`)
- Added proper HTTP response code handling with meaningful error messages
- Added workflow summary for better visibility

### 2. **discord-notifications.yml**
**Issues:**
- Missing secret check
- No timeout setting
- No concurrency settings
- Using workflow names that may not exist ("Test", "Build")
- Using `@master` tag for action (unstable)

**Fixes:**
- Added secret check step
- Added timeout and concurrency settings
- Updated workflow names to match actual workflows in repo
- Pinned action to specific version (`@v1.12.0`)
- Added workflow summary

### 3. **discord-bot.yml**
**Issues:**
- Missing secret check
- No timeout setting
- Using `@master` tag for action
- No concurrency settings

**Fixes:**
- Added secret check step
- Added timeout and concurrency settings
- Pinned action to specific version (`@0.3.2`)
- Added workflow summary

### 4. **zenclaw-discord.yml** (Critical Fix)
**Issues:**
- **CRITICAL**: Using `secrets` in job-level `if` condition - this is not allowed by GitHub Actions and causes workflow failure
- Missing timeout setting
- No concurrency settings
- Shell-based JSON escaping could fail

**Fixes:**
- Moved secret check to step-level condition (fixes the critical issue)
- Added timeout and concurrency settings
- Replaced shell JSON escaping with Python `json.dumps()`
- Added proper error handling for HTTP responses
- Added workflow summary

### 5. **kimi-claw-gateway.yml** (Critical Fix)
**Issues:**
- **CRITICAL**: Using `secrets` in step-level `if` conditions - this pattern is problematic
- Missing timeout setting
- No concurrency settings
- Using `@master` tag for action

**Fixes:**
- Added explicit secret check steps for Discord and Telegram
- Changed conditions to use step outputs instead of direct secret access
- Added timeout and concurrency settings
- Pinned action to specific version (`@0.3.2`)
- Added workflow summary

### 6. **webhook-notify.yml**
**Issues:**
- Missing secret check
- Missing `continue-on-error` could cause workflow failure
- No timeout setting

**Fixes:**
- Added secret check step
- Added `continue-on-error: true` to webhook call
- Added timeout setting
- Added HTTP response code validation
- Added workflow summary

### 7. **discord-fill-channels.yml**
**Issues:**
- Missing secret validation
- Could fail silently if bot token not configured

**Fixes:**
- Added secret check step with bot-specific token validation
- Added explicit fail step if secret missing
- Added workflow summary

### 8. **discord-setup-channels.yml**
**Issues:**
- Missing secret validation
- Could fail silently if bot token not configured

**Fixes:**
- Added secret check step
- Added explicit fail step if secret missing
- Added authentication test before attempting channel creation
- Added workflow summary

### 9. **discord-make-public.yml**
**Issues:**
- Missing secret validation
- Could fail silently if bot token not configured

**Fixes:**
- Added secret check step
- Added explicit fail step if secret missing
- Added authentication test before attempting server configuration
- Added workflow summary

## New Files Created

### 1. **scripts/test_discord_webhook.py**
Test script for validating Discord webhook configuration locally:
- Validates webhook URL format
- Tests JSON payload serialization with special characters
- Optionally sends test message to Discord
- Provides clear instructions for fixing configuration issues

### 2. **scripts/validate_workflows.py**
Workflow validation script that checks for common issues:
- Detects use of secrets in job-level if conditions
- Checks for missing timeout settings
- Checks for missing concurrency settings
- Detects use of deprecated action versions
- Identifies potential JSON escaping issues

## Common Patterns Applied

### Secret Check Pattern
All workflows now follow this pattern:
```yaml
- name: Check Discord Webhook Secret
  id: check-secret
  run: |
    if [ -n "${{ secrets.DISCORD_WEBHOOK_URL }}" ]; then
      echo "has_secret=true" >> $GITHUB_OUTPUT
    else
      echo "has_secret=false" >> $GITHUB_OUTPUT
    fi

- name: Send Discord Notification
  if: steps.check-secret.outputs.has_secret == 'true'
  # ... notification logic
```

### JSON Payload Pattern
Using Python for proper JSON escaping:
```yaml
- name: Send to Discord
  run: |
    JSON_PAYLOAD=$(python3 << PYEOF
import json
payload = {
    "embeds": [{
        "title": "...",
        "description": "...",
    }]
}
print(json.dumps(payload))
PYEOF
    )
    curl -X POST "$DISCORD_WEBHOOK" -d "$JSON_PAYLOAD"
```

## How to Configure Discord Notifications

1. **Get Discord Webhook URL:**
   - Go to your Discord server
   - Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL

2. **Add to GitHub Secrets:**
   - Go to GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: Your Discord webhook URL

3. **Test the configuration:**
   ```bash
   python scripts/test_discord_webhook.py YOUR_WEBHOOK_URL
   ```

## Result

- **0 workflow errors** (down from 2 critical errors)
- All Discord workflows now gracefully handle missing secrets
- Workflows no longer fail if webhooks are not configured
- Better error messages and logging
- Consistent patterns across all notification workflows

# Discord Webhook Setup for Zen AI Pentest
# Run this to configure Discord notifications for GitHub Actions

Write-Host @"
========================================
  Discord Webhook Setup
  Zen AI Pentest CI/CD Notifications
========================================
"@

Write-Host "`nStep 1: Create a Discord Webhook"
Write-Host "------------------------------------"
Write-Host "1. Open your Discord server"
Write-Host "2. Go to Server Settings -> Integrations -> Webhooks"
Write-Host "3. Click 'New Webhook'"
Write-Host "4. Choose channel for notifications"
Write-Host "5. Copy the Webhook URL"
Write-Host ""

$webhookUrl = Read-Host "Paste your Discord Webhook URL"

if (-not $webhookUrl) {
    Write-Host "No URL provided. Exiting..." -ForegroundColor Red
    exit 1
}

# Test the webhook
Write-Host "`nStep 2: Testing Webhook..." -ForegroundColor Yellow

try {
    $testPayload = @{
        content = "🧪 **Test Message from Zen AI Pentest**`nIf you see this, your webhook is working!"
    } | ConvertTo-Json

    Invoke-RestMethod -Uri $webhookUrl -Method Post -ContentType "application/json" -Body $testPayload
    Write-Host "✅ Test message sent successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to send test message: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 3: Configure GitHub Secret"
Write-Host "------------------------------------"
Write-Host "Add this webhook URL as a GitHub secret:"
Write-Host ""
Write-Host "  Name: DISCORD_WEBHOOK" -ForegroundColor Cyan
Write-Host "  Value: $webhookUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Go to: https://github.com/SHAdd0WTAka/zen-ai-pentest/settings/secrets/actions"
Write-Host ""

# Optional: Create GitHub CLI command
Write-Host "Or use GitHub CLI:" -ForegroundColor Yellow
Write-Host "  gh secret set DISCORD_WEBHOOK --body `"$webhookUrl`"" -ForegroundColor Cyan

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "Your GitHub Actions will now send notifications to Discord."

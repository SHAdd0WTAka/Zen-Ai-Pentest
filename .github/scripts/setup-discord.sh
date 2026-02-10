#!/bin/bash
# Discord Server Setup Script
# Run this after bot is added to server

echo "🤖 Setting up Discord Integration..."

# Create webhook via Discord API (requires bot token)
# This will be run manually once

echo "Steps to complete:"
echo "1. Add bot to server using:"
echo "   https://discord.com/api/oauth2/authorize?client_id=1470531751595086017&permissions=8&scope=bot%20applications.commands"
echo ""
echo "2. Create webhook in your server:"
echo "   - Go to Server Settings -> Integrations -> Webhooks"
echo "   - Create webhook named 'GitHub-CI'"
echo "   - Copy webhook URL"
echo ""
echo "3. Add to GitHub Secrets:"
echo "   Name: DISCORD_WEBHOOK_URL"
echo "   Value: [your webhook URL]"
echo ""
echo "✅ Bot Token is already configured in repository"

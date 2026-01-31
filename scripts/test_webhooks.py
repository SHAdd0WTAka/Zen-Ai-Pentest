#!/usr/bin/env python3
"""
Test script for Slack and Discord webhooks
Usage: python test_webhooks.py [slack|discord|both]
"""
import sys
import json
import urllib.request
import urllib.error
import os
from datetime import datetime

def test_slack_webhook(webhook_url):
    """Test Slack webhook"""
    print("\n" + "="*60)
    print("TESTING SLACK WEBHOOK")
    print("="*60)
    
    if not webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL not set")
        return False
    
    payload = {
        "text": "🧪 Test notification from Zen-AI-Pentest",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔔 Zen-AI-Pentest Notification Test"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\n✅ Webhook working"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This is a test message from the Zen-AI-Pentest repository health check system."
                }
            }
        ]
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Status: {response.status}")
            print("✅ Slack webhook is working!")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_discord_webhook(webhook_url):
    """Test Discord webhook"""
    print("\n" + "="*60)
    print("TESTING DISCORD WEBHOOK")
    print("="*60)
    
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL not set")
        return False
    
    payload = {
        "content": "🧪 Test notification from Zen-AI-Pentest",
        "embeds": [
            {
                "title": "🔔 Zen-AI-Pentest Notification Test",
                "description": "This is a test message from the Zen-AI-Pentest repository health check system.",
                "color": 3447003,
                "fields": [
                    {
                        "name": "Time",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "inline": True
                    },
                    {
                        "name": "Status",
                        "value": "✅ Webhook working",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Zen-AI-Pentest Health Check"
                }
            }
        ]
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Status: {response.status}")
            print("✅ Discord webhook is working!")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("ZEN-AI-PENTEST WEBHOOK TESTER")
    print("="*60)
    
    # Get webhook URLs from environment
    slack_url = os.environ.get('SLACK_WEBHOOK_URL', '')
    discord_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
    
    # Or from command line
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = 'both'
    
    results = []
    
    if test_type in ['slack', 'both']:
        if slack_url:
            results.append(('Slack', test_slack_webhook(slack_url)))
        else:
            print("\n⚠️  SLACK_WEBHOOK_URL not set in environment")
            print("Set it with: $env:SLACK_WEBHOOK_URL = 'your-url'")
    
    if test_type in ['discord', 'both']:
        if discord_url:
            results.append(('Discord', test_discord_webhook(discord_url)))
        else:
            print("\n⚠️  DISCORD_WEBHOOK_URL not set in environment")
            print("Set it with: $env:DISCORD_WEBHOOK_URL = 'your-url'")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✅ Working" if success else "❌ Failed"
        print(f"{name}: {status}")
    
    if not results:
        print("\nNo webhooks tested. Set environment variables:")
        print("  $env:SLACK_WEBHOOK_URL = 'https://hooks.slack.com/...'")
        print("  $env:DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'")
        print("\nOr pass URL as argument:")
        print("  python test_webhooks.py slack https://hooks.slack.com/...")

if __name__ == "__main__":
    main()

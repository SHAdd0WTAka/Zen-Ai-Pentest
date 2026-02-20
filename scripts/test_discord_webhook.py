#!/usr/bin/env python3
"""
Test Discord Webhook Format and Connectivity

This script tests Discord webhook configuration and JSON payload formatting.
Usage: python scripts/test_discord_webhook.py [WEBHOOK_URL]

If WEBHOOK_URL is not provided, it will check the DISCORD_WEBHOOK_URL environment variable.
"""

import json
import os
import re
import sys
from urllib.parse import urlparse


def validate_webhook_url(url: str) -> tuple[bool, str]:
    """Validate Discord webhook URL format."""
    if not url:
        return False, "Webhook URL is empty"
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False, f"Invalid scheme: {parsed.scheme}. Must be http or https."
        
        if not parsed.netloc:
            return False, "Missing host in URL"
        
        # Discord webhook URL pattern
        discord_pattern = r'^https?://(?:discord\.com|discordapp\.com)/api/webhooks/\d+/[\w-]+$'
        if not re.match(discord_pattern, url):
            return False, (
                "URL does not match Discord webhook format.\n"
                "Expected: https://discord.com/api/webhooks/{id}/{token}\n"
                "  or:     https://discordapp.com/api/webhooks/{id}/{token}"
            )
        
        return True, "Webhook URL format is valid"
    except Exception as e:
        return False, f"URL parsing error: {e}"


def create_test_payload() -> dict:
    """Create a test Discord embed payload."""
    return {
        "embeds": [{
            "title": "Test Notification",
            "description": "This is a test message from Zen-AI-Pentest webhook validator.",
            "color": 3447003,  # Blue
            "timestamp": "2024-01-01T00:00:00.000Z",
            "footer": {
                "text": "ZenClaw Guardian | Test"
            },
            "fields": [
                {
                    "name": "Status",
                    "value": "Webhook configuration valid",
                    "inline": True
                },
                {
                    "name": "Repository",
                    "value": "zen-ai-pentest",
                    "inline": True
                }
            ]
        }]
    }


def sanitize_for_json(text: str) -> str:
    """Sanitize text for safe JSON embedding."""
    # Replace backslashes first
    text = text.replace('\\', '\\\\')
    # Replace double quotes
    text = text.replace('"', '\\"')
    # Replace newlines
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '')
    # Replace tabs
    text = text.replace('\t', '\\t')
    return text


def test_json_serialization() -> bool:
    """Test JSON payload creation and serialization."""
    print("Testing JSON payload serialization...")
    
    # Test with problematic characters
    test_cases = [
        ("Simple text", "Simple text"),
        ("Text with \"quotes\"", 'Text with \\"quotes\\"'),
        ("Text with\\nnewlines", "Text with\\nnewlines"),
        ("Text with \\ backslash", "Text with \\\\ backslash"),
        ("Special: <>&'", "Special: <>&'"),
        ("Unicode: hello world", "Unicode: hello world"),
    ]
    
    all_passed = True
    for original, expected_escaped in test_cases:
        sanitized = sanitize_for_json(original)
        
        # Try to embed in JSON
        try:
            payload = f'{{"text": "{sanitized}"}}'
            parsed = json.loads(payload)
            
            # Verify round-trip
            if parsed["text"] != original:
                print(f"  [ERR] Round-trip failed for: {original}")
                print(f"     Expected: {original}")
                print(f"     Got: {parsed['text']}")
                all_passed = False
            else:
                print(f"  [OK] Pass: {original[:30]}...")
        except json.JSONDecodeError as e:
            print(f"  [ERR] JSON parse error for: {original}")
            print(f"     Error: {e}")
            all_passed = False
    
    return all_passed


def test_webhook_payload(webhook_url: str) -> bool:
    """Test sending a webhook payload (requires requests)."""
    try:
        import requests
    except ImportError:
        print("[WARN] 'requests' library not installed. Install with: pip install requests")
        print("   Skipping live webhook test.")
        return True
    
    print("\nTesting live webhook...")
    
    payload = create_test_payload()
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 204:
            print("  [OK] Webhook test message sent successfully!")
            return True
        elif response.status_code == 404:
            print(f"  [ERR] Webhook not found (404). Check your webhook URL.")
            return False
        elif response.status_code == 429:
            print(f"  [WARN] Rate limited (429). Too many requests.")
            return False
        else:
            print(f"  [ERR] Unexpected status code: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("  [ERR] Request timed out after 10 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("  [ERR] Connection error. Check your internet connection.")
        return False
    except Exception as e:
        print(f"  [ERR] Error: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Discord Webhook Validator")
    print("=" * 60)
    
    # Get webhook URL
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DISCORD_WEBHOOK_URL', '')
    
    # Validate URL format
    print("\n1. Validating webhook URL format...")
    is_valid, message = validate_webhook_url(webhook_url)
    if is_valid:
        print(f"  [OK] {message}")
    else:
        print(f"  [ERR] {message}")
        print("\nHow to fix:")
        print("   1. Get webhook URL from Discord: Server Settings -> Integrations -> Webhooks")
        print("   2. Add to GitHub Secrets: Settings -> Secrets -> DISCORD_WEBHOOK_URL")
        return 1
    
    # Test JSON serialization
    print("\n2. Testing JSON payload serialization...")
    if not test_json_serialization():
        print("\n  [WARN] Some serialization tests failed")
    
    # Test live webhook (optional)
    print("\n3. Testing live webhook (optional)...")
    test_live = input("   Send test message to Discord? (y/N): ").lower().strip() == 'y'
    
    if test_live:
        if not test_webhook_payload(webhook_url):
            return 1
    else:
        print("   [SKIP] Skipped live test")
    
    print("\n" + "=" * 60)
    print("Validation complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

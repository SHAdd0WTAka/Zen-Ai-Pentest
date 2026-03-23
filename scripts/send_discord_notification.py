#!/usr/bin/env python3
"""
Discord Notification Sender for GitHub Actions

Sends formatted Discord embed notifications for various GitHub events.
Reads configuration from environment variables.

Usage:
    python scripts/send_discord_notification.py

Environment Variables:
    DISCORD_WEBHOOK - Discord webhook URL (required)
    GITHUB_EVENT_NAME - Type of GitHub event (push, pull_request, etc.)
    GITHUB_ACTOR - Username of the actor
    GITHUB_REPOSITORY - Repository name
    GITHUB_REF_NAME - Branch name
    Plus various event-specific variables
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def mask_secrets(content: str) -> str:
    """Mask potential secrets in content."""
    import re

    patterns = [
        (r"sk-[a-zA-Z0-9]{20,}", "**********"),
        (r"gh[pousr]_[A-Za-z0-9_]{36,}", "**********"),
        (r"gho_[a-zA-Z0-9]{36}", "**********"),
        (r"ghs_[a-zA-Z0-9]{36}", "**********"),
        (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "**********"),
        (r"AKIA[0-9A-Z]{16}", "**********"),
        (r"ASIA[0-9A-Z]{16}", "**********"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    return content


def truncate(text: str, max_length: int = 500) -> str:
    """Truncate text to max length."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def build_payload(event_name: str, env: dict) -> dict:
    """Build Discord embed payload based on event type."""

    # Default values
    color = 3447003  # Blue
    title = "🔔 GitHub Event"
    description = f"Event: {event_name}"
    url = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{env.get('GITHUB_REPOSITORY', '')}"

    actor = env.get("GITHUB_ACTOR", "unknown")
    repo = env.get("GITHUB_REPOSITORY", "unknown")

    if event_name == "push":
        color = 3066993  # Green
        title = "🚀 Code Pushed"

        commit_msg = mask_secrets(env.get("COMMIT_MSG", ""))
        branch = env.get("GITHUB_REF_NAME", "unknown")

        security_warning = ""
        if env.get("SUSPICIOUS") == "1":
            security_warning = "\n\n🔒 **Security Notice:** Potential sensitive data detected and masked."

        commit_preview = (
            commit_msg.split("\n")[0] if commit_msg else "No message"
        )
        description = f"**Branch:** `{branch}`\n**Author:** {actor}\n**Commit:** `{commit_preview}`{security_warning}"
        url = env.get("COMMIT_URL", url)

    elif event_name == "pull_request":
        action = env.get("PR_ACTION", "unknown")
        pr_number = env.get("PR_NUMBER", "")
        pr_title = mask_secrets(env.get("PR_TITLE", ""))
        head_ref = env.get("HEAD_REF", "unknown")
        base_ref = env.get("BASE_REF", "unknown")
        merged = env.get("PR_MERGED", "false")

        if action == "opened":
            color = 3066993  # Green
            title = "🔀 Pull Request Opened"
        elif action == "closed":
            color = 15158332  # Orange
            if merged == "true":
                title = "✅ Pull Request Merged"
            else:
                title = "📝 Pull Request Closed"
        else:
            color = 15158332  # Orange
            title = f"📝 Pull Request {action}"

        description = f"**#{pr_number}:** {pr_title}\n**Author:** {actor}\n**Branch:** `{head_ref}` → `{base_ref}`"
        url = env.get("PR_URL", url)

    elif event_name == "issues":
        action = env.get("ISSUE_ACTION", "unknown")
        issue_number = env.get("ISSUE_NUMBER", "")
        issue_title = mask_secrets(env.get("ISSUE_TITLE", ""))

        if action == "opened":
            color = 15158332  # Orange
            title = "📋 Issue Opened"
        elif action == "closed":
            color = 3066993  # Green
            title = "✅ Issue Closed"
        else:
            color = 3447003  # Blue
            title = f"📝 Issue {action}"

        description = (
            f"**#{issue_number}:** {issue_title}\n**Author:** {actor}"
        )
        url = env.get("ISSUE_URL", url)

    elif event_name == "workflow_run":
        conclusion = env.get("WORKFLOW_CONCLUSION", "unknown")
        workflow_name = env.get("WORKFLOW_NAME", "Unknown")
        run_id = env.get("WORKFLOW_RUN_ID", "")
        head_branch = env.get("WORKFLOW_BRANCH", "unknown")

        if conclusion == "success":
            color = 3066993  # Green
            title = "✅ Workflow Success"
        elif conclusion == "failure":
            color = 15158332  # Red
            title = "❌ Workflow Failed"
        else:
            color = 3447003  # Blue
            title = f"⚠️ Workflow {conclusion}"

        description = f"**Workflow:** {workflow_name}\n**Branch:** `{head_branch}`\n**Run ID:** {run_id}"
        url = env.get("WORKFLOW_URL", url)

    elif event_name == "release":
        color = 10181046  # Purple
        title = "🎉 New Release Published"
        tag_name = env.get("RELEASE_TAG", "unknown")
        release_name = mask_secrets(env.get("RELEASE_NAME", ""))
        description = f"**Version:** {tag_name}\n**Name:** {release_name}"
        url = env.get("RELEASE_URL", url)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "embeds": [
            {
                "title": title,
                "description": description,
                "url": url,
                "color": color,
                "timestamp": timestamp,
                "footer": {"text": repo},
                "author": {
                    "name": actor,
                    "icon_url": f"https://github.com/{actor}.png",
                },
            }
        ]
    }


def send_notification(
    webhook_url: str, payload: dict, max_retries: int = 3
) -> bool:
    """Send notification to Discord with retry logic."""
    import time

    data = json.dumps(payload).encode("utf-8")

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.getcode()

                if status_code == 204:
                    print("✅ Discord notification sent successfully")
                    return True
                else:
                    print(f"⚠️ Unexpected status code: {status_code}")
                    return True  # Don't retry on unexpected codes

        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    print(
                        f"⚠️ Rate limited (429). Retrying in 5 seconds... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(5)
                    continue
                else:
                    print("⚠️ Discord rate limit hit. Max retries reached.")
                    return True  # Don't fail on rate limit
            elif e.code == 404:
                print(
                    "❌ Discord webhook not found (404). Check your DISCORD_WEBHOOK_URL secret."
                )
                return True  # Don't fail on 404
            elif e.code == 400:
                print("❌ Bad request (400). Check the payload format.")
                return True  # Don't fail on 400
            else:
                print(f"⚠️ HTTP Error: {e.code}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return True

        except Exception as e:
            print(f"⚠️ Error sending notification: {e}")
            if attempt < max_retries - 1:
                print(
                    f"Retrying in 3 seconds... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(3)
                continue
            else:
                print("⚠️ Max retries reached. Giving up.")
                return True  # Don't fail the workflow

    return True


def main():
    """Main entry point."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK")

    if not webhook_url:
        print("⚠️ DISCORD_WEBHOOK not set. Skipping notification.")
        print(
            "   To enable notifications, add DISCORD_WEBHOOK_URL to GitHub Secrets."
        )
        return 0

    event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")

    try:
        payload = build_payload(event_name, os.environ)

        # Validate JSON
        json.dumps(payload)

        # Send notification
        send_notification(webhook_url, payload)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 0  # Don't fail the workflow


if __name__ == "__main__":
    sys.exit(main())

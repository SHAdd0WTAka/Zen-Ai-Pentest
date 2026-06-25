"""
Legacy settings and integration routes extracted from api/main.py.

Deprecated: Use /api/v1/settings/* endpoints instead.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth_deps import verify_token
from database.models import get_db

router = APIRouter(tags=["Legacy Settings"])

# Store Slack webhook in memory (in production: use database)
SLACK_CONFIG = {"webhook_url": None, "enabled": False}


def _validate_slack_webhook_url(webhook_url: str) -> str:
    """
    Validate that the provided webhook URL is a Slack webhook URL.

    This prevents server-side request forgery by restricting outbound
    requests to the official Slack webhook host.
    """
    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url is required")

    try:
        # Reuse centralized validation logic from notifications.slack
        from notifications.slack import _validate_slack_webhook_url as _core_validate_slack_webhook_url

        return _core_validate_slack_webhook_url(webhook_url)
    except ValueError as e:
        # Map validation errors to HTTP 400 responses
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# SLACK SETTINGS
# ============================================================================


@router.get("/settings/slack")
async def get_slack_settings(user: Any = Depends(verify_token)):
    """Get Slack configuration (without sensitive data)"""
    return {
        "enabled": SLACK_CONFIG["enabled"],
        "configured": SLACK_CONFIG["webhook_url"] is not None,
    }


@router.post("/settings/slack")
async def update_slack_settings(webhook_url: str, enabled: bool = True, user: Any = Depends(verify_token)):
    """Update Slack configuration"""
    global SLACK_CONFIG
    SLACK_CONFIG["webhook_url"] = webhook_url
    SLACK_CONFIG["enabled"] = enabled
    return {"status": "success", "message": "Slack settings updated"}


# ============================================================================
# JIRA SETTINGS
# ============================================================================


@router.get("/settings/jira")
async def get_jira_settings(user: Any = Depends(verify_token)):
    """Get JIRA configuration (without sensitive data)"""
    from integrations.jira_client import JIRA_CONFIG

    return {
        "enabled": JIRA_CONFIG["enabled"],
        "configured": JIRA_CONFIG["base_url"] is not None,
        "base_url": JIRA_CONFIG["base_url"],
    }


@router.post("/settings/jira")
async def update_jira_settings(
    base_url: str,
    username: str,
    api_token: str,
    enabled: bool = True,
    user: Any = Depends(verify_token),
):
    """Update JIRA configuration"""
    from integrations.jira_client import JIRA_CONFIG

    JIRA_CONFIG["base_url"] = base_url
    JIRA_CONFIG["username"] = username
    JIRA_CONFIG["api_token"] = api_token
    JIRA_CONFIG["enabled"] = enabled
    return {"status": "success", "message": "JIRA settings updated"}


@router.post("/settings/jira/test")
async def test_jira_connection(user: Any = Depends(verify_token)):
    """Test JIRA connection"""
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    if client.test_connection():
        return {"status": "success", "message": "Connection successful"}
    else:
        raise HTTPException(status_code=400, detail="Connection failed")


@router.get("/settings/jira/projects")
async def get_jira_projects(user: Any = Depends(verify_token)):
    """Get available JIRA projects"""
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    projects = client.get_projects()
    return [{"key": p["key"], "name": p["name"]} for p in projects]


@router.post("/integrations/jira/create-ticket")
async def create_jira_ticket(
    finding_id: int,
    project_key: str,
    user: Any = Depends(verify_token),
    db=Depends(get_db),
):
    """Create JIRA ticket from finding"""
    from database.models import Finding
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    # Get finding
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Create ticket
    result = client.create_finding_ticket(
        project_key=project_key,
        finding={
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "target": finding.target,
            "tool": finding.tool,
        },
    )

    if result:
        return {
            "status": "success",
            "ticket_key": result.get("key"),
            "ticket_url": f"{client.base_url}/browse/{result.get('key')}",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create ticket")

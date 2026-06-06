"""
Notification API Routes for Zen-AI-Pentest

REST API endpoints for notification management.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database.models import get_db

logger = logging.getLogger(__name__)

# Import notification components
try:
    from notifications.manager import NotificationManager, get_notification_manager
    from notifications.models import NotificationHistory, NotificationSettings

    NOTIFICATIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Notification system not available: {e}")
    NOTIFICATIONS_AVAILABLE = False

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ============================================================================
# Pydantic Models
# ============================================================================


class NotificationSettingsBase(BaseModel):
    """Base notification settings"""

    # Slack
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = Field(None, max_length=500)
    slack_channel: Optional[str] = Field(None, max_length=100)

    # Discord
    discord_enabled: bool = False
    discord_webhook_url: Optional[str] = Field(None, max_length=500)

    # Email
    email_enabled: bool = False
    email_address: Optional[str] = Field(None, max_length=255)

    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = Field(None, max_length=255)
    telegram_chat_id: Optional[str] = Field(None, max_length=100)

    # Webhook
    webhook_enabled: bool = False
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_headers: Optional[Dict[str, str]] = Field(default_factory=dict)

    # Subscriptions
    notify_on_scan_start: bool = False
    notify_on_scan_complete: bool = True
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False
    notify_on_system_alert: bool = True
    notify_on_report_ready: bool = True

    # Rate limiting
    rate_limit_per_minute: int = Field(default=10, ge=1, le=60)


class NotificationSettingsCreate(NotificationSettingsBase):
    """Create notification settings"""

    pass


class NotificationSettingsUpdate(BaseModel):
    """Update notification settings"""

    slack_enabled: Optional[bool] = None
    slack_webhook_url: Optional[str] = Field(None, max_length=500)
    slack_channel: Optional[str] = Field(None, max_length=100)

    discord_enabled: Optional[bool] = None
    discord_webhook_url: Optional[str] = Field(None, max_length=500)

    email_enabled: Optional[bool] = None
    email_address: Optional[str] = Field(None, max_length=255)

    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = Field(None, max_length=255)
    telegram_chat_id: Optional[str] = Field(None, max_length=100)

    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_headers: Optional[Dict[str, str]] = None

    notify_on_scan_start: Optional[bool] = None
    notify_on_scan_complete: Optional[bool] = None
    notify_on_critical: Optional[bool] = None
    notify_on_high: Optional[bool] = None
    notify_on_medium: Optional[bool] = None
    notify_on_system_alert: Optional[bool] = None
    notify_on_report_ready: Optional[bool] = None

    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=60)


class NotificationSettingsResponse(BaseModel):
    """Notification settings response"""

    id: int
    user_id: int
    slack: Dict[str, Any]
    discord: Dict[str, Any]
    email: Dict[str, Any]
    telegram: Dict[str, Any]
    webhook: Dict[str, Any]
    subscriptions: Dict[str, bool]
    rate_limit: int
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationTestRequest(BaseModel):
    """Test notification request"""

    channel: str = Field(..., pattern="^(slack|discord|email|telegram|webhook)$")


class NotificationTestResponse(BaseModel):
    """Test notification response"""

    success: bool
    channel: str
    message: str
    details: Optional[Dict[str, Any]] = None


class NotificationHistoryResponse(BaseModel):
    """Notification history item"""

    id: int
    channel: str
    event_type: str
    status: str
    title: str
    message: str
    response_status: Optional[str] = None
    retry_count: int
    created_at: str
    sent_at: Optional[str] = None
    error_message: Optional[str] = None


class NotificationHistoryListResponse(BaseModel):
    """Notification history list"""

    items: List[NotificationHistoryResponse]
    total: int
    page: int
    page_size: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""

    total: int
    sent: int
    failed: int
    success_rate: float
    by_channel: Dict[str, int]


class RateLimitStatusResponse(BaseModel):
    """Rate limit status"""

    channels: Dict[str, Dict[str, Any]]


class SendNotificationRequest(BaseModel):
    """Send notification request (admin only)"""

    user_id: int
    event_type: str = Field(
        ..., pattern="^(scan_started|scan_completed|critical_finding|high_severity_cve|system_alert|report_ready)$"
    )
    data: Dict[str, Any]
    channels: Optional[List[str]] = None


class SendNotificationResponse(BaseModel):
    """Send notification response"""

    success: bool
    channels: Dict[str, Any]


# ============================================================================
# Dependencies
# ============================================================================


def get_manager(db: Session = Depends(get_db)) -> NotificationManager:
    """Get notification manager with database session"""
    if not NOTIFICATIONS_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification system not available")
    return get_notification_manager(db)


def get_current_user_id() -> int:
    """Get current user ID from auth (placeholder - integrate with actual auth)"""
    # This should be replaced with actual auth dependency
    # For now, returns a placeholder - in production use JWT token
    return 1


# ============================================================================
# Routes
# ============================================================================


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get notification settings for current user.

    Returns the user's notification configuration including:
    - Enabled channels (Slack, Discord, Email, Telegram, Webhook)
    - Channel-specific settings
    - Event subscriptions
    - Rate limiting configuration
    """
    if not NOTIFICATIONS_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification system not available")

    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()

    if not settings:
        # Return default settings
        return NotificationSettingsResponse(
            id=0,
            user_id=user_id,
            slack={"enabled": False, "channel": None, "configured": False},
            discord={"enabled": False, "configured": False},
            email={"enabled": False, "address": None, "configured": False},
            telegram={"enabled": False, "configured": False},
            webhook={"enabled": False, "url": None, "configured": False},
            subscriptions={
                "scan_start": False,
                "scan_complete": True,
                "critical": True,
                "high": True,
                "medium": False,
                "system_alert": True,
                "report_ready": True,
            },
            rate_limit=10,
        )

    return NotificationSettingsResponse(**settings.to_dict())


@router.post("/settings", response_model=NotificationSettingsResponse)
async def create_or_update_settings(
    settings_data: NotificationSettingsCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Create or update notification settings.

    Configure notification channels and event subscriptions.
    Sensitive data like tokens and webhooks are stored encrypted.
    """
    if not NOTIFICATIONS_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification system not available")

    # Check if settings exist
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()

    if settings:
        # Update existing
        for key, value in settings_data.model_dump().items():
            setattr(settings, key, value)
        settings.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        settings = NotificationSettings(user_id=user_id, **settings_data.model_dump())
        db.add(settings)

    db.commit()
    db.refresh(settings)

    return NotificationSettingsResponse(**settings.to_dict())


@router.patch("/settings", response_model=NotificationSettingsResponse)
async def update_settings(
    settings_data: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Partially update notification settings.

    Only updates provided fields, leaving others unchanged.
    """
    if not NOTIFICATIONS_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification system not available")

    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification settings not found. Create settings first."
        )

    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)

    return NotificationSettingsResponse(**settings.to_dict())


@router.post("/test", response_model=NotificationTestResponse)
async def test_notification(
    request: NotificationTestRequest,
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """
    Send test notification to specified channel.

    Use this to verify your notification configuration is working correctly.
    """
    result = await manager.test_channel(user_id, request.channel)

    return NotificationTestResponse(
        success=result.get("success", False),
        channel=request.channel,
        message="Test notification sent successfully" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )


@router.get("/history", response_model=NotificationHistoryListResponse)
async def get_notification_history(
    channel: Optional[str] = Query(None, pattern="^(slack|discord|email|telegram|webhook)$"),
    status: Optional[str] = Query(None, pattern="^(sent|failed|retrying)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get notification history for current user.

    Returns paginated list of sent notifications with status.
    """
    offset = (page - 1) * page_size

    history = manager.get_notification_history(
        user_id=user_id,
        limit=page_size,
        offset=offset,
        channel=channel,
        status=status,
    )

    # Get total count
    # Note: In production, use a count query instead of loading all
    total = len(history)  # Simplified - should query count from DB

    return NotificationHistoryListResponse(
        items=[NotificationHistoryResponse(**h) for h in history],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get notification statistics for current user.

    Returns counts and success rates by channel.
    """
    stats = manager.get_stats(user_id)
    return NotificationStatsResponse(**stats)


@router.get("/rate-limit", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """
    Get current rate limit status for all channels.

    Shows remaining requests per channel within the rate limit window.
    """
    status = await manager.get_rate_limit_status(user_id)
    return RateLimitStatusResponse(channels=status)


@router.post("/send", response_model=SendNotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    manager: NotificationManager = Depends(get_manager),
    # admin_user: bool = Depends(require_admin),  # Uncomment when auth is ready
):
    """
    Send notification to a user (Admin only).

    This endpoint allows administrators to send notifications to specific users.
    Requires admin privileges.
    """
    # TODO: Add admin check
    # if not admin_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )

    result = await manager.send_notification(
        user_id=request.user_id,
        event_type=request.event_type,
        data=request.data,
        channels=request.channels,
    )

    return SendNotificationResponse(
        success=result.get("success", False),
        channels=result.get("channels", {}),
    )


@router.delete("/history")
async def clear_notification_history(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    older_than_days: Optional[int] = Query(None, ge=1),
):
    """
    Clear notification history.

    If older_than_days is provided, only deletes entries older than specified days.
    Otherwise deletes all history for the user.
    """
    if not NOTIFICATIONS_AVAILABLE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification system not available")

    query = db.query(NotificationHistory).filter(NotificationHistory.user_id == user_id)

    if older_than_days:
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        query = query.filter(NotificationHistory.created_at < cutoff)

    deleted = query.delete()
    db.commit()

    return {
        "message": f"Deleted {deleted} notification history entries",
        "deleted_count": deleted,
    }


# ============================================================================
# Channel-specific shortcuts
# ============================================================================


@router.post("/test/slack", response_model=NotificationTestResponse)
async def test_slack(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """Quick test for Slack notifications"""
    result = await manager.test_channel(user_id, "slack")
    return NotificationTestResponse(
        success=result.get("success", False),
        channel="slack",
        message="Slack test " + ("successful" if result.get("success") else "failed"),
        details=result,
    )


@router.post("/test/discord", response_model=NotificationTestResponse)
async def test_discord(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """Quick test for Discord notifications"""
    result = await manager.test_channel(user_id, "discord")
    return NotificationTestResponse(
        success=result.get("success", False),
        channel="discord",
        message="Discord test " + ("successful" if result.get("success") else "failed"),
        details=result,
    )


@router.post("/test/email", response_model=NotificationTestResponse)
async def test_email(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """Quick test for Email notifications"""
    result = await manager.test_channel(user_id, "email")
    return NotificationTestResponse(
        success=result.get("success", False),
        channel="email",
        message="Email test " + ("successful" if result.get("success") else "failed"),
        details=result,
    )


@router.post("/test/telegram", response_model=NotificationTestResponse)
async def test_telegram(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """Quick test for Telegram notifications"""
    result = await manager.test_channel(user_id, "telegram")
    return NotificationTestResponse(
        success=result.get("success", False),
        channel="telegram",
        message="Telegram test " + ("successful" if result.get("success") else "failed"),
        details=result,
    )


@router.post("/test/webhook", response_model=NotificationTestResponse)
async def test_webhook(
    manager: NotificationManager = Depends(get_manager),
    user_id: int = Depends(get_current_user_id),
):
    """Quick test for Webhook notifications"""
    result = await manager.test_channel(user_id, "webhook")
    return NotificationTestResponse(
        success=result.get("success", False),
        channel="webhook",
        message="Webhook test " + ("successful" if result.get("success") else "failed"),
        details=result,
    )


# Import datetime for the routes
from datetime import datetime, timezone

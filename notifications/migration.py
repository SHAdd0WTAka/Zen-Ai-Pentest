"""
Database Migration for Notification System

Creates the necessary tables for the notification system.
Run this after adding the notification models.
"""

import logging
import sys

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)
Base = declarative_base()


def create_notification_tables(database_url: str = None):
    """
    Create notification tables.

    Args:
        database_url: Database URL. If None, uses DATABASE_URL env var.
    """
    import os

    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zen_pentest")

    engine = create_engine(database_url)

    # Import models to register them
    try:
        from notifications.models import NotificationHistory, NotificationSettings, NotificationTemplate

        logger.info("Using models from notifications.models")
    except ImportError:
        logger.warning("Could not import notification models, creating tables manually")
        # Define tables manually for migration

        class NotificationSettings(Base):
            __tablename__ = "notification_settings"

            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
            created_at = Column(DateTime)
            updated_at = Column(DateTime)

            # Slack
            slack_enabled = Column(Boolean, default=False)
            slack_webhook_url = Column(String(500))
            slack_channel = Column(String(100))

            # Discord
            discord_enabled = Column(Boolean, default=False)
            discord_webhook_url = Column(String(500))

            # Email
            email_enabled = Column(Boolean, default=False)
            email_address = Column(String(255))

            # Telegram
            telegram_enabled = Column(Boolean, default=False)
            telegram_bot_token = Column(String(255))
            telegram_chat_id = Column(String(100))

            # Webhook
            webhook_enabled = Column(Boolean, default=False)
            webhook_url = Column(String(500))
            webhook_headers = Column(JSON, default=dict)

            # Subscriptions
            notify_on_scan_start = Column(Boolean, default=False)
            notify_on_scan_complete = Column(Boolean, default=True)
            notify_on_critical = Column(Boolean, default=True)
            notify_on_high = Column(Boolean, default=True)
            notify_on_medium = Column(Boolean, default=False)
            notify_on_system_alert = Column(Boolean, default=True)
            notify_on_report_ready = Column(Boolean, default=True)

            # Rate limiting
            rate_limit_per_minute = Column(Integer, default=10)

            __table_args__ = (Index("ix_notification_settings_user", "user_id"),)

        class NotificationHistory(Base):
            __tablename__ = "notification_history"

            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
            channel = Column(String(50), nullable=False, index=True)
            event_type = Column(String(50), nullable=False, index=True)
            status = Column(String(20), nullable=False, index=True)
            title = Column(String(255))
            message = Column(Text)
            payload = Column(JSON, default=dict)
            response_status = Column(String(50))
            retry_count = Column(Integer, default=0)
            created_at = Column(DateTime)
            sent_at = Column(DateTime)
            error_message = Column(Text)

            __table_args__ = (
                Index("ix_notification_history_user_created", "user_id", "created_at"),
                Index("ix_notification_history_status", "status", "created_at"),
            )

        class NotificationTemplate(Base):
            __tablename__ = "notification_templates"

            id = Column(Integer, primary_key=True)
            user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
            name = Column(String(100), nullable=False)
            event_type = Column(String(50), nullable=False, index=True)
            channel = Column(String(50), nullable=False)
            subject_template = Column(String(500))
            body_template = Column(Text, nullable=False)
            color = Column(String(20))
            is_default = Column(Boolean, default=False)
            is_enabled = Column(Boolean, default=True)
            created_at = Column(DateTime)
            updated_at = Column(DateTime)

            __table_args__ = (
                Index("ix_notification_templates_event", "event_type", "channel"),
                Index("ix_notification_templates_user", "user_id", "name"),
            )

    # Create tables
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[
                NotificationSettings.__table__,
                NotificationHistory.__table__,
                NotificationTemplate.__table__,
            ],
        )
        logger.info("✅ Notification tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create notification tables: {e}")
        return False


def migrate_data():
    """Migrate any existing data if needed"""
    # Future: Add data migration logic here
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Allow database URL from command line
    db_url = sys.argv[1] if len(sys.argv) > 1 else None

    success = create_notification_tables(db_url)
    sys.exit(0 if success else 1)

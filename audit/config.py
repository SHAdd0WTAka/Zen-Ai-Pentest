"""
Audit Logging Configuration

Configuration for the audit logging system following ISO 27001 standards.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import List, Optional


class LogLevel(Enum):
    """Audit log severity levels"""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class EventCategory(Enum):
    """Categories of audit events"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY = "security"
    SYSTEM = "system"
    SCAN = "scan"
    EXPLOIT = "exploit"
    ADMIN = "administrative"


class RetentionPolicy(Enum):
    """Log retention policies based on compliance requirements"""

    SHORT = timedelta(days=30)  # Debug/Info logs
    STANDARD = timedelta(days=90)  # Normal operations
    EXTENDED = timedelta(days=365)  # Security events
    PERMANENT = None  # Critical security events


@dataclass
class AuditConfig:
    """Configuration for audit logging system"""

    # Storage Configuration
    storage_backend: str = "postgresql"  # postgresql, sqlite, elasticsearch
    connection_string: str = ""
    log_table: str = "audit_logs"
    archive_table: str = "audit_logs_archive"

    # Retention Policy
    retention_policies: dict = None
    archive_enabled: bool = True
    archive_after_days: int = 90

    # SIEM Integration
    siem_enabled: bool = False
    siem_url: str = ""
    siem_api_key: str = ""
    siem_batch_size: int = 100
    siem_flush_interval: int = 60

    # Alerting
    alert_on_critical: bool = True
    alert_on_security: bool = True
    alert_webhook_url: str = ""

    # Performance
    async_logging: bool = True
    buffer_size: int = 1000
    flush_interval: float = 5.0

    # Security
    sign_logs: bool = True
    signature_key: str = ""
    encrypt_sensitive: bool = True
    hash_algorithm: str = "sha256"

    # Compliance
    compliance_mode: str = "strict"  # strict, standard, relaxed
    include_pii: bool = False
    mask_fields: Optional[List[str]] = None

    def __post_init__(self):
        if self.retention_policies is None:
            self.retention_policies = {
                LogLevel.DEBUG: RetentionPolicy.SHORT,
                LogLevel.INFO: RetentionPolicy.STANDARD,
                LogLevel.NOTICE: RetentionPolicy.STANDARD,
                LogLevel.WARNING: RetentionPolicy.EXTENDED,
                LogLevel.ERROR: RetentionPolicy.EXTENDED,
                LogLevel.CRITICAL: RetentionPolicy.PERMANENT,
                LogLevel.ALERT: RetentionPolicy.PERMANENT,
                LogLevel.EMERGENCY: RetentionPolicy.PERMANENT,
            }

        if self.mask_fields is None:
            self.mask_fields = [
                "password",
                "secret",
                "token",
                "api_key",
                "private_key",
                "credit_card",
                "ssn",
                "personal_id",
            ]

    @classmethod
    def default(cls) -> "AuditConfig":
        """Get default audit configuration"""
        return cls(
            connection_string="postgresql://localhost/zen_audit",
            siem_enabled=False,
            async_logging=True,
            sign_logs=True,
            encrypt_sensitive=True,
        )

    @classmethod
    def strict(cls) -> "AuditConfig":
        """Get strict compliance configuration (ISO 27001)"""
        return cls(
            connection_string="postgresql://localhost/zen_audit",
            siem_enabled=True,
            async_logging=False,  # Synchronous for strict compliance
            sign_logs=True,
            encrypt_sensitive=True,
            compliance_mode="strict",
            include_pii=False,
            retention_policies={
                level: (
                    RetentionPolicy.EXTENDED
                    if level.value in ["debug", "info", "notice"]
                    else RetentionPolicy.PERMANENT
                )
                for level in LogLevel
            },
        )

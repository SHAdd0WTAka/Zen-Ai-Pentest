"""Scan model stub for CI/CD compatibility."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScanStatus(Enum):
    """Scan status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(Enum):
    """Scan types."""

    PORT_SCAN = "port_scan"
    VULNERABILITY = "vulnerability"
    WEB_APP = "web_app"
    NETWORK = "network"
    COMPLIANCE = "compliance"
    FULL = "full"


class Scan:
    """Stub Scan model for CI/CD compatibility."""

    def __init__(
        self,
        name: str,
        target: str,
        scan_type: ScanType = ScanType.PORT_SCAN,
        status: ScanStatus = ScanStatus.PENDING,
        created_by: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        schedule: Optional[Dict[str, Any]] = None,
    ):
        """Initialize scan."""
        self.id = "scan-stub-id"
        self.name = name
        self.target = target
        self.scan_type = scan_type
        self.status = status
        self.created_by = created_by
        self.config = config or {}
        self.schedule = schedule
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: int = 0
        self.findings_count: int = 0
        self.error_message: Optional[str] = None

    @classmethod
    async def find_one(cls, **kwargs) -> Optional["Scan"]:
        """Stub find method."""
        return None

    @classmethod
    async def find_many(cls, **kwargs) -> List["Scan"]:
        """Stub find many method."""
        return []

    async def save(self) -> None:
        """Stub save method."""
        pass

    async def update(self, **kwargs) -> None:
        """Stub update method."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_response(self) -> Dict[str, Any]:
        """Convert to response dict."""
        return {
            "id": str(self.id),
            "name": self.name,
            "target": self.target,
            "scan_type": self.scan_type.value,
            "status": self.status.value,
            "created_by": self.created_by,
            "config": self.config,
            "schedule": self.schedule,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "findings_count": self.findings_count,
            "error_message": self.error_message,
        }

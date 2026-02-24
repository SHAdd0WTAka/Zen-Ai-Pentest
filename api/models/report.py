"""Report model stub for CI/CD compatibility."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReportFormat(Enum):
    """Report formats."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    MARKDOWN = "markdown"


class ReportStatus(Enum):
    """Report status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report:
    """Stub Report model for CI/CD compatibility."""

    def __init__(
        self,
        name: str,
        scan_id: str,
        format: ReportFormat = ReportFormat.PDF,
        status: ReportStatus = ReportStatus.PENDING,
        created_by: Optional[str] = None,
        template: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """Initialize report."""
        self.id = "report-stub-id"
        self.name = name
        self.scan_id = scan_id
        self.format = format
        self.status = status
        self.created_by = created_by
        self.template = template or "default"
        self.filters = filters or {}
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.file_path: Optional[str] = None
        self.file_size: Optional[int] = None
        self.download_url: Optional[str] = None

    @classmethod
    async def find_one(cls, **kwargs) -> Optional["Report"]:
        """Stub find method."""
        return None

    @classmethod
    async def find_many(cls, **kwargs) -> List["Report"]:
        """Stub find many method."""
        return []

    async def save(self) -> None:
        """Stub save method."""
        pass

    async def update(self, **kwargs) -> None:
        """Stub update method."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        if kwargs.get("status") == ReportStatus.COMPLETED:
            self.completed_at = datetime.utcnow()

    def to_response(self) -> Dict[str, Any]:
        """Convert to response dict."""
        return {
            "id": str(self.id),
            "name": self.name,
            "scan_id": self.scan_id,
            "format": self.format.value,
            "status": self.status.value,
            "created_by": self.created_by,
            "template": self.template,
            "filters": self.filters,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "file_path": self.file_path,
            "file_size": self.file_size,
            "download_url": self.download_url,
        }

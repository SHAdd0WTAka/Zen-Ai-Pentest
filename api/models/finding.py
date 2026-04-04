"""Finding model stub for CI/CD compatibility."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class FindingSeverity(Enum):
    """Finding severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(Enum):
    """Finding status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    RISK_ACCEPTED = "risk_accepted"


class Finding:
    """Stub Finding model for CI/CD compatibility."""

    def __init__(
        self,
        title: str,
        description: str,
        severity: FindingSeverity = FindingSeverity.MEDIUM,
        status: FindingStatus = FindingStatus.OPEN,
        scan_id: Optional[str] = None,
        target: Optional[str] = None,
        tool: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cvss_score: Optional[float] = None,
        cwe_ids: Optional[List[str]] = None,
        cve_ids: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
    ):
        """Initialize finding."""
        self.id = "finding-stub-id"
        self.title = title
        self.description = description
        self.severity = severity
        self.status = status
        self.scan_id = scan_id
        self.target = target
        self.tool = tool
        self.evidence = evidence or {}
        self.remediation = remediation
        self.cvss_score = cvss_score
        self.cwe_ids = cwe_ids or []
        self.cve_ids = cve_ids or []
        self.references = references or []
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.resolved_at: Optional[datetime] = None
        self.resolved_by: Optional[str] = None

    @classmethod
    async def find_one(cls, **kwargs) -> Optional["Finding"]:
        """Stub find method."""
        return None

    @classmethod
    def find_many(cls, **kwargs):
        """Stub find many method - returns a query-like object."""

        class Query:
            def limit(self, n):
                return self

            def skip(self, n):
                return self

            async def to_list(self):
                return []

        return Query()

    async def save(self) -> None:
        """Stub save method."""

    async def update(self, **kwargs) -> None:
        """Stub update method."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)

    def to_response(self) -> Dict[str, Any]:
        """Convert to response dict."""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "scan_id": self.scan_id,
            "target": self.target,
            "tool": self.tool,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "cvss_score": self.cvss_score,
            "cwe_ids": self.cwe_ids,
            "cve_ids": self.cve_ids,
            "references": self.references,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

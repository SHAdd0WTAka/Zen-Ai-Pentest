"""
Pydantic Schemas für API Validierung
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    XML = "xml"


# ============================================================================
# AUTH SCHEMAS
# ============================================================================


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user", pattern="^(admin|user)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    role: str


class UserInfo(BaseModel):
    username: str
    role: str


# ============================================================================
# BASE SCHEMAS
# ============================================================================


class ScanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target: str = Field(..., min_length=1, max_length=500)
    scan_type: str = Field(..., min_length=1, max_length=100)
    config: Optional[Dict[str, Any]] = {}


class ScanCreate(ScanBase):
    objective: Optional[str] = "comprehensive security scan"


class ScanUpdate(BaseModel):
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ScanResponse(ScanBase):
    id: int
    status: str
    user_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[str] = None
    findings_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ============================================================================
# FINDING SCHEMAS
# ============================================================================


class FindingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    cvss_score: Optional[float] = Field(None, ge=0, le=10)
    cve_id: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    tool: Optional[str] = None
    target: Optional[str] = None
    port: Optional[int] = None
    service: Optional[str] = None


class FindingCreate(FindingBase):
    pass


class FindingResponse(FindingBase):
    id: int
    scan_id: int
    created_at: datetime
    verified: int = 0

    class Config:
        from_attributes = True


class FindingUpdate(BaseModel):
    severity: Optional[Severity] = None
    verified: Optional[int] = None
    remediation: Optional[str] = None


# ============================================================================
# REPORT SCHEMAS
# ============================================================================


class ReportBase(BaseModel):
    scan_id: int
    format: ReportFormat = ReportFormat.PDF
    template: Optional[str] = "default"


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# TOOL EXECUTION SCHEMAS
# ============================================================================


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    target: str = Field(..., description="Target to scan")
    parameters: Optional[Dict[str, Any]] = {}
    timeout: Optional[int] = 300


class ToolExecuteResponse(BaseModel):
    scan_id: int
    status: str
    message: str
    estimated_duration: Optional[int] = None


class ToolInfo(BaseModel):
    name: str
    description: str
    category: str
    parameters: Optional[Dict[str, Any]] = {}


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================


class DashboardStats(BaseModel):
    total_scans: int
    active_scans: int
    completed_scans: int
    failed_scans: int
    total_findings: int
    critical_findings: int
    high_findings: int
    reports_generated: int


class RecentActivity(BaseModel):
    id: int
    type: str  # scan, finding, report
    description: str
    timestamp: datetime
    user: str


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activities: List[RecentActivity]
    scans_by_status: Dict[str, int]
    findings_by_severity: Dict[str, int]


# ============================================================================
# WEBSOCKET SCHEMAS
# ============================================================================


class WSMessage(BaseModel):
    type: str  # status, log, result, error
    scan_id: Optional[int] = None
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSCommand(BaseModel):
    action: str  # start, stop, status, ping
    scan_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================


class NotificationBase(BaseModel):
    type: str
    title: str
    message: str


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    read: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ASSET SCHEMAS
# ============================================================================


class AssetBase(BaseModel):
    name: str
    asset_type: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    os: Optional[str] = None
    criticality: str = "medium"


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: int
    services: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_scanned: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# VULNERABILITY DB SCHEMAS
# ============================================================================


class VulnerabilityDBResponse(BaseModel):
    id: int
    cve_id: str
    title: str
    description: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    epss_score: Optional[float] = None
    affected_products: Optional[List[str]] = None
    references: Optional[List[str]] = None
    exploits: Optional[List[str]] = None


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


# ============================================================================
# SCHEDULED SCAN SCHEMAS
# ============================================================================


class ScheduleFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ScheduledScanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target: str = Field(..., min_length=1, max_length=500)
    scan_type: str = "comprehensive"
    frequency: ScheduleFrequency = ScheduleFrequency.WEEKLY
    schedule_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    schedule_day: Optional[int] = Field(None, ge=0, le=6)  # 0=Monday, 6=Sunday for weekly
    enabled: bool = True
    notification_email: Optional[str] = None
    notification_slack: Optional[str] = None


class ScheduledScanUpdate(BaseModel):
    name: Optional[str] = None
    target: Optional[str] = None
    scan_type: Optional[str] = None
    frequency: Optional[ScheduleFrequency] = None
    schedule_time: Optional[str] = None
    schedule_day: Optional[int] = None
    enabled: Optional[bool] = None
    notification_email: Optional[str] = None
    notification_slack: Optional[str] = None
    last_run_status: Optional[str] = None


class ScheduledScanResponse(BaseModel):
    id: int
    name: str
    target: str
    scan_type: str
    frequency: str
    schedule_time: str
    schedule_day: Optional[int] = None
    enabled: bool
    notification_email: Optional[str] = None
    notification_slack: Optional[str] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class ScheduleExecutionResponse(BaseModel):
    id: int
    scheduled_scan_id: int
    scan_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

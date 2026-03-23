"""
Pydantic schemas for scan management
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.scan import ScanType


class ScanConfig(BaseModel):
    """Scan configuration schema"""

    tools: List[str] = Field(default_factory=list)
    ports: Optional[str] = None
    threads: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=300, ge=30, le=3600)
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[str] = None
    follow_redirects: bool = True
    ssl_verification: bool = True
    custom_options: Optional[Dict[str, Any]] = None


class ScanCreate(BaseModel):
    """Scan creation schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target: str = Field(..., min_length=1, max_length=500)
    type: ScanType
    config: Optional[ScanConfig] = None
    template_id: Optional[str] = None
    auto_start: bool = False


class ScanUpdate(BaseModel):
    """Scan update schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[ScanConfig] = None


class ScanData(BaseModel):
    """Scan data schema"""

    id: str
    name: str
    description: Optional[str]
    target: str
    type: str
    status: str
    progress: int
    config: Dict
    findings: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int
    infoCount: int
    createdBy: str
    createdAt: Optional[str]
    startedAt: Optional[str]
    completedAt: Optional[str]
    errorMessage: Optional[str]


class ScanResponse(BaseModel):
    """Scan response schema"""

    success: bool
    data: ScanData


class ScanListResponse(BaseModel):
    """Scan list response schema"""

    success: bool
    data: List[ScanData]
    meta: Dict


class ScanDetailResponse(BaseModel):
    """Scan detail response schema"""

    success: bool
    data: Dict


class ScanProgressData(BaseModel):
    """Scan progress data schema"""

    scanId: str
    status: str
    progress: int
    findingsCount: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int
    infoCount: int


class ScanTemplateCreate(BaseModel):
    """Scan template creation schema"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ScanType
    config: ScanConfig
    is_default: bool = False


class ScanTemplateData(BaseModel):
    """Scan template data schema"""

    id: str
    name: str
    description: Optional[str]
    type: str
    config: Dict
    isDefault: bool
    createdBy: str
    createdAt: Optional[str]


class ScanTemplateResponse(BaseModel):
    """Scan template response schema"""

    id: str
    name: str
    description: Optional[str]
    type: str
    config: Dict
    isDefault: bool
    createdBy: str
    createdAt: Optional[str]

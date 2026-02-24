"""
Pydantic Models for Type Safety and Validation
All configuration, API requests/responses use these models
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Enums
class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackendType(str, Enum):
    DUCKDUCKGO = "duckduckgo"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamps"""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class APIKeyConfig(BaseModel):
    """Secure API key configuration"""

    model_config = ConfigDict(extra="forbid")

    openrouter_key: Optional[str] = Field(
        None, pattern=r"^sk-or-[a-zA-Z0-9]{20,}$"
    )
    openai_key: Optional[str] = Field(None, pattern=r"^sk-[a-zA-Z0-9]{20,}$")
    anthropic_key: Optional[str] = Field(
        None, pattern=r"^sk-ant-[a-zA-Z0-9]{20,}$"
    )
    github_token: Optional[str] = Field(None, min_length=20)
    shodan_key: Optional[str] = None

    @field_validator("*")
    @classmethod
    def mask_keys(cls, v: Optional[str]) -> Optional[str]:
        """Mask API keys in logs"""
        if v and len(v) > 10:
            return v  # Return full value, masking happens in repr
        return v

    def get_key(self, provider: BackendType) -> Optional[str]:
        """Get API key for provider"""
        mapping = {
            BackendType.OPENROUTER: self.openrouter_key,
            BackendType.OPENAI: self.openai_key,
            BackendType.ANTHROPIC: self.anthropic_key,
        }
        return mapping.get(provider)


class ScanConfig(BaseModel):
    """Scan configuration with validation"""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., min_length=1, max_length=253)
    scan_type: Literal["quick", "full", "stealth"] = "quick"
    ports: List[int] = Field(default_factory=lambda: [80, 443])
    templates: List[str] = Field(default_factory=list)
    timeout: int = Field(300, ge=10, le=3600)
    concurrent: int = Field(5, ge=1, le=50)
    follow_redirects: bool = True

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        """Validate target is domain or IP"""
        v = v.strip().lower()

        # Check for dangerous characters
        if re.search(r'[;&|`$(){}[\]\\\'"<>]', v):
            raise ValueError("Target contains dangerous characters")

        # Simple domain validation
        if not re.match(r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$", v):
            # Could be IP
            if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", v):
                raise ValueError("Invalid target format")

        return v

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, v: List[int]) -> List[int]:
        """Validate port numbers"""
        for port in v:
            if not 1 <= port <= 65535:
                raise ValueError(f"Invalid port: {port}")
        return v


class Finding(BaseModel):
    """Security finding/vulnerability"""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    severity: Severity
    cvss_score: Optional[float] = Field(None, ge=0, le=10)
    host: str
    port: Optional[int] = Field(None, ge=1, le=65535)
    service: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    cve_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    confidence: Literal["confirmed", "likely", "possible"] = "possible"

    @field_validator("cve_ids")
    @classmethod
    def validate_cve_format(cls, v: List[str]) -> List[str]:
        """Validate CVE ID format"""
        for cve in v:
            if not re.match(r"^CVE-\d{4}-\d{4,}$", cve, re.IGNORECASE):
                raise ValueError(f"Invalid CVE format: {cve}")
        return [cve.upper() for cve in v]


class ScanResult(BaseModel):
    """Complete scan result"""

    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    target: str
    status: ScanStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[Finding] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate scan duration"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def severity_counts(self) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        return counts


class LLMRequest(BaseModel):
    """LLM request with validation"""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=1, max_length=10000)
    system_prompt: Optional[str] = Field(None, max_length=5000)
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    backend: Optional[BackendType] = None

    @field_validator("prompt")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Basic prompt sanitization"""
        # Remove null bytes
        v = v.replace("\x00", "")
        # Remove control chars except newlines/tabs
        v = "".join(c for c in v if c == "\n" or c == "\t" or ord(c) >= 32)
        return v.strip()


class LLMResponse(BaseModel):
    """LLM response model"""

    model_config = ConfigDict(from_attributes=True)

    content: str
    backend: BackendType
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    cached: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class SubdomainInfo(BaseModel):
    """Subdomain information"""

    name: str
    ip_addresses: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    ports: List[int] = Field(default_factory=list)
    is_alive: bool = False


class DomainRecon(BaseModel):
    """Domain reconnaissance results"""

    domain: str
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    name_servers: List[str] = Field(default_factory=list)
    subdomains: List[SubdomainInfo] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)


class HealthStatus(BaseModel):
    """System health status"""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    checks: Dict[str, bool] = Field(default_factory=dict)
    backends: Dict[str, str] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Paginated API response"""

    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ReportConfig(BaseModel):
    """Report generation configuration"""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    client_name: str = Field(..., min_length=1, max_length=200)
    format: Literal["markdown", "html", "pdf", "json"] = "markdown"
    template: str = "technical"
    include_evidence: bool = True
    include_remediation: bool = True
    severity_filter: Optional[List[Severity]] = None

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        allowed = ["executive", "technical", "detailed"]
        if v not in allowed:
            raise ValueError(f"Template must be one of: {allowed}")
        return v

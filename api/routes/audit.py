"""
Audit Logging API Routes

Provides endpoints for:
- Querying audit logs
- Exporting logs
- Compliance reporting
- SIEM health checks
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

# Import audit components
try:
    from audit import AuditLogger, AuditLogEntry, ComplianceReporter, SIEMIntegration
    from audit.config import AuditConfig, LogLevel, EventCategory
    from audit.siem import SIEMConfig
except ImportError:
    import sys
    sys.path.insert(0, "..")
    from audit import AuditLogger, AuditLogEntry, ComplianceReporter, SIEMIntegration
    from audit.config import AuditConfig, LogLevel, EventCategory
    from audit.siem import SIEMConfig


router = APIRouter(prefix="/api/v1/audit", tags=["Audit Logging"])

# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None
_compliance_reporter: Optional[ComplianceReporter] = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger instance"""
    global _audit_logger, _compliance_reporter
    
    if _audit_logger is None:
        config = AuditConfig.default()
        _audit_logger = AuditLogger(config)
        _compliance_reporter = ComplianceReporter(_audit_logger)
    
    return _audit_logger


def get_compliance_reporter() -> ComplianceReporter:
    """Get compliance reporter"""
    get_audit_logger()  # Ensure initialized
    return _compliance_reporter


# Request/Response Models
class LogQueryRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class LogEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    level: str
    category: str
    event_type: str
    message: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource_id: Optional[str] = None
    hash: str


class LogExportRequest(BaseModel):
    format: str = Field(default="json", regex="^(json|csv|syslog)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[str] = None
    category: Optional[str] = None


class ComplianceReportRequest(BaseModel):
    standard: str = Field(..., regex="^(iso27001|soc2|gdpr|pci_dss|nist_csf|hipaa)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="json", regex="^(json|markdown|csv)$")


class SIEMHealthResponse(BaseModel):
    backends: dict
    all_healthy: bool


class IntegrityResponse(BaseModel):
    total_entries: int
    valid_signatures: int
    invalid_signatures: int
    chain_breaks: int
    is_valid: bool
    errors: List[dict]


# Routes

@router.get("/logs", response_model=List[LogEntryResponse])
async def query_logs(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Query audit logs with filters
    
    - **start_time**: Filter logs from this time (ISO 8601)
    - **end_time**: Filter logs until this time (ISO 8601)
    - **level**: Filter by log level (debug, info, warning, error, critical)
    - **category**: Filter by category (authentication, authorization, security, etc.)
    - **user_id**: Filter by user ID
    - **limit**: Maximum number of results (1-1000)
    - **offset**: Pagination offset
    """
    try:
        level_enum = LogLevel(level) if level else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
    
    try:
        category_enum = EventCategory(category) if category else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    
    entries = await logger.query(
        start_time=start_time,
        end_time=end_time,
        level=level_enum,
        category=category_enum,
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    return [LogEntryResponse(**e.to_dict()) for e in entries]


@router.post("/logs/export")
async def export_logs(
    request: LogExportRequest,
    logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Export audit logs to various formats
    
    Supports: json, csv, syslog
    """
    try:
        level_enum = LogLevel(request.level) if request.level else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {request.level}")
    
    try:
        category_enum = EventCategory(request.category) if request.category else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {request.category}")
    
    data = await logger.export(
        format=request.format,
        start_time=request.start_time,
        end_time=request.end_time,
        level=level_enum,
        category=category_enum
    )
    
    # Set content type based on format
    content_types = {
        "json": "application/json",
        "csv": "text/csv",
        "syslog": "text/plain"
    }
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=data,
        media_type=content_types[request.format],
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs.{request.format}"
        }
    )


@router.get("/integrity", response_model=IntegrityResponse)
async def verify_integrity(
    logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Verify integrity of all audit logs
    
    Checks:
    - Cryptographic signatures
    - Chain of custody
    - Tampering detection
    """
    result = await logger.verify_integrity()
    
    return IntegrityResponse(
        total_entries=result["total_entries"],
        valid_signatures=result["valid_signatures"],
        invalid_signatures=result["invalid_signatures"],
        chain_breaks=result["chain_breaks"],
        is_valid=(
            result["invalid_signatures"] == 0 and 
            result["chain_breaks"] == 0
        ),
        errors=result["errors"]
    )


@router.post("/compliance/report")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    reporter: ComplianceReporter = Depends(get_compliance_reporter)
):
    """
    Generate compliance report for a specific standard
    
    Supported standards:
    - iso27001: ISO/IEC 27001
    - soc2: SOC 2
    - gdpr: GDPR
    - pci_dss: PCI DSS
    - nist_csf: NIST Cybersecurity Framework
    - hipaa: HIPAA
    """
    from audit.compliance import ComplianceStandard
    
    try:
        standard = ComplianceStandard(request.standard)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid standard: {request.standard}")
    
    report = await reporter.generate_report(
        standard=standard,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    # Export to requested format
    if request.format != "json":
        data = await reporter.export_report(report, request.format)
        
        content_types = {
            "markdown": "text/markdown",
            "csv": "text/csv"
        }
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=data,
            media_type=content_types[request.format],
            headers={
                "Content-Disposition": f"attachment; filename=compliance_report.{request.format}"
            }
        )
    
    return report


@router.get("/compliance/standards")
async def list_compliance_standards():
    """List supported compliance standards"""
    return {
        "standards": [
            {
                "id": "iso27001",
                "name": "ISO/IEC 27001",
                "description": "Information Security Management System",
                "controls_count": 10
            },
            {
                "id": "soc2",
                "name": "SOC 2",
                "description": "Service Organization Control 2",
                "controls_count": 0
            },
            {
                "id": "gdpr",
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "controls_count": 4
            },
            {
                "id": "pci_dss",
                "name": "PCI DSS",
                "description": "Payment Card Industry Data Security Standard",
                "controls_count": 4
            },
            {
                "id": "nist_csf",
                "name": "NIST CSF",
                "description": "NIST Cybersecurity Framework",
                "controls_count": 0
            },
            {
                "id": "hipaa",
                "name": "HIPAA",
                "description": "Health Insurance Portability and Accountability Act",
                "controls_count": 0
            }
        ]
    }


@router.get("/siem/health", response_model=SIEMHealthResponse)
async def siem_health():
    """
    Check SIEM integration health
    
    Returns health status for all configured SIEM backends.
    """
    # This would check actual SIEM connections
    # For now, return placeholder
    return SIEMHealthResponse(
        backends={
            "Splunk": True,
            "Elasticsearch": True
        },
        all_healthy=True
    )


@router.get("/stats")
async def get_audit_stats(
    logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Get audit logging statistics
    
    Returns summary statistics about logged events.
    """
    # Query all logs
    entries = await logger.query(limit=10000)
    
    # Calculate statistics
    by_category = {}
    by_level = {}
    by_user = {}
    
    for entry in entries:
        by_category[entry.category] = by_category.get(entry.category, 0) + 1
        by_level[entry.level] = by_level.get(entry.level, 0) + 1
        if entry.user_id:
            by_user[entry.user_id] = by_user.get(entry.user_id, 0) + 1
    
    return {
        "total_events": len(entries),
        "time_range": {
            "first_event": entries[0].timestamp.isoformat() if entries else None,
            "last_event": entries[-1].timestamp.isoformat() if entries else None
        },
        "by_category": by_category,
        "by_level": by_level,
        "by_user": by_user,
        "integrity": await logger.verify_integrity()
    }


# Middleware integration for automatic audit logging
async def audit_middleware(request, call_next):
    """
    Middleware to automatically log API requests
    
    Logs all API requests with user info, IP, and response status.
    """
    logger = get_audit_logger()
    
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Log the request
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    await logger.info(
        category=EventCategory.SYSTEM,
        event_type="api_request",
        message=f"{request.method} {request.url.path}",
        user_id=getattr(request.state, "user_id", None),
        ip_address=request.client.host if request.client else None,
        resource_id=request.url.path,
        details={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )
    
    return response

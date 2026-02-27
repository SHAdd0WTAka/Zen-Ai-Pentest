"""
Reports API Routes

REST API endpoints for report generation and management.
"""

import os
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.models import SessionLocal
from reports import ReportGenerator
from reports.models import Report, ReportFormat, ReportStatus, ReportType

router = APIRouter(prefix="/reports", tags=["Reports"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Schemas
class ExecutiveReportRequest(BaseModel):
    """Request schema for executive report."""

    scan_id: str = Field(..., description="Scan UUID")
    company_name: str = Field(..., description="Client company name")
    pentest_start: Optional[str] = Field(
        None, description="Pentest start date (YYYY-MM-DD)"
    )
    pentest_end: Optional[str] = Field(
        None, description="Pentest end date (YYYY-MM-DD)"
    )
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")


class TechnicalReportRequest(BaseModel):
    """Request schema for technical report."""

    scan_id: str = Field(..., description="Scan UUID")
    include_evidence: bool = Field(
        True, description="Include evidence screenshots"
    )
    include_remediation: bool = Field(
        True, description="Include remediation steps"
    )
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")


class ComplianceReportRequest(BaseModel):
    """Request schema for compliance report."""

    scan_id: str = Field(..., description="Scan UUID")
    framework: str = Field(
        ..., description="Compliance framework (owasp, iso27001, pci_dss)"
    )
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")


class ReportResponse(BaseModel):
    """Response schema for report."""

    id: str
    scan_id: str
    report_type: str
    format: str
    status: str
    title: str
    company_name: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    generated_at: Optional[str]
    findings_summary: dict


@router.post(
    "/executive",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_executive_report(
    request: ExecutiveReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate an executive summary report.

    Creates a high-level report suitable for C-level executives and management.
    Includes risk summary, key findings, and strategic recommendations.
    """
    generator = ReportGenerator()

    # Determine output path
    output_path = (
        f"reports/outputs/exec_{request.scan_id}_{request.format.value}"
    )

    # Generate report in background
    background_tasks.add_task(
        generator.generate_executive_report,
        scan_id=request.scan_id,
        output_path=output_path,
        company_name=request.company_name,
        pentest_start=request.pentest_start,
        pentest_end=request.pentest_end,
        db=db,
    )

    return {
        "id": "pending",
        "scan_id": request.scan_id,
        "report_type": ReportType.EXECUTIVE.value,
        "format": request.format.value,
        "status": ReportStatus.GENERATING.value,
        "title": f"Executive Report - {request.company_name}",
        "company_name": request.company_name,
        "file_path": output_path,
        "file_size": None,
        "generated_at": None,
        "findings_summary": {},
    }


@router.post(
    "/technical",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_technical_report(
    request: TechnicalReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate a detailed technical report.

    Creates a comprehensive technical report for IT and security teams.
    Includes detailed findings, evidence, and step-by-step remediation.
    """
    generator = ReportGenerator()

    output_path = (
        f"reports/outputs/tech_{request.scan_id}_{request.format.value}"
    )

    background_tasks.add_task(
        generator.generate_technical_report,
        scan_id=request.scan_id,
        output_path=output_path,
        include_evidence=request.include_evidence,
        include_remediation=request.include_remediation,
        db=db,
    )

    return {
        "id": "pending",
        "scan_id": request.scan_id,
        "report_type": ReportType.TECHNICAL.value,
        "format": request.format.value,
        "status": ReportStatus.GENERATING.value,
        "title": "Technical Report",
        "company_name": None,
        "file_path": output_path,
        "file_size": None,
        "generated_at": None,
        "findings_summary": {},
    }


@router.post(
    "/compliance",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate a compliance assessment report.

    Maps findings to compliance frameworks (OWASP, ISO 27001, PCI DSS, etc.)
    and identifies compliance gaps.
    """
    generator = ReportGenerator()

    output_path = f"reports/outputs/compliance_{request.framework}_{request.scan_id}_{request.format.value}"

    background_tasks.add_task(
        generator.generate_compliance_report,
        scan_id=request.scan_id,
        output_path=output_path,
        framework=request.framework,
        db=db,
    )

    return {
        "id": "pending",
        "scan_id": request.scan_id,
        "report_type": ReportType.COMPLIANCE.value,
        "format": request.format.value,
        "status": ReportStatus.GENERATING.value,
        "title": f"Compliance Report - {request.framework}",
        "company_name": None,
        "file_path": output_path,
        "file_size": None,
        "generated_at": None,
        "findings_summary": {},
    }


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    scan_id: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all generated reports.

    Supports filtering by scan_id, report_type, and status.
    """
    query = db.query(Report)

    if scan_id:
        query = query.filter(Report.scan_id == scan_id)
    if report_type:
        query = query.filter(Report.report_type == report_type)
    if status:
        query = query.filter(Report.status == status)

    total = query.count()

    offset = (page - 1) * page_size
    reports = query.offset(offset).limit(page_size).all()

    return [
        {
            "id": r.id,
            "scan_id": r.scan_id,
            "report_type": r.report_type.value if r.report_type else None,
            "format": r.report_format.value if r.report_format else None,
            "status": r.status.value if r.status else None,
            "title": r.title,
            "company_name": r.company_name,
            "file_path": r.file_path,
            "file_size": r.file_size,
            "generated_at": (
                r.generated_at.isoformat() if r.generated_at else None
            ),
            "findings_summary": {
                "total": r.total_findings,
                "critical": r.critical_count,
                "high": r.high_count,
                "medium": r.medium_count,
                "low": r.low_count,
                "info": r.info_count,
            },
        }
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    return {
        "id": report.id,
        "scan_id": report.scan_id,
        "report_type": (
            report.report_type.value if report.report_type else None
        ),
        "format": report.report_format.value if report.report_format else None,
        "status": report.status.value if report.status else None,
        "title": report.title,
        "company_name": report.company_name,
        "file_path": report.file_path,
        "file_size": report.file_size,
        "generated_at": (
            report.generated_at.isoformat() if report.generated_at else None
        ),
        "findings_summary": {
            "total": report.total_findings,
            "critical": report.critical_count,
            "high": report.high_count,
            "medium": report.medium_count,
            "low": report.low_count,
            "info": report.info_count,
        },
    }


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    """
    Download a generated report file.

    Returns the actual PDF/HTML/DOCX file.
    """
    from fastapi.responses import FileResponse

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )

    filename = f"{report.title.replace(' ', '_')}_{report.id}.{report.report_format.value}"

    return FileResponse(
        report.file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    """Delete a report."""
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # Delete file if exists
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)

    db.delete(report)
    db.commit()

    return None


@router.get("/stats/summary")
def get_report_statistics(
    db: Session = Depends(get_db),
):
    """Get report generation statistics."""
    from sqlalchemy import func

    total_reports = db.query(Report).count()

    # By type
    type_counts = (
        db.query(Report.report_type, func.count(Report.id))
        .group_by(Report.report_type)
        .all()
    )

    # By format
    format_counts = (
        db.query(Report.report_format, func.count(Report.id))
        .group_by(Report.report_format)
        .all()
    )

    # Recent reports
    recent = (
        db.query(Report).order_by(Report.generated_at.desc()).limit(5).all()
    )

    return {
        "total_reports": total_reports,
        "by_type": {t.value: c for t, c in type_counts},
        "by_format": {f.value: c for f, c in format_counts},
        "recent": [
            {
                "id": r.id,
                "title": r.title,
                "type": r.report_type.value if r.report_type else None,
                "generated": (
                    r.generated_at.isoformat() if r.generated_at else None
                ),
            }
            for r in recent
        ],
    }


@router.get("/templates/list")
def list_report_templates():
    """List available report templates."""
    return {
        "templates": [
            {
                "id": "executive",
                "name": "Executive Summary",
                "description": "High-level report for C-level executives",
                "formats": ["pdf", "html", "docx"],
            },
            {
                "id": "technical",
                "name": "Technical Report",
                "description": "Detailed technical findings for IT teams",
                "formats": ["pdf", "html", "docx", "json"],
            },
            {
                "id": "compliance",
                "name": "Compliance Assessment",
                "description": "Compliance-focused report with framework mappings",
                "formats": ["pdf", "html", "json"],
            },
        ]
    }

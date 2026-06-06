"""
Reports API Routes

REST API endpoints for report generation and management.
"""

import io
import os
from typing import List, Optional

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
    pentest_start: Optional[str] = Field(None, description="Pentest start date (YYYY-MM-DD)")
    pentest_end: Optional[str] = Field(None, description="Pentest end date (YYYY-MM-DD)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")


class TechnicalReportRequest(BaseModel):
    """Request schema for technical report."""

    scan_id: str = Field(..., description="Scan UUID")
    include_evidence: bool = Field(True, description="Include evidence screenshots")
    include_remediation: bool = Field(True, description="Include remediation steps")
    format: ReportFormat = Field(ReportFormat.PDF, description="Output format")


class ComplianceReportRequest(BaseModel):
    """Request schema for compliance report."""

    scan_id: str = Field(..., description="Scan UUID")
    framework: str = Field(..., description="Compliance framework (owasp, iso27001, pci_dss)")
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
    output_path = f"reports/outputs/exec_{request.scan_id}_{request.format.value}"

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

    output_path = f"reports/outputs/tech_{request.scan_id}_{request.format.value}"

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


@router.get("/", response_model=List[ReportResponse])
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

    query.count()

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
            "generated_at": (r.generated_at.isoformat() if r.generated_at else None),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return {
        "id": report.id,
        "scan_id": report.scan_id,
        "report_type": (report.report_type.value if report.report_type else None),
        "format": report.report_format.value if report.report_format else None,
        "status": report.status.value if report.status else None,
        "title": report.title,
        "company_name": report.company_name,
        "file_path": report.file_path,
        "file_size": report.file_size,
        "generated_at": (report.generated_at.isoformat() if report.generated_at else None),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

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
    type_counts = db.query(Report.report_type, func.count(Report.id)).group_by(Report.report_type).all()

    # By format
    format_counts = db.query(Report.report_format, func.count(Report.id)).group_by(Report.report_format).all()

    # Recent reports
    recent = db.query(Report).order_by(Report.generated_at.desc()).limit(5).all()

    return {
        "total_reports": total_reports,
        "by_type": {t.value: c for t, c in type_counts},
        "by_format": {f.value: c for f, c in format_counts},
        "recent": [
            {
                "id": r.id,
                "title": r.title,
                "type": r.report_type.value if r.report_type else None,
                "generated": (r.generated_at.isoformat() if r.generated_at else None),
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


# =============================================================================
# REPORT EXPORT ENDPOINTS
# =============================================================================

from fastapi import Query as FastAPIQuery
from fastapi.responses import JSONResponse, StreamingResponse

from modules.report_generator import ReportExportGenerator


@router.get("/{scan_id}/export")
async def export_report(
    scan_id: str,
    format: str = FastAPIQuery(..., description="Export format: json, pdf, html, xml", pattern="^(json|pdf|html|xml)$"),
    db: Session = Depends(get_db),
):
    """
    Exportiert einen Scan-Report in verschiedenen Formaten.

    **Formate:**
    - `json` - Vollständige Scan-Ergebnisse als JSON
    - `pdf` - Professioneller PDF Report mit Deckblatt
    - `html` - Interaktiver HTML Report
    - `xml` - XML für Tool-Integrationen

    **Beispiele:**
    - `/reports/123/export?format=json`
    - `/reports/123/export?format=pdf`
    - `/reports/123/export?format=html`
    - `/reports/123/export?format=xml`
    """
    # Import database models
    try:
        from database.models import Scan
    except ImportError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database models not available")

    # Get scan from database
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan {scan_id} not found")

    # Get findings for this scan
    try:
        from database.models import Finding

        findings_db = db.query(Finding).filter(Finding.scan_id == scan_id).all()
        findings = [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "cvss_score": f.cvss_score,
                "cve_id": f.cve_id,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "target": f.target,
                "tool": f.tool,
                "port": f.port,
                "service": f.service,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in findings_db
        ]
    except Exception:
        # Fallback: empty findings list
        findings = []

    # Prepare scan data
    scan_data = {
        "id": scan.id,
        "name": scan.name,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }

    # Initialize generator
    generator = ReportExportGenerator()

    format = format.lower()

    try:
        if format == "json":
            # Generate JSON report
            report_data = generator.export_json(scan_id, scan_data, findings)

            return JSONResponse(
                content=report_data, headers={"Content-Disposition": f'attachment; filename="report_scan_{scan_id}.json"'}
            )

        elif format == "xml":
            # Generate XML report
            xml_content = generator.export_xml(scan_id, scan_data, findings)

            return StreamingResponse(
                io.StringIO(xml_content),
                media_type="application/xml",
                headers={"Content-Disposition": f'attachment; filename="report_scan_{scan_id}.xml"'},
            )

        elif format == "html":
            # Generate HTML report
            html_content = generator.export_html(scan_id, scan_data, findings, interactive=True)

            return StreamingResponse(
                io.StringIO(html_content),
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="report_scan_{scan_id}.html"'},
            )

        elif format == "pdf":
            # Generate PDF report
            pdf_bytes = generator.export_pdf(scan_id, scan_data, findings)

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="report_scan_{scan_id}.pdf"',
                    "Content-Type": "application/pdf",
                },
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {format}. Use json, pdf, html, or xml."
            )

    except ImportError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Missing dependency: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation failed: {str(e)}")


@router.get("/{scan_id}/export/preview")
async def preview_report(
    scan_id: str,
    format: str = FastAPIQuery(default="html", description="Preview format: html", pattern="^(html|json)$"),
    db: Session = Depends(get_db),
):
    """
    Zeigt eine Vorschau des Reports im Browser (ohne Download).

    **Verwendung:**
    - Öffnen im Browser für HTML Vorschau
    - JSON wird inline angezeigt
    """
    import io

    # Import database models
    try:
        from database.models import Scan
    except ImportError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database models not available")

    # Get scan from database
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan {scan_id} not found")

    # Get findings
    try:
        from database.models import Finding

        findings_db = db.query(Finding).filter(Finding.scan_id == scan_id).all()
        findings = [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "cvss_score": f.cvss_score,
                "cve_id": f.cve_id,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "target": f.target,
                "tool": f.tool,
            }
            for f in findings_db
        ]
    except Exception:
        findings = []

    scan_data = {
        "id": scan.id,
        "name": scan.name,
        "target": scan.target,
        "scan_type": scan.scan_type,
        "status": scan.status,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
    }

    generator = ReportExportGenerator()
    format = format.lower()

    try:
        if format == "html":
            html_content = generator.export_html(scan_id, scan_data, findings, interactive=True)
            return StreamingResponse(io.StringIO(html_content), media_type="text/html")
        elif format == "json":
            report_data = generator.export_json(scan_id, scan_data, findings)
            return JSONResponse(content=report_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Preview generation failed: {str(e)}")


@router.get("/formats/list")
def list_export_formats():
    """
    Listet alle verfügbaren Export-Formate auf.

    Returns:
        Liste der unterstützten Formate mit Beschreibungen
    """
    return {
        "formats": [
            {
                "id": "json",
                "name": "JSON",
                "description": "Vollständige Scan-Ergebnisse als strukturiertes JSON",
                "content_type": "application/json",
                "file_extension": ".json",
                "use_case": "Programmatische Verarbeitung, Integration mit anderen Tools",
            },
            {
                "id": "pdf",
                "name": "PDF Report",
                "description": "Professioneller PDF Report mit Deckblatt und Executive Summary",
                "content_type": "application/pdf",
                "file_extension": ".pdf",
                "use_case": "Kundenreports, Dokumentation, C-Level Präsentationen",
                "features": ["Deckblatt", "Executive Summary", "Detaillierte Findings", "CVSS/EPSS Scores"],
            },
            {
                "id": "html",
                "name": "HTML Report",
                "description": "Interaktiver HTML Report für Browser",
                "content_type": "text/html",
                "file_extension": ".html",
                "use_case": "Interaktive Analyse, Browser-basierte Ansicht",
                "features": ["Filter nach Severity", "Responsive Design", "Druck-optimiert"],
            },
            {
                "id": "xml",
                "name": "XML",
                "description": "XML Format für Tool-Integrationen",
                "content_type": "application/xml",
                "file_extension": ".xml",
                "use_case": "SIEM Integration, automatisierte Verarbeitung",
            },
        ],
        "endpoints": {
            "export": "/reports/{scan_id}/export?format={format}",
            "preview": "/reports/{scan_id}/export/preview?format={format}",
        },
    }

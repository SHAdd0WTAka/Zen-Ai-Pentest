"""
Report Generation Endpoints

Generate professional penetration testing reports in various formats.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.core.auth import get_current_user
from api.models.report import Report, ReportFormat, ReportStatus
from api.models.scan import Scan
from api.models.user import User

router = APIRouter()


class ReportCreate(BaseModel):
    """Report generation request"""

    scan_id: str
    name: Optional[str] = None
    format: ReportFormat = Field(default=ReportFormat.PDF)
    template: str = Field(default="executive", description="executive, technical, or full")
    include_evidence: bool = Field(default=True)
    include_remediation: bool = Field(default=True)


class ReportResponse(BaseModel):
    """Report response model"""

    id: str
    name: str
    scan_id: str
    format: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    file_path: Optional[str]
    file_size: Optional[int]
    download_url: Optional[str]


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new penetration testing report.

    Report generation happens asynchronously. Check status using the report ID.
    """
    # Verify scan exists
    scan = await Scan.find_one(id=report_data.scan_id, created_by=current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Create report record
    report = Report(
        name=report_data.name or f"Report-{scan.name}-{datetime.now().strftime('%Y%m%d')}",
        scan_id=report_data.scan_id,
        format=report_data.format,
        template=report_data.template,
        include_evidence=report_data.include_evidence,
        include_remediation=report_data.include_remediation,
        created_by=current_user.id,
        status=ReportStatus.PENDING,
    )

    await report.save()

    # Generate report in background
    background_tasks.add_task(generate_report_task, report.id)

    return report.to_response()


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    scan_id: Optional[str] = None,
    format: Optional[ReportFormat] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List all generated reports"""
    filters = {"created_by": current_user.id}

    if scan_id:
        filters["scan_id"] = scan_id
    if format:
        filters["format"] = format

    reports = await Report.find_many(**filters).limit(limit).skip(offset).to_list()
    return [r.to_response() for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, current_user: User = Depends(get_current_user)):
    """Get report details"""
    report = await Report.find_one(id=report_id, created_by=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report.to_response()


@router.get("/{report_id}/download")
async def download_report(report_id: str, current_user: User = Depends(get_current_user)):
    """
    Download generated report file.

    Returns the report file in the requested format (PDF, HTML, etc.)
    """
    report = await Report.find_one(id=report_id, created_by=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report not ready yet")

    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "csv": "text/csv",
        "md": "text/markdown",
    }

    ext = report.format.value.lower()
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(path=report.file_path, media_type=media_type, filename=f"{report.name}.{ext}")


@router.delete("/{report_id}")
async def delete_report(report_id: str, current_user: User = Depends(get_current_user)):
    """Delete a report"""
    report = await Report.find_one(id=report_id, created_by=current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await report.delete()
    return {"message": "Report deleted"}


async def generate_report_task(report_id: str):
    """Background task to generate report"""
    from modules.report_gen import ReportGenerator

    report = await Report.find_one(id=report_id)
    if not report:
        return

    try:
        await report.update_status(ReportStatus.GENERATING)

        # Get scan data
        scan = await Scan.find_one(id=report.scan_id)
        if not scan:
            raise Exception("Scan not found")

        # Get findings
        from api.models.finding import Finding

        findings = await Finding.find_many(scan_id=report.scan_id).to_list()

        # Generate report
        generator = ReportGenerator()

        output_path = await generator.generate(
            scan=scan,
            findings=findings,
            template=report.template,
            format=report.format,
            include_evidence=report.include_evidence,
            include_remediation=report.include_remediation,
        )

        report.file_path = output_path
        report.file_size = 0  # TODO: Get actual file size
        await report.update_status(ReportStatus.COMPLETED)

    except Exception as e:
        await report.update_status(ReportStatus.FAILED, error=str(e))

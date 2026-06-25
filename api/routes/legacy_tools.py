"""
Legacy tool and report routes extracted from api/main.py.

Deprecated: Use /api/v1/tools/* and /api/v1/reports/* endpoints instead.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from api.auth_deps import optional_auth, verify_token
from api.background import execute_tool_task, generate_report_task
from api.schemas import ReportCreate, ReportResponse, ToolExecuteRequest, ToolExecuteResponse
from database.crud import create_report, get_reports
from database.models import Report, get_db

router = APIRouter(tags=["Legacy Tools"])


@router.post("/tools/execute", response_model=ToolExecuteResponse, deprecated=True)
async def execute_tool(
    request: ToolExecuteRequest,
    background_tasks: BackgroundTasks,
    user: Any = Depends(verify_token),
    db=Depends(get_db),
):
    """
    DEPRECATED: Use POST /api/v1/tools/execute instead

    Execute a pentesting tool
    """
    from database.crud import create_scan

    # Create scan entry
    db_scan = create_scan(
        db,
        name=f"Tool: {request.tool_name}",
        target=request.target,
        scan_type="tool_execution",
        config=request.parameters,
        user_id=user.get("sub"),
    )

    # Execute in background
    background_tasks.add_task(
        execute_tool_task,
        db_scan.id,
        request.tool_name,
        request.target,
        request.parameters,
    )

    return ToolExecuteResponse(
        scan_id=db_scan.id,
        status="started",
        message=f"Tool {request.tool_name} execution started",
    )


@router.get("/tools", deprecated=True)
async def list_tools(user: Optional[dict] = Depends(optional_auth)):
    """
    DEPRECATED: Use GET /api/v1/tools instead

    List available tools
    """
    from tools import TOOL_REGISTRY

    tools = []
    for name, func in TOOL_REGISTRY.items():
        if func:
            tools.append(
                {
                    "name": name,
                    "description": func.__doc__ or "No description",
                    "category": get_tool_category(name),
                }
            )

    return {"tools": tools}


def get_tool_category(tool_name: str) -> str:
    """Get tool category based on name"""
    categories = {
        "nmap": "network",
        "masscan": "network",
        "scapy": "network",
        "tshark": "network",
        "burp": "web",
        "sqlmap": "web",
        "gobuster": "web",
        "metasploit": "exploitation",
        "hydra": "brute_force",
        "amass": "recon",
        "bloodhound": "ad",
        "cme": "ad",
        "responder": "ad",
        "aircrack": "wireless",
    }

    for key, cat in categories.items():
        if key in tool_name.lower():
            return cat
    return "other"


@router.post("/reports", response_model=ReportResponse, deprecated=True)
async def generate_report(
    report: ReportCreate,
    background_tasks: BackgroundTasks,
    user: Any = Depends(verify_token),
    db=Depends(get_db),
):
    """
    DEPRECATED: Use POST /api/v1/reports instead

    Generate a report from scan findings
    """
    db_report = create_report(
        db,
        scan_id=report.scan_id,
        format=report.format,
        template=report.template,
        user_id=user.get("sub"),
    )

    # Generate in background
    background_tasks.add_task(generate_report_task, db_report.id, report.scan_id, report.format)

    return db_report


@router.get("/reports", response_model=List[ReportResponse], deprecated=True)
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    user: Any = Depends(verify_token),
    db=Depends(get_db),
):
    """
    DEPRECATED: Use GET /api/v1/reports instead

    List all reports
    """
    reports = get_reports(db, skip, limit)
    return reports


@router.get("/reports/{report_id}/download", deprecated=True)
async def download_report(report_id: int, user: Any = Depends(verify_token), db=Depends(get_db)):
    """
    DEPRECATED: Use GET /api/v1/reports/{report_id}/download instead

    Download a generated report
    """
    from fastapi.responses import FileResponse

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report.file_path, filename=f"report_{report_id}.{report.format}")

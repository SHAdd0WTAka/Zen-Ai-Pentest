"""
Scan Management Endpoints

Create, manage, and monitor penetration testing scans.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.core.auth import get_current_user
from api.models.scan import Scan, ScanStatus, ScanType
from api.models.user import User

router = APIRouter()


class ScanCreate(BaseModel):
    """Scan creation request"""

    target: str = Field(..., description="Target URL or IP address")
    scan_type: ScanType = Field(default=ScanType.FULL)
    name: Optional[str] = Field(None, description="Optional scan name")
    description: Optional[str] = None
    options: dict = Field(default_factory=dict)


class ScanResponse(BaseModel):
    """Scan response model"""

    id: str
    name: str
    target: str
    scan_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: int = Field(0, ge=0, le=100)
    findings_count: int
    error_message: Optional[str]


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Create and start a new security scan.

    The scan runs asynchronously in the background.
    Use the scan ID to check progress and retrieve results.
    """
    scan = Scan(
        name=scan_data.name or f"Scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        target=scan_data.target,
        scan_type=scan_data.scan_type,
        description=scan_data.description,
        created_by=current_user.id,
        options=scan_data.options,
    )

    await scan.save()

    # Start scan in background
    background_tasks.add_task(run_scan, scan.id)

    return scan.to_response()


@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    status: Optional[ScanStatus] = None,
    scan_type: Optional[ScanType] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List all scans with optional filtering"""
    filters = {"created_by": current_user.id}
    if status:
        filters["status"] = status
    if scan_type:
        filters["scan_type"] = scan_type

    scans = await Scan.find_many(**filters).limit(limit).skip(offset).to_list()
    return [s.to_response() for s in scans]


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, current_user: User = Depends(get_current_user)):
    """Get scan details by ID"""
    scan = await Scan.find_one(id=scan_id, created_by=current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan.to_response()


@router.post("/{scan_id}/stop")
async def stop_scan(scan_id: str, current_user: User = Depends(get_current_user)):
    """Stop a running scan"""
    scan = await Scan.find_one(id=scan_id, created_by=current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status not in [ScanStatus.PENDING, ScanStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Scan cannot be stopped")

    await scan.stop()
    return {"message": "Scan stopped", "scan": scan.to_response()}


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, current_user: User = Depends(get_current_user)):
    """Delete a scan and all associated data"""
    scan = await Scan.find_one(id=scan_id, created_by=current_user.id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    await scan.delete()
    return {"message": "Scan deleted"}


async def run_scan(scan_id: str):
    """Background task to execute scan"""
    scan = await Scan.find_one(id=scan_id)
    if not scan:
        return

    try:
        await scan.update_status(ScanStatus.RUNNING)

        # Import and run appropriate scanner
        from modules.vuln_scanner import VulnScannerModule

        scanner = VulnScannerModule()

        async for progress in scanner.scan(scan.target, scan.options):
            await scan.update_progress(progress)

        await scan.update_status(ScanStatus.COMPLETED)

    except Exception as e:
        await scan.update_status(ScanStatus.FAILED, error=str(e))

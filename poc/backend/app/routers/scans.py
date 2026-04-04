"""
Scan Management Router for Zen-AI-Pentest
Handles scan CRUD operations, execution, and monitoring
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.scan import Scan, ScanStatus, ScanTemplate, ScanType
from app.models.user import User
from app.routers.auth import get_current_active_user, require_admin
from app.schemas.scans import (
    ScanCreate,
    ScanDetailResponse,
    ScanListResponse,
    ScanResponse,
    ScanTemplateCreate,
    ScanTemplateResponse,
    ScanUpdate,
)
from app.services.scan_service import ScanService

router = APIRouter()


@router.get("", response_model=ScanListResponse)
async def list_scans(
    status: Optional[ScanStatus] = None,
    type: Optional[ScanType] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all scans with filtering and pagination."""
    query = select(Scan)

    # Apply filters
    if status:
        query = query.where(Scan.status == status)
    if type:
        query = query.where(Scan.type == type)
    if search:
        query = query.where(Scan.name.ilike(f"%{search}%") | Scan.target.ilike(f"%{search}%"))

    # Apply sorting
    if sort_order == "desc":
        query = query.order_by(desc(getattr(Scan, sort_by)))
    else:
        query = query.order_by(getattr(Scan, sort_by))

    # Get total count
    count_result = await db.execute(select(Scan))
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    scans = result.scalars().all()

    return ScanListResponse(
        success=True,
        data=[scan.to_dict() for scan in scans],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit,
            "hasNext": page * limit < total,
            "hasPrev": page > 1,
        },
    )


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new scan."""
    # Validate template if provided
    if scan_data.template_id:
        result = await db.execute(select(ScanTemplate).where(ScanTemplate.id == scan_data.template_id))
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan template not found",
            )

    # Create scan
    new_scan = Scan(
        name=scan_data.name,
        description=scan_data.description,
        target=scan_data.target,
        type=scan_data.type,
        status=ScanStatus.PENDING,
        progress=0,
        config=scan_data.config.dict() if scan_data.config else {},
        created_by=current_user.id,
        template_id=scan_data.template_id,
    )

    db.add(new_scan)
    await db.commit()
    await db.refresh(new_scan)

    # Start scan in background if auto_start is enabled
    if scan_data.auto_start:
        background_tasks.add_task(ScanService.execute_scan, str(new_scan.id), new_scan.config)
        new_scan.status = ScanStatus.QUEUED
        await db.commit()

    return ScanResponse(success=True, data=new_scan.to_dict())


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed information about a specific scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # Get vulnerabilities for this scan
    vulnerabilities = []
    if scan.vulnerabilities:
        vulnerabilities = [v.to_dict() for v in scan.vulnerabilities]

    scan_data = scan.to_dict()
    scan_data["vulnerabilities"] = vulnerabilities

    return ScanDetailResponse(success=True, data=scan_data)


@router.patch("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: str,
    scan_data: ScanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a scan (only if not running)."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # Cannot update running scans
    if scan.status == ScanStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a running scan",
        )

    # Update fields
    if scan_data.name is not None:
        scan.name = scan_data.name
    if scan_data.description is not None:
        scan.description = scan_data.description
    if scan_data.config is not None:
        scan.config = scan_data.config.dict()

    scan.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(scan)

    return ScanResponse(success=True, data=scan.to_dict())


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a scan and all associated data."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # Cannot delete running scans
    if scan.status == ScanStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running scan",
        )

    await db.delete(scan)
    await db.commit()

    return None


@router.post("/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Start a pending scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    if scan.status not in [
        ScanStatus.PENDING,
        ScanStatus.FAILED,
        ScanStatus.CANCELLED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start scan with status: {scan.status}",
        )

    # Update status
    scan.status = ScanStatus.QUEUED
    scan.started_at = None
    scan.completed_at = None
    scan.error_message = None
    await db.commit()

    # Start scan in background
    background_tasks.add_task(ScanService.execute_scan, str(scan.id), scan.config)

    return ScanResponse(success=True, data=scan.to_dict())


@router.post("/{scan_id}/stop", response_model=ScanResponse)
async def stop_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stop a running scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    if scan.status != ScanStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan is not running",
        )

    # Update status
    scan.status = ScanStatus.CANCELLED
    scan.completed_at = datetime.now(timezone.utc)
    await db.commit()

    # TODO: Implement actual scan stopping logic with Celery

    return ScanResponse(success=True, data=scan.to_dict())


@router.get("/{scan_id}/progress")
async def get_scan_progress(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get real-time scan progress."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    return {
        "success": True,
        "data": {
            "scanId": str(scan.id),
            "status": scan.status.value,
            "progress": scan.progress,
            "findingsCount": scan.findings_count,
            "criticalCount": scan.critical_count,
            "highCount": scan.high_count,
            "mediumCount": scan.medium_count,
            "lowCount": scan.low_count,
            "infoCount": scan.info_count,
        },
    }


# Scan Templates
@router.get("/templates", response_model=List[ScanTemplateResponse])
async def list_scan_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all scan templates."""
    result = await db.execute(select(ScanTemplate))
    templates = result.scalars().all()

    return [ScanTemplateResponse(**template.to_dict()) for template in templates]


@router.post(
    "/templates",
    response_model=ScanTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scan_template(
    template_data: ScanTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new scan template (admin only)."""
    new_template = ScanTemplate(
        name=template_data.name,
        description=template_data.description,
        type=template_data.type,
        config=template_data.config.dict(),
        is_default=template_data.is_default,
        created_by=current_user.id,
    )

    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return ScanTemplateResponse(**new_template.to_dict())

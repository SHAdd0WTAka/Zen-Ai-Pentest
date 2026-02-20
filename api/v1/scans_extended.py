"""
Extended Scan Management API - Issue #24

Enhanced scan management endpoints with streaming logs support.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth import verify_token
from api.schemas import ScanResponse
from api.websocket import ConnectionManager
from database.crud import create_scan, get_scan, update_scan_status
from database.models import Finding, get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["scans-extended"])

# Scan-specific WebSocket manager
scan_ws_manager = ConnectionManager()

# In-memory scan logs storage (in production, use Redis or database)
scan_logs: Dict[int, List[Dict[str, Any]]] = {}


# ============================================================================
# Pydantic Models
# ============================================================================


class CreateScanRequest(BaseModel):
    """Extended scan creation request"""

    name: str = Field(..., min_length=1, max_length=255, description="Scan name")
    target: str = Field(..., min_length=1, max_length=500, description="Target URL or IP")
    scan_type: str = Field(default="comprehensive", description="Scan type: quick, standard, comprehensive")
    config: Dict[str, Any] = Field(default_factory=dict, description="Scan configuration")
    objective: Optional[str] = Field(default=None, description="Scan objective")
    priority: int = Field(default=2, ge=1, le=4, description="Priority: 1=low, 2=normal, 3=high, 4=critical")
    scheduled_for: Optional[str] = Field(default=None, description="ISO datetime for scheduled scan")


class ScanStatusResponse(BaseModel):
    """Detailed scan status response"""

    id: int
    name: str
    target: str
    scan_type: str
    status: str
    progress: int = Field(0, ge=0, le=100)
    current_phase: Optional[str]
    phase_description: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    findings_count: int
    error_message: Optional[str]
    config: Dict[str, Any]


class ScanLogEntry(BaseModel):
    """Scan log entry"""

    timestamp: str
    level: str  # DEBUG, INFO, WARNING, ERROR
    phase: str
    message: str
    details: Optional[Dict[str, Any]]


class ScanListFilters(BaseModel):
    """Scan list filter parameters"""

    status: Optional[str] = None
    scan_type: Optional[str] = None
    target: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ScanActionRequest(BaseModel):
    """Scan action request (pause, resume, stop)"""

    action: str = Field(..., description="Action: pause, resume, stop, restart")
    reason: Optional[str] = Field(default=None, description="Reason for action")


# ============================================================================
# Helper Functions
# ============================================================================


def get_scan_logs(scan_id: int) -> List[Dict]:
    """Get logs for a specific scan"""
    return scan_logs.get(scan_id, [])


def add_scan_log(scan_id: int, level: str, phase: str, message: str, details: Dict = None):
    """Add a log entry for a scan"""
    if scan_id not in scan_logs:
        scan_logs[scan_id] = []

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "phase": phase,
        "message": message,
        "details": details or {},
    }
    scan_logs[scan_id].append(entry)

    # Keep only last 10000 logs per scan
    if len(scan_logs[scan_id]) > 10000:
        scan_logs[scan_id] = scan_logs[scan_id][-10000:]

    return entry


async def broadcast_scan_update(scan_id: int, update_type: str, data: Dict):
    """Broadcast update to scan WebSocket clients"""
    await scan_ws_manager.broadcast_to_scan(
        scan_id, {"type": update_type, "scan_id": scan_id, "timestamp": datetime.utcnow().isoformat(), **data}
    )


def calculate_progress(phase: str, step: int, total_steps: int) -> int:
    """Calculate scan progress percentage based on phase"""
    phase_progress = {
        "initializing": (0, 5),
        "reconnaissance": (5, 20),
        "port_scanning": (20, 40),
        "vulnerability_scanning": (40, 70),
        "exploit_testing": (70, 85),
        "analysis": (85, 95),
        "reporting": (95, 100),
    }

    if phase in phase_progress:
        start, end = phase_progress[phase]
        if total_steps > 0:
            phase_completion = (step / total_steps) * (end - start)
            return min(int(start + phase_completion), 99)

    return 0


# ============================================================================
# REST Endpoints
# ============================================================================


@router.get("/", response_model=List[ScanStatusResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    List all scans with optional filtering.
    """
    from database.crud import get_scans

    scans = get_scans(db, skip=skip, limit=limit, status=status)

    result = []
    for scan in scans:
        duration = None
        if scan.started_at:
            end_time = scan.completed_at or datetime.utcnow()
            duration = int((end_time - scan.started_at).total_seconds())

        findings_count = db.query(Finding).filter(Finding.scan_id == scan.id).count()

        progress = 0
        if scan.status == "running" and scan.started_at:
            elapsed = (datetime.utcnow() - scan.started_at).total_seconds()
            progress = min(int((elapsed / 600) * 100), 99)
        elif scan.status == "completed":
            progress = 100

        result.append(
            ScanStatusResponse(
                id=scan.id,
                name=scan.name,
                target=scan.target,
                scan_type=scan.scan_type,
                status=scan.status,
                progress=progress,
                current_phase=scan.config.get("phase") if scan.config else None,
                phase_description=None,
                started_at=scan.started_at.isoformat() if scan.started_at else None,
                completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
                duration_seconds=duration,
                findings_count=findings_count,
                error_message=None,
                config=scan.config or {},
            )
        )

    return result


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_new_scan(
    request: CreateScanRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Create and start a new security scan.

    The scan is created in 'pending' status and automatically started
    in the background unless scheduled for later.
    """
    try:
        # Create scan in database
        db_scan = create_scan(
            db,
            name=request.name,
            target=request.target,
            scan_type=request.scan_type,
            config={
                **request.config,
                "priority": request.priority,
                "objective": request.objective or f"Security scan of {request.target}",
                "scheduled_for": request.scheduled_for,
            },
            user_id=1,  # TODO: Map username to user_id properly
        )

        # Initialize logs
        scan_logs[db_scan.id] = []
        add_scan_log(
            db_scan.id,
            "INFO",
            "initializing",
            f"Scan '{request.name}' created",
            {"target": request.target, "scan_type": request.scan_type, "user": user.get("sub")},
        )

        # Start scan in background (unless scheduled)
        if not request.scheduled_for:
            background_tasks.add_task(run_scan_task, db_scan.id, request.dict())
            add_scan_log(db_scan.id, "INFO", "initializing", "Scan queued for execution")
        else:
            add_scan_log(db_scan.id, "INFO", "initializing", f"Scan scheduled for {request.scheduled_for}")

        # Broadcast creation event
        await broadcast_scan_update(
            db_scan.id, "created", {"name": request.name, "target": request.target, "status": "pending"}
        )

        return db_scan

    except Exception as e:
        logger.error(f"Error creating scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create scan: {str(e)}")


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status_detail(scan_id: int, user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Get detailed status of a specific scan.

    Includes current phase, progress percentage, duration, and findings count.
    """
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Calculate duration
    duration = None
    if scan.started_at:
        end_time = scan.completed_at or datetime.utcnow()
        duration = int((end_time - scan.started_at).total_seconds())

    # Get findings count
    findings_count = db.query(Finding).filter(Finding.scan_id == scan_id).count()

    # Determine current phase from logs
    current_phase = "initializing"
    phase_description = "Preparing scan environment"
    progress = 0

    logs = get_scan_logs(scan_id)
    if logs:
        # Get most recent phase
        for log in reversed(logs):
            if log.get("phase"):
                current_phase = log["phase"]
                phase_description = log["message"]
                break

        # Calculate progress based on phase
        progress = calculate_progress(current_phase, len(logs), 100)

    if scan.status == "completed":
        progress = 100
    elif scan.status == "failed":
        progress = 0

    return ScanStatusResponse(
        id=scan.id,
        name=scan.name,
        target=scan.target,
        scan_type=scan.scan_type,
        status=scan.status,
        progress=progress,
        current_phase=current_phase,
        phase_description=phase_description,
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        duration_seconds=duration,
        findings_count=findings_count,
        error_message=scan.result_summary if scan.status == "failed" else None,
        config=scan.config or {},
    )


@router.get("/{scan_id}/logs")
async def get_scan_logs_endpoint(
    scan_id: int,
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
    since: Optional[str] = None,
    user: dict = Depends(verify_token),
):
    """
    Get scan execution logs.

    - **limit**: Number of log entries (default: 100, max: 1000)
    - **offset**: Offset for pagination
    - **level**: Filter by log level (DEBUG, INFO, WARNING, ERROR)
    - **since**: Get logs after this ISO timestamp

    Returns logs in reverse chronological order (newest first).
    """
    logs = get_scan_logs(scan_id)

    # Filter by level
    if level:
        logs = [log for log in logs if log.get("level") == level.upper()]

    # Filter by timestamp
    if since:
        logs = [log for log in logs if log.get("timestamp", "") > since]

    # Sort by timestamp descending
    logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)

    # Paginate
    total = len(logs)
    limit = min(limit, 1000)
    paginated = logs[offset : offset + limit]

    return {"scan_id": scan_id, "total": total, "offset": offset, "limit": limit, "logs": paginated}


@router.get("/{scan_id}/logs/stream")
async def stream_scan_logs(scan_id: int, request: Request, user: dict = Depends(verify_token)):
    """
    Stream scan logs in real-time using Server-Sent Events (SSE).

    This endpoint provides a streaming connection that sends new log
    entries as they are generated. Use this for live log viewing.

    Content-Type: text/event-stream
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        last_index = 0
        scan = get_scan(request.state.db, scan_id)

        if not scan:
            yield f"data: {json.dumps({'error': 'Scan not found'})}\n\n"
            return

        # Send existing logs first
        logs = get_scan_logs(scan_id)
        for log in logs[last_index:]:
            yield f"data: {json.dumps(log)}\n\n"
        last_index = len(logs)

        # Stream new logs while scan is active
        while True:
            await asyncio.sleep(1)

            logs = get_scan_logs(scan_id)
            if len(logs) > last_index:
                for log in logs[last_index:]:
                    yield f"data: {json.dumps(log)}\n\n"
                last_index = len(logs)

            # Check if scan is still active
            scan = get_scan(request.state.db, scan_id)
            if scan and scan.status not in ["pending", "running"]:
                yield f"data: {json.dumps({'type': 'complete', 'status': scan.status})}\n\n"
                break

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/{scan_id}/action")
async def scan_action(
    scan_id: int, action_request: ScanActionRequest, user: dict = Depends(verify_token), db: Session = Depends(get_db)
):
    """
    Perform an action on a scan (pause, resume, stop).

    - **action**: pause, resume, stop, restart
    - **reason**: Optional reason for the action
    """
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    action = action_request.action.lower()

    if action == "stop":
        if scan.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail=f"Cannot stop scan with status: {scan.status}")

        update_scan_status(db, scan_id, "cancelled", {"stopped_by": user.get("sub"), "reason": action_request.reason})
        add_scan_log(scan_id, "WARNING", "control", f"Scan stopped by user: {action_request.reason or 'No reason provided'}")

        await broadcast_scan_update(scan_id, "stopped", {"reason": action_request.reason})

    elif action == "restart":
        if scan.status not in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Can only restart completed/failed/cancelled scans")

        # Reset status and re-queue
        update_scan_status(db, scan_id, "pending")
        scan_logs[scan_id] = []  # Clear old logs
        add_scan_log(scan_id, "INFO", "initializing", "Scan restarted")

        await broadcast_scan_update(scan_id, "restarted", {})

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    return {"message": f"Scan {action} successful", "scan_id": scan_id}


@router.get("/{scan_id}/timeline")
async def get_scan_timeline(scan_id: int, user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Get scan execution timeline.

    Returns a chronological list of scan phases and their durations.
    """
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    logs = get_scan_logs(scan_id)

    # Build timeline from logs
    phases = {}
    timeline = []

    for log in sorted(logs, key=lambda x: x.get("timestamp", "")):
        phase = log.get("phase", "unknown")
        timestamp = log.get("timestamp")

        if phase not in phases:
            phases[phase] = {"start": timestamp, "end": None}
            timeline.append(
                {"phase": phase, "started_at": timestamp, "completed_at": None, "duration_seconds": None, "logs_count": 1}
            )
        else:
            phases[phase]["end"] = timestamp
            for item in timeline:
                if item["phase"] == phase:
                    item["completed_at"] = timestamp
                    item["logs_count"] = item.get("logs_count", 0) + 1

    # Calculate durations
    for item in timeline:
        if item["started_at"] and item["completed_at"]:
            try:
                start = datetime.fromisoformat(item["started_at"])
                end = datetime.fromisoformat(item["completed_at"])
                item["duration_seconds"] = int((end - start).total_seconds())
            except Exception:
                pass

    return {"scan_id": scan_id, "scan_status": scan.status, "timeline": timeline}


# ============================================================================
# WebSocket Endpoint for Real-time Updates
# ============================================================================


@router.websocket("/{scan_id}/ws")
async def scan_websocket(websocket: WebSocket, scan_id: int):
    """
    WebSocket endpoint for real-time scan updates.

    Clients will receive:
    - log: New log entries
    - finding: New findings discovered
    - status: Status changes
    - progress: Progress updates
    - complete: Scan completion

    Client messages:
    - { "action": "ping" }
    - { "action": "get_logs" }
    - { "action": "subscribe", "events": ["logs", "findings"] }
    """
    await scan_ws_manager.connect(websocket, scan_id)

    try:
        # Send connection acknowledgment
        await websocket.send_json(
            {
                "type": "connected",
                "scan_id": scan_id,
                "message": f"Connected to scan {scan_id} updates",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")

            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            elif action == "get_logs":
                # Send recent logs
                logs = get_scan_logs(scan_id)[-100:]  # Last 100 logs
                await websocket.send_json({"type": "logs", "scan_id": scan_id, "logs": logs})

            elif action == "subscribe":
                await websocket.send_json({"type": "subscribed", "events": message.get("events", ["all"])})

    except WebSocketDisconnect:
        scan_ws_manager.disconnect(websocket, scan_id)
    except Exception as e:
        logger.error(f"Scan WebSocket error for scan {scan_id}: {e}")
        scan_ws_manager.disconnect(websocket, scan_id)


# ============================================================================
# Background Task (Mock implementation - replace with actual scan logic)
# ============================================================================


async def run_scan_task(scan_id: int, config: Dict):
    """
    Background task to execute a scan.
    This is a mock implementation - replace with actual scan orchestration.
    """
    from database.crud import update_scan_status
    from database.models import SessionLocal

    db = SessionLocal()

    try:
        # Update status to running
        update_scan_status(db, scan_id, "running")
        add_scan_log(scan_id, "INFO", "initializing", "Scan execution started")
        await broadcast_scan_update(scan_id, "status", {"status": "running"})

        # Mock scan phases
        phases = [
            ("reconnaissance", "Gathering target information", 2),
            ("port_scanning", "Scanning open ports", 3),
            ("vulnerability_scanning", "Testing for vulnerabilities", 5),
            ("analysis", "Analyzing findings", 2),
            ("reporting", "Generating report", 1),
        ]

        for phase, description, duration in phases:
            add_scan_log(scan_id, "INFO", phase, f"Starting: {description}")
            await broadcast_scan_update(scan_id, "phase", {"phase": phase, "description": description})

            # Simulate work
            for i in range(duration):
                await asyncio.sleep(1)
                progress = ((i + 1) / duration) * 100
                await broadcast_scan_update(scan_id, "progress", {"phase": phase, "progress": int(progress)})

            add_scan_log(scan_id, "INFO", phase, f"Completed: {description}")

        # Mark as completed
        update_scan_status(db, scan_id, "completed", {"summary": "Scan completed successfully"})
        add_scan_log(scan_id, "INFO", "complete", "Scan completed successfully")
        await broadcast_scan_update(scan_id, "complete", {"status": "completed"})

    except Exception as e:
        logger.error(f"Scan task error for scan {scan_id}: {e}")
        update_scan_status(db, scan_id, "failed", {"error": str(e)})
        add_scan_log(scan_id, "ERROR", "failed", f"Scan failed: {str(e)}")
        await broadcast_scan_update(scan_id, "error", {"error": str(e)})
    finally:
        db.close()

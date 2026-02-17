"""
ZenOrchestrator API Routes

REST API endpoints for orchestrator management.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

# Import orchestrator
try:
    from orchestrator import ZenOrchestrator, TaskPriority
    from orchestrator.events import EventType
except ImportError:
    import sys
    sys.path.insert(0, "../..")
    from orchestrator import ZenOrchestrator, TaskPriority
    from orchestrator.events import EventType


router = APIRouter(prefix="/api/v1/orchestrator", tags=["Orchestrator"])

# Global orchestrator instance
_orchestrator: Optional[ZenOrchestrator] = None


def get_orchestrator() -> ZenOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator

    if _orchestrator is None:
        from orchestrator import OrchestratorConfig
        config = OrchestratorConfig.default()
        _orchestrator = ZenOrchestrator(config)

    return _orchestrator


# Request/Response Models
class TaskSubmitRequest(BaseModel):
    type: str = Field(..., description="Task type")
    target: str = Field(..., description="Target for the task")
    options: dict = Field(default_factory=dict, description="Task options")
    priority: str = Field(default="normal", description="Task priority")
    metadata: dict = Field(default_factory=dict, description="Task metadata")


class TaskResponse(BaseModel):
    id: str
    type: str
    state: str
    priority: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float
    error: Optional[str] = None


class OrchestratorStatusResponse(BaseModel):
    instance_id: str
    status: str
    started_at: Optional[str]
    uptime_seconds: float
    config: dict
    components: dict


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class OrchestratorStatsResponse(BaseModel):
    total_tasks: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    state_counts: dict


# Routes

@router.get("/status", response_model=OrchestratorStatusResponse)
async def get_status(
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Get orchestrator status and configuration"""
    return orchestrator.get_status()


@router.post("/start")
async def start_orchestrator(
    background_tasks: BackgroundTasks,
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Start the orchestrator"""
    if orchestrator._running:
        return {"status": "already_running"}

    success = await orchestrator.start()

    return {
        "status": "started" if success else "failed",
        "instance_id": orchestrator.instance_id
    }


@router.post("/stop")
async def stop_orchestrator(
    timeout: int = Query(default=30, ge=5, le=300),
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Stop the orchestrator gracefully"""
    if not orchestrator._running:
        return {"status": "not_running"}

    success = await orchestrator.stop(timeout=timeout)

    return {
        "status": "stopped" if success else "failed"
    }


@router.get("/health")
async def health_check(
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Comprehensive health check"""
    return await orchestrator.health_check()


# Task Management

@router.post("/tasks", response_model=dict)
async def submit_task(
    request: TaskSubmitRequest,
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """
    Submit a new task

    - **type**: Task type (e.g., "vulnerability_scan", "subdomain_enum")
    - **target**: Target URL/hostname/IP
    - **options**: Task-specific options
    - **priority**: "critical", "high", "normal", "low", "background"
    """
    # Validate priority
    try:
        priority = TaskPriority(request.priority.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority: {request.priority}"
        )

    # Build task data
    task_data = {
        "type": request.type,
        "target": request.target,
        "options": request.options
    }

    try:
        task_id = await orchestrator.submit_task(
            task_data=task_data,
            priority=priority,
            metadata=request.metadata
        )

        return {
            "task_id": task_id,
            "status": "submitted",
            "submitted_at": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Get task status and details"""
    status = await orchestrator.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return TaskResponse(**status)


@router.get("/tasks/{task_id}/results")
async def get_task_results(
    task_id: str,
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Get task results (if completed)"""
    results = await orchestrator.get_task_results(task_id)

    if results is None:
        # Check if task exists
        status = await orchestrator.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        if status["state"] != "completed":
            return {
                "task_id": task_id,
                "state": status["state"],
                "results_available": False
            }

        return {"task_id": task_id, "results": None}

    return {
        "task_id": task_id,
        "state": "completed",
        "results_available": True,
        "results": results
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Cancel a running or pending task"""
    success = await orchestrator.cancel_task(task_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} not found or cannot be cancelled"
        )

    return {
        "task_id": task_id,
        "status": "cancelled"
    }


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """
    List tasks with optional filtering

    - **status**: Filter by state (pending, running, completed, failed, cancelled)
    - **task_type**: Filter by task type
    - **limit**: Maximum results (1-1000)
    """
    tasks = await orchestrator.list_tasks(
        status=status,
        task_type=task_type,
        limit=limit
    )

    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks)
    )


@router.get("/stats", response_model=OrchestratorStatsResponse)
async def get_statistics(
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Get orchestrator statistics"""
    if not orchestrator.task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    stats = await orchestrator.task_manager.get_statistics()

    return OrchestratorStatsResponse(**stats)


# Event Streaming (WebSocket would be better for production)

@router.get("/events/recent")
async def get_recent_events(
    event_type: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """Get recent events from the event bus"""
    try:
        event_type_enum = EventType(event_type) if event_type else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    events = await orchestrator.event_bus.get_history(
        event_type=event_type_enum,
        limit=limit
    )

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events)
    }


# Analysis Integration

@router.post("/analyze")
async def analyze_results(
    results: dict,
    analysis_type: str = "vulnerability",
    orchestrator: ZenOrchestrator = Depends(get_orchestrator)
):
    """
    Analyze scan results using the Analysis Bot

    - **results**: Scan results to analyze
    - **analysis_type**: Type of analysis to perform
    """
    analysis = await orchestrator.analyze_results(results, analysis_type)

    return {
        "analysis_type": analysis_type,
        "results": analysis,
        "timestamp": datetime.utcnow().isoformat()
    }

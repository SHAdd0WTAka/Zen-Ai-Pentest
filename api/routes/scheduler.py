"""
Task Scheduler API Routes

REST API endpoints for job scheduling and management.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Import scheduler
try:
    from scheduler import TaskScheduler
    from scheduler.job import JobStatus
    from scheduler.recurring import RecurringSchedule, SchedulePresets
except ImportError:
    import sys
    sys.path.insert(0, "../..")
    from scheduler import TaskScheduler
    from scheduler.job import JobStatus
    from scheduler.recurring import RecurringSchedule, SchedulePresets


router = APIRouter(prefix="/api/v1/scheduler", tags=["Task Scheduler"])

# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create scheduler instance"""
    global _scheduler
    
    if _scheduler is None:
        from scheduler import ScheduleConfig
        config = ScheduleConfig()
        _scheduler = TaskScheduler(config)
    
    return _scheduler


# Request/Response Models
class ScheduleJobRequest(BaseModel):
    name: str = Field(..., description="Job name")
    description: str = Field(default="", description="Job description")
    task_type: str = Field(..., description="Type of task to execute")
    task_data: dict = Field(default_factory=dict, description="Task configuration")
    cron: Optional[str] = Field(default=None, description="Cron expression")
    interval: Optional[int] = Field(default=None, description="Interval in minutes")
    once_at: Optional[datetime] = Field(default=None, description="One-time execution time")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=3600, ge=60, le=86400)


class JobResponse(BaseModel):
    id: str
    name: str
    description: str
    task_type: str
    schedule_type: str
    schedule_expr: str
    status: str
    enabled: bool
    created_at: str
    last_run: Optional[str]
    next_run: Optional[str]
    run_count: int
    fail_count: int


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


class ExecutionResponse(BaseModel):
    id: str
    job_id: str
    started_at: str
    completed_at: Optional[str]
    status: str
    error: Optional[str]


class SchedulerStatsResponse(BaseModel):
    total_jobs: int
    enabled_jobs: int
    running_jobs: int
    due_jobs: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float


# Routes

@router.get("/status")
async def get_status(
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Get scheduler status and statistics"""
    stats = await scheduler.get_statistics()
    
    return {
        "running": scheduler._running,
        "total_jobs": stats["total_jobs"],
        "enabled_jobs": stats["enabled_jobs"],
        "next_check_seconds": scheduler.config.check_interval
    }


@router.post("/start")
async def start_scheduler(
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Start the scheduler"""
    if scheduler._running:
        return {"status": "already_running"}
    
    await scheduler.start()
    
    return {
        "status": "started",
        "jobs_loaded": len(scheduler._jobs)
    }


@router.post("/stop")
async def stop_scheduler(
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Stop the scheduler"""
    if not scheduler._running:
        return {"status": "not_running"}
    
    await scheduler.stop()
    
    return {"status": "stopped"}


# Job Management

@router.post("/jobs", response_model=dict)
async def schedule_job(
    request: ScheduleJobRequest,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """
    Schedule a new job
    
    Provide exactly one of: cron, interval, or once_at
    
    Examples:
    - Daily at 2 AM: cron="0 2 * * *"
    - Every 5 minutes: interval=5
    - One-time: once_at="2024-12-31T23:59:59"
    """
    # Validate schedule
    schedule_count = sum([
        1 if request.cron else 0,
        1 if request.interval else 0,
        1 if request.once_at else 0
    ])
    
    if schedule_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Must provide exactly one of: cron, interval, or once_at"
        )
    
    if schedule_count > 1:
        raise HTTPException(
            status_code=400,
            detail="Can only provide one schedule type"
        )
    
    try:
        job_id = await scheduler.schedule(
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            task_data=request.task_data,
            cron=request.cron,
            interval=request.interval,
            once=request.once_at,
            timezone=request.timezone,
            max_retries=request.max_retries,
            timeout=request.timeout
        )
        
        return {
            "job_id": job_id,
            "status": "scheduled",
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    enabled_only: bool = Query(default=False),
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """
    List scheduled jobs
    
    - **status**: Filter by status (scheduled, running, paused, etc.)
    - **task_type**: Filter by task type
    - **enabled_only**: Only show enabled jobs
    """
    jobs = await scheduler.list_jobs(
        status=status,
        task_type=task_type,
        enabled_only=enabled_only
    )
    
    return JobListResponse(
        jobs=[JobResponse(**job.to_dict()) for job in jobs],
        total=len(jobs)
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Get job details"""
    job = await scheduler.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobResponse(**job.to_dict())


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Remove a scheduled job"""
    success = await scheduler.unschedule(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": "removed"
    }


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Pause a job temporarily"""
    success = await scheduler.pause_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": "paused"
    }


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Resume a paused job"""
    success = await scheduler.resume_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": "resumed"
    }


@router.post("/jobs/{job_id}/run")
async def run_job_now(
    job_id: str,
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Manually trigger a job to run immediately"""
    try:
        execution_id = await scheduler.run_job_now(job_id)
        
        return {
            "job_id": job_id,
            "execution_id": execution_id,
            "status": "triggered"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/executions")
async def get_job_executions(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Get execution history for a job"""
    executions = await scheduler.get_executions(job_id, limit)
    
    return {
        "job_id": job_id,
        "executions": [
            {
                "id": e.id,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "status": e.status,
                "error": e.error
            }
            for e in executions
        ],
        "total": len(executions)
    }


# Statistics

@router.get("/stats", response_model=SchedulerStatsResponse)
async def get_statistics(
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """Get scheduler statistics"""
    stats = await scheduler.get_statistics()
    return SchedulerStatsResponse(**stats)


# Presets

@router.get("/presets")
async def get_presets():
    """Get common schedule presets"""
    return {
        "schedules": {
            "every_minute": "* * * * *",
            "every_5_minutes": "*/5 * * * *",
            "every_15_minutes": "*/15 * * * *",
            "every_30_minutes": "*/30 * * * *",
            "hourly": "0 * * * *",
            "every_2_hours": "0 */2 * * *",
            "daily": "0 0 * * *",
            "daily_morning": "0 9 * * *",
            "daily_evening": "0 18 * * *",
            "weekly": "0 0 * * 0",
            "weekly_monday": "0 0 * * 1",
            "monthly": "0 0 1 * *",
            "yearly": "0 0 1 1 *"
        },
        "pentest_schedules": {
            "daily_vulnerability_scan": SchedulePresets.daily_vulnerability_scan(),
            "weekly_deep_scan": SchedulePresets.weekly_deep_scan(),
            "subdomain_monitoring": SchedulePresets.subdomain_monitoring(),
            "certificate_check": SchedulePresets.certificate_expiry_check(),
            "threat_intel_update": SchedulePresets.threat_intelligence_update(),
            "weekly_report": SchedulePresets.weekly_report(),
            "monthly_compliance": SchedulePresets.monthly_compliance_audit()
        }
    }


@router.get("/presets/describe")
async def describe_cron(cron: str):
    """Get human-readable description of a cron expression"""
    from scheduler.cron import CronParser
    
    if not CronParser.is_valid(cron):
        raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    description = CronParser.describe(cron)
    next_run = CronParser.get_next_run(cron)
    
    return {
        "cron": cron,
        "description": description,
        "next_run": next_run.isoformat()
    }

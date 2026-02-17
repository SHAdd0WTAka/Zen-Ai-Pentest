"""
Task Scheduler Core

Main scheduler implementation with job execution and management.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .job import ScheduledJob, JobStatus, ScheduleType, JobExecution
from .cron import CronParser


logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for the task scheduler"""
    
    # Timing
    check_interval: int = 60  # Check for due jobs every 60 seconds
    max_concurrent_jobs: int = 5
    default_timeout: int = 3600  # 1 hour
    
    # Persistence
    persistence_enabled: bool = True
    persistence_path: str = "scheduler_state.json"
    
    # Recovery
    auto_recover: bool = True
    catch_up_missed: bool = True  # Run missed jobs on startup
    max_catch_up_hours: int = 24  # Don't run jobs older than this
    
    # Features
    enable_notifications: bool = True
    webhook_url: Optional[str] = None


class TaskScheduler:
    """
    Main task scheduler for recurring and scheduled tasks
    
    Features:
    - Cron expression support
    - Interval-based scheduling
    - One-time jobs
    - Job persistence
    - Concurrent execution
    - Missed job recovery
    
    Example:
        scheduler = TaskScheduler()
        await scheduler.start()
        
        # Schedule daily vulnerability scan
        job_id = await scheduler.schedule(
            name="Daily Scan",
            task_type="vulnerability_scan",
            task_data={"target": "example.com"},
            cron="0 2 * * *"  # 2 AM daily
        )
        
        # Schedule weekly report
        job_id = await scheduler.schedule(
            name="Weekly Report",
            task_type="generate_report",
            task_data={"type": "summary"},
            cron="0 9 * * 1"  # Monday 9 AM
        )
    """
    
    def __init__(self, config: Optional[ScheduleConfig] = None):
        self.config = config or ScheduleConfig()
        
        # Jobs storage
        self._jobs: Dict[str, ScheduledJob] = {}
        self._executions: Dict[str, List[JobExecution]] = {}
        
        # Runtime
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Execution tracking
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)
        
        # Callbacks
        self._job_callbacks: Dict[str, Callable] = {}
        self._on_execution_complete: Optional[Callable] = None
        
        # Statistics
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
    
    # ==================== Lifecycle ====================
    
    async def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            return
        
        logger.info("Starting TaskScheduler...")
        
        # Load persisted state
        if self.config.persistence_enabled:
            await self._load_state()
        
        # Catch up on missed jobs
        if self.config.catch_up_missed:
            await self._catch_up_missed_jobs()
        
        # Start scheduler loop
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"✅ TaskScheduler started with {len(self._jobs)} jobs")
    
    async def stop(self) -> None:
        """Stop the scheduler"""
        if not self._running:
            return
        
        logger.info("Stopping TaskScheduler...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Cancel running jobs
        for job_id, task in list(self._running_jobs.items()):
            task.cancel()
        
        # Wait for scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Save state
        if self.config.persistence_enabled:
            await self._save_state()
        
        logger.info("✅ TaskScheduler stopped")
    
    # ==================== Job Management ====================
    
    async def schedule(
        self,
        name: str,
        task_type: str,
        task_data: Dict[str, Any],
        cron: Optional[str] = None,
        interval: Optional[int] = None,
        once: Optional[datetime] = None,
        description: str = "",
        **kwargs
    ) -> str:
        """
        Schedule a new job
        
        Args:
            name: Job name
            task_type: Type of task to execute
            task_data: Task configuration
            cron: Cron expression (e.g., "0 2 * * *")
            interval: Interval in minutes
            once: One-time execution datetime
            description: Job description
            **kwargs: Additional job options
        
        Returns:
            Job ID
        """
        from .job import JobBuilder
        
        builder = JobBuilder().name(name).task(task_type, **task_data)
        
        if description:
            builder.description(description)
        
        # Determine schedule type
        if cron:
            builder.cron(cron)
            # Calculate next run
            next_run = CronParser.get_next_run(cron)
        elif interval:
            builder.interval(interval)
            next_run = datetime.utcnow() + timedelta(minutes=interval)
        elif once:
            builder.once(once)
            next_run = once
        else:
            raise ValueError("Must specify cron, interval, or once")
        
        # Apply additional options
        if "timezone" in kwargs:
            builder.timezone(kwargs["timezone"])
        if "retries" in kwargs:
            builder.retries(kwargs["retries"])
        if "timeout" in kwargs:
            builder.timeout(kwargs["timeout"])
        
        job = builder.build()
        job.next_run = next_run
        
        # Store job
        self._jobs[job.id] = job
        
        logger.info(f"Scheduled job {job.id}: {name} (next: {next_run})")
        
        return job.id
    
    async def unschedule(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id in self._jobs:
            # Cancel if running
            if job_id in self._running_jobs:
                self._running_jobs[job_id].cancel()
            
            del self._jobs[job_id]
            logger.info(f"Removed job {job_id}")
            return True
        
        return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job temporarily"""
        job = self._jobs.get(job_id)
        if job:
            job.pause()
            logger.info(f"Paused job {job_id}")
            return True
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        job = self._jobs.get(job_id)
        if job:
            job.resume()
            # Recalculate next run
            if job.schedule_type == ScheduleType.CRON:
                job.next_run = CronParser.get_next_run(job.schedule_expr)
            logger.info(f"Resumed job {job_id}")
            return True
        return False
    
    async def run_job_now(self, job_id: str) -> str:
        """Manually trigger a job to run immediately"""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        execution_id = await self._execute_job(job, manual=True)
        return execution_id
    
    async def update_job(self, job_id: str, **updates) -> bool:
        """Update job properties"""
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        allowed_fields = ["name", "description", "task_data", "enabled"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(job, field, value)
        
        job.updated_at = datetime.utcnow()
        
        # Recalculate next run if schedule changed
        if "cron" in updates:
            job.schedule_expr = updates["cron"]
            job.next_run = CronParser.get_next_run(job.schedule_expr)
        
        return True
    
    # ==================== Scheduler Loop ====================
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self._running and not self._shutdown_event.is_set():
            try:
                # Check for due jobs
                await self._check_due_jobs()
                
                # Wait for next check
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.check_interval
                )
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
    
    async def _check_due_jobs(self) -> None:
        """Check and execute due jobs"""
        now = datetime.utcnow()
        
        for job in self._jobs.values():
            # Skip if not enabled or already running
            if not job.enabled or job.status == JobStatus.RUNNING:
                continue
            
            # Check if job is due
            if job.next_run and job.next_run <= now:
                # Execute job (with concurrency limit)
                asyncio.create_task(self._execute_job_wrapper(job))
    
    async def _execute_job_wrapper(self, job: ScheduledJob) -> None:
        """Wrapper to execute job with semaphore"""
        async with self._semaphore:
            await self._execute_job(job)
    
    async def _execute_job(self, job: ScheduledJob, manual: bool = False) -> str:
        """
        Execute a scheduled job
        
        Args:
            job: Job to execute
            manual: Whether this is a manual trigger
        
        Returns:
            Execution ID
        """
        execution_id = f"exec-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{job.id}"
        
        # Create execution record
        execution = JobExecution(
            id=execution_id,
            job_id=job.id,
            started_at=datetime.utcnow()
        )
        
        if job.id not in self._executions:
            self._executions[job.id] = []
        self._executions[job.id].append(execution)
        
        # Update job status
        job.status = JobStatus.RUNNING
        
        logger.info(f"Executing job {job.id} ({job.name})")
        
        try:
            # Get callback
            callback = self._job_callbacks.get(job.task_type)
            
            if callback:
                # Execute with timeout
                task = asyncio.create_task(
                    self._run_callback(callback, job)
                )
                self._running_jobs[job.id] = task
                
                result = await asyncio.wait_for(
                    task,
                    timeout=job.timeout
                )
                
                # Success
                execution.status = "completed"
                execution.result = result
                execution.completed_at = datetime.utcnow()
                
                job.record_execution(success=True, result=result)
                self._successful_executions += 1
                
                logger.info(f"Job {job.id} completed successfully")
                
            else:
                raise RuntimeError(f"No callback registered for task type: {job.task_type}")
                
        except asyncio.TimeoutError:
            execution.status = "failed"
            execution.error = f"Timeout after {job.timeout}s"
            execution.completed_at = datetime.utcnow()
            
            job.record_execution(success=False, error=execution.error)
            self._failed_executions += 1
            
            logger.error(f"Job {job.id} timed out")
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            job.record_execution(success=False, error=str(e))
            self._failed_executions += 1
            
            logger.error(f"Job {job.id} failed: {e}")
        
        finally:
            # Cleanup
            if job.id in self._running_jobs:
                del self._running_jobs[job.id]
            
            self._total_executions += 1
            
            # Calculate next run for recurring jobs
            if job.schedule_type == ScheduleType.CRON and job.enabled:
                job.next_run = CronParser.get_next_run(job.schedule_expr)
            elif job.schedule_type == ScheduleType.INTERVAL and job.enabled:
                interval = int(job.schedule_expr)
                job.next_run = datetime.utcnow() + timedelta(minutes=interval)
            
            # Call completion handler
            if self._on_execution_complete:
                await self._on_execution_complete(job, execution)
        
        return execution_id
    
    async def _run_callback(
        self,
        callback: Callable,
        job: ScheduledJob
    ) -> Any:
        """Run job callback with error handling"""
        try:
            if asyncio.iscoroutinefunction(callback):
                return await callback(job.task_data)
            else:
                return callback(job.task_data)
        except Exception as e:
            raise
    
    # ==================== Callbacks ====================
    
    def register_callback(self, task_type: str, callback: Callable) -> None:
        """
        Register a callback for a task type
        
        Args:
            task_type: Task type to handle
            callback: Function to call when job executes
        """
        self._job_callbacks[task_type] = callback
        logger.debug(f"Registered callback for task type: {task_type}")
    
    def on_execution_complete(self, callback: Callable) -> None:
        """Set callback for execution completion"""
        self._on_execution_complete = callback
    
    # ==================== Persistence ====================
    
    async def _save_state(self) -> None:
        """Save scheduler state to disk"""
        import json
        
        data = {
            "saved_at": datetime.utcnow().isoformat(),
            "jobs": {jid: job.to_dict() for jid, job in self._jobs.items()},
            "statistics": {
                "total_executions": self._total_executions,
                "successful": self._successful_executions,
                "failed": self._failed_executions
            }
        }
        
        try:
            with open(self.config.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Scheduler state saved")
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")
    
    async def _load_state(self) -> None:
        """Load scheduler state from disk"""
        import json
        import os
        
        if not os.path.exists(self.config.persistence_path):
            return
        
        try:
            with open(self.config.persistence_path, 'r') as f:
                data = json.load(f)
            
            # Load jobs
            for job_id, job_data in data.get("jobs", {}).items():
                job = ScheduledJob.from_dict(job_data)
                self._jobs[job_id] = job
            
            # Load statistics
            stats = data.get("statistics", {})
            self._total_executions = stats.get("total_executions", 0)
            self._successful_executions = stats.get("successful", 0)
            self._failed_executions = stats.get("failed", 0)
            
            logger.info(f"Loaded {len(self._jobs)} jobs from state")
            
        except Exception as e:
            logger.error(f"Failed to load scheduler state: {e}")
    
    async def _catch_up_missed_jobs(self) -> None:
        """Execute jobs that were missed while scheduler was down"""
        if not self.config.catch_up_missed:
            return
        
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self.config.max_catch_up_hours)
        
        caught_up = 0
        
        for job in self._jobs.values():
            if not job.enabled or job.schedule_type == ScheduleType.ONCE:
                continue
            
            # Check if job was missed
            if job.next_run and job.next_run < now:
                # Only catch up recent jobs
                if job.next_run > cutoff:
                    logger.info(f"Catching up missed job: {job.id}")
                    asyncio.create_task(self._execute_job_wrapper(job))
                    caught_up += 1
                else:
                    # Too old, just calculate next run
                    if job.schedule_type == ScheduleType.CRON:
                        job.next_run = CronParser.get_next_run(job.schedule_expr)
        
        if caught_up > 0:
            logger.info(f"Caught up {caught_up} missed jobs")
    
    # ==================== Queries ====================
    
    async def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get job by ID"""
        return self._jobs.get(job_id)
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[ScheduledJob]:
        """List jobs with optional filtering"""
        jobs = list(self._jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        
        if task_type:
            jobs = [j for j in jobs if j.task_type == task_type]
        
        if enabled_only:
            jobs = [j for j in jobs if j.enabled]
        
        return jobs
    
    async def get_executions(
        self,
        job_id: str,
        limit: int = 100
    ) -> List[JobExecution]:
        """Get execution history for a job"""
        executions = self._executions.get(job_id, [])
        return executions[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        now = datetime.utcnow()
        
        # Count due jobs
        due_jobs = sum(
            1 for j in self._jobs.values()
            if j.enabled and j.next_run and j.next_run <= now
        )
        
        return {
            "total_jobs": len(self._jobs),
            "enabled_jobs": sum(1 for j in self._jobs.values() if j.enabled),
            "running_jobs": len(self._running_jobs),
            "due_jobs": due_jobs,
            "total_executions": self._total_executions,
            "successful_executions": self._successful_executions,
            "failed_executions": self._failed_executions,
            "success_rate": (
                self._successful_executions / self._total_executions * 100
                if self._total_executions > 0 else 0
            )
        }

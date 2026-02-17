"""
Task Management System

Advanced task scheduling, execution, and lifecycle management.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskState(Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class Task:
    """
    Task definition
    
    Attributes:
        id: Unique task ID
        type: Task type (e.g., "vulnerability_scan")
        data: Task configuration/data
        priority: Task priority
        state: Current state
        metadata: Additional metadata
        created_at: Creation timestamp
        started_at: When task started running
        completed_at: When task finished
        progress: Progress percentage (0-100)
        result: Task result data
        error: Error message if failed
        retry_count: Number of retries
        max_retries: Maximum retries allowed
        timeout: Task timeout in seconds
    """
    id: str
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 3600
    
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "priority": self.priority.value,
            "state": self.state.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration_seconds": self.duration_seconds()
        }


# Task handler type
TaskHandler = Callable[[Task], Coroutine[Any, Any, Dict[str, Any]]]


class TaskManager:
    """
    Advanced task management system
    
    Features:
    - Priority-based scheduling
    - Concurrent execution with worker pool
    - Task timeouts and cancellation
    - Progress tracking
    - Retry logic
    - Result caching
    
    Example:
        manager = TaskManager(max_workers=4)
        await manager.start()
        
        # Register task handler
        manager.register_handler("vulnerability_scan", scan_handler)
        
        # Submit task
        task_id = await manager.submit(Task(
            id="task-123",
            type="vulnerability_scan",
            data={"target": "example.com"}
        ))
        
        # Check status
        task = await manager.get_task(task_id)
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        max_concurrent: int = 10,
        queue_size: int = 1000
    ):
        self.max_workers = max_workers
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        
        # Task storage
        self._tasks: Dict[str, Task] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        
        # Priority queue
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=queue_size)
        
        # Handlers
        self._handlers: Dict[str, TaskHandler] = {}
        
        # Worker management
        self._workers: List[asyncio.Task] = []
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        
        # Runtime
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.submitted_count = 0
        self.completed_count = 0
        self.failed_count = 0
        self.cancelled_count = 0
    
    @property
    def pending_tasks(self) -> List[str]:
        """Get list of pending task IDs"""
        return [
            tid for tid, task in self._tasks.items()
            if task.state in (TaskState.PENDING, TaskState.QUEUED)
        ]
    
    @property
    def running_tasks(self) -> List[str]:
        """Get list of running task IDs"""
        return [
            tid for tid, task in self._tasks.items()
            if task.state == TaskState.RUNNING
        ]
    
    # ==================== Lifecycle ====================
    
    async def start(self) -> None:
        """Start the task manager"""
        if self._running:
            return
        
        logger.info(f"Starting TaskManager with {self.max_workers} workers")
        
        self._running = True
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Start worker tasks
        self._workers = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self.max_workers)
        ]
        
        logger.info("✅ TaskManager started")
    
    async def stop(self, timeout: int = 30) -> None:
        """Stop the task manager gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping TaskManager...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Cancel running tasks
        for task_id, task in list(self._running_tasks.items()):
            task.cancel()
        
        # Wait for workers with timeout
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("TaskManager shutdown timed out")
        
        self._workers.clear()
        self._running_tasks.clear()
        
        logger.info("✅ TaskManager stopped")
    
    # ==================== Task Submission ====================
    
    async def submit(self, task: Task) -> str:
        """
        Submit a task for execution
        
        Args:
            task: Task to execute
        
        Returns:
            Task ID
        """
        # Store task
        self._tasks[task.id] = task
        task.state = TaskState.QUEUED
        
        # Add to priority queue
        # Lower priority value = higher priority
        priority_tuple = (task.priority.value, task.created_at.timestamp(), task.id)
        
        try:
            self._queue.put_nowait((priority_tuple, task))
            self.submitted_count += 1
            logger.debug(f"Task {task.id} submitted ({task.type})")
        except asyncio.QueueFull:
            task.state = TaskState.FAILED
            task.error = "Task queue is full"
            raise RuntimeError("Task queue is full")
        
        return task.id
    
    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task to cancel
        
        Returns:
            True if cancelled
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        if task.state == TaskState.RUNNING:
            # Cancel running task
            running_task = self._running_tasks.get(task_id)
            if running_task:
                running_task.cancel()
        
        task.state = TaskState.CANCELLED
        self.cancelled_count += 1
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    # ==================== Task Handlers ====================
    
    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        """
        Register a handler for a task type
        
        Args:
            task_type: Task type to handle
            handler: Async function to execute tasks
        """
        self._handlers[task_type] = handler
        logger.debug(f"Handler registered for task type: {task_type}")
    
    def unregister_handler(self, task_type: str) -> bool:
        """Unregister a task handler"""
        if task_type in self._handlers:
            del self._handlers[task_type]
            return True
        return False
    
    # ==================== Task Execution ====================
    
    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing tasks"""
        logger.debug(f"Worker {worker_id} started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Wait for task with timeout
                try:
                    _, task = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if task was cancelled
                if task.state == TaskState.CANCELLED:
                    self._queue.task_done()
                    continue
                
                # Execute task
                await self._execute_task(task)
                
                # Mark as done
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a single task"""
        handler = self._handlers.get(task.type)
        
        if not handler:
            task.state = TaskState.FAILED
            task.error = f"No handler for task type: {task.type}"
            self.failed_count += 1
            return
        
        # Acquire semaphore for concurrency limit
        async with self._semaphore:
            task.state = TaskState.RUNNING
            task.started_at = datetime.utcnow()
            
            # Create asyncio task
            asyncio_task = asyncio.create_task(
                self._run_with_timeout(task, handler)
            )
            self._running_tasks[task.id] = asyncio_task
            
            try:
                # Wait for completion
                result = await asyncio_task
                
                # Success
                task.state = TaskState.COMPLETED
                task.result = result
                task.completed_at = datetime.utcnow()
                task.progress = 100.0
                self._results[task.id] = result
                self.completed_count += 1
                
                logger.info(f"Task {task.id} completed ({task.type})")
                
            except asyncio.CancelledError:
                task.state = TaskState.CANCELLED
                self.cancelled_count += 1
                logger.info(f"Task {task.id} cancelled")
                
            except asyncio.TimeoutError:
                task.state = TaskState.TIMEOUT
                task.error = f"Task timed out after {task.timeout}s"
                self.failed_count += 1
                logger.warning(f"Task {task.id} timed out")
                
                # Retry logic
                if task.retry_count < task.max_retries:
                    await self._retry_task(task)
                
            except Exception as e:
                task.state = TaskState.FAILED
                task.error = str(e)
                self.failed_count += 1
                logger.error(f"Task {task.id} failed: {e}")
                
                # Retry logic
                if task.retry_count < task.max_retries:
                    await self._retry_task(task)
            
            finally:
                # Cleanup
                if task.id in self._running_tasks:
                    del self._running_tasks[task.id]
    
    async def _run_with_timeout(
        self,
        task: Task,
        handler: TaskHandler
    ) -> Dict[str, Any]:
        """Run task handler with timeout"""
        return await asyncio.wait_for(
            handler(task),
            timeout=task.timeout
        )
    
    async def _retry_task(self, task: Task) -> None:
        """Retry a failed task"""
        task.retry_count += 1
        task.state = TaskState.RETRYING
        
        # Exponential backoff
        delay = min(2 ** task.retry_count, 60)  # Max 60 seconds
        
        logger.info(
            f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries}) "
            f"in {delay}s"
        )
        
        await asyncio.sleep(delay)
        
        # Resubmit
        task.state = TaskState.PENDING
        task.error = None
        await self.submit(task)
    
    # ==================== Progress Updates ====================
    
    def update_progress(self, task_id: str, progress: float, message: str = "") -> None:
        """
        Update task progress
        
        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        task = self._tasks.get(task_id)
        if task:
            task.progress = max(0.0, min(100.0, progress))
            if message:
                task.metadata["progress_message"] = message
    
    # ==================== Query Methods ====================
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    async def get_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task results"""
        return self._results.get(task_id)
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """List tasks with filtering"""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.state.value == status]
        
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Remove old completed tasks
        
        Args:
            max_age_hours: Maximum age in hours
        
        Returns:
            Number of tasks removed
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
                if task.completed_at and task.completed_at < cutoff:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
            if task_id in self._results:
                del self._results[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old tasks")
        return len(to_remove)
    
    # ==================== Health Check ====================
    
    async def health_check(self) -> bool:
        """Check if task manager is healthy"""
        # Check if workers are running
        if not self._running:
            return False
        
        # Check if all workers are alive
        alive_workers = sum(
            1 for w in self._workers
            if not w.done()
        )
        
        if alive_workers < self.max_workers / 2:
            logger.warning(f"Only {alive_workers}/{self.max_workers} workers alive")
            return False
        
        return True
    
    # ==================== Statistics ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        state_counts = {state.value: 0 for state in TaskState}
        for task in self._tasks.values():
            state_counts[task.state.value] += 1
        
        return {
            "total_tasks": len(self._tasks),
            "pending": len(self.pending_tasks),
            "running": len(self.running_tasks),
            "submitted": self.submitted_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "cancelled": self.cancelled_count,
            "state_counts": state_counts,
            "queue_size": self._queue.qsize(),
            "active_workers": sum(1 for w in self._workers if not w.done()),
            "registered_handlers": list(self._handlers.keys())
        }

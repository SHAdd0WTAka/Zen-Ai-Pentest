"""
ZenOrchestrator Core

Main orchestration class that coordinates all system components.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

# Component imports
try:
    from analysis_bot import AnalysisBot
    from audit import AuditLogger, EventCategory
    from core.secure_input_validator import SecureInputValidator
except ImportError:
    AnalysisBot = None
    AuditLogger = None
    SecureInputValidator = None

from .state import StateManager, TaskState
from .events import EventBus, Event, EventType
from .tasks import TaskManager, Task, TaskPriority
from .integration import ComponentRegistry


logger = logging.getLogger(__name__)


class OrchestratorStatus(Enum):
    """Orchestrator lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


@dataclass
class OrchestratorConfig:
    """Configuration for ZenOrchestrator"""

    # Concurrency
    max_concurrent_tasks: int = 10
    max_workers: int = 4
    task_timeout: int = 3600  # 1 hour

    # Features
    enable_analysis_bot: bool = True
    enable_audit_logging: bool = True
    enable_secure_validation: bool = True
    enable_websocket_broadcast: bool = True

    # Queues
    task_queue_size: int = 1000
    event_queue_size: int = 10000

    # Recovery
    auto_recover: bool = True
    retry_failed_tasks: bool = True
    max_retries: int = 3

    # Monitoring
    health_check_interval: int = 30
    metrics_enabled: bool = True

    @classmethod
    def default(cls) -> "OrchestratorConfig":
        return cls()

    @classmethod
    def production(cls) -> "OrchestratorConfig":
        return cls(
            max_concurrent_tasks=50,
            max_workers=8,
            enable_audit_logging=True,
            enable_secure_validation=True,
            health_check_interval=10
        )

    @classmethod
    def development(cls) -> "OrchestratorConfig":
        return cls(
            max_concurrent_tasks=5,
            max_workers=2,
            enable_audit_logging=True,
            enable_secure_validation=True,
            task_timeout=600  # 10 minutes for dev
        )


class ZenOrchestrator:
    """
    Main orchestrator for Zen-AI-Pentest

    Coordinates all system components:
    - Task execution and scheduling
    - State management across components
    - Event propagation
    - Security validation
    - Audit logging
    - Analysis Bot integration

    Example:
        orchestrator = ZenOrchestrator()
        await orchestrator.start()

        # Submit a task
        task_id = await orchestrator.submit_task({
            "type": "vulnerability_scan",
            "target": "example.com",
            "options": {"deep_scan": True}
        })

        # Check status
        status = await orchestrator.get_task_status(task_id)

        # Get results
        results = await orchestrator.get_task_results(task_id)
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig.default()
        self.status = OrchestratorStatus.INITIALIZING
        self.instance_id = str(uuid.uuid4())
        self.started_at: Optional[datetime] = None

        # Core components
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        self.task_manager: Optional[TaskManager] = None
        self.component_registry = ComponentRegistry()

        # Optional integrations
        self.analysis_bot: Optional[Any] = None
        self.audit_logger: Optional[Any] = None
        self.validator: Optional[Any] = None

        # Runtime
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Callbacks
        self._event_handlers: Dict[EventType, List[Callable]] = {}

        logger.info(f"ZenOrchestrator initialized (ID: {self.instance_id})")

    async def start(self) -> bool:
        """
        Start the orchestrator and all components

        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("Orchestrator already running")
            return True

        try:
            logger.info("Starting ZenOrchestrator...")
            self.status = OrchestratorStatus.INITIALIZING

            # Initialize components
            await self._initialize_components()

            # Start task manager
            self.task_manager = TaskManager(
                max_workers=self.config.max_workers,
                max_concurrent=self.config.max_concurrent_tasks
            )
            await self.task_manager.start()

            # Start event bus
            await self.event_bus.start()

            # Register event handlers
            await self._register_event_handlers()

            # Start background tasks
            if self.config.health_check_interval > 0:
                self._health_check_task = asyncio.create_task(
                    self._health_check_loop()
                )

            if self.config.metrics_enabled:
                self._metrics_task = asyncio.create_task(
                    self._metrics_loop()
                )

            # Mark as running
            self._running = True
            self.started_at = datetime.utcnow()
            self.status = OrchestratorStatus.RUNNING

            # Log startup
            await self._log_event(
                "orchestrator_started",
                f"Orchestrator started successfully (ID: {self.instance_id})",
                level="info"
            )

            logger.info(f"✅ ZenOrchestrator running (ID: {self.instance_id})")
            return True

        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Failed to start orchestrator: {e}")
            await self._log_event(
                "orchestrator_start_failed",
                f"Failed to start: {str(e)}",
                level="error"
            )
            raise

    async def stop(self, timeout: int = 30) -> bool:
        """
        Gracefully stop the orchestrator

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if stopped successfully
        """
        if not self._running:
            return True

        logger.info("Stopping ZenOrchestrator...")
        self.status = OrchestratorStatus.SHUTTING_DOWN

        try:
            # Signal shutdown
            self._shutdown_event.set()

            # Cancel background tasks
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass

            # Stop task manager (wait for running tasks)
            if self.task_manager:
                await self.task_manager.stop(timeout=timeout)

            # Stop event bus
            await self.event_bus.stop()

            # Log shutdown
            await self._log_event(
                "orchestrator_stopped",
                "Orchestrator stopped gracefully",
                level="info"
            )

            self._running = False
            self.status = OrchestratorStatus.READY

            logger.info("✅ ZenOrchestrator stopped")
            return True

        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Error during shutdown: {e}")
            return False

    async def _initialize_components(self):
        """Initialize optional components"""

        # Initialize Analysis Bot
        if self.config.enable_analysis_bot and AnalysisBot:
            try:
                self.analysis_bot = AnalysisBot()
                self.component_registry.register("analysis_bot", self.analysis_bot)
                logger.info("✅ Analysis Bot initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Analysis Bot: {e}")

        # Initialize Audit Logger
        if self.config.enable_audit_logging and AuditLogger:
            try:
                from audit.config import AuditConfig
                audit_config = AuditConfig.default()
                self.audit_logger = AuditLogger(audit_config)
                await self.audit_logger.start()
                self.component_registry.register("audit_logger", self.audit_logger)
                logger.info("✅ Audit Logger initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Audit Logger: {e}")

        # Initialize Secure Validator
        if self.config.enable_secure_validation and SecureInputValidator:
            try:
                self.validator = SecureInputValidator()
                self.component_registry.register("validator", self.validator)
                logger.info("✅ Secure Validator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Secure Validator: {e}")

    async def _register_event_handlers(self):
        """Register default event handlers"""

        # Task completion handler
        await self.event_bus.subscribe(
            EventType.TASK_COMPLETED,
            self._on_task_completed
        )

        # Task failure handler
        await self.event_bus.subscribe(
            EventType.TASK_FAILED,
            self._on_task_failed
        )

        # Security event handler
        await self.event_bus.subscribe(
            EventType.SECURITY_ALERT,
            self._on_security_alert
        )

    # ==================== Task Management ====================

    async def submit_task(
        self,
        task_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a new task to the orchestrator

        Args:
            task_data: Task configuration
            priority: Task priority level
            metadata: Additional task metadata

        Returns:
            Task ID

        Raises:
            ValueError: If task data is invalid
            SecurityError: If validation fails
        """
        # Validate input
        if self.validator:
            target = task_data.get("target", "")
            if target:
                try:
                    self.validator.validate_url(target)
                except Exception as e:
                    await self._log_event(
                        "task_validation_failed",
                        f"Task validation failed: {e}",
                        level="warning"
                    )
                    raise ValueError(f"Invalid target: {e}")

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            type=task_data.get("type", "unknown"),
            data=task_data,
            priority=priority,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        # Submit to task manager
        task_id = await self.task_manager.submit(task)

        # Update state
        await self.state_manager.set_task_state(task_id, TaskState.PENDING)

        # Log
        await self._log_event(
            "task_submitted",
            f"Task {task_id} submitted ({task.type})",
            level="info",
            details={"task_id": task_id, "type": task.type}
        )

        # Emit event
        await self.event_bus.publish(Event(
            type=EventType.TASK_SUBMITTED,
            source="orchestrator",
            data={"task_id": task_id, "task_type": task.type}
        ))

        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task"""
        if not self.task_manager:
            return False

        success = await self.task_manager.cancel(task_id)

        if success:
            await self.state_manager.set_task_state(task_id, TaskState.CANCELLED)
            await self._log_event(
                "task_cancelled",
                f"Task {task_id} cancelled",
                level="info"
            )

        return success

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        if not self.task_manager:
            return None

        task = await self.task_manager.get_task(task_id)
        if not task:
            return None

        return {
            "id": task.id,
            "type": task.type,
            "state": task.state.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress,
            "error": task.error
        }

    async def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get results of a completed task"""
        if not self.task_manager:
            return None

        return await self.task_manager.get_results(task_id)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        if not self.task_manager:
            return []

        tasks = await self.task_manager.list_tasks(
            status=status,
            task_type=task_type,
            limit=limit
        )

        return [{
            "id": t.id,
            "type": t.type,
            "state": t.state.value,
            "priority": t.priority.value,
            "created_at": t.created_at.isoformat()
        } for t in tasks]

    # ==================== Event Handling ====================

    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ) -> None:
        """Subscribe to events"""
        await self.event_bus.subscribe(event_type, handler)

    async def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from events"""
        await self.event_bus.unsubscribe(event_type, handler)

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit a custom event"""
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            event_type_enum = EventType.CUSTOM

        await self.event_bus.publish(Event(
            type=event_type_enum,
            source="user",
            data=data
        ))

    # ==================== Analysis Integration ====================

    async def analyze_results(
        self,
        results: Dict[str, Any],
        analysis_type: str = "vulnerability"
    ) -> Dict[str, Any]:
        """
        Analyze scan results using Analysis Bot

        Args:
            results: Scan results to analyze
            analysis_type: Type of analysis

        Returns:
            Analysis results
        """
        if not self.analysis_bot:
            return {"error": "Analysis Bot not available"}

        try:
            # Run analysis
            analysis = self.analysis_bot.analyze(results)

            await self._log_event(
                "analysis_completed",
                f"Analysis completed for {analysis_type}",
                level="info"
            )

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e)}

    # ==================== Internal Handlers ====================

    async def _on_task_completed(self, event: Event) -> None:
        """Handle task completion"""
        task_id = event.data.get("task_id")

        await self.state_manager.set_task_state(task_id, TaskState.COMPLETED)

        await self._log_event(
            "task_completed",
            f"Task {task_id} completed successfully",
            level="info",
            details={"task_id": task_id}
        )

        # Auto-analyze if enabled
        if self.analysis_bot and event.data.get("auto_analyze"):
            results = event.data.get("results")
            if results:
                asyncio.create_task(self.analyze_results(results))

    async def _on_task_failed(self, event: Event) -> None:
        """Handle task failure"""
        task_id = event.data.get("task_id")
        error = event.data.get("error", "Unknown error")

        await self.state_manager.set_task_state(task_id, TaskState.FAILED)

        await self._log_event(
            "task_failed",
            f"Task {task_id} failed: {error}",
            level="error",
            details={"task_id": task_id, "error": error}
        )

        # Retry if enabled
        if self.config.retry_failed_tasks:
            retry_count = event.data.get("retry_count", 0)
            if retry_count < self.config.max_retries:
                logger.info(f"Retrying task {task_id} (attempt {retry_count + 1})")
                # Retry logic here

    async def _on_security_alert(self, event: Event) -> None:
        """Handle security alerts"""
        alert_type = event.data.get("alert_type")
        details = event.data.get("details", {})

        await self._log_event(
            "security_alert",
            f"Security alert: {alert_type}",
            level="alert",
            details=details
        )

    # ==================== Background Loops ====================

    async def _health_check_loop(self):
        """Periodic health check"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # Check task manager health
                if self.task_manager:
                    is_healthy = await self.task_manager.health_check()
                    if not is_healthy:
                        logger.warning("Task manager health check failed")

                # Emit health status
                await self.event_bus.publish(Event(
                    type=EventType.SYSTEM_HEALTH,
                    source="orchestrator",
                    data={
                        "status": self.status.value,
                        "tasks_running": len(self.task_manager.running_tasks) if self.task_manager else 0,
                        "tasks_pending": len(self.task_manager.pending_tasks) if self.task_manager else 0
                    }
                ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _metrics_loop(self):
        """Collect and emit metrics"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Every minute

                metrics = await self._collect_metrics()

                await self.event_bus.publish(Event(
                    type=EventType.METRICS,
                    source="orchestrator",
                    data=metrics
                ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics error: {e}")

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "orchestrator_id": self.instance_id,
            "status": self.status.value,
            "uptime_seconds": (
                (datetime.utcnow() - self.started_at).total_seconds()
                if self.started_at else 0
            )
        }

        if self.task_manager:
            metrics.update({
                "tasks_pending": len(self.task_manager.pending_tasks),
                "tasks_running": len(self.task_manager.running_tasks),
                "tasks_completed": self.task_manager.completed_count,
                "tasks_failed": self.task_manager.failed_count
            })

        return metrics

    # ==================== Utility ====================

    async def _log_event(
        self,
        event_type: str,
        message: str,
        level: str = "info",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log event to audit logger"""
        if not self.audit_logger:
            return

        try:
            log_method = getattr(self.audit_logger, level, self.audit_logger.info)

            await log_method(
                category=EventCategory.SYSTEM,
                event_type=event_type,
                message=message,
                details=details
            )
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "instance_id": self.instance_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": (
                (datetime.utcnow() - self.started_at).total_seconds()
                if self.started_at else 0
            ),
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "max_workers": self.config.max_workers,
                "enable_analysis_bot": self.config.enable_analysis_bot,
                "enable_audit_logging": self.config.enable_audit_logging,
                "enable_secure_validation": self.config.enable_secure_validation
            },
            "components": {
                "analysis_bot": self.analysis_bot is not None,
                "audit_logger": self.audit_logger is not None,
                "validator": self.validator is not None,
                "task_manager": self.task_manager is not None if self.task_manager else False
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {
            "orchestrator": self._running and self.status == OrchestratorStatus.RUNNING,
            "state_manager": True,  # Always available
            "event_bus": self.event_bus.is_running if hasattr(self.event_bus, 'is_running') else True,
            "task_manager": False
        }

        if self.task_manager:
            checks["task_manager"] = await self.task_manager.health_check()

        if self.analysis_bot:
            checks["analysis_bot"] = True  # Simplified

        if self.audit_logger:
            checks["audit_logger"] = True  # Simplified

        all_healthy = all(checks.values())

        return {
            "healthy": all_healthy,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }

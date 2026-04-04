"""
Enhanced Workflow Orchestrator with Load Balancing
Coordinates all components for 100+ concurrent agent support
"""

import asyncio
import atexit
import logging
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from state.state_manager import get_state_manager

from agents.agent_pool_manager import AgentInstance, get_pool_manager
from core.celery_app import send_task_with_priority
from core.circuit_breaker import CircuitBreakerRegistry
from core.config import AgentState, TaskPriority, TaskStatus, get_config
from orchestrator.task_distributor import get_task_distributor
from tools.tool_executor import get_tool_executor

logger = logging.getLogger(__name__)
config = get_config()

# Global registry for cleanup
_orchestrators: Set[weakref.ref] = set()


def _cleanup_orchestrators():
    """Cleanup all orchestrators at program exit"""
    for ref in list(_orchestrators):
        orchestrator = ref()
        if orchestrator is not None:
            try:
                asyncio.get_event_loop().run_until_complete(orchestrator.shutdown())
            except Exception:
                pass
    _orchestrators.clear()


atexit.register(_cleanup_orchestrators)


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowDefinition:
    """Workflow definition"""

    workflow_id: str
    name: str
    description: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WorkflowExecution:
    """Active workflow execution"""

    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    agent_id: Optional[str] = None
    current_task_index: int = 0
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class OrchestratorMetrics:
    """Orchestrator performance metrics"""

    active_workflows: int = 0
    completed_workflows: int = 0
    failed_workflows: int = 0
    active_tasks: int = 0
    queued_tasks: int = 0
    average_task_duration: float = 0.0
    system_load: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EnhancedOrchestrator:
    """
    Enhanced workflow orchestrator supporting 100+ concurrent agents
    Coordinates task distribution, agent management, and tool execution
    """

    def __init__(self):
        self.state_manager = None
        self.pool_manager = None
        self.task_distributor = None
        self.tool_executor = None

        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self._workflow_callbacks: List[Callable] = []
        self._metrics = OrchestratorMetrics()
        self._metrics_history: List[OrchestratorMetrics] = []

        self._running = False
        self._lock = asyncio.Lock()
        self._orchestrator_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the orchestrator and all subsystems"""
        logger.info("Initializing Enhanced Orchestrator...")

        # Initialize all subsystems
        self.state_manager = await get_state_manager()
        self.pool_manager = await get_pool_manager()
        self.task_distributor = await get_task_distributor()
        self.tool_executor = await get_tool_executor()

        self._running = True

        # Start background tasks
        self._orchestrator_task = asyncio.create_task(self._orchestrator_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())
        self._recovery_task = asyncio.create_task(self._recovery_loop())

        # Register for cleanup
        _orchestrators.add(weakref.ref(self))

        logger.info("Enhanced Orchestrator initialized successfully")

    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        if not self._running:
            return

        logger.info("Shutting down Enhanced Orchestrator...")
        self._running = False

        # Cancel background tasks
        for task in [
            self._orchestrator_task,
            self._metrics_task,
            self._recovery_task,
        ]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Remove from registry
        for ref in list(_orchestrators):
            if ref() is self:
                _orchestrators.discard(ref)
                break

        # Shutdown subsystems
        await self.task_distributor.shutdown()
        await self.pool_manager.shutdown()
        await self.tool_executor.shutdown()
        await self.state_manager.close()

        logger.info("Enhanced Orchestrator shutdown complete")

    # Workflow Management

    async def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """Register a new workflow"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.name} ({workflow.workflow_id})")
        return workflow.workflow_id

    async def start_workflow(
        self,
        workflow_id: str,
        agent_id: Optional[str] = None,
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Start a workflow execution"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        execution_id = f"wf-exec-{workflow_id}-{int(datetime.now(timezone.utc).timestamp())}"

        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            agent_id=agent_id,
            started_at=datetime.now(timezone.utc),
        )

        async with self._lock:
            self.active_executions[execution_id] = execution

        # If agent specified, assign workflow
        if agent_id:
            agent = await self.pool_manager.get_agent(agent_id)
            if agent and agent.is_available:
                await self._assign_workflow_to_agent(execution, agent)
            else:
                # Queue for later assignment
                await self._queue_workflow(execution)
        else:
            # Find available agent
            agent = await self.pool_manager.get_available_agent()
            if agent:
                await self._assign_workflow_to_agent(execution, agent)
            else:
                await self._queue_workflow(execution)

        logger.info(f"Started workflow execution: {execution_id}")
        return execution_id

    async def _assign_workflow_to_agent(self, execution: WorkflowExecution, agent: AgentInstance):
        """Assign a workflow to an agent"""
        execution.status = WorkflowStatus.RUNNING
        execution.agent_id = agent.agent_id

        # Update agent state
        await self.state_manager.set_agent_state(
            agent.agent_id,
            AgentState.BUSY,
            metadata={"workflow_execution_id": execution.execution_id},
        )

        # Submit first task
        await self._submit_next_task(execution)

    async def _queue_workflow(self, execution: WorkflowExecution):
        """Queue workflow for later execution"""
        execution.status = WorkflowStatus.PENDING

        # Send to Celery for delayed processing
        send_task_with_priority(
            "orchestrator.tasks.process_workflow",
            args=(execution.execution_id,),
            priority=TaskPriority.NORMAL,
        )

    async def _submit_next_task(self, execution: WorkflowExecution):
        """Submit the next task in a workflow"""
        workflow = self.workflows.get(execution.workflow_id)
        if not workflow:
            return

        # Get next task
        if execution.current_task_index >= len(workflow.tasks):
            # Workflow complete
            await self._complete_workflow(execution)
            return

        task_def = workflow.tasks[execution.current_task_index]

        # Check dependencies
        task_id = task_def.get("task_id")
        dependencies = workflow.dependencies.get(task_id, [])

        for dep in dependencies:
            if dep not in execution.completed_tasks:
                # Dependency not met, wait
                return

        # Submit task
        task_type = task_def.get("type", "default")
        payload = task_def.get("payload", {})
        priority = TaskPriority(task_def.get("priority", 2))
        capabilities = task_def.get("required_capabilities", [])

        task_id = await self.task_distributor.submit_task(
            task_type=task_type,
            payload=payload,
            priority=priority,
            required_capabilities=capabilities,
        )

        # Track task in execution
        execution.current_task_index += 1

        logger.info(f"Submitted task {task_id} for workflow {execution.execution_id}")

    async def _complete_workflow(self, execution: WorkflowExecution):
        """Complete a workflow execution"""
        execution.status = WorkflowStatus.COMPLETED
        execution.completed_at = datetime.now(timezone.utc)

        # Release agent
        if execution.agent_id:
            await self.state_manager.set_agent_state(execution.agent_id, AgentState.IDLE)

        # Notify callbacks
        await self._notify_workflow_callbacks(execution)

        logger.info(f"Completed workflow execution: {execution.execution_id}")

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a workflow execution"""
        async with self._lock:
            execution = self.active_executions.get(execution_id)
            if not execution:
                return False

            execution.status = WorkflowStatus.CANCELLED

            # Release agent
            if execution.agent_id:
                await self.state_manager.set_agent_state(execution.agent_id, AgentState.IDLE)

            return True

    async def get_workflow_status(self, execution_id: str) -> Optional[Dict]:
        """Get workflow execution status"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return None

        return {
            "execution_id": execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "agent_id": execution.agent_id,
            "progress": {
                "current": execution.current_task_index,
                "completed": len(execution.completed_tasks),
                "failed": len(execution.failed_tasks),
            },
            "started_at": (execution.started_at.isoformat() if execution.started_at else None),
            "completed_at": (execution.completed_at.isoformat() if execution.completed_at else None),
            "error_message": execution.error_message,
        }

    # Background Loops

    async def _orchestrator_loop(self):
        """Main orchestration loop"""
        while self._running:
            try:
                await asyncio.sleep(5)
                await self._process_pending_workflows()
                await self._check_task_completions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")

    async def _process_pending_workflows(self):
        """Process pending workflows waiting for agents"""
        pending = [e for e in self.active_executions.values() if e.status == WorkflowStatus.PENDING]

        for execution in pending:
            agent = await self.pool_manager.get_available_agent()
            if agent:
                await self._assign_workflow_to_agent(execution, agent)

    async def _check_task_completions(self):
        """Check for completed tasks and advance workflows"""
        running = [e for e in self.active_executions.values() if e.status == WorkflowStatus.RUNNING]

        for execution in running:
            # Check last task status
            workflow = self.workflows.get(execution.workflow_id)
            if not workflow:
                continue

            if execution.current_task_index > 0:
                last_task = workflow.tasks[execution.current_task_index - 1]
                task_id = last_task.get("task_id")

                # Get task status
                task_status = await self.task_distributor.get_task_status(task_id)
                if task_status:
                    status = task_status.get("status")

                    if status == TaskStatus.COMPLETED.value:
                        execution.completed_tasks.append(task_id)
                        execution.results[task_id] = task_status.get("result")
                        await self._submit_next_task(execution)

                    elif status in [
                        TaskStatus.FAILED.value,
                        TaskStatus.TIMEOUT.value,
                    ]:
                        execution.failed_tasks.append(task_id)
                        # Handle failure based on workflow configuration
                        await self._handle_task_failure(execution, task_id, task_status)

    async def _handle_task_failure(self, execution: WorkflowExecution, task_id: str, task_status: Dict):
        """Handle task failure in workflow"""
        workflow = self.workflows.get(execution.workflow_id)

        # Check if workflow should continue or fail
        continue_on_failure = workflow.metadata.get("continue_on_failure", False)
        max_failures = workflow.metadata.get("max_failures", 1)

        if len(execution.failed_tasks) >= max_failures and not continue_on_failure:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = f"Task {task_id} failed: {task_status.get('error_message')}"
            execution.completed_at = datetime.now(timezone.utc)

            # Release agent
            if execution.agent_id:
                await self.state_manager.set_agent_state(execution.agent_id, AgentState.IDLE)
        else:
            # Continue with next task
            await self._submit_next_task(execution)

    async def _metrics_loop(self):
        """Collect metrics periodically"""
        while self._running:
            try:
                await asyncio.sleep(60)
                await self._update_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")

    async def _update_metrics(self):
        """Update orchestrator metrics"""
        async with self._lock:
            pool_metrics = await self.pool_manager.get_metrics()
            distributor_metrics = await self.task_distributor.get_metrics()

            self._metrics = OrchestratorMetrics(
                active_workflows=sum(1 for e in self.active_executions.values() if e.status == WorkflowStatus.RUNNING),
                completed_workflows=sum(1 for e in self.active_executions.values() if e.status == WorkflowStatus.COMPLETED),
                failed_workflows=sum(1 for e in self.active_executions.values() if e.status == WorkflowStatus.FAILED),
                active_tasks=pool_metrics.busy_agents,
                queued_tasks=distributor_metrics.tasks_queued,
                system_load=pool_metrics.average_load,
            )

            self._metrics_history.append(self._metrics)

            if len(self._metrics_history) > 60:
                self._metrics_history.pop(0)

    async def _recovery_loop(self):
        """Handle system recovery and cleanup"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Recover stale agents
                recovered = await self.state_manager.recover_stale_agents()
                if recovered:
                    logger.info(f"Recovery: Recovered {len(recovered)} stale agents")

                # Clean up completed workflows
                await self._cleanup_workflows()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")

    async def _cleanup_workflows(self):
        """Clean up old completed workflows"""
        cutoff = datetime.now(timezone.utc) - __import__("datetime").timedelta(hours=24)

        async with self._lock:
            to_remove = [
                eid
                for eid, exec in self.active_executions.items()
                if exec.status
                in [
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.FAILED,
                    WorkflowStatus.CANCELLED,
                ]
                and exec.completed_at
                and exec.completed_at < cutoff
            ]

            for eid in to_remove:
                del self.active_executions[eid]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old workflow executions")

    async def _notify_workflow_callbacks(self, execution: WorkflowExecution):
        """Notify registered workflow callbacks"""
        for callback in self._workflow_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(execution))
                else:
                    callback(execution)
            except Exception as e:
                logger.error(f"Workflow callback failed: {e}")

    # Public API

    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        required_capabilities: List[str] = None,
    ) -> str:
        """Submit a standalone task"""
        return await self.task_distributor.submit_task(
            task_type=task_type,
            payload=payload,
            priority=priority,
            required_capabilities=required_capabilities,
        )

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        pool_metrics = await self.pool_manager.get_metrics()
        distributor_metrics = await self.task_distributor.get_metrics()
        system_health = await self.state_manager.get_system_health()
        circuit_status = CircuitBreakerRegistry.get_all_status()

        return {
            "agents": {
                "total": pool_metrics.total_agents,
                "idle": pool_metrics.idle_agents,
                "busy": pool_metrics.busy_agents,
                "unhealthy": pool_metrics.unhealthy_agents,
                "load": pool_metrics.average_load,
            },
            "tasks": {
                "submitted": distributor_metrics.tasks_submitted,
                "routed": distributor_metrics.tasks_routed,
                "queued": distributor_metrics.tasks_queued,
                "failed": distributor_metrics.tasks_failed,
                "average_routing_time_ms": distributor_metrics.average_routing_time_ms,
            },
            "workflows": {
                "active": self._metrics.active_workflows,
                "completed": self._metrics.completed_workflows,
                "failed": self._metrics.failed_workflows,
            },
            "system_health": system_health,
            "circuit_breakers": circuit_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def get_metrics(self) -> OrchestratorMetrics:
        """Get current orchestrator metrics"""
        return self._metrics

    async def get_metrics_history(self) -> List[OrchestratorMetrics]:
        """Get historical metrics"""
        return self._metrics_history

    def register_workflow_callback(self, callback: Callable):
        """Register a callback for workflow events"""
        self._workflow_callbacks.append(callback)

    async def scale_agents(self, count: int) -> int:
        """Manually scale agents up or down"""
        if count > 0:
            return await self.pool_manager.force_scale_up(count)
        else:
            return await self.pool_manager.force_scale_down(abs(count))


# Global orchestrator instance
_orchestrator: Optional[EnhancedOrchestrator] = None


async def get_orchestrator() -> EnhancedOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator

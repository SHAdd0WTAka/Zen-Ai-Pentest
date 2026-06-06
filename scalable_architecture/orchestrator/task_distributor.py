"""
Task Distributor with Priority Queues and Load Balancing
Routes tasks to optimal agents based on capabilities, load, and priority
"""

import asyncio
import atexit
import logging
import uuid
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from state.state_manager import get_state_manager

from agents.agent_pool_manager import get_pool_manager
from core.celery_app import send_task_with_priority
from core.config import TaskPriority, TaskStatus, get_config

logger = logging.getLogger(__name__)
config = get_config()

# Global registry for cleanup
_task_distributors: Set[weakref.ref] = set()


def _cleanup_task_distributors():
    """Cleanup all task distributors at program exit"""
    for ref in list(_task_distributors):
        distributor = ref()
        if distributor is not None:
            try:
                asyncio.get_event_loop().run_until_complete(distributor.shutdown())
            except Exception:
                pass
    _task_distributors.clear()


atexit.register(_cleanup_task_distributors)


class RoutingStrategy(Enum):
    """Task routing strategies"""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_MATCH = "capability_match"
    PRIORITY_BASED = "priority_based"
    WEIGHTED = "weighted"


@dataclass
class TaskDefinition:
    """Task definition with all routing information"""

    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    required_capabilities: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: int = 3600
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "required_capabilities": self.required_capabilities,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": (self.scheduled_at.isoformat() if self.scheduled_at else None),
            "expires_at": (self.expires_at.isoformat() if self.expires_at else None),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskDefinition":
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            payload=data["payload"],
            priority=TaskPriority(data.get("priority", 2)),
            required_capabilities=data.get("required_capabilities", []),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 3600),
            created_at=(datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc)),
            scheduled_at=(datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None),
            expires_at=(datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None),
            metadata=data.get("metadata", {}),
        )


@dataclass
class RoutingDecision:
    """Result of a routing decision"""

    task_id: str
    agent_id: Optional[str]
    strategy_used: RoutingStrategy
    estimated_wait_time: float
    reason: str
    alternative_agents: List[str] = field(default_factory=list)


@dataclass
class DistributorMetrics:
    """Task distributor metrics"""

    tasks_submitted: int = 0
    tasks_routed: int = 0
    tasks_queued: int = 0
    tasks_failed: int = 0
    average_routing_time_ms: float = 0.0
    queue_depths: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TaskDistributor:
    """
    Distributes tasks to agents with intelligent routing and load balancing
    Supports 100+ concurrent agents with multiple routing strategies
    """

    def __init__(self):
        self.state_manager = None
        self.pool_manager = None
        self._routing_strategies: Dict[RoutingStrategy, Callable] = {}
        self._strategy_weights: Dict[RoutingStrategy, float] = {
            RoutingStrategy.CAPABILITY_MATCH: 0.4,
            RoutingStrategy.LEAST_LOADED: 0.3,
            RoutingStrategy.PRIORITY_BASED: 0.2,
            RoutingStrategy.ROUND_ROBIN: 0.1,
        }
        self._round_robin_index = 0
        self._pending_tasks: Dict[str, TaskDefinition] = {}
        self._task_callbacks: Dict[str, List[Callable]] = {}
        self._metrics = DistributorMetrics()
        self._metrics_history: List[DistributorMetrics] = []
        self._lock = asyncio.Lock()
        self._running = False
        self._distributor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Register routing strategies
        self._register_strategies()

    def _register_strategies(self):
        """Register available routing strategies"""
        self._routing_strategies = {
            RoutingStrategy.ROUND_ROBIN: self._route_round_robin,
            RoutingStrategy.LEAST_LOADED: self._route_least_loaded,
            RoutingStrategy.CAPABILITY_MATCH: self._route_capability_match,
            RoutingStrategy.PRIORITY_BASED: self._route_priority_based,
            RoutingStrategy.WEIGHTED: self._route_weighted,
        }

    async def initialize(self):
        """Initialize the task distributor"""
        logger.info("Initializing Task Distributor...")

        self.state_manager = await get_state_manager()
        self.pool_manager = await get_pool_manager()

        self._running = True

        # Start background tasks
        self._distributor_task = asyncio.create_task(self._distributor_loop())
        self._metrics_task = asyncio.create_task(self._metrics_loop())

        # Register for cleanup
        _task_distributors.add(weakref.ref(self))

        logger.info("Task Distributor initialized successfully")

    async def shutdown(self):
        """Gracefully shutdown the task distributor"""
        if not self._running:
            return

        logger.info("Shutting down Task Distributor...")
        self._running = False

        for task in [self._distributor_task, self._metrics_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Remove from registry
        for ref in list(_task_distributors):
            if ref() is self:
                _task_distributors.discard(ref)
                break

        logger.info("Task Distributor shutdown complete")

    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        required_capabilities: List[str] = None,
        max_retries: int = None,
        timeout: int = None,
        scheduled_at: Optional[datetime] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Submit a new task for distribution

        Args:
            task_type: Type of task to execute
            payload: Task-specific data
            priority: Task priority level
            required_capabilities: Required agent capabilities
            max_retries: Maximum retry attempts
            timeout: Task timeout in seconds
            scheduled_at: When to schedule the task
            task_id: Optional custom task ID

        Returns:
            Task ID
        """
        task_id = task_id or f"task-{uuid.uuid4().hex[:12]}"

        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            required_capabilities=required_capabilities or [],
            max_retries=max_retries or config.task_queue.max_retries,
            timeout=timeout or config.task_queue.task_timeout,
            scheduled_at=scheduled_at,
        )

        async with self._lock:
            self._pending_tasks[task_id] = task
            self._metrics.tasks_submitted += 1

        # Create task state in database
        await self.state_manager.set_task_state(task_id, TaskStatus.PENDING)

        logger.info(f"Task {task_id} submitted with priority {priority.name}")

        # Notify callbacks
        await self._notify_task_callbacks(task_id, "submitted", task.to_dict())

        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or queued task"""
        async with self._lock:
            task = self._pending_tasks.pop(task_id, None)

        if task:
            await self.state_manager.set_task_state(task_id, TaskStatus.CANCELLED)
            logger.info(f"Task {task_id} cancelled")
            return True

        return False

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task"""
        # Check pending tasks
        async with self._lock:
            if task_id in self._pending_tasks:
                return {
                    "task_id": task_id,
                    "status": TaskStatus.PENDING.value,
                    "task": self._pending_tasks[task_id].to_dict(),
                }

        # Check database
        task_state = await self.state_manager.get_task_state(task_id)
        if task_state:
            return {
                "task_id": task_id,
                "status": task_state.status.value,
                "agent_id": task_state.agent_id,
                "result": task_state.result,
                "error_message": task_state.error_message,
                "started_at": (task_state.started_at.isoformat() if task_state.started_at else None),
                "completed_at": (task_state.completed_at.isoformat() if task_state.completed_at else None),
            }

        return None

    async def _distributor_loop(self):
        """Main distribution loop"""
        while self._running:
            try:
                await asyncio.sleep(1)  # Process every second
                await self._process_pending_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Distributor loop error: {e}")

    async def _process_pending_tasks(self):
        """Process all pending tasks"""
        tasks_to_process = []

        async with self._lock:
            now = datetime.now(timezone.utc)
            for task_id, task in list(self._pending_tasks.items()):
                # Check if task is ready to be processed
                if task.scheduled_at and task.scheduled_at > now:
                    continue

                # Check if task has expired
                if task.expires_at and task.expires_at < now:
                    await self.state_manager.set_task_state(
                        task_id,
                        TaskStatus.FAILED,
                        error_message="Task expired before processing",
                    )
                    del self._pending_tasks[task_id]
                    continue

                tasks_to_process.append((task_id, task))

        # Sort by priority (lower value = higher priority)
        tasks_to_process.sort(key=lambda x: x[1].priority.value)

        # Process tasks
        for task_id, task in tasks_to_process:
            try:
                await self._route_task(task)
            except Exception as e:
                logger.error(f"Failed to route task {task_id}: {e}")
                self._metrics.tasks_failed += 1

    async def _route_task(self, task: TaskDefinition):
        """Route a single task to an appropriate agent"""
        start_time = datetime.now(timezone.utc)

        # Select routing strategy
        strategy = self._select_routing_strategy(task)

        # Execute routing
        route_func = self._routing_strategies.get(strategy, self._route_weighted)
        decision = await route_func(task)

        routing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._metrics.average_routing_time_ms = (
            self._metrics.average_routing_time_ms * self._metrics.tasks_routed + routing_time
        ) / (self._metrics.tasks_routed + 1)

        if decision.agent_id:
            # Direct routing to agent
            success = await self._assign_to_agent(task, decision.agent_id)
            if success:
                async with self._lock:
                    self._pending_tasks.pop(task.task_id, None)
                    self._metrics.tasks_routed += 1
                return

        # Fallback to Celery queue
        await self._queue_to_celery(task)

        async with self._lock:
            self._pending_tasks.pop(task.task_id, None)
            self._metrics.tasks_queued += 1

    def _select_routing_strategy(self, task: TaskDefinition) -> RoutingStrategy:
        """Select the best routing strategy for a task"""
        if task.required_capabilities:
            return RoutingStrategy.CAPABILITY_MATCH
        elif task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            return RoutingStrategy.PRIORITY_BASED
        else:
            return RoutingStrategy.WEIGHTED

    # Routing Strategy Implementations

    async def _route_round_robin(self, task: TaskDefinition) -> RoutingDecision:
        """Route using round-robin strategy"""
        agents = await self.pool_manager.get_all_agents()
        available = [a for a in agents if a.is_available]

        if not available:
            return RoutingDecision(
                task_id=task.task_id,
                agent_id=None,
                strategy_used=RoutingStrategy.ROUND_ROBIN,
                estimated_wait_time=10.0,
                reason="No available agents",
            )

        # Select using round-robin
        agent = available[self._round_robin_index % len(available)]
        self._round_robin_index = (self._round_robin_index + 1) % len(available)

        return RoutingDecision(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            strategy_used=RoutingStrategy.ROUND_ROBIN,
            estimated_wait_time=0.0,
            reason="Round-robin selection",
            alternative_agents=[a.agent_id for a in available if a.agent_id != agent.agent_id],
        )

    async def _route_least_loaded(self, task: TaskDefinition) -> RoutingDecision:
        """Route to the least loaded agent"""
        agent = await self.pool_manager.get_available_agent(task.required_capabilities)

        if agent:
            return RoutingDecision(
                task_id=task.task_id,
                agent_id=agent.agent_id,
                strategy_used=RoutingStrategy.LEAST_LOADED,
                estimated_wait_time=0.0,
                reason="Least loaded agent selected",
            )

        return RoutingDecision(
            task_id=task.task_id,
            agent_id=None,
            strategy_used=RoutingStrategy.LEAST_LOADED,
            estimated_wait_time=15.0,
            reason="No available agents matching requirements",
        )

    async def _route_capability_match(self, task: TaskDefinition) -> RoutingDecision:
        """Route based on capability matching"""
        agents = await self.pool_manager.get_all_agents()

        # Score agents based on capability match
        scored_agents = []
        for agent in agents:
            if not agent.is_available:
                continue

            score = 0
            if task.required_capabilities:
                matched = sum(1 for cap in task.required_capabilities if cap in agent.capabilities)
                score = matched / len(task.required_capabilities)
            else:
                score = 1.0

            # Factor in load
            score = score * (1.0 / (1 + agent.task_count * 0.1))

            scored_agents.append((agent, score))

        if scored_agents:
            scored_agents.sort(key=lambda x: x[1], reverse=True)
            best_agent = scored_agents[0][0]

            return RoutingDecision(
                task_id=task.task_id,
                agent_id=best_agent.agent_id,
                strategy_used=RoutingStrategy.CAPABILITY_MATCH,
                estimated_wait_time=0.0,
                reason=f"Best capability match: {scored_agents[0][1]:.2f}",
                alternative_agents=[a[0].agent_id for a in scored_agents[1:3]],
            )

        return RoutingDecision(
            task_id=task.task_id,
            agent_id=None,
            strategy_used=RoutingStrategy.CAPABILITY_MATCH,
            estimated_wait_time=20.0,
            reason="No agents with required capabilities",
        )

    async def _route_priority_based(self, task: TaskDefinition) -> RoutingDecision:
        """Route based on task priority"""
        # For high priority tasks, try multiple strategies
        if task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            # First try capability match
            decision = await self._route_capability_match(task)
            if decision.agent_id:
                return decision

            # Then try least loaded
            decision = await self._route_least_loaded(task)
            if decision.agent_id:
                return decision

        # Fall back to round-robin
        return await self._route_round_robin(task)

    async def _route_weighted(self, task: TaskDefinition) -> RoutingDecision:
        """Route using weighted combination of strategies"""
        strategies = list(self._strategy_weights.keys())
        [self._strategy_weights[s] for s in strategies]

        # Try strategies in weighted order
        for strategy in strategies:
            route_func = self._routing_strategies.get(strategy)
            if route_func:
                decision = await route_func(task)
                if decision.agent_id:
                    decision.strategy_used = RoutingStrategy.WEIGHTED
                    return decision

        return RoutingDecision(
            task_id=task.task_id,
            agent_id=None,
            strategy_used=RoutingStrategy.WEIGHTED,
            estimated_wait_time=30.0,
            reason="All routing strategies failed",
        )

    async def _assign_to_agent(self, task: TaskDefinition, agent_id: str) -> bool:
        """Assign task directly to an agent"""
        try:
            # Update task state
            await self.state_manager.set_task_state(task.task_id, TaskStatus.ASSIGNED, agent_id=agent_id)

            # Assign to agent in pool manager
            success = await self.pool_manager.assign_task(agent_id, task.task_id)
            if not success:
                return False

            # Send task to agent via Celery
            send_task_with_priority(
                "agents.agent_tasks.execute_task",
                args=(task.task_id, task.task_type, task.payload),
                kwargs={"timeout": task.timeout},
                priority=task.priority,
            )

            logger.info(f"Task {task.task_id} assigned to agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to assign task {task.task_id} to agent {agent_id}: {e}")
            return False

    async def _queue_to_celery(self, task: TaskDefinition):
        """Queue task to Celery for later processing"""
        await self.state_manager.set_task_state(task.task_id, TaskStatus.QUEUED)

        # Send to Celery with appropriate priority queue
        send_task_with_priority(
            "orchestrator.tasks.process_task",
            args=(task.to_dict(),),
            priority=task.priority,
            countdown=0,
        )

        logger.info(f"Task {task.task_id} queued to Celery")

    async def _metrics_loop(self):
        """Collect metrics periodically"""
        while self._running:
            try:
                await asyncio.sleep(60)

                async with self._lock:
                    self._metrics.timestamp = datetime.now(timezone.utc)
                    self._metrics_history.append(self._metrics)

                    # Reset counters
                    self._metrics = DistributorMetrics(queue_depths=self._metrics.queue_depths.copy())

                    # Keep only last 60 minutes
                    if len(self._metrics_history) > 60:
                        self._metrics_history.pop(0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")

    async def _notify_task_callbacks(self, task_id: str, event: str, data: dict):
        """Notify registered callbacks for task events"""
        callbacks = self._task_callbacks.get(task_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(task_id, event, data))
                else:
                    callback(task_id, event, data)
            except Exception as e:
                logger.error(f"Task callback failed: {e}")

    # Public API

    async def register_task_callback(self, task_id: str, callback: Callable):
        """Register a callback for task events"""
        if task_id not in self._task_callbacks:
            self._task_callbacks[task_id] = []
        self._task_callbacks[task_id].append(callback)

    async def get_metrics(self) -> DistributorMetrics:
        """Get current distributor metrics"""
        return self._metrics

    async def get_metrics_history(self) -> List[DistributorMetrics]:
        """Get historical metrics"""
        return self._metrics_history

    async def get_pending_tasks(self) -> List[TaskDefinition]:
        """Get all pending tasks"""
        async with self._lock:
            return list(self._pending_tasks.values())


# Global task distributor instance
_distributor: Optional[TaskDistributor] = None


async def get_task_distributor() -> TaskDistributor:
    """Get or create global task distributor instance"""
    global _distributor
    if _distributor is None:
        _distributor = TaskDistributor()
        await _distributor.initialize()
    return _distributor

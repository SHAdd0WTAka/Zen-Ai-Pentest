#!/usr/bin/env python3
"""
Zen-AI-Pentest Agent Coordinator
Erweiterter Agent-Koordinator für Multi-Agent-Orchestrierung.

Author: Zen-AI-Pentest Team
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("ZenAI.Orchestrator.AgentCoordinator")


class AgentType(Enum):
    """Agent-Typen für Pentesting"""

    RECON = "reconnaissance"
    SCANNER = "scanner"
    EXPLOIT = "exploitation"
    POST_EXPLOIT = "post_exploitation"
    ANALYSIS = "analysis"
    REPORTER = "reporter"
    COORDINATOR = "coordinator"
    CUSTOM = "custom"


class AgentState(Enum):
    """Agent-Zustände"""

    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"
    ERROR = "error"


class MessageType(Enum):
    """Nachrichtentypen"""

    COMMAND = "command"
    RESULT = "result"
    EVENT = "event"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    BROADCAST = "broadcast"
    DIRECT = "direct"


@dataclass
class AgentMessage:
    """Nachricht zwischen Agents"""

    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    msg_type: MessageType = MessageType.DIRECT
    sender_id: str = ""
    recipient_id: str = ""  # "*" für Broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1-5, höher = wichtiger
    correlation_id: Optional[str] = None
    ttl: int = 300  # Time-to-live in Sekunden


@dataclass
class AgentCapability:
    """Fähigkeit eines Agents"""

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Informationen über einen Agent"""

    agent_id: str
    agent_type: AgentType
    name: str
    state: AgentState = AgentState.INITIALIZING
    capabilities: List[AgentCapability] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    task_count: int = 0
    success_rate: float = 1.0
    current_task: Optional[str] = None


@dataclass
class TaskAssignment:
    """Task-Zuweisung an Agent"""

    task_id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    assigned_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    priority: int = 1


class Agent(ABC):
    """Abstrakter Base-Agent"""

    def __init__(self, agent_id: str, agent_type: AgentType, name: str, capabilities: List[AgentCapability] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.capabilities = capabilities or []
        self.state = AgentState.INITIALIZING
        self.info = AgentInfo(agent_id=agent_id, agent_type=agent_type, name=name, capabilities=self.capabilities)

        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._coordinator: Optional["AgentCoordinator"] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._current_task: Optional[TaskAssignment] = None

        # Callbacks
        self._message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self._state_change_handlers: List[Callable] = []

    async def register_with_coordinator(self, coordinator: "AgentCoordinator"):
        """Registriere beim Koordinator"""
        self._coordinator = coordinator
        await coordinator.register_agent(self)
        self.state = AgentState.IDLE
        logger.info(f"[Agent:{self.name}] Registriert beim Koordinator")

    async def start(self):
        """Starte Agent"""
        self._running = True
        self._task = asyncio.create_task(self._main_loop())
        logger.info(f"[Agent:{self.name}] Gestartet")

    async def stop(self):
        """Stoppe Agent"""
        self._running = False
        self.state = AgentState.SHUTTING_DOWN

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._coordinator:
            await self._coordinator.unregister_agent(self.agent_id)

        logger.info(f"[Agent:{self.name}] Gestoppt")

    async def send_message(self, recipient_id: str, msg_type: MessageType, payload: Dict[str, Any], priority: int = 1):
        """Sende Nachricht"""
        if self._coordinator:
            msg = AgentMessage(
                msg_type=msg_type, sender_id=self.agent_id, recipient_id=recipient_id, payload=payload, priority=priority
            )
            await self._coordinator.route_message(msg)

    async def broadcast(self, msg_type: MessageType, payload: Dict[str, Any], priority: int = 1):
        """Broadcast Nachricht an alle Agents"""
        await self.send_message("*", msg_type, payload, priority)

    def on_message(self, msg_type: MessageType):
        """Decorator für Message-Handler"""

        def decorator(func: Callable):
            self._message_handlers[msg_type].append(func)
            return func

        return decorator

    def on_state_change(self, func: Callable):
        """Decorator für State-Change-Handler"""
        self._state_change_handlers.append(func)
        return func

    async def _main_loop(self):
        """Haupt-Loop des Agents"""
        while self._running:
            try:
                # Verarbeite Nachrichten
                try:
                    msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                    await self._handle_message(msg)
                except asyncio.TimeoutError:
                    pass

                # Verarbeite Tasks
                if self.state == AgentState.IDLE:
                    try:
                        task = self._task_queue.get_nowait()
                        await self._execute_task(task)
                    except asyncio.QueueEmpty:
                        pass

                # Sende Heartbeat
                await self._send_heartbeat()

            except Exception as e:
                logger.error(f"[Agent:{self.name}] Fehler im Haupt-Loop: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, msg: AgentMessage):
        """Verarbeite eingehende Nachricht"""
        handlers = self._message_handlers.get(msg.msg_type, [])

        for handler in handlers:
            try:
                await handler(msg)
            except Exception as e:
                logger.error(f"[Agent:{self.name}] Handler-Fehler: {e}")

    async def _execute_task(self, task: TaskAssignment):
        """Führe Task aus"""
        self.state = AgentState.BUSY
        self._current_task = task
        self.info.current_task = task.task_id

        try:
            result = await self.execute(task)

            # Sende Ergebnis
            await self.send_message(
                recipient_id="coordinator",
                msg_type=MessageType.RESULT,
                payload={"task_id": task.task_id, "status": "success", "result": result},
            )

            self.info.task_count += 1

        except Exception as e:
            logger.error(f"[Agent:{self.name}] Task-Fehler: {e}")

            await self.send_message(
                recipient_id="coordinator", msg_type=MessageType.ERROR, payload={"task_id": task.task_id, "error": str(e)}
            )

            self.info.success_rate = max(0, self.info.success_rate - 0.1)

        finally:
            self.state = AgentState.IDLE
            self._current_task = None
            self.info.current_task = None

    async def _send_heartbeat(self):
        """Sende Heartbeat"""
        if self._coordinator:
            await self._coordinator.update_agent_status(
                self.agent_id, state=self.state, current_task=self._current_task.task_id if self._current_task else None
            )

    @abstractmethod
    async def execute(self, task: TaskAssignment) -> Any:
        """Führe Task aus - muss implementiert werden"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """Hole Agent-Fähigkeiten"""
        pass


class AgentCoordinator:
    """
    Erweiterter Agent-Koordinator für Zen-AI-Pentest

    Features:
    - Agent-Registrierung und -Verwaltung
    - Nachrichten-Routing
    - Task-Zuweisung
    - Capability-Matching
    - Workflow-Orchestrierung
    - Event-Broadcasting
    """

    def __init__(self, max_concurrent_tasks: int = 100, heartbeat_timeout: int = 60):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.heartbeat_timeout = heartbeat_timeout

        # Agent-Verwaltung
        self._agents: Dict[str, Agent] = {}
        self._agent_info: Dict[str, AgentInfo] = {}
        self._agents_by_type: Dict[AgentType, Set[str]] = defaultdict(set)
        self._agent_lock = asyncio.Lock()

        # Nachrichten
        self._message_router: Dict[str, asyncio.Queue] = {}
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()

        # Tasks
        self._task_assignments: Dict[str, TaskAssignment] = {}
        self._pending_tasks: asyncio.Queue = asyncio.Queue()
        self._task_results: Dict[str, Any] = {}

        # Workflows
        self._workflows: Dict[str, Dict] = {}
        self._workflow_executions: Dict[str, Dict] = {}

        # Event-Bus
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: deque = deque(maxlen=1000)

        # Monitoring
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._stats = {
            "messages_routed": 0,
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "agents_registered": 0,
            "agents_disconnected": 0,
        }

        logger.info("[AgentCoordinator] Initialisiert")

    async def start(self):
        """Starte Koordinator"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("[AgentCoordinator] Gestartet")

    async def stop(self):
        """Stoppe Koordinator"""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Stoppe alle Agents
        async with self._agent_lock:
            for agent in list(self._agents.values()):
                await agent.stop()

        logger.info("[AgentCoordinator] Gestoppt")

    # === Agent Management ===

    async def register_agent(self, agent: Agent) -> bool:
        """Registriere einen Agent"""
        async with self._agent_lock:
            if agent.agent_id in self._agents:
                logger.warning(f"[AgentCoordinator] Agent {agent.agent_id} bereits registriert")
                return False

            self._agents[agent.agent_id] = agent
            self._agent_info[agent.agent_id] = agent.info
            self._agents_by_type[agent.agent_type].add(agent.agent_id)
            self._message_router[agent.agent_id] = asyncio.Queue()

            self._stats["agents_registered"] += 1

            logger.info(f"[AgentCoordinator] Agent {agent.name} ({agent.agent_id}) registriert")

            # Broadcast Event
            await self._broadcast_event("agent_registered", {"agent_id": agent.agent_id, "agent_type": agent.agent_type.value})

            return True

    async def unregister_agent(self, agent_id: str) -> bool:
        """Entferne einen Agent"""
        async with self._agent_lock:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]

            del self._agents[agent_id]
            del self._agent_info[agent_id]
            self._agents_by_type[agent.agent_type].discard(agent_id)

            if agent_id in self._message_router:
                del self._message_router[agent_id]

            self._stats["agents_disconnected"] += 1

            logger.info(f"[AgentCoordinator] Agent {agent_id} entfernt")

            # Broadcast Event
            await self._broadcast_event("agent_unregistered", {"agent_id": agent_id})

            return True

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Hole Agent"""
        async with self._agent_lock:
            return self._agents.get(agent_id)

    async def get_agents_by_type(self, agent_type: AgentType) -> List[Agent]:
        """Hole Agents nach Typ"""
        async with self._agent_lock:
            return [self._agents[aid] for aid in self._agents_by_type.get(agent_type, []) if aid in self._agents]

    async def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[AgentInfo]:
        """Hole verfügbare Agents"""
        async with self._agent_lock:
            agents = []
            for aid, info in self._agent_info.items():
                if info.state == AgentState.IDLE:
                    if agent_type is None or info.agent_type == agent_type:
                        agents.append(info)
            return agents

    async def update_agent_status(self, agent_id: str, state: Optional[AgentState] = None, current_task: Optional[str] = None):
        """Aktualisiere Agent-Status"""
        async with self._agent_lock:
            if agent_id in self._agent_info:
                info = self._agent_info[agent_id]
                if state:
                    info.state = state
                if current_task:
                    info.current_task = current_task
                info.last_seen = datetime.now()

    # === Message Routing ===

    async def route_message(self, msg: AgentMessage):
        """Route Nachricht zum Empfänger"""
        self._stats["messages_routed"] += 1

        # Prüfe TTL
        if (datetime.now() - msg.timestamp).total_seconds() > msg.ttl:
            logger.debug(f"[AgentCoordinator] Nachricht {msg.msg_id} abgelaufen")
            return

        if msg.recipient_id == "*":
            # Broadcast
            await self._broadcast_message(msg)
        elif msg.recipient_id == "coordinator":
            # An Koordinator
            await self._handle_coordinator_message(msg)
        else:
            # Direkte Nachricht
            await self._send_direct_message(msg)

    async def _broadcast_message(self, msg: AgentMessage):
        """Broadcast Nachricht an alle Agents"""
        async with self._agent_lock:
            for agent_id in self._agents:
                if agent_id != msg.sender_id:
                    await self._message_router[agent_id].put(msg)

    async def _send_direct_message(self, msg: AgentMessage):
        """Sende direkte Nachricht"""
        if msg.recipient_id in self._message_router:
            await self._message_router[msg.recipient_id].put(msg)
        else:
            logger.warning(f"[AgentCoordinator] Empfänger {msg.recipient_id} nicht gefunden")

    async def _handle_coordinator_message(self, msg: AgentMessage):
        """Verarbeite Nachricht an Koordinator"""
        if msg.msg_type == MessageType.RESULT:
            # Task-Ergebnis
            task_id = msg.payload.get("task_id")
            if task_id:
                self._task_results[task_id] = msg.payload
                self._stats["tasks_completed"] += 1

                await self._broadcast_event("task_completed", {"task_id": task_id, "status": "success"})

        elif msg.msg_type == MessageType.ERROR:
            # Task-Fehler
            task_id = msg.payload.get("task_id")
            if task_id:
                self._stats["tasks_failed"] += 1

                await self._broadcast_event("task_failed", {"task_id": task_id, "error": msg.payload.get("error")})

    # === Task Assignment ===

    async def assign_task(
        self,
        agent_type: AgentType,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 1,
        timeout: Optional[int] = None,
        preferred_agents: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Weise Task einem Agent zu

        Returns:
            task_id oder None bei Fehler
        """
        # Finde verfügbaren Agent
        available = await self.get_available_agents(agent_type)

        if preferred_agents:
            available = [a for a in available if a.agent_id in preferred_agents]

        if not available:
            # Queue für später
            task_id = str(uuid.uuid4())[:12]
            await self._pending_tasks.put(
                {
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "task_type": task_type,
                    "parameters": parameters,
                    "priority": priority,
                }
            )
            logger.info(f"[AgentCoordinator] Task {task_id} in Warteschlange")
            return task_id

        # Wähle besten Agent (einfache Heuristik)
        best_agent = min(available, key=lambda a: a.task_count)

        task_id = str(uuid.uuid4())[:12]
        assignment = TaskAssignment(
            task_id=task_id,
            agent_id=best_agent.agent_id,
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            deadline=datetime.now() + timedelta(seconds=timeout) if timeout else None,
        )

        # Sende Task an Agent
        agent = self._agents.get(best_agent.agent_id)
        if agent:
            await agent._task_queue.put(assignment)
            self._task_assignments[task_id] = assignment
            self._stats["tasks_assigned"] += 1

            logger.info(f"[AgentCoordinator] Task {task_id} an {best_agent.agent_id} zugewiesen")
            return task_id

        return None

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Warte auf Task-Abschluss"""
        start = datetime.now()

        while True:
            if task_id in self._task_results:
                return self._task_results[task_id]

            if timeout:
                elapsed = (datetime.now() - start).total_seconds()
                if elapsed > timeout:
                    return None

            await asyncio.sleep(0.5)

    # === Capability Matching ===

    async def find_agents_with_capability(
        self, capability_name: str, required_params: Optional[Dict] = None
    ) -> List[AgentInfo]:
        """Finde Agents mit bestimmter Fähigkeit"""
        matching = []

        async with self._agent_lock:
            for info in self._agent_info.values():
                for cap in info.capabilities:
                    if cap.name == capability_name:
                        if required_params:
                            # Prüfe Parameter-Kompatibilität
                            if all(param in cap.parameters for param in required_params.keys()):
                                matching.append(info)
                        else:
                            matching.append(info)

        return matching

    # === Workflow Orchestration ===

    async def define_workflow(self, workflow_id: str, steps: List[Dict[str, Any]]):
        """Definiere einen Workflow"""
        self._workflows[workflow_id] = {"steps": steps, "created_at": datetime.now()}
        logger.info(f"[AgentCoordinator] Workflow {workflow_id} definiert")

    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> str:
        """Führe Workflow aus"""
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow {workflow_id} nicht definiert")

        execution_id = str(uuid.uuid4())[:12]
        self._workflows[workflow_id]

        self._workflow_executions[execution_id] = {
            "workflow_id": workflow_id,
            "context": context,
            "status": "running",
            "current_step": 0,
            "results": {},
            "started_at": datetime.now(),
        }

        # Starte Workflow-Execution
        asyncio.create_task(self._run_workflow(execution_id))

        logger.info(f"[AgentCoordinator] Workflow {workflow_id} gestartet (exec={execution_id})")
        return execution_id

    async def _run_workflow(self, execution_id: str):
        """Führe Workflow-Schritte aus"""
        execution = self._workflow_executions[execution_id]
        workflow = self._workflows[execution["workflow_id"]]

        try:
            for i, step in enumerate(workflow["steps"]):
                execution["current_step"] = i

                step_type = step.get("type")

                if step_type == "task":
                    # Weise Task zu
                    task_id = await self.assign_task(
                        agent_type=AgentType(step["agent_type"]),
                        task_type=step["task_type"],
                        parameters={**step.get("parameters", {}), **execution["context"]},
                        priority=step.get("priority", 1),
                    )

                    if task_id:
                        result = await self.wait_for_task(task_id, timeout=step.get("timeout", 300))
                        execution["results"][step.get("name", f"step_{i}")] = result

                elif step_type == "parallel":
                    # Parallele Tasks
                    tasks = []
                    for sub_step in step.get("steps", []):
                        task_id = await self.assign_task(
                            agent_type=AgentType(sub_step["agent_type"]),
                            task_type=sub_step["task_type"],
                            parameters={**sub_step.get("parameters", {}), **execution["context"]},
                            priority=sub_step.get("priority", 1),
                        )
                        if task_id:
                            tasks.append(task_id)

                    # Warte auf alle
                    results = await asyncio.gather(
                        *[self.wait_for_task(tid, timeout=step.get("timeout", 300)) for tid in tasks]
                    )
                    execution["results"][step.get("name", f"step_{i}")] = results

                elif step_type == "condition":
                    # Bedingte Ausführung
                    condition = step.get("condition")
                    if self._evaluate_condition(condition, execution["results"]):
                        # Führe Then-Branch aus
                        pass

                elif step_type == "event":
                    # Sende Event
                    await self._broadcast_event(step.get("event_name"), step.get("event_data", {}))

            execution["status"] = "completed"
            execution["completed_at"] = datetime.now()

        except Exception as e:
            logger.error(f"[AgentCoordinator] Workflow-Fehler: {e}")
            execution["status"] = "failed"
            execution["error"] = str(e)

    def _evaluate_condition(self, condition: str, results: Dict) -> bool:
        """Evaluiere Bedingung"""
        try:
            # Einfache Bedingungsauswertung
            return eval(condition, {"results": results, "__builtins__": {}})  # nosec B307
        except Exception:
            return False

    # === Event Bus ===

    async def subscribe(self, event_type: str, handler: Callable):
        """Abonniere Event-Typ"""
        self._event_handlers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: Callable):
        """Deabonniere Event-Typ"""
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)

    async def _broadcast_event(self, event_type: str, data: Dict):
        """Broadcast Event"""
        event = {"type": event_type, "data": data, "timestamp": datetime.now().isoformat()}

        self._event_history.append(event)

        # Rufe Handler auf
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"[AgentCoordinator] Event-Handler-Fehler: {e}")

    # === Monitoring ===

    async def _monitor_loop(self):
        """Monitoring-Loop"""
        while self._running:
            try:
                # Prüfe Agent-Health
                await self._check_agent_health()

                # Verarbeite pending Tasks
                await self._process_pending_tasks()

                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[AgentCoordinator] Monitor-Fehler: {e}")
                await asyncio.sleep(5)

    async def _check_agent_health(self):
        """Prüfe Agent-Health"""
        async with self._agent_lock:
            current_time = datetime.now()

            for agent_id, info in list(self._agent_info.items()):
                elapsed = (current_time - info.last_seen).total_seconds()

                if elapsed > self.heartbeat_timeout:
                    logger.warning(f"[AgentCoordinator] Agent {agent_id} timeout")
                    info.state = AgentState.OFFLINE

    async def _process_pending_tasks(self):
        """Verarbeite wartende Tasks"""
        while not self._pending_tasks.empty():
            try:
                pending = self._pending_tasks.get_nowait()

                # Versuche erneute Zuweisung
                task_id = await self.assign_task(
                    agent_type=pending["agent_type"],
                    task_type=pending["task_type"],
                    parameters=pending["parameters"],
                    priority=pending["priority"],
                )

                if task_id == pending["task_id"]:
                    # Noch nicht zugewiesen, zurück in Queue
                    await self._pending_tasks.put(pending)
                    break

            except asyncio.QueueEmpty:
                break

    async def get_stats(self) -> Dict[str, Any]:
        """Hole Koordinator-Statistiken"""
        async with self._agent_lock:
            return {
                **self._stats,
                "agents_online": len([a for a in self._agent_info.values() if a.state != AgentState.OFFLINE]),
                "agents_idle": len([a for a in self._agent_info.values() if a.state == AgentState.IDLE]),
                "agents_busy": len([a for a in self._agent_info.values() if a.state == AgentState.BUSY]),
                "pending_tasks": self._pending_tasks.qsize(),
                "active_workflows": len([w for w in self._workflow_executions.values() if w["status"] == "running"]),
            }


# Singleton-Instanz
_default_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """Hole globale Coordinator-Instanz"""
    global _default_coordinator
    if _default_coordinator is None:
        _default_coordinator = AgentCoordinator()
    return _default_coordinator

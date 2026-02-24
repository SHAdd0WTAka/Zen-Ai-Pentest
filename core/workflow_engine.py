#!/usr/bin/env python3
"""
Zen-Ai-Pentest Workflow Engine
==============================
Eine flexible Workflow-Engine für Pentest-Automatisierung.

Features:
- Workflow-Definition (YAML/JSON/Dict)
- State-Management Integration
- Conditional Logic
- Parallel Execution
- Error Handling & Retry Logic
- Event-Driven Architecture
"""

import asyncio
import logging
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

# Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkflowEngine")


class TaskStatus(Enum):
    """Status eines Workflow-Tasks"""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()
    SKIPPED = auto()
    CANCELLED = auto()


class WorkflowStatus(Enum):
    """Status eines Workflows"""

    CREATED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class TaskResult:
    """Ergebnis eines Task-Executions"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class TaskState:
    """Zustand eines einzelnen Tasks"""

    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.name,
            "result": self.result.to_dict() if self.result else None,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class WorkflowState:
    """Zustand eines kompletten Workflows"""

    workflow_id: str
    name: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.name,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
        }


class Task(ABC):
    """Abstrakte Basisklasse für alle Workflow-Tasks"""

    def __init__(
        self,
        name: str,
        task_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        parallel: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.task_id = task_id or f"{name}_{uuid.uuid4().hex[:8]}"
        self.dependencies = dependencies or []
        self.condition = condition
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.parallel = parallel
        self.metadata = metadata or {}

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> TaskResult:
        """Führt den Task aus - muss von Subklassen implementiert werden"""
        pass

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Prüft ob der Task ausgeführt werden soll (Conditional Logic)"""
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception as e:
            logger.warning(
                f"Condition evaluation failed for task {self.name}: {e}"
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task_id": self.task_id,
            "dependencies": self.dependencies,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "parallel": self.parallel,
            "metadata": self.metadata,
        }


class FunctionTask(Task):
    """Task der eine Funktion ausführt"""

    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        **task_kwargs,
    ):
        super().__init__(name, **task_kwargs)
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}

    async def execute(self, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        try:
            # Kontext in kwargs mergen
            merged_kwargs = {**self.kwargs, "context": context}

            # Funktion ausführen (sync oder async)
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*self.args, **merged_kwargs)
            else:
                # Sync-Funktion in ThreadPool ausführen
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as pool:
                    result = await loop.run_in_executor(
                        pool, lambda: self.func(*self.args, **merged_kwargs)
                    )

            execution_time = time.time() - start_time
            return TaskResult(
                success=True, data=result, execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={"traceback": traceback.format_exc()},
            )


class SubWorkflowTask(Task):
    """Task der einen Sub-Workflow ausführt"""

    def __init__(self, name: str, workflow: "Workflow", **task_kwargs):
        super().__init__(name, **task_kwargs)
        self.sub_workflow = workflow

    async def execute(self, context: Dict[str, Any]) -> TaskResult:
        engine = WorkflowEngine()
        result = await engine.execute_workflow(self.sub_workflow, context)

        return TaskResult(
            success=result.status == WorkflowStatus.COMPLETED,
            data=result.to_dict(),
            metadata={"sub_workflow_id": result.workflow_id},
        )


class Workflow:
    """Workflow Definition"""

    def __init__(
        self,
        name: str,
        workflow_id: Optional[str] = None,
        description: str = "",
        version: str = "1.0.0",
    ):
        self.name = name
        self.workflow_id = workflow_id or f"workflow_{uuid.uuid4().hex[:8]}"
        self.description = description
        self.version = version
        self.tasks: Dict[str, Task] = {}
        self.task_order: List[str] = []

    def add_task(self, task: Task) -> "Workflow":
        """Fügt einen Task zum Workflow hinzu"""
        self.tasks[task.task_id] = task
        if task.task_id not in self.task_order:
            self.task_order.append(task.task_id)
        return self

    def add_tasks(self, *tasks: Task) -> "Workflow":
        """Fügt mehrere Tasks hinzu"""
        for task in tasks:
            self.add_task(task)
        return self

    def get_task(self, task_id: str) -> Optional[Task]:
        """Holt einen Task nach ID"""
        return self.tasks.get(task_id)

    def get_dependencies(self, task_id: str) -> List[str]:
        """Holt alle Dependencies eines Tasks"""
        task = self.tasks.get(task_id)
        return task.dependencies if task else []

    def get_execution_order(self) -> List[List[str]]:
        """
        Berechnet die Ausführungsreihenfolge mit parallelen Gruppen.
        Returns: Liste von Task-Gruppen die parallel ausgeführt werden können
        """
        executed = set()
        pending = set(self.tasks.keys())
        execution_groups = []

        while pending:
            # Finde alle Tasks deren Dependencies erfüllt sind
            ready = []
            for task_id in pending:
                task = self.tasks[task_id]
                deps_satisfied = all(
                    dep in executed or dep not in self.tasks
                    for dep in task.dependencies
                )
                if deps_satisfied:
                    ready.append(task_id)

            if not ready:
                # Zyklische Abhängigkeit oder fehlende Dependencies
                raise ValueError(
                    f"Cannot resolve dependencies for tasks: {pending}"
                )

            execution_groups.append(ready)
            executed.update(ready)
            pending -= set(ready)

        return execution_groups

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "workflow_id": self.workflow_id,
            "description": self.description,
            "version": self.version,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "task_order": self.task_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Erstellt einen Workflow aus einem Dictionary"""
        workflow = cls(
            name=data["name"],
            workflow_id=data.get("workflow_id"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
        )
        # Tasks müssen extern hinzugefügt werden
        return workflow


class EventBus:
    """Event-Bus für Workflow-Events"""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable):
        """Registriert einen Event-Listener"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        """Entfernt einen Event-Listener"""
        if event in self._listeners:
            self._listeners[event] = [
                cb for cb in self._listeners[event] if cb != callback
            ]

    async def emit(self, event: str, data: Any = None):
        """Emitted ein Event"""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event}: {e}")


class WorkflowEngine:
    """
    Haupt-Workflow-Engine

    Verwaltet die Ausführung von Workflows mit:
    - State Management
    - Conditional Logic
    - Parallel Execution
    - Error Handling & Retry
    """

    def __init__(
        self,
        max_parallel_tasks: int = 10,
        state_manager: Optional["StateManager"] = None,
    ):
        self.max_parallel_tasks = max_parallel_tasks
        self.state_manager = state_manager
        self.event_bus = EventBus()
        self._running_workflows: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_parallel_tasks)

    def on(self, event: str, callback: Callable):
        """Registriert einen Event-Listener"""
        self.event_bus.on(event, callback)
        return self

    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
    ) -> WorkflowState:
        """
        Führt einen Workflow aus

        Args:
            workflow: Der auszuführende Workflow
            initial_context: Initialer Kontext für den Workflow
            workflow_id: Optionale Workflow-ID (für Wiederaufnahme)

        Returns:
            Der finale Workflow-State
        """
        workflow_id = (
            workflow_id or f"{workflow.workflow_id}_{uuid.uuid4().hex[:8]}"
        )

        # State initialisieren oder laden
        if self.state_manager and await self.state_manager.exists(workflow_id):
            state = await self.state_manager.load(workflow_id)
            logger.info(f"Resumed workflow {workflow_id}")
        else:
            state = WorkflowState(
                workflow_id=workflow_id,
                name=workflow.name,
                context=initial_context or {},
                tasks={
                    task_id: TaskState(
                        task_id=task_id,
                        name=workflow.tasks[task_id].name,
                        dependencies=workflow.tasks[task_id].dependencies,
                        max_retries=workflow.tasks[task_id].max_retries,
                    )
                    for task_id in workflow.tasks
                },
            )

        state.status = WorkflowStatus.RUNNING
        state.started_at = datetime.now()

        await self.event_bus.emit("workflow.started", state)

        try:
            # Berechne Ausführungsreihenfolge
            execution_groups = workflow.get_execution_order()

            for group in execution_groups:
                # Prüfe auf Abbruch
                if state.status == WorkflowStatus.CANCELLED:
                    break

                # Führe Tasks in der Gruppe aus
                if len(group) == 1:
                    # Einzelner Task - sequentiell
                    await self._execute_single_task(workflow, state, group[0])
                else:
                    # Mehrere Tasks - parallel
                    await self._execute_parallel_tasks(workflow, state, group)

                # State speichern
                if self.state_manager:
                    await self.state_manager.save(state)

            # Finaler Status
            failed_tasks = [
                t
                for t in state.tasks.values()
                if t.status == TaskStatus.FAILED
            ]

            if state.status == WorkflowStatus.CANCELLED:
                pass  # Bereits gesetzt
            elif failed_tasks:
                state.status = WorkflowStatus.FAILED
                state.error_message = f"{len(failed_tasks)} task(s) failed"
            else:
                state.status = WorkflowStatus.COMPLETED

            state.completed_at = datetime.now()

        except Exception as e:
            state.status = WorkflowStatus.FAILED
            state.error_message = str(e)
            state.completed_at = datetime.now()
            logger.error(f"Workflow {workflow_id} failed: {e}")

        await self.event_bus.emit("workflow.completed", state)

        if self.state_manager:
            await self.state_manager.save(state)

        return state

    async def _execute_single_task(
        self, workflow: Workflow, state: WorkflowState, task_id: str
    ):
        """Führt einen einzelnen Task aus"""
        task = workflow.tasks[task_id]
        task_state = state.tasks[task_id]

        # Prüfe Condition
        if not task.should_execute(state.context):
            task_state.status = TaskStatus.SKIPPED
            await self.event_bus.emit("task.skipped", task_state)
            return

        # Führe Task mit Retry-Logik aus
        await self._execute_task_with_retry(task, task_state, state)

    async def _execute_parallel_tasks(
        self, workflow: Workflow, state: WorkflowState, task_ids: List[str]
    ):
        """Führt mehrere Tasks parallel aus"""
        tasks_to_run = []

        for task_id in task_ids:
            task = workflow.tasks[task_id]
            task_state = state.tasks[task_id]

            if task.should_execute(state.context):
                tasks_to_run.append(
                    self._execute_task_with_retry(task, task_state, state)
                )
            else:
                task_state.status = TaskStatus.SKIPPED

        if tasks_to_run:
            await asyncio.gather(*tasks_to_run, return_exceptions=True)

    async def _execute_task_with_retry(
        self, task: Task, task_state: TaskState, workflow_state: WorkflowState
    ):
        """Führt einen Task mit Retry-Logik aus"""
        async with self._semaphore:
            task_state.status = TaskStatus.RUNNING
            task_state.started_at = datetime.now()

            await self.event_bus.emit("task.started", task_state)

            for attempt in range(task.max_retries + 1):
                try:
                    # Timeout-Handling
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.execute(workflow_state.context),
                            timeout=task.timeout,
                        )
                    else:
                        result = await task.execute(workflow_state.context)

                    task_state.result = result
                    task_state.retry_count = attempt

                    if result.success:
                        task_state.status = TaskStatus.COMPLETED

                        # Ergebnis in Kontext speichern (wenn konfiguriert)
                        if task.metadata.get("save_to_context"):
                            key = task.metadata.get("context_key", task.name)
                            workflow_state.context[key] = result.data

                        await self.event_bus.emit("task.completed", task_state)
                        break
                    else:
                        raise Exception(result.error or "Task failed")

                except asyncio.TimeoutError:
                    result = TaskResult(
                        success=False,
                        error=f"Task timeout after {task.timeout}s",
                    )
                    task_state.result = result

                    if attempt < task.max_retries:
                        task_state.status = TaskStatus.RETRYING
                        await self.event_bus.emit("task.retrying", task_state)
                        await asyncio.sleep(task.retry_delay * (attempt + 1))
                    else:
                        task_state.status = TaskStatus.FAILED
                        await self.event_bus.emit("task.failed", task_state)

                except Exception as e:
                    result = TaskResult(
                        success=False,
                        error=str(e),
                        metadata={"traceback": traceback.format_exc()},
                    )
                    task_state.result = result

                    if attempt < task.max_retries:
                        task_state.status = TaskStatus.RETRYING
                        await self.event_bus.emit("task.retrying", task_state)
                        await asyncio.sleep(task.retry_delay * (attempt + 1))
                    else:
                        task_state.status = TaskStatus.FAILED
                        await self.event_bus.emit("task.failed", task_state)

            task_state.completed_at = datetime.now()

    async def cancel_workflow(self, workflow_id: str):
        """Bricht einen laufenden Workflow ab"""
        if workflow_id in self._running_workflows:
            self._running_workflows[workflow_id].cancel()
            await self.event_bus.emit(
                "workflow.cancelled", {"workflow_id": workflow_id}
            )

    def create_workflow_from_config(self, config: Dict[str, Any]) -> Workflow:
        """Erstellt einen Workflow aus einer Konfiguration"""
        workflow = Workflow.from_dict(config)

        # Tasks aus Konfiguration erstellen
        for task_config in config.get("tasks", []):
            task_type = task_config.get("type", "function")

            if task_type == "function":
                # Funktion muss registriert sein
                func_name = task_config["function"]
                func = self._get_registered_function(func_name)

                task = FunctionTask(
                    name=task_config["name"],
                    func=func,
                    args=task_config.get("args", []),
                    kwargs=task_config.get("kwargs", {}),
                    task_id=task_config.get("task_id"),
                    dependencies=task_config.get("dependencies", []),
                    max_retries=task_config.get("max_retries", 3),
                    retry_delay=task_config.get("retry_delay", 1.0),
                    timeout=task_config.get("timeout"),
                    parallel=task_config.get("parallel", False),
                    metadata=task_config.get("metadata", {}),
                )
                workflow.add_task(task)

        return workflow

    def _get_registered_function(self, name: str) -> Callable:
        """Holt eine registrierte Funktion"""
        # Diese Methode sollte erweitert werden
        raise NotImplementedError(f"Function {name} not found")


class StateManager(ABC):
    """Abstrakte Basisklasse für State-Management"""

    @abstractmethod
    async def save(self, state: WorkflowState) -> bool:
        """Speichert einen Workflow-State"""
        pass

    @abstractmethod
    async def load(self, workflow_id: str) -> Optional[WorkflowState]:
        """Lädt einen Workflow-State"""
        pass

    @abstractmethod
    async def exists(self, workflow_id: str) -> bool:
        """Prüft ob ein Workflow-State existiert"""
        pass

    @abstractmethod
    async def delete(self, workflow_id: str) -> bool:
        """Löscht einen Workflow-State"""
        pass

    @abstractmethod
    async def list_workflows(
        self, status: Optional[WorkflowStatus] = None
    ) -> List[str]:
        """Listet alle Workflow-IDs auf"""
        pass


# Decorator für Task-Registrierung
def task(
    name: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    condition: Optional[Callable] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None,
    parallel: bool = False,
    save_to_context: bool = False,
    context_key: Optional[str] = None,
):
    """Decorator für Task-Funktionen"""

    def decorator(func: Callable) -> FunctionTask:
        task_name = name or func.__name__
        return FunctionTask(
            name=task_name,
            func=func,
            dependencies=dependencies,
            condition=condition,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            parallel=parallel,
            metadata={
                "save_to_context": save_to_context,
                "context_key": context_key or task_name,
            },
        )

    return decorator


# Beispiel-Workflow-Definition als Dictionary
EXAMPLE_WORKFLOW_CONFIG = {
    "name": "Pentest Scan Workflow",
    "description": "Automatisierte Pentest-Scan-Sequenz",
    "version": "1.0.0",
    "tasks": [
        {
            "name": "target_validation",
            "type": "function",
            "function": "validate_target",
            "task_id": "validate",
            "max_retries": 1,
            "save_to_context": True,
            "context_key": "target_info",
        },
        {
            "name": "port_scan",
            "type": "function",
            "function": "nmap_scan",
            "task_id": "portscan",
            "dependencies": ["validate"],
            "max_retries": 2,
            "timeout": 300,
            "save_to_context": True,
            "context_key": "open_ports",
        },
        {
            "name": "service_detection",
            "type": "function",
            "function": "detect_services",
            "task_id": "services",
            "dependencies": ["portscan"],
            "parallel": True,
            "save_to_context": True,
        },
        {
            "name": "vulnerability_scan",
            "type": "function",
            "function": "vuln_scan",
            "task_id": "vulnscan",
            "dependencies": ["services"],
            "condition": "context.get('open_ports', [])",
            "timeout": 600,
            "save_to_context": True,
        },
    ],
}


if __name__ == "__main__":
    # Demo-Code
    print("Zen-Ai-Pentest Workflow Engine")
    print("=" * 40)

    # Beispiel-Tasks definieren
    async def demo_task_1(context):
        print("Executing demo_task_1")
        await asyncio.sleep(0.5)
        return {"result": "task1_complete"}

    async def demo_task_2(context):
        print("Executing demo_task_2")
        await asyncio.sleep(0.5)
        return {"result": "task2_complete"}

    async def demo_task_3(context):
        print("Executing demo_task_3")
        await asyncio.sleep(0.5)
        return {"result": "task3_complete"}

    # Workflow erstellen
    workflow = Workflow("Demo Workflow")

    task1 = FunctionTask(
        name="task1",
        func=demo_task_1,
        task_id="t1",
        metadata={"save_to_context": True, "context_key": "task1"},
    )

    task2 = FunctionTask(
        name="task2",
        func=demo_task_2,
        task_id="t2",
        dependencies=["t1"],
        parallel=True,
    )

    task3 = FunctionTask(
        name="task3",
        func=demo_task_3,
        task_id="t3",
        dependencies=["t1"],
        parallel=True,
    )

    workflow.add_tasks(task1, task2, task3)

    # Engine erstellen und Workflow ausführen
    async def main():
        engine = WorkflowEngine()

        # Event-Listener
        engine.on(
            "workflow.started", lambda s: print(f"Workflow started: {s.name}")
        )
        engine.on(
            "workflow.completed",
            lambda s: print(f"Workflow completed: {s.status}"),
        )
        engine.on(
            "task.completed", lambda s: print(f"Task completed: {s.name}")
        )

        result = await engine.execute_workflow(
            workflow, {"target": "example.com"}
        )
        print(f"\nFinal result: {result.to_dict()}")

    asyncio.run(main())

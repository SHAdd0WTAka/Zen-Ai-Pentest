"""
ZenOrchestrator - Core Orchestration System

The heart of Zen-AI-Pentest. Coordinates all components:
- Task scheduling and execution
- State management
- Event bus for component communication
- Integration with Analysis Bot, Audit Logger, Secure Validator
- Multi-agent coordination

Usage:
    from orchestrator import ZenOrchestrator

    orchestrator = ZenOrchestrator()
    await orchestrator.start()

    task_id = await orchestrator.submit_task({
        "type": "vulnerability_scan",
        "target": "example.com"
    })
"""

from .core import OrchestratorConfig, ZenOrchestrator
from .events import Event, EventBus, EventType
from .integration import ComponentRegistry
from .state import StateManager, TaskState
from .tasks import Task, TaskManager, TaskPriority

__all__ = [
    "ZenOrchestrator",
    "OrchestratorConfig",
    "StateManager",
    "TaskState",
    "EventBus",
    "Event",
    "EventType",
    "TaskManager",
    "Task",
    "TaskPriority",
    "ComponentRegistry",
]

__version__ = "1.0.0"

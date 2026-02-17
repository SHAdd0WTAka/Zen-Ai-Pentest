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

from .core import ZenOrchestrator, OrchestratorConfig
from .state import StateManager, TaskState
from .events import EventBus, Event, EventType
from .tasks import TaskManager, Task, TaskPriority
from .integration import ComponentRegistry

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

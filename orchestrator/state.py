"""
State Management System

Manages state across all orchestrator components with:
- Distributed state storage
- State transitions with validation
- Persistence and recovery
- State snapshots
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import hashlib


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


class SystemState(Enum):
    """Overall system states"""
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class StateSnapshot:
    """Immutable state snapshot"""
    id: str
    timestamp: datetime
    task_states: Dict[str, str]
    system_state: str
    metadata: Dict[str, Any]
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for integrity"""
        data = json.dumps({
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "task_states": self.task_states,
            "system_state": self.system_state,
            "metadata": self.metadata
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify snapshot integrity"""
        return self.checksum == self._calculate_checksum()


class StateManager:
    """
    Manages state for the orchestrator and all tasks

    Features:
    - In-memory state storage with optional persistence
    - State transition validation
    - Automatic snapshots
    - State recovery

    Example:
        state_manager = StateManager()

        # Set task state
        await state_manager.set_task_state("task-123", TaskState.RUNNING)

        # Get task state
        state = await state_manager.get_task_state("task-123")

        # Create snapshot
        snapshot = await state_manager.create_snapshot()
    """

    # Valid state transitions
    VALID_TRANSITIONS = {
        TaskState.PENDING: [TaskState.QUEUED, TaskState.CANCELLED],
        TaskState.QUEUED: [TaskState.RUNNING, TaskState.CANCELLED],
        TaskState.RUNNING: [TaskState.PAUSED, TaskState.COMPLETED, TaskState.FAILED, TaskState.TIMEOUT],
        TaskState.PAUSED: [TaskState.RUNNING, TaskState.CANCELLED],
        TaskState.FAILED: [TaskState.RETRYING, TaskState.CANCELLED],
        TaskState.RETRYING: [TaskState.QUEUED, TaskState.FAILED],
        TaskState.COMPLETED: [],  # Terminal state
        TaskState.CANCELLED: [],  # Terminal state
        TaskState.TIMEOUT: [TaskState.RETRYING, TaskState.FAILED],
    }

    def __init__(self, persistence_enabled: bool = False):
        self.persistence_enabled = persistence_enabled

        # State storage
        self._task_states: Dict[str, TaskState] = {}
        self._task_data: Dict[str, Dict[str, Any]] = {}
        self._system_state = SystemState.INITIALIZING
        self._system_metadata: Dict[str, Any] = {}

        # History
        self._state_history: List[Dict[str, Any]] = []
        self._snapshots: List[StateSnapshot] = []
        self._max_history = 10000
        self._max_snapshots = 100

        # Locks
        self._lock = asyncio.Lock()

        # Statistics
        self._state_changes = 0
        self._transition_errors = 0

    # ==================== Task State Management ====================

    async def set_task_state(
        self,
        task_id: str,
        new_state: TaskState,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> bool:
        """
        Set task state with transition validation

        Args:
            task_id: Task identifier
            new_state: New state to set
            metadata: Optional state metadata
            force: Force transition even if invalid

        Returns:
            True if state was changed
        """
        async with self._lock:
            current_state = self._task_states.get(task_id)

            # Validate transition
            if not force and current_state:
                valid_next = self.VALID_TRANSITIONS.get(current_state, [])
                if new_state not in valid_next:
                    self._transition_errors += 1
                    raise ValueError(
                        f"Invalid state transition: {current_state.value} -> {new_state.value}"
                    )

            # Update state
            old_state = current_state
            self._task_states[task_id] = new_state

            # Store metadata
            if metadata:
                if task_id not in self._task_data:
                    self._task_data[task_id] = {}
                self._task_data[task_id]["state_metadata"] = metadata
                self._task_data[task_id]["last_updated"] = datetime.utcnow().isoformat()

            # Record history
            self._record_state_change(task_id, old_state, new_state)
            self._state_changes += 1

            return True

    async def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get current state of a task"""
        async with self._lock:
            return self._task_states.get(task_id)

    async def get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get stored data for a task"""
        async with self._lock:
            return self._task_data.get(task_id)

    async def update_task_data(
        self,
        task_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """Update task data"""
        async with self._lock:
            if task_id not in self._task_data:
                self._task_data[task_id] = {}

            if merge:
                self._task_data[task_id].update(data)
            else:
                self._task_data[task_id] = data

            self._task_data[task_id]["last_updated"] = datetime.utcnow().isoformat()

    async def get_all_task_states(self) -> Dict[str, TaskState]:
        """Get all task states"""
        async with self._lock:
            return self._task_states.copy()

    async def get_tasks_by_state(self, state: TaskState) -> List[str]:
        """Get all task IDs in a specific state"""
        async with self._lock:
            return [
                task_id for task_id, task_state in self._task_states.items()
                if task_state == state
            ]

    async def remove_task(self, task_id: str) -> bool:
        """Remove a task from state management"""
        async with self._lock:
            if task_id in self._task_states:
                del self._task_states[task_id]
                if task_id in self._task_data:
                    del self._task_data[task_id]
                return True
            return False

    # ==================== System State ====================

    async def set_system_state(
        self,
        state: SystemState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set overall system state"""
        async with self._lock:
            old_state = self._system_state
            self._system_state = state

            if metadata:
                self._system_metadata.update(metadata)

            self._record_state_change("SYSTEM", old_state, state)

    async def get_system_state(self) -> SystemState:
        """Get current system state"""
        async with self._lock:
            return self._system_state

    async def get_system_metadata(self) -> Dict[str, Any]:
        """Get system metadata"""
        async with self._lock:
            return self._system_metadata.copy()

    # ==================== State History ====================

    def _record_state_change(
        self,
        entity_id: str,
        old_state: Optional[Enum],
        new_state: Enum
    ) -> None:
        """Record a state change in history"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "entity_id": entity_id,
            "old_state": old_state.value if old_state else None,
            "new_state": new_state.value
        }

        self._state_history.append(entry)

        # Trim history if needed
        if len(self._state_history) > self._max_history:
            self._state_history = self._state_history[-self._max_history:]

    async def get_state_history(
        self,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get state change history"""
        async with self._lock:
            history = self._state_history

            if entity_id:
                history = [h for h in history if h["entity_id"] == entity_id]

            return history[-limit:]

    # ==================== Snapshots ====================

    async def create_snapshot(self) -> StateSnapshot:
        """Create a state snapshot"""
        async with self._lock:
            snapshot = StateSnapshot(
                id=f"snap-{datetime.utcnow().strftime('%Y%m%d-%H%M%S-%f')}",
                timestamp=datetime.utcnow(),
                task_states={
                    tid: state.value
                    for tid, state in self._task_states.items()
                },
                system_state=self._system_state.value,
                metadata=self._system_metadata.copy()
            )

            self._snapshots.append(snapshot)

            # Trim snapshots
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]

            return snapshot

    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore state from a snapshot"""
        async with self._lock:
            snapshot = None
            for snap in self._snapshots:
                if snap.id == snapshot_id:
                    snapshot = snap
                    break

            if not snapshot:
                return False

            # Verify integrity
            if not snapshot.verify():
                raise ValueError("Snapshot integrity check failed")

            # Restore state
            self._task_states = {
                tid: TaskState(state)
                for tid, state in snapshot.task_states.items()
            }
            self._system_state = SystemState(snapshot.system_state)
            self._system_metadata = snapshot.metadata.copy()

            return True

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots"""
        async with self._lock:
            return [
                {
                    "id": snap.id,
                    "timestamp": snap.timestamp.isoformat(),
                    "task_count": len(snap.task_states),
                    "system_state": snap.system_state,
                    "verified": snap.verify()
                }
                for snap in reversed(self._snapshots)
            ]

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get state management statistics"""
        async with self._lock:
            state_counts = {}
            for state in TaskState:
                count = sum(1 for s in self._task_states.values() if s == state)
                state_counts[state.value] = count

            return {
                "total_tasks": len(self._task_states),
                "state_counts": state_counts,
                "state_changes": self._state_changes,
                "transition_errors": self._transition_errors,
                "history_entries": len(self._state_history),
                "snapshots": len(self._snapshots),
                "system_state": self._system_state.value
            }

    # ==================== Persistence ====================

    async def save_to_file(self, filepath: str) -> bool:
        """Save state to file"""
        try:
            async with self._lock:
                data = {
                    "version": "1.0",
                    "saved_at": datetime.utcnow().isoformat(),
                    "system_state": self._system_state.value,
                    "system_metadata": self._system_metadata,
                    "task_states": {
                        tid: state.value
                        for tid, state in self._task_states.items()
                    },
                    "task_data": self._task_data
                }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Failed to save state: {e}")
            return False

    async def load_from_file(self, filepath: str) -> bool:
        """Load state from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            async with self._lock:
                self._system_state = SystemState(data["system_state"])
                self._system_metadata = data.get("system_metadata", {})
                self._task_states = {
                    tid: TaskState(state)
                    for tid, state in data.get("task_states", {}).items()
                }
                self._task_data = data.get("task_data", {})

            return True
        except Exception as e:
            print(f"Failed to load state: {e}")
            return False

    # ==================== Utility ====================

    async def clear(self) -> None:
        """Clear all state (use with caution)"""
        async with self._lock:
            self._task_states.clear()
            self._task_data.clear()
            self._state_history.clear()
            self._system_state = SystemState.INITIALIZING
            self._system_metadata.clear()

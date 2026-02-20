"""
Working memory (scratchpad) for agent context
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseMemory, MemoryEntry, MemoryType


class WorkingMemory(BaseMemory):
    """
    Short-term working memory for current task context.
    Like a scratchpad for the agent's current thoughts and observations.
    """

    def __init__(self, max_items: int = 50):
        super().__init__(MemoryType.WORKING)
        self.max_items = max_items
        self._scratchpad: Dict[str, Any] = {}

    def add(self, content: str, key: Optional[str] = None, **metadata) -> str:
        """Add item to working memory"""
        entry_id = key or str(uuid.uuid4())

        entry = MemoryEntry(
            id=entry_id, content=content, memory_type=MemoryType.WORKING, metadata={"added_to_scratchpad": True, **metadata}
        )

        self._cache.append(entry)

        # Maintain limit
        if len(self._cache) > self.max_items:
            removed = self._cache.pop(0)
            if removed.id in self._scratchpad:
                del self._scratchpad[removed.id]

        return entry_id

    def set_scratchpad(self, key: str, value: Any):
        """Set a scratchpad value"""
        self._scratchpad[key] = {"value": value, "timestamp": datetime.now().isoformat()}

    def get_scratchpad(self, key: str) -> Optional[Any]:
        """Get scratchpad value"""
        if key in self._scratchpad:
            return self._scratchpad[key]["value"]
        return None

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        for entry in self._cache:
            if entry.id == entry_id:
                return entry
        return None

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        return self._cache[-limit:]

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        query_lower = query.lower()
        return [e for e in self._cache if query_lower in e.content.lower()][-limit:]

    def get_current_context(self) -> str:
        """Get current working context for LLM"""
        lines = []

        # Add scratchpad items
        for key, data in self._scratchpad.items():
            lines.append(f"[{key}]: {data['value']}")

        # Add recent memory entries
        for entry in self.get_recent(5):
            lines.append(f"- {entry.content}")

        return "\n".join(lines) if lines else "No active context."

    def clear_task_context(self):
        """Clear current task but keep scratchpad"""
        self._cache.clear()

    def full_reset(self):
        """Complete reset"""
        self._cache.clear()
        self._scratchpad.clear()

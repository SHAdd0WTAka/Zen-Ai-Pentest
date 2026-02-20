"""
Base memory interface and types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Types of memory storage"""

    CONVERSATION = "conversation"
    WORKING = "working"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


@dataclass
class MemoryEntry:
    """Single memory entry"""

    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 0.0 - 1.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 1.0),
        )


class BaseMemory(ABC):
    """Abstract base class for all memory systems"""

    def __init__(self, memory_type: MemoryType, storage=None):
        self.memory_type = memory_type
        self.storage = storage
        self._cache: List[MemoryEntry] = []

    @abstractmethod
    def add(self, content: str, **metadata) -> str:
        """Add a memory entry, returns entry ID"""
        pass

    @abstractmethod
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search memories by content similarity"""
        pass

    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get most recent memories"""
        pass

    def clear(self):
        """Clear all memories of this type"""
        self._cache.clear()

    def get_context_string(self, limit: int = 5) -> str:
        """Get formatted context for LLM prompts"""
        entries = self.get_recent(limit)
        if not entries:
            return ""

        context_parts = []
        for entry in entries:
            time_str = entry.timestamp.strftime("%H:%M:%S")
            context_parts.append(f"[{time_str}] {entry.content}")

        return "\n".join(context_parts)

"""
Memory lifecycle management and factory
"""

from typing import Dict, Optional

from .conversation import ConversationMemory
from .storage import RedisStorage, SQLiteStorage


class MemoryManager:
    """
    Central manager for all memory systems.
    Handles creation, lifecycle, and cleanup of memory instances.
    """

    def __init__(self, storage_backend: str = "sqlite", **storage_config):
        self.storage = self._create_storage(storage_backend, **storage_config)
        self._memories: Dict[str, ConversationMemory] = {}

    def _create_storage(self, backend: str, **config):
        """Factory for storage backends"""
        if backend == "sqlite":
            return SQLiteStorage(**config)
        elif backend == "redis":
            return RedisStorage(**config)
        else:
            raise ValueError(f"Unknown storage backend: {backend}")

    def create_conversation_memory(self, session_id: str, max_history: int = 20) -> ConversationMemory:
        """Create or retrieve conversation memory for a session"""
        if session_id not in self._memories:
            self._memories[session_id] = ConversationMemory(
                session_id=session_id, storage=self.storage, max_history=max_history
            )
        return self._memories[session_id]

    def get_memory(self, session_id: str) -> Optional[ConversationMemory]:
        """Get existing memory for session"""
        return self._memories.get(session_id)

    def clear_session(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self._memories:
            self._memories[session_id].clear()
            del self._memories[session_id]

    def get_all_sessions(self) -> list:
        """List all active sessions"""
        return list(self._memories.keys())

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than specified hours"""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for session_id, memory in self._memories.items():
            if memory._cache:
                last_entry = memory._cache[-1]
                if last_entry.timestamp < cutoff:
                    to_remove.append(session_id)

        for session_id in to_remove:
            self.clear_session(session_id)

        return len(to_remove)

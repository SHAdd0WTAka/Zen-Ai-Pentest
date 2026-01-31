"""
Conversation memory with LangGraph integration
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .base import BaseMemory, MemoryEntry, MemoryType


class ConversationMemory(BaseMemory):
    """
    Manages conversation history for multi-turn interactions.
    Integrates with LangGraph for state management.
    """
    
    def __init__(self, session_id: str, storage=None, max_history: int = 20):
        super().__init__(MemoryType.CONVERSATION, storage)
        self.session_id = session_id
        self.max_history = max_history
        self._turn_count = 0
    
    def add(self, content: str, role: str = "user", **metadata) -> str:
        """Add a conversation turn"""
        entry_id = str(uuid.uuid4())
        
        entry = MemoryEntry(
            id=entry_id,
            content=f"{role}: {content}",
            memory_type=MemoryType.CONVERSATION,
            metadata={
                'session_id': self.session_id,
                'role': role,
                'turn': self._turn_count,
                **metadata
            }
        )
        
        self._cache.append(entry)
        self._turn_count += 1
        
        # Maintain size limit
        if len(self._cache) > self.max_history:
            self._cache.pop(0)
        
        # Persist if storage available
        if self.storage:
            self.storage.save(entry)
        
        return entry_id
    
    def add_user_message(self, message: str, **metadata) -> str:
        """Convenience method for user messages"""
        return self.add(message, role="user", **metadata)
    
    def add_assistant_message(self, message: str, **metadata) -> str:
        """Convenience method for assistant messages"""
        return self.add(message, role="assistant", **metadata)
    
    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get specific entry by ID"""
        for entry in self._cache:
            if entry.id == entry_id:
                return entry
        
        # Try storage if not in cache
        if self.storage:
            return self.storage.load(entry_id)
        
        return None
    
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent conversation turns"""
        return self._cache[-limit:]
    
    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Simple keyword search (can be enhanced with embeddings)"""
        query_lower = query.lower()
        matches = [
            entry for entry in self._cache
            if query_lower in entry.content.lower()
        ]
        return matches[-limit:]
    
    def get_messages_for_langgraph(self) -> List[Dict[str, str]]:
        """
        Format conversation for LangGraph state
        Returns list of {role, content} dicts
        """
        messages = []
        for entry in self._cache:
            role = entry.metadata.get('role', 'user')
            # Strip role prefix from content
            content = entry.content
            if ': ' in content:
                content = content.split(': ', 1)[1]
            
            messages.append({
                'role': role,
                'content': content,
                'timestamp': entry.timestamp.isoformat()
            })
        
        return messages
    
    def get_summary(self) -> str:
        """Get conversation summary for context"""
        return self.get_context_string(self.max_history)
    
    def get_turn_count(self) -> int:
        """Get number of conversation turns"""
        return self._turn_count

"""
Memory System for Zen AI Pentest

Provides conversation memory, working memory, and long-term storage
for intelligent agent interactions.
"""

from .base import BaseMemory, MemoryType
from .conversation import ConversationMemory
from .manager import MemoryManager
from .storage import RedisStorage, SQLiteStorage

__all__ = [
    "BaseMemory",
    "MemoryType",
    "ConversationMemory",
    "SQLiteStorage",
    "RedisStorage",
    "MemoryManager",
]

__version__ = "0.1.0"

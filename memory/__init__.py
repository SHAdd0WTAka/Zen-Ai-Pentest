"""
Memory System for Zen AI Pentest

Provides conversation memory, working memory, and long-term storage
for intelligent agent interactions.
"""

from .base import BaseMemory, MemoryType
from .conversation import ConversationMemory
from .storage import SQLiteStorage, RedisStorage
from .manager import MemoryManager

__all__ = [
    "BaseMemory",
    "MemoryType",
    "ConversationMemory",
    "SQLiteStorage",
    "RedisStorage",
    "MemoryManager",
]

__version__ = "2.3.9"

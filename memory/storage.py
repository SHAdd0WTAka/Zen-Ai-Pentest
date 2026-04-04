"""
Storage backends for memory system
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .base import MemoryEntry, MemoryType


class SQLiteStorage:
    """SQLite-based persistent storage for memories"""

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    importance REAL DEFAULT 1.0
                )
            """)

            # Index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type_time
                ON memories(memory_type, timestamp)
            """)

            conn.commit()

    def save(self, entry: MemoryEntry):
        """Save memory entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memories
                   (id, content, memory_type, timestamp, metadata, importance)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    entry.id,
                    entry.content,
                    entry.memory_type.value,
                    entry.timestamp.isoformat(),
                    json.dumps(entry.metadata),
                    entry.importance,
                ),
            )
            conn.commit()

    def load(self, entry_id: str) -> Optional[MemoryEntry]:
        """Load memory entry by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (entry_id,))
            row = cursor.fetchone()

            if row:
                return MemoryEntry(
                    id=row[0],
                    content=row[1],
                    memory_type=MemoryType(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    metadata=json.loads(row[4]) if row[4] else {},
                    importance=row[5],
                )
            return None

    def load_by_type(self, memory_type: MemoryType, limit: int = 100) -> List[MemoryEntry]:
        """Load memories by type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT * FROM memories
                   WHERE memory_type = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (memory_type.value, limit),
            )

            entries = []
            for row in cursor.fetchall():
                entries.append(
                    MemoryEntry(
                        id=row[0],
                        content=row[1],
                        memory_type=MemoryType(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        metadata=json.loads(row[4]) if row[4] else {},
                        importance=row[5],
                    )
                )
            return entries

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT * FROM memories
                   WHERE content LIKE ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (f"%{query}%", limit),
            )

            entries = []
            for row in cursor.fetchall():
                entries.append(
                    MemoryEntry(
                        id=row[0],
                        content=row[1],
                        memory_type=MemoryType(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        metadata=json.loads(row[4]) if row[4] else {},
                        importance=row[5],
                    )
                )
            return entries


class RedisStorage:
    """Redis-based storage for high-performance scenarios"""

    def __init__(self, host="localhost", port=6379, db=0):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not installed. Run: pip install redis")

        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def save(self, entry: MemoryEntry):
        """Save memory entry to Redis"""
        key = f"memory:{entry.memory_type.value}:{entry.id}"
        self.client.hset(
            key,
            mapping={
                "content": entry.content,
                "timestamp": entry.timestamp.isoformat(),
                "metadata": json.dumps(entry.metadata),
                "importance": str(entry.importance),
            },
        )

        # Set TTL based on importance (higher = longer)
        ttl = int(86400 * entry.importance * 7)  # Up to 1 week
        self.client.expire(key, ttl)

    def load(self, entry_id: str, memory_type: MemoryType = None) -> Optional[MemoryEntry]:
        """Load memory entry from Redis"""
        # Try to find without knowing type
        if memory_type:
            key = f"memory:{memory_type.value}:{entry_id}"
            data = self.client.hgetall(key)

            if data:
                return MemoryEntry(
                    id=entry_id,
                    content=data["content"],
                    memory_type=memory_type,
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    metadata=json.loads(data["metadata"]),
                    importance=float(data["importance"]),
                )
        return None

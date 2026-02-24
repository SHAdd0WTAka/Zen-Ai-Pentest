"""
Connection Pool Management

Generic connection pooling for databases, HTTP clients, etc.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Pool configuration"""

    min_size: int = 5
    max_size: int = 20
    max_idle_time: int = 300  # 5 minutes
    max_lifetime: int = 3600  # 1 hour
    acquire_timeout: int = 30
    validate_on_borrow: bool = True


class PooledConnection:
    """Wrapped connection with metadata"""

    def __init__(self, connection: Any, pool: "ConnectionPool"):
        self.connection = connection
        self.pool = pool
        self.created_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        self.use_count = 0
        self.in_use = False

    def mark_used(self):
        self.last_used = datetime.utcnow()
        self.use_count += 1
        self.in_use = True

    def mark_returned(self):
        self.in_use = False

    def is_expired(self) -> bool:
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.pool.config.max_lifetime

    def is_idle_too_long(self) -> bool:
        idle = (datetime.utcnow() - self.last_used).total_seconds()
        return idle > self.pool.config.max_idle_time


class ConnectionPool:
    """
    Generic connection pool

    Manages a pool of reusable connections.

    Example:
        async def create_connection():
            return await create_database_connection()

        pool = ConnectionPool(create_connection)
        await pool.start()

        async with pool.acquire() as conn:
            await conn.execute("SELECT * FROM table")
    """

    def __init__(
        self,
        factory: Callable,
        config: Optional[PoolConfig] = None,
        name: str = "default",
    ):
        self.factory = factory
        self.config = config or PoolConfig()
        self.name = name

        self._pool: List[PooledConnection] = []
        self._lock = asyncio.Lock()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._running = False

        # Statistics
        self._created = 0
        self._destroyed = 0
        self._acquired = 0
        self._returned = 0
        self._wait_time_total = 0

    async def start(self):
        """Initialize pool with minimum connections"""
        self._semaphore = asyncio.Semaphore(self.config.max_size)
        self._running = True

        # Create minimum connections
        for _ in range(self.config.min_size):
            conn = await self._create_connection()
            if conn:
                self._pool.append(conn)

        logger.info(
            f"Pool '{self.name}' started with {len(self._pool)} connections"
        )

    async def stop(self):
        """Close all connections"""
        self._running = False

        async with self._lock:
            for pooled in self._pool:
                await self._destroy_connection(pooled)
            self._pool.clear()

        logger.info(f"Pool '{self.name}' stopped")

    async def acquire(self) -> PooledConnection:
        """Acquire connection from pool"""
        async with self._semaphore:
            async with self._lock:
                # Try to find available connection
                for pooled in self._pool:
                    if not pooled.in_use and not pooled.is_expired():
                        if self.config.validate_on_borrow:
                            if not await self._validate(pooled):
                                continue

                        pooled.mark_used()
                        self._acquired += 1
                        return pooled

                # Create new connection if under max_size
                if len(self._pool) < self.config.max_size:
                    pooled = await self._create_connection()
                    if pooled:
                        pooled.mark_used()
                        self._pool.append(pooled)
                        self._acquired += 1
                        return pooled

        raise RuntimeError("Failed to acquire connection from pool")

    async def release(self, pooled: PooledConnection):
        """Return connection to pool"""
        async with self._lock:
            pooled.mark_returned()
            self._returned += 1

    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create new connection"""
        try:
            if asyncio.iscoroutinefunction(self.factory):
                conn = await self.factory()
            else:
                conn = self.factory()

            self._created += 1
            return PooledConnection(conn, self)
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None

    async def _destroy_connection(self, pooled: PooledConnection):
        """Destroy connection"""
        try:
            if hasattr(pooled.connection, "close"):
                if asyncio.iscoroutinefunction(pooled.connection.close):
                    await pooled.connection.close()
                else:
                    pooled.connection.close()
            self._destroyed += 1
        except Exception as e:
            logger.error(f"Error destroying connection: {e}")

    async def _validate(self, pooled: PooledConnection) -> bool:
        """Validate connection is still good"""
        try:
            if hasattr(pooled.connection, "ping"):
                if asyncio.iscoroutinefunction(pooled.connection.ping):
                    await pooled.connection.ping()
                else:
                    pooled.connection.ping()
                return True
            return True
        except Exception:
            return False

    async def cleanup(self):
        """Remove expired/idle connections"""
        async with self._lock:
            to_remove = [
                p
                for p in self._pool
                if not p.in_use and (p.is_expired() or p.is_idle_too_long())
            ]

            for pooled in to_remove:
                await self._destroy_connection(pooled)
                self._pool.remove(pooled)

            # Ensure minimum connections
            while len(self._pool) < self.config.min_size:
                conn = await self._create_connection()
                if conn:
                    self._pool.append(conn)

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        in_use = sum(1 for p in self._pool if p.in_use)
        available = len(self._pool) - in_use

        return {
            "name": self.name,
            "total": len(self._pool),
            "in_use": in_use,
            "available": available,
            "min_size": self.config.min_size,
            "max_size": self.config.max_size,
            "created": self._created,
            "destroyed": self._destroyed,
            "acquired": self._acquired,
            "returned": self._returned,
        }


class PoolManager:
    """Manages multiple connection pools"""

    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}

    def register(self, name: str, pool: ConnectionPool):
        """Register a pool"""
        self._pools[name] = pool

    def get(self, name: str) -> Optional[ConnectionPool]:
        """Get pool by name"""
        return self._pools.get(name)

    async def start_all(self):
        """Start all pools"""
        for pool in self._pools.values():
            await pool.start()

    async def stop_all(self):
        """Stop all pools"""
        for pool in self._pools.values():
            await pool.stop()

    def get_all_stats(self) -> Dict[str, Any]:
        """Get stats for all pools"""
        return {name: pool.get_stats() for name, pool in self._pools.items()}

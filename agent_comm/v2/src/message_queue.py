"""
Message Queue for gRPC Agent Communication v2 - Optimized for 10 Agents (Free Plan)

Features:
- Redis-based message queue for reliable delivery
- Batching support to reduce request count
- Priority queues for critical messages
- TTL-based message expiration
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory fallback")


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageType(Enum):
    """Message types."""
    COMMAND = "command"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    STATUS = "status"
    EVENT = "event"


@dataclass
class QueueMessage:
    """Message for the queue.
    
    Attributes:
        message_id: Unique message ID
        sender_id: Sender agent ID
        recipient_id: Recipient agent ID (or "broadcast")
        message_type: Type of message
        priority: Message priority
        payload: Message payload
        timestamp: Creation timestamp
        ttl: Time-to-live in seconds
    """
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: str
    priority: int
    payload: Dict[str, Any]
    timestamp: float
    ttl: int = 300  # 5 minutes default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type,
            "priority": self.priority,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueueMessage":
        """Create from dictionary."""
        return cls(**data)


class MessageQueue:
    """Message queue for agent communication.
    
    Optimized for 10 agents on Cloudflare Free Plan:
    - Batching to reduce request count
    - Priority queues for critical messages
    - In-memory fallback if Redis unavailable
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        batch_size: int = 10,
        batch_timeout: float = 5.0
    ):
        """Initialize message queue.
        
        Args:
            redis_url: Redis connection URL (None for in-memory)
            batch_size: Number of messages to batch
            batch_timeout: Seconds to wait before flushing batch
        """
        self.redis_url = redis_url
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        self._redis: Optional[redis.Redis] = None
        self._memory_queue: Dict[str, List[QueueMessage]] = {}
        self._batch_buffers: Dict[str, List[QueueMessage]] = {}
        self._batch_timers: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        
        # Metrics
        self._metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "batches_flushed": 0,
            "messages_dropped": 0,
        }
    
    async def connect(self) -> bool:
        """Connect to Redis or initialize in-memory.
        
        Returns:
            True if connected, False otherwise
        """
        if self.redis_url and REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(self.redis_url)
                await self._redis.ping()
                logger.info("Connected to Redis")
                return True
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._redis = None
        
        logger.info("Using in-memory message queue")
        return True
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def send(
        self,
        message: QueueMessage,
        immediate: bool = False
    ) -> bool:
        """Send a message to the queue.
        
        Args:
            message: Message to send
            immediate: Skip batching and send immediately
            
        Returns:
            True if sent successfully
        """
        async with self._lock:
            self._metrics["messages_sent"] += 1
            
            if immediate or message.priority >= MessagePriority.CRITICAL.value:
                return await self._send_immediate(message)
            else:
                return await self._batch_message(message)
    
    async def _send_immediate(self, message: QueueMessage) -> bool:
        """Send message immediately without batching."""
        queue_key = f"queue:{message.recipient_id}"
        
        try:
            if self._redis:
                # Add to Redis sorted set (priority queue)
                await self._redis.zadd(
                    queue_key,
                    {json.dumps(message.to_dict()): -message.priority}
                )
                # Set expiration
                await self._redis.expire(queue_key, message.ttl)
            else:
                # In-memory queue
                if queue_key not in self._memory_queue:
                    self._memory_queue[queue_key] = []
                self._memory_queue[queue_key].append(message)
            
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._metrics["messages_dropped"] += 1
            return False
    
    async def _batch_message(self, message: QueueMessage) -> bool:
        """Add message to batch buffer."""
        queue_key = f"queue:{message.recipient_id}"
        
        if queue_key not in self._batch_buffers:
            self._batch_buffers[queue_key] = []
        
        self._batch_buffers[queue_key].append(message)
        
        # Start batch timer if not running
        if queue_key not in self._batch_timers or self._batch_timers[queue_key].done():
            self._batch_timers[queue_key] = asyncio.create_task(
                self._flush_batch_after_timeout(queue_key)
            )
        
        # Flush if batch is full
        if len(self._batch_buffers[queue_key]) >= self.batch_size:
            await self._flush_batch(queue_key)
        
        return True
    
    async def _flush_batch_after_timeout(self, queue_key: str):
        """Flush batch after timeout."""
        await asyncio.sleep(self.batch_timeout)
        await self._flush_batch(queue_key)
    
    async def _flush_batch(self, queue_key: str):
        """Flush batch buffer to queue."""
        async with self._lock:
            if queue_key not in self._batch_buffers:
                return
            
            batch = self._batch_buffers[queue_key]
            if not batch:
                return
            
            # Clear buffer
            del self._batch_buffers[queue_key]
            
            # Cancel timer if exists
            if queue_key in self._batch_timers:
                timer = self._batch_timers[queue_key]
                if not timer.done():
                    timer.cancel()
                del self._batch_timers[queue_key]
        
        # Send batch
        try:
            if self._redis:
                pipe = self._redis.pipeline()
                for message in batch:
                    pipe.zadd(
                        queue_key,
                        {json.dumps(message.to_dict()): -message.priority}
                    )
                pipe.expire(queue_key, 300)  # 5 min TTL
                await pipe.execute()
            else:
                if queue_key not in self._memory_queue:
                    self._memory_queue[queue_key] = []
                self._memory_queue[queue_key].extend(batch)
            
            self._metrics["batches_flushed"] += 1
            logger.debug(f"Flushed batch of {len(batch)} messages to {queue_key}")
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")
            self._metrics["messages_dropped"] += len(batch)
    
    async def receive(
        self,
        recipient_id: str,
        timeout: float = 30.0,
        max_messages: int = 10
    ) -> List[QueueMessage]:
        """Receive messages for a recipient.
        
        Args:
            recipient_id: Recipient agent ID
            timeout: Timeout in seconds (long-polling)
            max_messages: Maximum messages to receive
            
        Returns:
            List of messages
        """
        queue_key = f"queue:{recipient_id}"
        
        async with self._lock:
            self._metrics["messages_received"] += 1
        
        try:
            if self._redis:
                # Poll with timeout
                start_time = time.time()
                while time.time() - start_time < timeout:
                    # Get messages from sorted set
                    messages_data = await self._redis.zpopmin(
                        queue_key,
                        max_messages
                    )
                    
                    if messages_data:
                        messages = [
                            QueueMessage.from_dict(json.loads(m[0]))
                            for m in messages_data
                        ]
                        return messages
                    
                    # Wait before retry
                    await asyncio.sleep(1.0)
                
                return []
            else:
                # In-memory queue
                if queue_key not in self._memory_queue:
                    return []
                
                # Get up to max_messages
                messages = self._memory_queue[queue_key][:max_messages]
                self._memory_queue[queue_key] = self._memory_queue[queue_key][max_messages:]
                
                return messages
        
        except Exception as e:
            logger.error(f"Failed to receive messages: {e}")
            return []
    
    async def broadcast(
        self,
        message: QueueMessage,
        recipient_ids: List[str]
    ) -> Dict[str, bool]:
        """Broadcast message to multiple recipients.
        
        Args:
            message: Message to broadcast
            recipient_ids: List of recipient IDs
            
        Returns:
            Dictionary mapping recipient ID to success status
        """
        results = {}
        
        for recipient_id in recipient_ids:
            msg_copy = QueueMessage(
                message_id=f"{message.message_id}-{recipient_id}",
                sender_id=message.sender_id,
                recipient_id=recipient_id,
                message_type=message.message_type,
                priority=message.priority,
                payload=message.payload,
                timestamp=message.timestamp,
                ttl=message.ttl
            )
            results[recipient_id] = await self.send(msg_copy)
        
        return results
    
    async def get_queue_length(self, recipient_id: str) -> int:
        """Get number of messages in queue.
        
        Args:
            recipient_id: Recipient agent ID
            
        Returns:
            Number of messages
        """
        queue_key = f"queue:{recipient_id}"
        
        try:
            if self._redis:
                return await self._redis.zcard(queue_key)
            else:
                return len(self._memory_queue.get(queue_key, []))
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0
    
    async def clear_queue(self, recipient_id: str) -> bool:
        """Clear all messages from queue.
        
        Args:
            recipient_id: Recipient agent ID
            
        Returns:
            True if cleared successfully
        """
        queue_key = f"queue:{recipient_id}"
        
        try:
            if self._redis:
                await self._redis.delete(queue_key)
            else:
                if queue_key in self._memory_queue:
                    del self._memory_queue[queue_key]
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics.
        
        Returns:
            Dictionary with metrics
        """
        return {
            **self._metrics,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "using_redis": self._redis is not None,
            "pending_batches": len(self._batch_buffers),
        }


class BatchedMessageSender:
    """Helper class for sending messages in batches.
    
    Automatically batches messages to reduce request count.
    """
    
    def __init__(
        self,
        message_queue: MessageQueue,
        sender_id: str,
        default_priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Initialize batched sender.
        
        Args:
            message_queue: Message queue instance
            sender_id: Sender agent ID
            default_priority: Default message priority
        """
        self.queue = message_queue
        self.sender_id = sender_id
        self.default_priority = default_priority
    
    async def send_command(
        self,
        recipient_id: str,
        command: str,
        params: Dict[str, Any],
        immediate: bool = False
    ) -> bool:
        """Send command to agent.
        
        Args:
            recipient_id: Target agent ID
            command: Command name
            params: Command parameters
            immediate: Skip batching
            
        Returns:
            True if sent successfully
        """
        message = QueueMessage(
            message_id=f"cmd-{int(time.time() * 1000)}",
            sender_id=self.sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.COMMAND.value,
            priority=MessagePriority.HIGH.value,
            payload={"command": command, "params": params},
            timestamp=time.time(),
            ttl=60  # Commands expire after 1 minute
        )
        
        return await self.queue.send(message, immediate)
    
    async def send_status(
        self,
        recipient_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """Send status update (batched by default).
        
        Args:
            recipient_id: Target agent ID
            status: Status data
            
        Returns:
            True if sent successfully
        """
        message = QueueMessage(
            message_id=f"status-{int(time.time() * 1000)}",
            sender_id=self.sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.STATUS.value,
            priority=self.default_priority.value,
            payload=status,
            timestamp=time.time(),
            ttl=300
        )
        
        return await self.queue.send(message, immediate=False)  # Always batch
    
    async def send_heartbeat(self, status: str = "online") -> bool:
        """Send heartbeat to coordinator.
        
        Args:
            status: Agent status
            
        Returns:
            True if sent successfully
        """
        message = QueueMessage(
            message_id=f"hb-{int(time.time() * 1000)}",
            sender_id=self.sender_id,
            recipient_id="coordinator",  # Special coordinator queue
            message_type=MessageType.HEARTBEAT.value,
            priority=MessagePriority.NORMAL.value,
            payload={"status": status, "timestamp": time.time()},
            timestamp=time.time(),
            ttl=60
        )
        
        return await self.queue.send(message, immediate=True)  # Heartbeats immediate

"""
Message Queue Integration
=========================

Redis-based message queue for reliable agent communication.

Features:
- Pub/Sub for real-time messaging
- Reliable queues with acknowledgment
- Message persistence
- Priority queues
- Dead letter queue for failed messages

Usage:
    queue = AgentMessageQueue(redis_url="redis://localhost:6379")
    await queue.connect()

    # Publish
    await queue.publish("agent.events", message)

    # Subscribe
    async for msg in queue.subscribe(["agent.events"]):
        process(msg)
        await queue.ack(msg.id)
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

try:
    import aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Fallback for development

from .secure_message import SecureMessage

logger = logging.getLogger("zen.agents.queue")


class MessageStatus(Enum):
    """Message delivery status"""

    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class QueuedMessage:
    """Message in queue"""

    id: str
    channel: str
    payload: str  # Serialized SecureMessage
    status: MessageStatus
    priority: int  # 1-10, higher = more urgent
    created_at: str
    delivered_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueuedMessage":
        # Handle enum conversion
        data = data.copy()
        if isinstance(data.get("status"), str):
            data["status"] = MessageStatus(data["status"])
        return cls(**data)


class MessageQueueError(Exception):
    """Message queue error"""

    pass


class AgentMessageQueue:
    """
    Redis-backed message queue for agents

    Provides reliable message delivery with:
    - Persistence
    - Acknowledgment
    - Retry logic
    - Dead letter queue
    """

    # Redis key prefixes
    KEY_QUEUE = "zen:queue:{channel}"
    KEY_PROCESSING = "zen:processing:{channel}"
    KEY_DEAD_LETTER = "zen:dead:{channel}"
    KEY_STATUS = "zen:status:{message_id}"

    def __init__(self, redis_url: str = "redis://localhost:6379", max_retries: int = 3, visibility_timeout: int = 30):
        """
        Initialize message queue

        Args:
            redis_url: Redis connection URL
            max_retries: Maximum delivery attempts
            visibility_timeout: Seconds before message reappears in queue
        """
        if not REDIS_AVAILABLE:
            raise ImportError("aioredis required. Install with: pip install aioredis")

        self.redis_url = redis_url
        self.max_retries = max_retries
        self.visibility_timeout = visibility_timeout

        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self._connected = False

        # Subscription handlers
        self._handlers: Dict[str, List[Callable]] = {}
        self._subscriber_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)

            # Test connection
            await self.redis.ping()
            self._connected = True

            logger.info(f"✅ Connected to Redis at {self.redis_url}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise MessageQueueError(f"Redis connection failed: {e}")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._subscriber_task:
            self._subscriber_task.cancel()

        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def publish(self, channel: str, message: SecureMessage, priority: int = 5, persist: bool = True) -> str:
        """
        Publish message to channel

        Args:
            channel: Target channel
            message: Message to publish
            priority: Message priority (1-10)
            persist: Whether to persist message for reliability

        Returns:
            Message ID
        """
        if not self._connected:
            raise MessageQueueError("Not connected to Redis")

        # Create queued message
        queued = QueuedMessage(
            id=message.header.message_id,
            channel=channel,
            payload=message.to_json(),
            status=MessageStatus.PENDING,
            priority=priority,
            created_at=datetime.utcnow().isoformat(),
            max_retries=self.max_retries,
        )

        # Store status
        await self.redis.set(
            self.KEY_STATUS.format(message_id=queued.id), json.dumps(queued.to_dict()), ex=3600  # Expire after 1 hour
        )

        if persist:
            # Add to reliable queue (sorted by priority)
            score = 10 - priority  # Lower score = higher priority
            await self.redis.zadd(self.KEY_QUEUE.format(channel=channel), {queued.id: score})

            # Store message data
            await self.redis.set(f"zen:msg:{queued.id}", json.dumps(queued.to_dict()), ex=3600)

        # Publish for real-time subscribers
        await self.redis.publish(
            channel, json.dumps({"type": "new_message", "message_id": queued.id, "channel": channel, "priority": priority})
        )

        logger.debug(f"Published message {queued.id} to {channel}")
        return queued.id

    async def subscribe(
        self, channels: List[str], handler: Optional[Callable[[QueuedMessage], None]] = None
    ) -> AsyncIterator[QueuedMessage]:
        """
        Subscribe to channels

        Args:
            channels: List of channels to subscribe to
            handler: Optional callback handler

        Yields:
            QueuedMessage
        """
        if not self._connected:
            raise MessageQueueError("Not connected to Redis")

        # Create pub/sub connection
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)

        logger.info(f"Subscribed to channels: {channels}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])

                    if data.get("type") == "new_message":
                        # Fetch full message from queue
                        msg_id = data["message_id"]
                        data["channel"]

                        # Get from reliable queue
                        queued = await self._fetch_message(msg_id)

                        if queued:
                            if handler:
                                handler(queued)
                            yield queued

        finally:
            await pubsub.unsubscribe(*channels)

    async def receive(self, channel: str, timeout: Optional[float] = None) -> Optional[QueuedMessage]:
        """
        Receive message from queue (blocking)

        Args:
            channel: Channel to receive from
            timeout: Max seconds to wait

        Returns:
            QueuedMessage or None if timeout
        """
        if not self._connected:
            raise MessageQueueError("Not connected to Redis")

        # Try to get from queue
        queue_key = self.KEY_QUEUE.format(channel=channel)
        self.KEY_PROCESSING.format(channel=channel)

        # Get highest priority item
        result = await self.redis.zpopmin(queue_key, count=1)

        if not result:
            # No message available
            return None

        msg_id, score = result[0]

        # Fetch message data
        queued = await self._fetch_message(msg_id)

        if not queued:
            return None

        # Move to processing queue
        queued.status = MessageStatus.DELIVERED
        queued.delivered_at = datetime.utcnow().isoformat()

        await self.redis.set(f"zen:processing:{msg_id}", json.dumps(queued.to_dict()), ex=self.visibility_timeout)

        # Schedule visibility timeout
        asyncio.create_task(self._visibility_timeout_handler(channel, msg_id))

        return queued

    async def ack(self, message_id: str):
        """
        Acknowledge message receipt

        Args:
            message_id: Message to acknowledge
        """
        # Remove from processing
        await self.redis.delete(f"zen:processing:{message_id}")

        # Update status
        status_key = self.KEY_STATUS.format(message_id=message_id)
        data = await self.redis.get(status_key)

        if data:
            queued = QueuedMessage.from_dict(json.loads(data))
            queued.status = MessageStatus.ACKNOWLEDGED
            queued.acknowledged_at = datetime.utcnow().isoformat()

            await self.redis.set(status_key, json.dumps(queued.to_dict()), ex=3600)

        # Clean up message data
        await self.redis.delete(f"zen:msg:{message_id}")

        logger.debug(f"Acknowledged message {message_id}")

    async def nack(self, message_id: str, requeue: bool = True):
        """
        Negative acknowledgment - message not processed

        Args:
            message_id: Message to reject
            requeue: Whether to requeue for retry
        """
        # Get message
        queued = await self._fetch_message(message_id)

        if not queued:
            return

        if requeue and queued.retry_count < queued.max_retries:
            # Requeue with incremented retry count
            queued.retry_count += 1
            queued.status = MessageStatus.PENDING

            await self.redis.zadd(self.KEY_QUEUE.format(channel=queued.channel), {message_id: 10 - queued.priority})

            logger.debug(f"Requeued message {message_id} (retry {queued.retry_count})")
        else:
            # Move to dead letter queue
            await self._to_dead_letter(queued, "Max retries exceeded")

    async def get_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get message delivery status"""
        data = await self.redis.get(self.KEY_STATUS.format(message_id=message_id))

        if data:
            queued = QueuedMessage.from_dict(json.loads(data))
            return queued.status
        return None

    async def retry_failed(self, channel: str):
        """Retry all failed messages in channel"""
        # This would scan dead letter queue and requeue
        pass

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _fetch_message(self, msg_id: str) -> Optional[QueuedMessage]:
        """Fetch message data by ID"""
        # Try processing queue first
        data = await self.redis.get(f"zen:processing:{msg_id}")

        if not data:
            # Try message store
            data = await self.redis.get(f"zen:msg:{msg_id}")

        if data:
            return QueuedMessage.from_dict(json.loads(data))

        return None

    async def _visibility_timeout_handler(self, channel: str, msg_id: str):
        """Handle visibility timeout - requeue if not acknowledged"""
        await asyncio.sleep(self.visibility_timeout)

        # Check if still in processing
        processing_key = f"zen:processing:{msg_id}"
        exists = await self.redis.exists(processing_key)

        if exists:
            # Not acknowledged, requeue
            await self.nack(msg_id, requeue=True)

    async def _to_dead_letter(self, queued: QueuedMessage, reason: str):
        """Move message to dead letter queue"""
        queued.status = MessageStatus.DEAD_LETTER
        queued.error = reason

        dead_key = self.KEY_DEAD_LETTER.format(channel=queued.channel)

        await self.redis.zadd(dead_key, {queued.id: datetime.utcnow().timestamp()})
        await self.redis.set(f"zen:dead:msg:{queued.id}", json.dumps(queued.to_dict()), ex=86400)  # Keep for 24 hours

        # Clean up processing
        await self.redis.delete(f"zen:processing:{queued.id}")

        logger.warning(f"Message {queued.id} moved to dead letter queue: {reason}")


# ============================================================================
# In-Memory Fallback for Development
# ============================================================================


class InMemoryMessageQueue:
    """
    In-memory message queue for development/testing

    Same interface as AgentMessageQueue but no Redis required.
    """

    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.messages: Dict[str, QueuedMessage] = {}

    async def connect(self):
        """No-op for in-memory"""
        logger.info("Using in-memory message queue (development mode)")

    async def disconnect(self):
        """No-op"""
        pass

    async def publish(self, channel: str, message: SecureMessage, priority: int = 5, persist: bool = True) -> str:
        """Publish message"""
        import uuid

        msg_id = str(uuid.uuid4())

        queued = QueuedMessage(
            id=msg_id,
            channel=channel,
            payload=message.to_json(),
            status=MessageStatus.PENDING,
            priority=priority,
            created_at=datetime.utcnow().isoformat(),
        )

        self.messages[msg_id] = queued

        # Add to queue
        if channel not in self.queues:
            self.queues[channel] = asyncio.Queue()

        await self.queues[channel].put(queued)

        # Notify subscribers
        for sub in self.subscribers.get(channel, []):
            await sub.put(queued)

        return msg_id

    async def subscribe(
        self, channels: List[str], handler: Optional[Callable[[QueuedMessage], None]] = None
    ) -> AsyncIterator[QueuedMessage]:
        """Subscribe to channels"""
        # Create subscription queue
        sub_queue = asyncio.Queue()

        for channel in channels:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(sub_queue)

        try:
            while True:
                msg = await sub_queue.get()
                if handler:
                    handler(msg)
                yield msg
        finally:
            # Cleanup
            for channel in channels:
                if channel in self.subscribers:
                    self.subscribers[channel].remove(sub_queue)

    async def receive(self, channel: str, timeout: Optional[float] = None) -> Optional[QueuedMessage]:
        """Receive message"""
        if channel not in self.queues:
            return None

        try:
            if timeout:
                return await asyncio.wait_for(self.queues[channel].get(), timeout=timeout)
            else:
                return await self.queues[channel].get()
        except asyncio.TimeoutError:
            return None

    async def ack(self, message_id: str):
        """Acknowledge message"""
        if message_id in self.messages:
            self.messages[message_id].status = MessageStatus.ACKNOWLEDGED

    async def nack(self, message_id: str, requeue: bool = True):
        """Negative acknowledge"""
        pass


def create_message_queue(redis_url: Optional[str] = None) -> AgentMessageQueue:
    """
    Factory function to create appropriate message queue

    Args:
        redis_url: Redis URL or None for in-memory

    Returns:
        Message queue instance
    """
    if redis_url and REDIS_AVAILABLE:
        return AgentMessageQueue(redis_url)
    else:
        if redis_url and not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory queue")
        return InMemoryMessageQueue()


# ============================================================================
# Test Functions
# ============================================================================


async def test_in_memory_queue():
    """Test in-memory queue"""
    queue = InMemoryMessageQueue()
    await queue.connect()

    from .secure_message import EncryptedPayload, MessageHeader

    # Create test message
    msg = SecureMessage(
        header=MessageHeader(
            message_id="test-1",
            sender_id="agent-a",
            recipient_id="agent-b",
            timestamp=datetime.utcnow().isoformat(),
            msg_type="test",
        ),
        payload=EncryptedPayload(ciphertext="encrypted", nonce="nonce", salt="salt"),
        signature="sig",
    )

    # Publish
    msg_id = await queue.publish("test.channel", msg)
    print(f"✅ Published message: {msg_id}")

    # Receive
    received = await queue.receive("test.channel", timeout=1.0)
    assert received is not None
    assert received.id == msg_id
    print(f"✅ Received message: {received.id}")

    # Ack
    await queue.ack(msg_id)
    print("✅ Acknowledged message")


if __name__ == "__main__":
    asyncio.run(test_in_memory_queue())

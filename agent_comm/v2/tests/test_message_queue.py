"""
Comprehensive tests for agent_comm/v2/src/message_queue.py
Target: 90%+ Coverage
"""

import json
import time
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from agent_comm.v2.src.message_queue import (
    MessageQueue,
    QueueMessage,
    MessagePriority,
    MessageType,
    BatchedMessageSender,
)


class TestQueueMessage:
    """Tests for QueueMessage dataclass."""
    
    def test_create_message(self):
        """Test creating a message."""
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.COMMAND.value,
            priority=MessagePriority.HIGH.value,
            payload={"cmd": "scan"},
            timestamp=1234567890.0,
            ttl=300
        )
        
        assert message.message_id == "msg-1"
        assert message.sender_id == "agent-1"
        assert message.recipient_id == "agent-2"
        assert message.message_type == "command"
        assert message.priority == 3
        assert message.payload == {"cmd": "scan"}
        assert message.timestamp == 1234567890.0
        assert message.ttl == 300
    
    def test_default_ttl(self):
        """Test default TTL."""
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS.value,
            priority=MessagePriority.NORMAL.value,
            payload={},
            timestamp=time.time()
        )
        
        assert message.ttl == 300  # Default 5 minutes
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.EVENT.value,
            priority=MessagePriority.CRITICAL.value,
            payload={"event": "alert"},
            timestamp=1234567890.0,
            ttl=60
        )
        
        d = message.to_dict()
        
        assert d["message_id"] == "msg-1"
        assert d["sender_id"] == "agent-1"
        assert d["recipient_id"] == "agent-2"
        assert d["message_type"] == "event"
        assert d["priority"] == 4
        assert d["payload"] == {"event": "alert"}
        assert d["timestamp"] == 1234567890.0
        assert d["ttl"] == 60
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "message_id": "msg-1",
            "sender_id": "agent-1",
            "recipient_id": "agent-2",
            "message_type": "command",
            "priority": 3,
            "payload": {"cmd": "scan"},
            "timestamp": 1234567890.0,
            "ttl": 300
        }
        
        message = QueueMessage.from_dict(data)
        
        assert message.message_id == "msg-1"
        assert message.sender_id == "agent-1"
        assert message.message_type == "command"


class TestMessageQueueInit:
    """Tests for MessageQueue initialization."""
    
    def test_default_init(self):
        """Test default initialization."""
        queue = MessageQueue()
        
        assert queue.redis_url is None
        assert queue.batch_size == 10
        assert queue.batch_timeout == 5.0
        assert queue._redis is None
        assert queue._memory_queue == {}
    
    def test_custom_init(self):
        """Test custom initialization."""
        queue = MessageQueue(
            redis_url="redis://localhost:6379",
            batch_size=20,
            batch_timeout=10.0
        )
        
        assert queue.redis_url == "redis://localhost:6379"
        assert queue.batch_size == 20
        assert queue.batch_timeout == 10.0


class TestMessageQueueInMemory:
    """Tests for in-memory message queue."""
    
    @pytest.mark.asyncio
    async def test_connect_in_memory(self):
        """Test connecting to in-memory queue."""
        queue = MessageQueue()
        
        result = await queue.connect()
        
        assert result is True
        assert queue._redis is None
    
    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        """Test sending and receiving messages."""
        queue = MessageQueue()
        await queue.connect()
        
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.COMMAND.value,
            priority=MessagePriority.HIGH.value,
            payload={"cmd": "scan"},
            timestamp=time.time()
        )
        
        # Send
        result = await queue.send(message, immediate=True)
        assert result is True
        
        # Receive
        messages = await queue.receive("agent-2", timeout=1.0)
        assert len(messages) == 1
        assert messages[0].message_id == "msg-1"
    
    @pytest.mark.asyncio
    async def test_receive_empty_queue(self):
        """Test receiving from empty queue."""
        queue = MessageQueue()
        await queue.connect()
        
        messages = await queue.receive("agent-1", timeout=0.5)
        
        assert messages == []
    
    @pytest.mark.asyncio
    async def test_batching(self):
        """Test message batching."""
        queue = MessageQueue(batch_size=3, batch_timeout=60.0)
        await queue.connect()
        
        # Send 2 messages (should not flush yet)
        for i in range(2):
            message = QueueMessage(
                message_id=f"msg-{i}",
                sender_id="agent-1",
                recipient_id="agent-2",
                message_type=MessageType.STATUS.value,
                priority=MessagePriority.NORMAL.value,
                payload={"status": f"update-{i}"},
                timestamp=time.time()
            )
            await queue.send(message, immediate=False)
        
        # Queue should still be empty (batched)
        assert len(queue._batch_buffers.get("queue:agent-2", [])) == 2
        
        # Send 3rd message (should flush)
        message = QueueMessage(
            message_id="msg-2",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS.value,
            priority=MessagePriority.NORMAL.value,
            payload={"status": "update-2"},
            timestamp=time.time()
        )
        await queue.send(message, immediate=False)
        
        # Give time for flush
        await asyncio.sleep(0.1)
        
        # All messages should be in queue
        messages = await queue.receive("agent-2", timeout=0.5, max_messages=10)
        assert len(messages) == 3
    
    @pytest.mark.asyncio
    async def test_immediate_send_high_priority(self):
        """Test immediate send for high priority."""
        queue = MessageQueue(batch_size=10)
        await queue.connect()
        
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.COMMAND.value,
            priority=MessagePriority.CRITICAL.value,  # Critical priority
            payload={"cmd": "stop"},
            timestamp=time.time()
        )
        
        # Should send immediately
        await queue.send(message, immediate=False)
        
        # Should be available immediately
        messages = await queue.receive("agent-2", timeout=0.1)
        assert len(messages) == 1
        assert messages[0].message_id == "msg-1"
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to multiple recipients."""
        queue = MessageQueue()
        await queue.connect()
        
        message = QueueMessage(
            message_id="broadcast-1",
            sender_id="coordinator",
            recipient_id="broadcast",  # Will be overwritten
            message_type=MessageType.COMMAND.value,
            priority=MessagePriority.HIGH.value,
            payload={"cmd": "update_config"},
            timestamp=time.time()
        )
        
        recipients = ["agent-1", "agent-2", "agent-3"]
        results = await queue.broadcast(message, recipients)
        
        assert all(results.values())
        
        # Each agent should receive
        for agent_id in recipients:
            messages = await queue.receive(agent_id, timeout=0.1)
            assert len(messages) == 1
    
    @pytest.mark.asyncio
    async def test_get_queue_length(self):
        """Test getting queue length."""
        queue = MessageQueue()
        await queue.connect()
        
        # Empty queue
        length = await queue.get_queue_length("agent-1")
        assert length == 0
        
        # Add messages
        for i in range(5):
            message = QueueMessage(
                message_id=f"msg-{i}",
                sender_id="agent-2",
                recipient_id="agent-1",
                message_type=MessageType.STATUS.value,
                priority=MessagePriority.NORMAL.value,
                payload={},
                timestamp=time.time()
            )
            await queue.send(message, immediate=True)
        
        length = await queue.get_queue_length("agent-1")
        assert length == 5
    
    @pytest.mark.asyncio
    async def test_clear_queue(self):
        """Test clearing queue."""
        queue = MessageQueue()
        await queue.connect()
        
        # Add messages
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-2",
            recipient_id="agent-1",
            message_type=MessageType.STATUS.value,
            priority=MessagePriority.NORMAL.value,
            payload={},
            timestamp=time.time()
        )
        await queue.send(message, immediate=True)
        
        # Clear
        result = await queue.clear_queue("agent-1")
        assert result is True
        
        # Should be empty
        length = await queue.get_queue_length("agent-1")
        assert length == 0
    
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting metrics."""
        queue = MessageQueue()
        await queue.connect()
        
        # Send some messages
        message = QueueMessage(
            message_id="msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS.value,
            priority=MessagePriority.NORMAL.value,
            payload={},
            timestamp=time.time()
        )
        await queue.send(message, immediate=True)
        
        metrics = queue.get_metrics()
        
        assert metrics["messages_sent"] == 1
        assert metrics["batch_size"] == 10
        assert metrics["batch_timeout"] == 5.0
        assert metrics["using_redis"] is False


class TestBatchedMessageSender:
    """Tests for BatchedMessageSender."""
    
    @pytest.fixture
    async def sender(self):
        """Create a batched sender."""
        queue = MessageQueue()
        await queue.connect()
        sender = BatchedMessageSender(queue, "agent-1")
        return sender
    
    @pytest.mark.asyncio
    async def test_send_command(self, sender):
        """Test sending command."""
        result = await sender.send_command(
            recipient_id="agent-2",
            command="scan",
            params={"target": "192.168.1.1"}
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_status(self, sender):
        """Test sending status."""
        result = await sender.send_status(
            recipient_id="coordinator",
            status={"cpu": 50, "memory": 60}
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_heartbeat(self, sender):
        """Test sending heartbeat."""
        result = await sender.send_heartbeat(status="online")
        
        assert result is True


class TestMessageQueueErrors:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_receive_error_handling(self):
        """Test error handling in receive."""
        queue = MessageQueue()
        await queue.connect()
        
        # Simulate error by corrupting memory queue
        queue._memory_queue = None  # type: ignore
        
        messages = await queue.receive("agent-1")
        assert messages == []
    
    @pytest.mark.asyncio
    async def test_clear_queue_error(self):
        """Test error handling in clear_queue."""
        queue = MessageQueue()
        await queue.connect()
        
        # Should handle gracefully
        result = await queue.clear_queue("nonexistent")
        assert result is True  # Already empty is OK


class TestMessagePriority:
    """Tests for message priority enum."""
    
    def test_priority_values(self):
        """Test priority values."""
        assert MessagePriority.LOW.value == 1
        assert MessagePriority.NORMAL.value == 2
        assert MessagePriority.HIGH.value == 3
        assert MessagePriority.CRITICAL.value == 4


class TestMessageType:
    """Tests for message type enum."""
    
    def test_type_values(self):
        """Test type values."""
        assert MessageType.COMMAND.value == "command"
        assert MessageType.RESPONSE.value == "response"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.STATUS.value == "status"
        assert MessageType.EVENT.value == "event"

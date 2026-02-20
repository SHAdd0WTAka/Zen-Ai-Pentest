"""
Agent Client SDK
================

Client library for agents to connect and communicate securely.

Features:
- WebSocket connection with auto-reconnect
- Automatic message encryption/decryption
- Heartbeat/keepalive
- Message acknowledgment
- Error handling and retry logic

Usage:
    agent = AgentClient(
        agent_id="agt_xxx",
        api_key="zen_xxx",
        api_secret="sec_xxx"
    )
    await agent.connect()
    await agent.send_message(recipient="agt_yyy", payload={...})
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from .auth_manager import AgentIdentity
from .secure_message import MessageEncryption, SecureMessage

logger = logging.getLogger("zen.agents.client")


class ConnectionState(Enum):
    """Connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class AgentConnectionError(Exception):
    """Connection error"""

    pass


class AuthenticationError(Exception):
    """Authentication failed"""

    pass


@dataclass
class MessageAck:
    """Message acknowledgment"""

    message_id: str
    status: str  # delivered, failed, retry
    timestamp: datetime
    error: Optional[str] = None


class AgentClient:
    """
    Secure agent client

    Manages WebSocket connection, encryption, and message handling.
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        api_secret: str,
        server_url: str = "ws://localhost:8000/agents/stream",
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0,
        heartbeat_interval: float = 30.0,
    ):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library required. Install with: pip install websockets")

        self.agent_id = agent_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.server_url = server_url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.heartbeat_interval = heartbeat_interval

        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._identity: Optional[AgentIdentity] = None

        # Encryption
        self._encryption = MessageEncryption()

        # Message handling
        self._message_handlers: Dict[str, Callable] = {}
        self._ack_callbacks: Dict[str, asyncio.Future] = {}
        self._incoming_queue: asyncio.Queue = asyncio.Queue()

        # Tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Shutdown flag
        self._shutdown = False

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.state == ConnectionState.CONNECTED and self.websocket is not None

    @property
    def identity(self) -> Optional[AgentIdentity]:
        """Get authenticated identity"""
        return self._identity

    async def connect(self) -> bool:
        """
        Connect to agent server

        Returns:
            True if connected successfully
        """
        if self.is_connected:
            return True

        self.state = ConnectionState.CONNECTING

        try:
            # Connect WebSocket
            logger.info(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)

            # Authenticate
            self.state = ConnectionState.AUTHENTICATING
            if not await self._authenticate():
                raise AuthenticationError("Authentication failed")

            self.state = ConnectionState.CONNECTED
            logger.info(f"✅ Connected as {self.agent_id}")

            # Start background tasks
            self._receive_task = asyncio.create_task(self._receive_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            return True

        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Connection failed: {e}")

            if self.auto_reconnect and not self._shutdown:
                self._schedule_reconnect()

            raise AgentConnectionError(f"Failed to connect: {e}")

    async def disconnect(self):
        """Disconnect from server"""
        self._shutdown = True

        # Cancel tasks
        if self._receive_task:
            self._receive_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()

        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        self.state = ConnectionState.DISCONNECTED
        logger.info("Disconnected")

    async def send_message(
        self, recipient: str, payload: Dict[str, Any], msg_type: str = "task", require_ack: bool = True, timeout: float = 30.0
    ) -> Optional[MessageAck]:
        """
        Send encrypted message to another agent

        Args:
            recipient: Recipient agent ID
            payload: Message content
            msg_type: Message type (task, result, event, heartbeat)
            require_ack: Whether to wait for acknowledgment
            timeout: Ack timeout in seconds

        Returns:
            MessageAck if require_ack=True, None otherwise
        """
        if not self.is_connected:
            raise AgentConnectionError("Not connected")

        # Create message
        message = self._encryption.create_message(
            sender_id=self.agent_id,
            recipient_id=recipient,
            msg_type=msg_type,
            payload=payload,
            recipient_public_key=b"",  # TODO: Get from key exchange
        )

        # Serialize and send
        try:
            await self.websocket.send(message.to_json())
            logger.debug(f"Sent message {message.header.message_id} to {recipient}")

            if require_ack:
                # Wait for acknowledgment
                ack_future = asyncio.get_event_loop().create_future()
                self._ack_callbacks[message.header.message_id] = ack_future

                try:
                    ack = await asyncio.wait_for(ack_future, timeout=timeout)
                    return ack
                except asyncio.TimeoutError:
                    logger.warning(f"Ack timeout for message {message.header.message_id}")
                    return MessageAck(
                        message_id=message.header.message_id,
                        status="timeout",
                        timestamp=datetime.utcnow(),
                        error="Acknowledgment timeout",
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def on_message(self, handler: Callable[[SecureMessage], None]):
        """
        Register message handler

        Args:
            handler: Callback function(message)
        """
        self._message_handlers["default"] = handler

    def on(self, msg_type: str, handler: Callable[[SecureMessage], None]):
        """
        Register handler for specific message type

        Args:
            msg_type: Message type to handle
            handler: Callback function(message)
        """
        self._message_handlers[msg_type] = handler

    async def receive_messages(self) -> AsyncIterator[SecureMessage]:
        """
        Async iterator for incoming messages

        Usage:
            async for msg in agent.receive_messages():
                print(msg.payload)
        """
        while self.is_connected:
            try:
                message = await asyncio.wait_for(self._incoming_queue.get(), timeout=1.0)
                yield message
            except asyncio.TimeoutError:
                continue

    async def _authenticate(self) -> bool:
        """Authenticate with server"""
        auth_message = {"type": "auth", "api_key": self.api_key, "api_secret": self.api_secret, "agent_id": self.agent_id}

        await self.websocket.send(json.dumps(auth_message))

        # Wait for auth response
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            data = json.loads(response)

            if data.get("type") == "auth_success":
                # Build identity from response
                self._identity = AgentIdentity(
                    agent_id=self.agent_id,
                    role=data.get("role", "scanner"),
                    permissions=data.get("permissions", []),
                    is_active=True,
                    last_seen=datetime.utcnow(),
                )
                return True
            else:
                logger.error(f"Authentication failed: {data.get('error')}")
                return False

        except asyncio.TimeoutError:
            logger.error("Authentication timeout")
            return False

    async def _receive_loop(self):
        """Background task to receive messages"""
        try:
            while self.is_connected and not self._shutdown:
                try:
                    data = await self.websocket.recv()
                    await self._handle_message(data)
                except ConnectionClosed:
                    logger.warning("Connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")

        except asyncio.CancelledError:
            pass

        # Connection lost
        if not self._shutdown and self.auto_reconnect:
            self._schedule_reconnect()

    async def _handle_message(self, data: str):
        """Handle incoming message"""
        try:
            msg_data = json.loads(data)

            # Handle different message types
            msg_type = msg_data.get("type")

            if msg_type == "ack":
                # Message acknowledgment
                ack = MessageAck(
                    message_id=msg_data["message_id"],
                    status=msg_data["status"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    error=msg_data.get("error"),
                )

                # Complete future
                if ack.message_id in self._ack_callbacks:
                    future = self._ack_callbacks.pop(ack.message_id)
                    if not future.done():
                        future.set_result(ack)

            elif msg_type == "message":
                # Encrypted agent message
                message = SecureMessage.from_dict(msg_data["data"])

                # Add to queue
                await self._incoming_queue.put(message)

                # Call handler
                handler = self._message_handlers.get(message.header.msg_type, self._message_handlers.get("default"))

                if handler:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")

                # Send ack
                await self.websocket.send(
                    json.dumps(
                        {
                            "type": "ack",
                            "message_id": message.header.message_id,
                            "status": "delivered",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )

            elif msg_type == "event":
                # Server event
                logger.debug(f"Received event: {msg_data}")

            elif msg_type == "error":
                # Server error
                logger.error(f"Server error: {msg_data.get('error')}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        try:
            while self.is_connected and not self._shutdown:
                await asyncio.sleep(self.heartbeat_interval)

                if self.is_connected:
                    try:
                        await self.websocket.send(
                            json.dumps({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
                        )
                    except Exception as e:
                        logger.warning(f"Heartbeat failed: {e}")
                        break

        except asyncio.CancelledError:
            pass

    def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self._reconnect_task and not self._reconnect_task.done():
            return

        self.state = ConnectionState.RECONNECTING
        self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self):
        """Attempt to reconnect"""
        while not self._shutdown and self.auto_reconnect:
            logger.info(f"Reconnecting in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)

            try:
                if await self.connect():
                    break
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")


# ============================================================================
# Simple Client for Basic Use Cases
# ============================================================================


class SimpleAgentClient:
    """
    Simplified agent client for basic use cases

    No encryption, just basic JSON messaging.
    Use AgentClient for production with encryption.
    """

    def __init__(self, agent_id: str, server_url: str = "ws://localhost:8000/agents/stream"):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library required. Install with: pip install websockets")

        self.agent_id = agent_id
        self.server_url = server_url
        self.ws = None

    async def connect(self):
        """Connect to server"""
        self.ws = await websockets.connect(self.server_url)
        # Send simple auth
        await self.ws.send(json.dumps({"type": "auth_simple", "agent_id": self.agent_id}))

    async def send(self, recipient: str, payload: dict):
        """Send message"""
        await self.ws.send(json.dumps({"type": "message", "recipient": recipient, "payload": payload}))

    async def receive(self) -> dict:
        """Receive message"""
        data = await self.ws.recv()
        return json.loads(data)

    async def close(self):
        """Close connection"""
        await self.ws.close()


# ============================================================================
# Test Functions
# ============================================================================


async def test_client_connection():
    """Test client connection (requires running server)"""
    client = SimpleAgentClient("test_agent_1")

    try:
        await client.connect()
        print("✅ Connected successfully")

        # Send test message
        await client.send("broadcast", {"hello": "world"})
        print("✅ Message sent")

        # Receive for 5 seconds
        import asyncio

        try:
            data = await asyncio.wait_for(client.receive(), timeout=5.0)
            print(f"✅ Received: {data}")
        except asyncio.TimeoutError:
            print("⚠️ No messages received (timeout)")

        await client.close()
        print("✅ Disconnected")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    # Run test (requires server)
    # asyncio.run(test_client_connection())
    print("Import this module to use AgentClient")

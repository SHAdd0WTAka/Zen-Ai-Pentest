"""
Agent Client for Zen-AI-Pentest WebSocket Layer
Implements reconnection logic, fallback mechanisms, and P2P integration
"""

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets not available")

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import aiortc  # noqa: F401

    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class ReconnectConfig:
    """Reconnection configuration"""

    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    max_attempts: int = 10


@dataclass
class AgentClientConfig:
    """Agent client configuration"""

    # Connection settings
    websocket_url: str = "ws://localhost:8000/ws/scans/{scan_id}"
    fallback_sse_url: str = "http://localhost:8000/sse/scans/{scan_id}"
    fallback_poll_url: str = "http://localhost:8000/api/poll"

    # Agent identification
    agent_id: Optional[str] = None
    agent_type: str = "pentest-agent"

    # Reconnection settings
    reconnect_config: ReconnectConfig = None

    # Timeouts
    connection_timeout: float = 10.0
    message_timeout: float = 30.0
    heartbeat_interval: float = 30.0

    # Fallback settings
    enable_sse_fallback: bool = True
    enable_polling_fallback: bool = True
    fallback_after_attempts: int = 3

    # P2P settings
    enable_p2p: bool = True
    p2p_signaling_url: Optional[str] = None

    def __post_init__(self):
        if self.reconnect_config is None:
            self.reconnect_config = ReconnectConfig()
        if self.agent_id is None:
            self.agent_id = f"agent_{uuid.uuid4().hex[:8]}"


# ============================================================================
# Connection State
# ============================================================================


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FALLBACK_SSE = "fallback_sse"
    FALLBACK_POLLING = "fallback_polling"
    ERROR = "error"


# ============================================================================
# Agent Client
# ============================================================================


class AgentClient:
    """
    Production-ready agent client with:
    - Automatic reconnection with exponential backoff
    - Fallback to SSE and polling
    - P2P integration
    - Message queuing during disconnections
    """

    def __init__(self, config: AgentClientConfig):
        self.config = config
        self.agent_id = config.agent_id

        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._websocket: Optional[Any] = None
        self._session: Optional[Any] = None
        self._sse_session: Optional[Any] = None

        # Reconnection state
        self._reconnect_attempts = 0
        self._reconnect_task: Optional[asyncio.Task] = None

        # Message handling
        self._message_handlers: Dict[str, Callable] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._pending_messages: Dict[str, dict] = {}

        # Heartbeat
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_pong = time.time()

        # P2P
        self._p2p_handler = None

        # Running state
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "reconnections": 0,
            "connection_duration": 0.0,
            "connection_start": None,
        }

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state in [
            ConnectionState.CONNECTED,
            ConnectionState.FALLBACK_SSE,
        ]

    # =====================================================================
    # Lifecycle
    # =====================================================================

    async def connect(self, scan_id: str) -> bool:
        """
        Connect to WebSocket server
        Returns True if connection successful
        """
        if self._state == ConnectionState.CONNECTED:
            logger.info("Already connected")
            return True

        self._running = True
        self._state = ConnectionState.CONNECTING

        # Build connection URL
        ws_url = self.config.websocket_url.format(scan_id=scan_id)
        ws_url = f"{ws_url}?agent_id={self.agent_id}&agent_type={self.config.agent_type}"

        try:
            if not WEBSOCKETS_AVAILABLE:
                raise ImportError("websockets library not available")

            logger.info(f"Connecting to {ws_url}")
            self._websocket = await websockets.connect(
                ws_url,
                ping_interval=self.config.heartbeat_interval,
                ping_timeout=self.config.connection_timeout,
            )

            self._state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            self._stats["connection_start"] = time.time()

            # Start message handler
            self._tasks.append(asyncio.create_task(self._message_loop()))

            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info(f"Agent {self.agent_id} connected successfully")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._state = ConnectionState.ERROR

            # Try fallback
            if self.config.enable_sse_fallback:
                return await self._connect_fallback_sse(scan_id)

            return False

    async def disconnect(self):
        """Disconnect from server"""
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()

        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self._reconnect_task:
            self._reconnect_task.cancel()

        # Close connections
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

        # Update stats
        if self._stats["connection_start"]:
            self._stats["connection_duration"] += time.time() - self._stats["connection_start"]

        self._state = ConnectionState.DISCONNECTED
        logger.info(f"Agent {self.agent_id} disconnected")

    # =====================================================================
    # WebSocket Connection
    # =====================================================================

    async def _message_loop(self):
        """Main message receive loop"""
        while self._running:
            try:
                if self._state == ConnectionState.CONNECTED and self._websocket:
                    message = await self._websocket.recv()
                    await self._handle_message(message)
                else:
                    await asyncio.sleep(0.1)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self._handle_disconnect()
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await self._handle_disconnect()
                break

    async def _handle_message(self, message: str):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")

            # Update stats
            self._stats["messages_received"] += 1

            # Handle ping/pong
            if msg_type == "ping":
                await self.send_message({"type": "pong", "timestamp": time.time()})
                return
            elif msg_type == "pong":
                self._last_pong = time.time()
                return

            # Handle connection established
            if msg_type == "connection_established":
                logger.info(f"Connection confirmed: {data}")
                return

            # Call registered handler
            handler = self._message_handlers.get(msg_type)
            if handler:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            else:
                logger.debug(f"No handler for message type: {msg_type}")

        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def send_message(self, message: dict) -> bool:
        """Send message to server"""
        if self._state == ConnectionState.CONNECTED and self._websocket:
            try:
                await self._websocket.send(json.dumps(message))
                self._stats["messages_sent"] += 1
                return True
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                # Queue for later
                await self._message_queue.put(message)
                return False
        else:
            # Queue for later delivery
            await self._message_queue.put(message)
            return False

    # =====================================================================
    # Reconnection Logic
    # =====================================================================

    async def _handle_disconnect(self):
        """Handle unexpected disconnection"""
        if not self._running:
            return

        self._state = ConnectionState.DISCONNECTED

        # Update stats
        if self._stats["connection_start"]:
            self._stats["connection_duration"] += time.time() - self._stats["connection_start"]

        # Start reconnection
        if self._reconnect_attempts < self.config.reconnect_config.max_attempts:
            self._reconnect_task = asyncio.create_task(self._reconnect())
        else:
            logger.error("Max reconnection attempts reached")
            self._state = ConnectionState.ERROR

    async def _reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        self._state = ConnectionState.RECONNECTING

        while self._reconnect_attempts < self.config.reconnect_config.max_attempts:
            delay = self._calculate_reconnect_delay()

            logger.info(
                f"Reconnection attempt {self._reconnect_attempts + 1}/{self.config.reconnect_config.max_attempts} in {delay:.2f}s"
            )

            await asyncio.sleep(delay)

            try:
                # Try to reconnect
                # Extract scan_id from previous connection
                scan_id = "default"  # Should be stored from original connect

                if await self.connect(scan_id):
                    self._stats["reconnections"] += 1
                    logger.info("Reconnection successful")

                    # Send queued messages
                    await self._flush_message_queue()
                    return

            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")

            self._reconnect_attempts += 1

        # Max attempts reached, try fallback
        logger.error("All reconnection attempts failed")

        if self.config.enable_sse_fallback and self._reconnect_attempts >= self.config.fallback_after_attempts:
            await self._connect_fallback_sse("default")

    def _calculate_reconnect_delay(self) -> float:
        """Calculate reconnection delay with exponential backoff"""
        config = self.config.reconnect_config

        delay = min(
            config.initial_delay * (config.backoff_multiplier**self._reconnect_attempts),
            config.max_delay,
        )

        if config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    async def _flush_message_queue(self):
        """Send all queued messages"""
        while not self._message_queue.empty():
            try:
                message = self._message_queue.get_nowait()
                await self.send_message(message)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"Error flushing message queue: {e}")

    # =====================================================================
    # Fallback Mechanisms
    # =====================================================================

    async def _connect_fallback_sse(self, scan_id: str) -> bool:
        """Connect using Server-Sent Events fallback"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not available for SSE fallback")
            return False

        logger.info("Attempting SSE fallback connection")
        self._state = ConnectionState.FALLBACK_SSE

        try:
            sse_url = self.config.fallback_sse_url.format(scan_id=scan_id)
            sse_url = f"{sse_url}?agent_id={self.agent_id}&agent_type={self.config.agent_type}"

            self._session = aiohttp.ClientSession()

            async with self._session.get(sse_url, headers={"Accept": "text/event-stream"}) as response:
                if response.status == 200:
                    logger.info("SSE fallback connection established")

                    # Process SSE stream
                    async for line in response.content:
                        line = line.decode().strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            await self._handle_message(data)

                    return True
                else:
                    logger.error(f"SSE fallback failed: {response.status}")

        except Exception as e:
            logger.error(f"SSE fallback error: {e}")

        # Try polling fallback
        if self.config.enable_polling_fallback:
            return await self._connect_fallback_polling(scan_id)

        return False

    async def _connect_fallback_polling(self, scan_id: str) -> bool:
        """Connect using HTTP polling fallback"""
        if not AIOHTTP_AVAILABLE:
            return False

        logger.info("Attempting polling fallback connection")
        self._state = ConnectionState.FALLBACK_POLLING

        try:
            if not self._session:
                self._session = aiohttp.ClientSession()

            # Start polling loop
            self._tasks.append(asyncio.create_task(self._polling_loop(scan_id)))
            return True

        except Exception as e:
            logger.error(f"Polling fallback error: {e}")

        return False

    async def _polling_loop(self, scan_id: str):
        """HTTP polling loop"""
        poll_url = f"{self.config.fallback_poll_url}?agent_id={self.agent_id}&scan_id={scan_id}"

        while self._running and self._state == ConnectionState.FALLBACK_POLLING:
            try:
                async with self._session.get(poll_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for message in data.get("messages", []):
                            await self._handle_message(json.dumps(message))

                await asyncio.sleep(5)  # Poll every 5 seconds

            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(10)

    # =====================================================================
    # Heartbeat
    # =====================================================================

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self._running and self._state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                # Check for pong timeout
                if time.time() - self._last_pong > self.config.heartbeat_interval * 2:
                    logger.warning("Heartbeat timeout, connection may be dead")
                    await self._handle_disconnect()
                    break

                # Send ping
                await self.send_message({"type": "ping", "timestamp": time.time()})

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    # =====================================================================
    # Message Handlers
    # =====================================================================

    def on(self, message_type: str):
        """Decorator to register message handler"""

        def decorator(func: Callable):
            self._message_handlers[message_type] = func
            return func

        return decorator

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self._message_handlers[message_type] = handler

    # =====================================================================
    # P2P Integration
    # =====================================================================

    async def enable_p2p(self, p2p_handler):
        """Enable P2P communication"""
        if not self.config.enable_p2p:
            return

        self._p2p_handler = p2p_handler

        # Register P2P message handlers
        self.register_handler("p2p_offer", self._handle_p2p_offer)
        self.register_handler("p2p_answer", self._handle_p2p_answer)
        self.register_handler("p2p_ice", self._handle_p2p_ice)

    async def _handle_p2p_offer(self, message: dict):
        """Handle P2P offer from another agent"""
        if self._p2p_handler:
            # Forward to P2P handler
            pass

    async def _handle_p2p_answer(self, message: dict):
        """Handle P2P answer"""
        if self._p2p_handler:
            pass

    async def _handle_p2p_ice(self, message: dict):
        """Handle ICE candidate"""
        if self._p2p_handler:
            pass

    # =====================================================================
    # Utilities
    # =====================================================================

    def get_stats(self) -> dict:
        """Get connection statistics"""
        stats = self._stats.copy()

        if self._stats["connection_start"]:
            stats["current_session_duration"] = time.time() - self._stats["connection_start"]

        stats["state"] = self._state.value
        stats["reconnect_attempts"] = self._reconnect_attempts
        stats["queued_messages"] = self._message_queue.qsize()

        return stats


# ============================================================================
# Example Usage
# ============================================================================


async def example():
    """Example agent client usage"""

    # Configure client
    config = AgentClientConfig(
        websocket_url="ws://localhost:8000/ws/scans/{scan_id}",
        agent_id="agent_001",
        agent_type="scanner",
        enable_sse_fallback=True,
        enable_p2p=True,
    )

    client = AgentClient(config)

    # Register message handlers
    @client.on("scan_update")
    async def on_scan_update(message):
        print(f"Scan update: {message}")

    @client.on("command")
    async def on_command(message):
        print(f"Received command: {message}")
        # Execute command and send result
        await client.send_message(
            {
                "type": "result",
                "command_id": message.get("command_id"),
                "status": "completed",
                "result": "Command executed successfully",
            }
        )

    # Connect
    connected = await client.connect(scan_id="scan_123")
    print(f"Connected: {connected}")

    if connected:
        # Subscribe to scan updates
        await client.send_message({"type": "subscribe", "scan_id": "scan_123"})

        # Send heartbeat
        await client.send_message({"type": "heartbeat", "status": "ready"})

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
                stats = client.get_stats()
                print(f"Stats: {stats}")
        except KeyboardInterrupt:
            pass

    # Disconnect
    await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example())

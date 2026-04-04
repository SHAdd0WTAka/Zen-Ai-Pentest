"""
🌐 P2P WebRTC Connection Handler.

Manages peer-to-peer connections using WebRTC.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from aiortc import RTCPeerConnection, RTCSessionDescription

logger = logging.getLogger(__name__)


@dataclass
class P2PConfig:
    """Configuration for P2P connection."""

    stun_servers: list = None
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 60

    def __post_init__(self):
        if self.stun_servers is None:
            self.stun_servers = [
                "stun:stun.l.google.com:19302",
                "stun:stun.cloudflare.com:3478",
            ]


class P2PConnection:
    """
    WebRTC P2P connection handler.

    Manages direct peer-to-peer connection with mobile device.
    """

    def __init__(self, config: Optional[P2PConfig] = None):
        self.config = config or P2PConfig()
        self.pc: Optional[RTCPeerConnection] = None
        self.channel: Optional[Any] = None
        self._on_message_handler: Optional[Callable] = None
        self._on_connect_handler: Optional[Callable] = None
        self._on_disconnect_handler: Optional[Callable] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_heartbeat: float = 0
        self._connected = False

    async def create_offer(self) -> Dict[str, str]:
        """
        Create WebRTC offer for mobile connection.

        Returns:
            Dict with 'sdp' and 'type'
        """
        # Create peer connection
        self.pc = RTCPeerConnection({"iceServers": [{"urls": self.config.stun_servers}]})

        # Setup connection handlers
        self._setup_handlers()

        # Create data channel
        self.channel = self.pc.createDataChannel("secure", {"ordered": True, "maxRetransmits": 3})

        self._setup_channel_handlers(self.channel)

        # Create offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # Wait for ICE gathering
        await self._wait_for_ice_gathering()

        return {
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type,
        }

    async def handle_answer(self, answer_sdp: str) -> bool:
        """
        Handle answer from mobile device.

        Args:
            answer_sdp: SDP answer from mobile

        Returns:
            True if successful
        """
        if not self.pc:
            raise RuntimeError("No peer connection")

        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

        logger.info("📡 P2P Answer received, establishing connection...")
        return True

    async def handle_offer(self, offer_sdp: str) -> Dict[str, str]:
        """
        Handle offer from mobile (for incoming connections).

        Args:
            offer_sdp: SDP offer from mobile

        Returns:
            Answer SDP
        """
        # Create peer connection
        self.pc = RTCPeerConnection({"iceServers": [{"urls": self.config.stun_servers}]})

        # Setup handlers
        self._setup_handlers()

        # Handle data channel from mobile
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"📨 Data channel received: {channel.label}")
            self.channel = channel
            self._setup_channel_handlers(channel)

        # Set remote description
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self.pc.setRemoteDescription(offer)

        # Create answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # Wait for ICE gathering
        await self._wait_for_ice_gathering()

        return {
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type,
        }

    def _setup_handlers(self):
        """Setup WebRTC connection handlers."""

        @self.pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            state = self.pc.iceConnectionState
            logger.info(f"🧊 ICE state: {state}")

            if state == "connected":
                logger.info("✅ P2P Connected!")
                self._connected = True
                if self._on_connect_handler:
                    await self._on_connect_handler()

            elif state == "failed" or state == "disconnected":
                logger.warning(f"❌ P2P {state}")
                self._connected = False
                if self._on_disconnect_handler:
                    await self._on_disconnect_handler()

        @self.pc.on("connectionstatechange")
        async def on_connection_state_change():
            state = self.pc.connectionState
            logger.info(f"🔗 Connection state: {state}")

            if state == "connected":
                self._start_heartbeat()

    def _setup_channel_handlers(self, channel):
        """Setup data channel handlers."""

        @channel.on("open")
        def on_open():
            logger.info("🔓 Data channel open!")
            self._connected = True
            self._last_heartbeat = time.time()

        @channel.on("close")
        def on_close():
            logger.warning("🔒 Data channel closed!")
            self._connected = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()

        @channel.on("message")
        async def on_message(msg):
            try:
                data = json.loads(msg)

                # Handle heartbeat
                if data.get("type") == "heartbeat":
                    self._last_heartbeat = time.time()
                    # Send ACK
                    await self.send({"type": "heartbeat_ack"})

                # Forward to handler
                if self._on_message_handler:
                    await self._on_message_handler(data)

            except json.JSONDecodeError:
                logger.warning(f"Invalid message: {msg}")

    async def _wait_for_ice_gathering(self, timeout: float = 5.0) -> bool:
        """Wait for ICE candidate gathering to complete."""
        if not self.pc:
            return False

        # Wait for gathering to complete
        start = time.time()
        while self.pc.iceGatheringState != "complete":
            if time.time() - start > timeout:
                logger.warning("ICE gathering timeout")
                return False
            await asyncio.sleep(0.1)

        return True

    def _start_heartbeat(self):
        """Start sending heartbeats."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        """Heartbeat loop."""
        while self._connected:
            try:
                await self.send(
                    {
                        "type": "heartbeat",
                        "timestamp": time.time(),
                        "source": "local",
                    }
                )
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def send(self, data: Dict) -> bool:
        """
        Send data over P2P channel.

        Args:
            data: Data to send

        Returns:
            True if sent
        """
        if not self.channel or not self._connected:
            logger.warning("Cannot send: channel not open")
            return False

        try:
            msg = json.dumps(data)
            self.channel.send(msg)
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    def on_message(self, handler: Callable):
        """Register message handler."""
        self._on_message_handler = handler

    def on_connect(self, handler: Callable):
        """Register connect handler."""
        self._on_connect_handler = handler

    def on_disconnect(self, handler: Callable):
        """Register disconnect handler."""
        self._on_disconnect_handler = handler

    def is_connected(self) -> bool:
        """Check if P2P connection is active."""
        return self._connected and (time.time() - self._last_heartbeat) < self.config.heartbeat_timeout

    def get_stats(self) -> Dict:
        """Get connection statistics."""
        return {
            "connected": self._connected,
            "ice_state": self.pc.iceConnectionState if self.pc else "unknown",
            "last_heartbeat": self._last_heartbeat,
            "heartbeat_age": (time.time() - self._last_heartbeat if self._last_heartbeat else None),
        }

    async def close(self):
        """Close P2P connection."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.channel:
            self.channel.close()

        if self.pc:
            await self.pc.close()

        self._connected = False
        logger.info("🔒 P2P Connection closed")


# Convenience function
async def create_p2p_connection(
    config: Optional[P2PConfig] = None,
) -> P2PConnection:
    """Create and return P2P connection."""
    return P2PConnection(config)

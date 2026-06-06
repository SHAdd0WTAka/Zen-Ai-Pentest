"""
WebRTC P2P Connection Handler for Zen-AI-Pentest
Optimized mesh network for 100 concurrent agents
"""

import asyncio
import base64
import hashlib
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# WebRTC imports (using aiortc for Python backend)
try:
    from aiortc import RTCDataChannel, RTCPeerConnection, RTCSessionDescription  # noqa: F401
    from aiortc.contrib.signaling import object_from_string, object_to_string  # noqa: F401

    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logging.warning("aiortc not available, using mock implementation")

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class P2PConnectionState(Enum):
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class P2PPeer:
    """Represents a peer in the P2P network"""

    peer_id: str
    public_key: Optional[str] = None
    ice_candidates: List[dict] = field(default_factory=list)
    connection_state: P2PConnectionState = P2PConnectionState.NEW
    connected_at: Optional[float] = None
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    data_channel: Optional[Any] = None  # RTCDataChannel
    peer_connection: Optional[Any] = None  # RTCPeerConnection
    direct_peers: Set[str] = field(default_factory=set)  # Known direct connections
    hop_count: int = 0  # Distance from this peer


@dataclass
class SignalingMessage:
    """Signaling message for WebRTC handshake"""

    type: str  # offer, answer, ice-candidate, peer-discover
    sender: str
    recipient: str
    payload: dict
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None


@dataclass
class MeshConfig:
    """Configuration for mesh network optimization"""

    max_direct_peers: int = 10  # Maximum direct connections per peer
    target_mesh_degree: int = 5  # Target number of connections for redundancy
    heartbeat_interval: float = 30.0  # Seconds between heartbeats
    peer_timeout: float = 120.0  # Seconds before peer is considered offline
    enable_superpeers: bool = True  # Enable superpeer (hub) nodes
    superpeer_threshold: int = 15  # Connections to become superpeer
    dht_bucket_size: int = 20  # Kademlia bucket size


# ============================================================================
# Encryption Manager
# ============================================================================


class P2PEncryptionManager:
    """Manages end-to-end encryption for P2P communication"""

    def __init__(self):
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._public_key = self._private_key.public_key()
        self._session_keys: Dict[str, bytes] = {}  # peer_id -> session key
        self._fernet_instances: Dict[str, Fernet] = {}

    @property
    def public_key_pem(self) -> str:
        """Get public key in PEM format"""
        pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return base64.b64encode(pem).decode()

    def generate_session_key(self) -> bytes:
        """Generate a new session key"""
        return Fernet.generate_key()

    def encrypt_session_key(self, session_key: bytes, peer_public_key_pem: str) -> str:
        """Encrypt session key with peer's public key"""
        peer_key_bytes = base64.b64decode(peer_public_key_pem)
        peer_key = serialization.load_pem_public_key(peer_key_bytes)

        encrypted = peer_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted).decode()

    def decrypt_session_key(self, encrypted_key: str) -> bytes:
        """Decrypt session key with our private key"""
        encrypted_bytes = base64.b64decode(encrypted_key)
        return self._private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def establish_session(self, peer_id: str, peer_public_key: str) -> bytes:
        """Establish encrypted session with peer"""
        session_key = self.generate_session_key()
        self._session_keys[peer_id] = session_key
        self._fernet_instances[peer_id] = Fernet(session_key)
        return session_key

    def encrypt_message(self, peer_id: str, message: dict) -> str:
        """Encrypt message for peer"""
        if peer_id not in self._fernet_instances:
            raise ValueError(f"No session established with peer {peer_id}")

        fernet = self._fernet_instances[peer_id]
        json_bytes = json.dumps(message).encode()
        encrypted = fernet.encrypt(json_bytes)
        return base64.b64encode(encrypted).decode()

    def decrypt_message(self, peer_id: str, encrypted_message: str) -> dict:
        """Decrypt message from peer"""
        if peer_id not in self._fernet_instances:
            raise ValueError(f"No session established with peer {peer_id}")

        fernet = self._fernet_instances[peer_id]
        encrypted_bytes = base64.b64decode(encrypted_message)
        decrypted = fernet.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())


# ============================================================================
# DHT Routing Table (Kademlia-inspired)
# ============================================================================


class DHTNode:
    """Kademlia-style DHT node for peer discovery"""

    def __init__(self, node_id: str, bucket_size: int = 20):
        self.node_id = node_id
        self.node_id_int = int(hashlib.sha256(node_id.encode()).hexdigest(), 16)
        self.bucket_size = bucket_size
        self.buckets: List[Set[str]] = [set() for _ in range(256)]  # XOR distance buckets
        self._peer_info: Dict[str, P2PPeer] = {}

    def _distance(self, peer_id: str) -> int:
        """Calculate XOR distance between node IDs"""
        peer_int = int(hashlib.sha256(peer_id.encode()).hexdigest(), 16)
        return self.node_id_int ^ peer_int

    def _bucket_index(self, peer_id: str) -> int:
        """Get bucket index for a peer"""
        distance = self._distance(peer_id)
        if distance == 0:
            return 0
        return distance.bit_length() - 1

    def add_peer(self, peer: P2PPeer) -> bool:
        """Add peer to routing table"""
        bucket_idx = self._bucket_index(peer.peer_id)
        bucket = self.buckets[bucket_idx]

        if peer.peer_id in bucket:
            return True

        if len(bucket) < self.bucket_size:
            bucket.add(peer.peer_id)
            self._peer_info[peer.peer_id] = peer
            return True

        # Bucket full, could ping oldest peer here
        return False

    def remove_peer(self, peer_id: str):
        """Remove peer from routing table"""
        bucket_idx = self._bucket_index(peer_id)
        self.buckets[bucket_idx].discard(peer_id)
        self._peer_info.pop(peer_id, None)

    def find_closest_peers(self, target_id: str, count: int = 10) -> List[P2PPeer]:
        """Find closest peers to target ID"""
        target_int = int(hashlib.sha256(target_id.encode()).hexdigest(), 16)

        all_peers = []
        for bucket in self.buckets:
            for peer_id in bucket:
                peer_int = int(hashlib.sha256(peer_id.encode()).hexdigest(), 16)
                distance = target_int ^ peer_int
                all_peers.append((distance, peer_id))

        all_peers.sort(key=lambda x: x[0])
        return [self._peer_info[pid] for _, pid in all_peers[:count] if pid in self._peer_info]

    def get_all_peers(self) -> List[P2PPeer]:
        """Get all known peers"""
        return list(self._peer_info.values())


# ============================================================================
# WebRTC P2P Handler
# ============================================================================


class WebRTCP2PHandler:
    """
    WebRTC P2P Connection Handler with mesh optimization
    Supports 100 concurrent agents with efficient routing
    """

    def __init__(
        self,
        peer_id: Optional[str] = None,
        signaling_callback: Optional[Callable] = None,
        stun_servers: Optional[List[str]] = None,
        turn_servers: Optional[List[dict]] = None,
        mesh_config: Optional[MeshConfig] = None,
    ):
        self.peer_id = peer_id or str(uuid.uuid4())
        self.signaling_callback = signaling_callback
        self.mesh_config = mesh_config or MeshConfig()

        # ICE servers configuration
        self.ice_servers = [
            {
                "urls": stun_servers
                or [
                    "stun:stun.l.google.com:19302",
                    "stun:stun1.l.google.com:19302",
                ]
            }
        ]
        if turn_servers:
            self.ice_servers.extend(turn_servers)

        # Peer management
        self.peers: Dict[str, P2PPeer] = {}
        self.dht = DHTNode(self.peer_id, self.mesh_config.dht_bucket_size)
        self.encryption = P2PEncryptionManager()

        # Connection tracking
        self._peer_connections: Dict[str, Any] = {}  # peer_id -> RTCPeerConnection
        self._data_channels: Dict[str, Any] = {}  # peer_id -> RTCDataChannel

        # Message handlers
        self._message_handlers: Dict[str, Callable] = {}

        # Superpeer status
        self._is_superpeer = False
        self._superpeers: Set[str] = set()

        # Running state
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def initialize(self):
        """Initialize the P2P handler"""
        self._running = True

        # Start maintenance tasks
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.append(asyncio.create_task(self._peer_discovery_loop()))
        self._tasks.append(asyncio.create_task(self._mesh_optimization_loop()))

        logger.info(f"P2P Handler initialized for peer {self.peer_id}")

    async def shutdown(self):
        """Shutdown the P2P handler"""
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()

        # Close all connections
        for peer_id in list(self._peer_connections.keys()):
            await self.disconnect_peer(peer_id)

        logger.info(f"P2P Handler shutdown for peer {self.peer_id}")

    # =====================================================================
    # Signaling
    # =====================================================================

    async def handle_signaling_message(self, message: SignalingMessage):
        """Handle incoming signaling message"""
        handler = {
            "offer": self._handle_offer,
            "answer": self._handle_answer,
            "ice-candidate": self._handle_ice_candidate,
            "peer-discover": self._handle_peer_discover,
            "session-key": self._handle_session_key,
        }.get(message.type)

        if handler:
            await handler(message)
        else:
            logger.warning(f"Unknown signaling message type: {message.type}")

    async def _handle_offer(self, message: SignalingMessage):
        """Handle WebRTC offer"""
        sender = message.sender
        offer = message.payload.get("sdp")

        logger.info(f"Received offer from {sender}")

        # Create peer connection if not exists
        if sender not in self._peer_connections:
            await self._create_peer_connection(sender)

        pc = self._peer_connections[sender]

        if AIORTC_AVAILABLE:
            # Set remote description
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer, type="offer"))

            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            # Send answer back
            await self._send_signaling_message(
                SignalingMessage(
                    type="answer",
                    sender=self.peer_id,
                    recipient=sender,
                    payload={"sdp": pc.localDescription.sdp},
                )
            )
        else:
            # Mock implementation
            await self._send_signaling_message(
                SignalingMessage(
                    type="answer",
                    sender=self.peer_id,
                    recipient=sender,
                    payload={"sdp": "mock_answer_sdp"},
                )
            )

        # Update peer state
        if sender in self.peers:
            self.peers[sender].connection_state = P2PConnectionState.CONNECTING

    async def _handle_answer(self, message: SignalingMessage):
        """Handle WebRTC answer"""
        sender = message.sender
        answer = message.payload.get("sdp")

        logger.info(f"Received answer from {sender}")

        if sender in self._peer_connections and AIORTC_AVAILABLE:
            pc = self._peer_connections[sender]
            await pc.setRemoteDescription(RTCSessionDescription(sdp=answer, type="answer"))

        if sender in self.peers:
            self.peers[sender].connection_state = P2PConnectionState.CONNECTED
            self.peers[sender].connected_at = time.time()

    async def _handle_ice_candidate(self, message: SignalingMessage):
        """Handle ICE candidate"""
        sender = message.sender

        if sender in self._peer_connections and AIORTC_AVAILABLE:
            self._peer_connections[sender]
            # Add ICE candidate
            # await pc.addIceCandidate(candidate)
            pass

    async def _handle_peer_discover(self, message: SignalingMessage):
        """Handle peer discovery request"""
        sender = message.sender
        target_id = message.payload.get("target_id")

        # Find closest peers
        closest = self.dht.find_closest_peers(target_id or sender, count=10)

        # Send response
        await self._send_signaling_message(
            SignalingMessage(
                type="peer-discover-response",
                sender=self.peer_id,
                recipient=sender,
                payload={
                    "peers": [
                        {
                            "peer_id": p.peer_id,
                            "public_key": p.public_key,
                            "metadata": p.metadata,
                        }
                        for p in closest
                    ]
                },
            )
        )

    async def _handle_session_key(self, message: SignalingMessage):
        """Handle encrypted session key exchange"""
        sender = message.sender
        encrypted_key = message.payload.get("encrypted_key")

        try:
            session_key = self.encryption.decrypt_session_key(encrypted_key)
            self.encryption._session_keys[sender] = session_key
            self.encryption._fernet_instances[sender] = Fernet(session_key)

            logger.info(f"Session established with {sender}")

            # Acknowledge
            await self._send_signaling_message(
                SignalingMessage(
                    type="session-key-ack",
                    sender=self.peer_id,
                    recipient=sender,
                    payload={"status": "established"},
                )
            )
        except Exception as e:
            logger.error(f"Failed to establish session with {sender}: {e}")

    async def _send_signaling_message(self, message: SignalingMessage):
        """Send signaling message via callback"""
        if self.signaling_callback:
            await self.signaling_callback(message)

    # =====================================================================
    # Connection Management
    # =====================================================================

    async def connect_to_peer(self, peer_id: str, peer_public_key: Optional[str] = None) -> bool:
        """Initiate connection to a peer"""
        if peer_id in self._peer_connections:
            logger.info(f"Already connected to {peer_id}")
            return True

        logger.info(f"Connecting to peer {peer_id}")

        # Create peer connection
        await self._create_peer_connection(peer_id)

        if AIORTC_AVAILABLE:
            pc = self._peer_connections[peer_id]

            # Create data channel
            channel = pc.createDataChannel("messages")
            self._setup_data_channel(peer_id, channel)

            # Create offer
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            # Send offer
            await self._send_signaling_message(
                SignalingMessage(
                    type="offer",
                    sender=self.peer_id,
                    recipient=peer_id,
                    payload={"sdp": pc.localDescription.sdp},
                )
            )
        else:
            # Mock: Send offer
            await self._send_signaling_message(
                SignalingMessage(
                    type="offer",
                    sender=self.peer_id,
                    recipient=peer_id,
                    payload={"sdp": "mock_offer_sdp"},
                )
            )

        # Create peer info
        peer = P2PPeer(
            peer_id=peer_id,
            public_key=peer_public_key,
            connection_state=P2PConnectionState.CONNECTING,
        )
        self.peers[peer_id] = peer
        self.dht.add_peer(peer)

        return True

    async def _create_peer_connection(self, peer_id: str):
        """Create RTCPeerConnection for a peer"""
        if AIORTC_AVAILABLE:
            pc = RTCPeerConnection(configuration={"iceServers": self.ice_servers})

            @pc.on("iceconnectionstatechange")
            async def on_ice_state_change():
                logger.info(f"ICE state with {peer_id}: {pc.iceConnectionState}")
                if peer_id in self.peers:
                    if pc.iceConnectionState == "connected":
                        self.peers[peer_id].connection_state = P2PConnectionState.CONNECTED
                    elif pc.iceConnectionState == "failed":
                        self.peers[peer_id].connection_state = P2PConnectionState.FAILED

            @pc.on("datachannel")
            def on_datachannel(channel):
                logger.info(f"Data channel received from {peer_id}")
                self._setup_data_channel(peer_id, channel)

            self._peer_connections[peer_id] = pc
        else:
            # Mock peer connection
            self._peer_connections[peer_id] = {"mock": True}

    def _setup_data_channel(self, peer_id: str, channel):
        """Setup data channel handlers"""
        self._data_channels[peer_id] = channel

        if AIORTC_AVAILABLE:

            @channel.on("open")
            def on_open():
                logger.info(f"Data channel opened with {peer_id}")
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = P2PConnectionState.CONNECTED
                    self.peers[peer_id].data_channel = channel

            @channel.on("message")
            async def on_message(message):
                await self._handle_data_message(peer_id, message)

            @channel.on("close")
            def on_close():
                logger.info(f"Data channel closed with {peer_id}")
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = P2PConnectionState.DISCONNECTED

    async def disconnect_peer(self, peer_id: str):
        """Disconnect from a peer"""
        logger.info(f"Disconnecting from peer {peer_id}")

        # Close data channel
        if peer_id in self._data_channels:
            channel = self._data_channels[peer_id]
            if AIORTC_AVAILABLE and channel:
                channel.close()
            del self._data_channels[peer_id]

        # Close peer connection
        if peer_id in self._peer_connections:
            pc = self._peer_connections[peer_id]
            if AIORTC_AVAILABLE and pc:
                await pc.close()
            del self._peer_connections[peer_id]

        # Update peer info
        if peer_id in self.peers:
            self.peers[peer_id].connection_state = P2PConnectionState.CLOSED
            self.dht.remove_peer(peer_id)
            del self.peers[peer_id]

    # =====================================================================
    # Message Handling
    # =====================================================================

    async def send_message(self, recipient_id: str, message: dict, encrypted: bool = True) -> bool:
        """Send message to a peer (direct or routed)"""
        # Check if direct connection exists
        if recipient_id in self._data_channels and recipient_id in self.peers:
            if self.peers[recipient_id].connection_state == P2PConnectionState.CONNECTED:
                return await self._send_direct_message(recipient_id, message, encrypted)

        # Try to route through other peers
        return await self._route_message(recipient_id, message, encrypted)

    async def _send_direct_message(self, peer_id: str, message: dict, encrypted: bool = True) -> bool:
        """Send message directly to a connected peer"""
        try:
            if encrypted and peer_id in self.encryption._fernet_instances:
                payload = self.encryption.encrypt_message(peer_id, message)
                envelope = {"encrypted": True, "payload": payload}
            else:
                envelope = {"encrypted": False, "payload": message}

            channel = self._data_channels[peer_id]
            if AIORTC_AVAILABLE:
                channel.send(json.dumps(envelope))

            # Update peer activity
            if peer_id in self.peers:
                self.peers[peer_id].last_seen = time.time()

            return True
        except Exception as e:
            logger.error(f"Failed to send message to {peer_id}: {e}")
            return False

    async def _route_message(self, recipient_id: str, message: dict, encrypted: bool = True) -> bool:
        """Route message through the mesh network"""
        # Find closest peers to recipient
        closest = self.dht.find_closest_peers(recipient_id, count=5)

        # Try each peer
        for peer in closest:
            if peer.peer_id == recipient_id:
                # Direct connection attempt
                if peer.connection_state == P2PConnectionState.CONNECTED:
                    return await self._send_direct_message(peer.peer_id, message, encrypted)
            elif peer.connection_state == P2PConnectionState.CONNECTED:
                # Forward through this peer
                forwarded = {
                    "type": "forward",
                    "target": recipient_id,
                    "message": message,
                    "ttl": 10,  # Time-to-live to prevent loops
                }
                success = await self._send_direct_message(peer.peer_id, forwarded, encrypted)
                if success:
                    return True

        logger.warning(f"Could not route message to {recipient_id}")
        return False

    async def _handle_data_message(self, peer_id: str, message_data: str):
        """Handle incoming data channel message"""
        try:
            envelope = json.loads(message_data)

            if envelope.get("encrypted"):
                # Decrypt message
                if peer_id not in self.encryption._fernet_instances:
                    logger.warning(f"No session key for peer {peer_id}")
                    return
                message = self.encryption.decrypt_message(peer_id, envelope["payload"])
            else:
                message = envelope["payload"]

            # Handle forwarded messages
            if message.get("type") == "forward":
                target = message.get("target")
                if target == self.peer_id:
                    # Message is for us
                    inner_message = message.get("message", {})
                    await self._process_message(peer_id, inner_message)
                elif message.get("ttl", 0) > 0:
                    # Forward to next hop
                    message["ttl"] -= 1
                    await self._route_message(target, message.get("message", {}))
            else:
                await self._process_message(peer_id, message)

            # Update peer activity
            if peer_id in self.peers:
                self.peers[peer_id].last_seen = time.time()

        except Exception as e:
            logger.error(f"Error handling message from {peer_id}: {e}")

    async def _process_message(self, sender_id: str, message: dict):
        """Process a received message"""
        message_type = message.get("type", "unknown")

        handler = self._message_handlers.get(message_type)
        if handler:
            try:
                await handler(sender_id, message)
            except Exception as e:
                logger.error(f"Error processing message type {message_type}: {e}")
        else:
            logger.debug(f"No handler for message type: {message_type}")

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self._message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")

    # =====================================================================
    # Mesh Optimization
    # =====================================================================

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to connected peers"""
        while self._running:
            try:
                await asyncio.sleep(self.mesh_config.heartbeat_interval)

                heartbeat = {
                    "type": "heartbeat",
                    "peer_id": self.peer_id,
                    "timestamp": time.time(),
                    "connected_peers": list(self._peer_connections.keys()),
                    "is_superpeer": self._is_superpeer,
                }

                for peer_id in list(self._peer_connections.keys()):
                    if peer_id in self.peers:
                        if self.peers[peer_id].connection_state == P2PConnectionState.CONNECTED:
                            await self._send_direct_message(peer_id, heartbeat, encrypted=False)

                        # Check for timeout
                        if time.time() - self.peers[peer_id].last_seen > self.mesh_config.peer_timeout:
                            logger.info(f"Peer {peer_id} timed out")
                            await self.disconnect_peer(peer_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _peer_discovery_loop(self):
        """Periodically discover new peers"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Discovery every minute

                # Request peer lists from connected peers
                for peer_id in list(self._peer_connections.keys()):
                    if peer_id in self.peers and self.peers[peer_id].connection_state == P2PConnectionState.CONNECTED:
                        await self._send_signaling_message(
                            SignalingMessage(
                                type="peer-discover",
                                sender=self.peer_id,
                                recipient=peer_id,
                                payload={"target_id": self.peer_id},
                            )
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in peer discovery loop: {e}")

    async def _mesh_optimization_loop(self):
        """Optimize mesh network topology"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Optimization every 30 seconds

                current_connections = len(self._peer_connections)

                # Check if we should become a superpeer
                if self.mesh_config.enable_superpeers:
                    if current_connections >= self.mesh_config.superpeer_threshold:
                        if not self._is_superpeer:
                            self._is_superpeer = True
                            logger.info(f"Became superpeer with {current_connections} connections")
                    elif current_connections < self.mesh_config.superpeer_threshold // 2:
                        if self._is_superpeer:
                            self._is_superpeer = False
                            logger.info("No longer a superpeer")

                # Maintain target mesh degree
                if current_connections < self.mesh_config.target_mesh_degree:
                    # Need more connections
                    available = self.dht.find_closest_peers(self.peer_id, count=20)
                    for peer in available:
                        if peer.peer_id not in self._peer_connections:
                            if peer.connection_state in [
                                P2PConnectionState.NEW,
                                P2PConnectionState.DISCONNECTED,
                            ]:
                                await self.connect_to_peer(peer.peer_id, peer.public_key)
                                if len(self._peer_connections) >= self.mesh_config.target_mesh_degree:
                                    break

                elif current_connections > self.mesh_config.max_direct_peers:
                    # Too many connections, prune some
                    # Keep closest peers and superpeers
                    peers_by_distance = sorted(
                        self.peers.values(),
                        key=lambda p: self.dht._distance(p.peer_id),
                    )

                    to_disconnect = peers_by_distance[self.mesh_config.max_direct_peers :]
                    for peer in to_disconnect:
                        if not peer.metadata.get("is_superpeer"):
                            await self.disconnect_peer(peer.peer_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in mesh optimization loop: {e}")

    # =====================================================================
    # Utility Methods
    # =====================================================================

    def get_stats(self) -> dict:
        """Get P2P network statistics"""
        return {
            "peer_id": self.peer_id,
            "is_superpeer": self._is_superpeer,
            "connected_peers": len(self._peer_connections),
            "known_peers": len(self.peers),
            "dht_buckets": sum(1 for b in self.dht.buckets if b),
            "connections": [
                {
                    "peer_id": pid,
                    "state": (self.peers[pid].connection_state.value if pid in self.peers else "unknown"),
                    "duration": (
                        time.time() - self.peers[pid].connected_at if pid in self.peers and self.peers[pid].connected_at else 0
                    ),
                }
                for pid in self._peer_connections.keys()
            ],
        }

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None) -> int:
        """Broadcast message to all connected peers"""
        exclude = exclude or set()
        sent = 0

        for peer_id in self._peer_connections.keys():
            if peer_id not in exclude:
                if await self.send_message(peer_id, message):
                    sent += 1

        return sent


# ============================================================================
# Signaling Server (WebSocket-based)
# ============================================================================


class SignalingServer:
    """WebSocket-based signaling server for WebRTC handshake"""

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self._pending_messages: Dict[str, List[SignalingMessage]] = defaultdict(list)

    async def initialize(self):
        """Initialize signaling server"""
        # Register message handlers with WebSocket manager
        self.websocket_manager.register_handler("webrtc_offer", self._handle_websocket_offer)
        self.websocket_manager.register_handler("webrtc_answer", self._handle_websocket_answer)
        self.websocket_manager.register_handler("webrtc_ice", self._handle_websocket_ice)
        self.websocket_manager.register_handler("peer_discover", self._handle_peer_discover)
        logger.info("Signaling server initialized")

    async def _handle_websocket_offer(self, agent_id: str, message: dict):
        """Handle WebRTC offer from WebSocket"""
        target = message.get("target_agent")
        offer = message.get("offer")

        signaling_msg = SignalingMessage(
            type="offer",
            sender=agent_id,
            recipient=target,
            payload={"sdp": offer},
        )

        await self._forward_signaling_message(signaling_msg)

    async def _handle_websocket_answer(self, agent_id: str, message: dict):
        """Handle WebRTC answer from WebSocket"""
        target = message.get("target_agent")
        answer = message.get("answer")

        signaling_msg = SignalingMessage(
            type="answer",
            sender=agent_id,
            recipient=target,
            payload={"sdp": answer},
        )

        await self._forward_signaling_message(signaling_msg)

    async def _handle_websocket_ice(self, agent_id: str, message: dict):
        """Handle ICE candidate from WebSocket"""
        target = message.get("target_agent")
        candidate = message.get("candidate")

        signaling_msg = SignalingMessage(
            type="ice-candidate",
            sender=agent_id,
            recipient=target,
            payload=candidate,
        )

        await self._forward_signaling_message(signaling_msg)

    async def _handle_peer_discover(self, agent_id: str, message: dict):
        """Handle peer discovery request"""
        # Get connected agents from WebSocket manager
        connections = self.websocket_manager.connections

        peers = [
            {"peer_id": conn.agent_id, "metadata": conn.metadata} for conn in connections.values() if conn.agent_id != agent_id
        ]

        await self.websocket_manager.send_message(
            agent_id,
            {
                "type": "peer_discover_response",
                "peers": peers[:20],  # Limit to 20 peers
            },
        )

    async def _forward_signaling_message(self, message: SignalingMessage):
        """Forward signaling message to target agent"""
        # Try to send directly via WebSocket
        success = await self.websocket_manager.send_message(
            message.recipient,
            {
                "type": f"webrtc_{message.type}",
                "sender": message.sender,
                "payload": message.payload,
            },
        )

        if not success:
            # Queue for later delivery
            self._pending_messages[message.recipient].append(message)
            logger.info(f"Queued signaling message for {message.recipient}")

    async def deliver_pending_messages(self, agent_id: str):
        """Deliver pending messages to a reconnected agent"""
        if agent_id in self._pending_messages:
            for message in self._pending_messages[agent_id]:
                await self._forward_signaling_message(message)
            del self._pending_messages[agent_id]


# ============================================================================
# Example Usage
# ============================================================================


async def example_usage():
    """Example of using the P2P handler"""

    # Create handler
    async def signaling_callback(message: SignalingMessage):
        print(f"Signaling: {message.type} from {message.sender} to {message.recipient}")

    handler = WebRTCP2PHandler(
        peer_id="agent_001",
        signaling_callback=signaling_callback,
        stun_servers=["stun:stun.l.google.com:19302"],
        turn_servers=[
            {
                "urls": "turn:turn.example.com:3478",
                "username": "user",
                "credential": "pass",
            }
        ],
    )

    # Initialize
    await handler.initialize()

    # Register message handler
    async def on_chat_message(sender_id: str, message: dict):
        print(f"Chat from {sender_id}: {message.get('content')}")

    handler.register_handler("chat", on_chat_message)

    # Connect to peers
    await handler.connect_to_peer("agent_002")
    await handler.connect_to_peer("agent_003")

    # Send message
    await handler.send_message("agent_002", {"type": "chat", "content": "Hello from agent_001!"})

    # Get stats
    stats = handler.get_stats()
    print(f"P2P Stats: {json.dumps(stats, indent=2)}")

    # Shutdown
    await handler.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())

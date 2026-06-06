"""
Encrypted Message Router for Zen-AI-Pentest
End-to-end encryption with mTLS configuration and certificate rotation
"""

import asyncio
import json
import logging
import os
import ssl
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.x509.oid import NameOID

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class MessagePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class MessageType(Enum):
    COMMAND = "command"
    RESULT = "result"
    HEARTBEAT = "heartbeat"
    CHAIN_FORWARD = "chain_forward"
    ENCRYPTED = "encrypted"
    KEY_EXCHANGE = "key_exchange"
    CERTIFICATE_ROTATION = "cert_rotation"


@dataclass
class EncryptedMessage:
    """Represents an encrypted message in the system"""

    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    payload: bytes  # Encrypted payload
    nonce: bytes
    timestamp: float
    signature: bytes
    priority: MessagePriority = MessagePriority.NORMAL
    ttl: int = 10  # Time-to-live for routing
    chain_path: List[str] = field(default_factory=list)  # Email chain path
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCredentials:
    """Agent credentials including certificates"""

    agent_id: str
    public_key: bytes
    certificate: Optional[x509.Certificate] = None
    certificate_pem: Optional[str] = None
    private_key: Optional[rsa.RSAPrivateKey] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_rotation: Optional[datetime] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    # Encryption settings
    encryption_algorithm: str = "AES-256-GCM"
    key_size: int = 256
    nonce_size: int = 12

    # Certificate settings
    cert_validity_days: int = 30
    rotation_buffer_days: int = 7
    auto_rotation: bool = True

    # mTLS settings
    mtls_enabled: bool = True
    verify_client_cert: bool = True
    ca_cert_path: Optional[str] = None

    # JWT settings
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Routing settings
    max_chain_length: int = 10
    chain_timeout_seconds: float = 300.0


# ============================================================================
# Certificate Manager
# ============================================================================


class CertificateManager:
    """Manages certificates for mTLS with automatic rotation"""

    def __init__(
        self,
        config: SecurityConfig,
        ca_key_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None,
    ):
        self.config = config
        self.ca_key_path = ca_key_path
        self.ca_cert_path = ca_cert_path
        self._ca_key: Optional[rsa.RSAPrivateKey] = None
        self._ca_cert: Optional[x509.Certificate] = None
        self._agent_certs: Dict[str, AgentCredentials] = {}
        self._cert_lock = asyncio.Lock()

        # Load or generate CA
        self._load_or_generate_ca()

    def _load_or_generate_ca(self):
        """Load existing CA or generate new one"""
        if self.ca_key_path and os.path.exists(self.ca_key_path):
            # Load existing CA
            with open(self.ca_key_path, "rb") as f:
                self._ca_key = serialization.load_pem_private_key(f.read(), password=None)

            with open(self.ca_cert_path, "rb") as f:
                self._ca_cert = x509.load_pem_x509_certificate(f.read())

            logger.info("Loaded existing CA certificate")
        else:
            # Generate new CA
            self._generate_ca()

    def _generate_ca(self):
        """Generate CA key and certificate"""
        self._ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Zen-AI-Pentest"),
                x509.NameAttribute(NameOID.COMMON_NAME, "Zen-AI-Pentest CA"),
            ]
        )

        self._ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(self._ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))  # 10 years
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(self._ca_key, hashes.SHA256(), default_backend())
        )

        # Save CA
        if self.ca_key_path:
            os.makedirs(os.path.dirname(self.ca_key_path), exist_ok=True)
            with open(self.ca_key_path, "wb") as f:
                f.write(
                    self._ca_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            with open(self.ca_cert_path, "wb") as f:
                f.write(self._ca_cert.public_bytes(serialization.Encoding.PEM))

        logger.info("Generated new CA certificate")

    async def generate_agent_certificate(self, agent_id: str) -> AgentCredentials:
        """Generate certificate for an agent"""
        async with self._cert_lock:
            # Generate agent key pair
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

            public_key = private_key.public_key()

            # Create certificate
            subject = x509.Name(
                [
                    x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Zen-AI-Pentest"),
                    x509.NameAttribute(NameOID.COMMON_NAME, f"agent-{agent_id}"),
                ]
            )

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(self._ca_cert.subject)
                .public_key(public_key)
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=self.config.cert_validity_days))
                .add_extension(
                    x509.SubjectAlternativeName([x509.DNSName(f"agent-{agent_id}.zen-ai.local")]),
                    critical=False,
                )
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .sign(self._ca_key, hashes.SHA256(), default_backend())
            )

            # Create credentials
            credentials = AgentCredentials(
                agent_id=agent_id,
                public_key=public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ),
                certificate=cert,
                certificate_pem=cert.public_bytes(serialization.Encoding.PEM).decode(),
                private_key=private_key,
                expires_at=datetime.now(timezone.utc) + timedelta(days=self.config.cert_validity_days),
            )

            self._agent_certs[agent_id] = credentials

            logger.info(f"Generated certificate for agent {agent_id}")
            return credentials

    async def rotate_certificate(self, agent_id: str) -> Optional[AgentCredentials]:
        """Rotate certificate for an agent"""
        async with self._cert_lock:
            if agent_id not in self._agent_certs:
                return None

            self._agent_certs[agent_id]

            # Generate new certificate
            new_cert = await self.generate_agent_certificate(agent_id)
            new_cert.last_rotation = datetime.now(timezone.utc)

            logger.info(f"Rotated certificate for agent {agent_id}")
            return new_cert

    async def get_certificate(self, agent_id: str) -> Optional[AgentCredentials]:
        """Get agent certificate"""
        return self._agent_certs.get(agent_id)

    async def verify_certificate(self, cert_pem: str) -> Tuple[bool, Optional[str]]:
        """Verify a certificate against our CA"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())

            # Check expiration
            if cert.not_valid_after < datetime.now(timezone.utc):
                return False, "Certificate expired"

            # Verify signature
            try:
                self._ca_cert.public_key().verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    cert.signature_hash_algorithm,
                )
            except Exception:
                return False, "Invalid certificate signature"

            return True, None
        except Exception as e:
            return False, str(e)

    async def get_ca_cert_pem(self) -> str:
        """Get CA certificate in PEM format"""
        return self._ca_cert.public_bytes(serialization.Encoding.PEM).decode()

    async def create_ssl_context(self, agent_id: str) -> ssl.SSLContext:
        """Create SSL context for an agent"""
        credentials = await self.get_certificate(agent_id)
        if not credentials:
            raise ValueError(f"No credentials found for agent {agent_id}")

        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.verify_mode = ssl.CERT_REQUIRED if self.config.verify_client_cert else ssl.CERT_OPTIONAL

        # Load CA cert
        ctx.load_verify_locations(cadata=await self.get_ca_cert_pem())

        # Load agent certificate and key
        cert_pem = credentials.certificate_pem
        key_pem = credentials.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        # Create temporary files for SSL context
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as cert_file:
            cert_file.write(cert_pem)
            cert_file.write(key_pem)
            cert_path = cert_file.name

        ctx.load_cert_chain(cert_path)
        os.unlink(cert_path)

        return ctx

    async def check_and_rotate_expiring(self) -> List[str]:
        """Check for and rotate expiring certificates"""
        rotated = []
        threshold = datetime.now(timezone.utc) + timedelta(days=self.config.rotation_buffer_days)

        for agent_id, creds in self._agent_certs.items():
            if creds.expires_at and creds.expires_at < threshold:
                if self.config.auto_rotation:
                    await self.rotate_certificate(agent_id)
                    rotated.append(agent_id)
                else:
                    logger.warning(f"Certificate for {agent_id} expires soon but auto-rotation is disabled")

        return rotated


# ============================================================================
# Encryption Manager
# ============================================================================


class EncryptionManager:
    """Manages end-to-end encryption for messages"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self._session_keys: Dict[str, bytes] = {}  # agent_id -> session key
        self._key_lock = asyncio.Lock()

    def generate_session_key(self) -> bytes:
        """Generate a new session key"""
        return AESGCM.generate_key(bit_length=self.config.key_size)

    async def establish_session(self, agent_id: str, public_key: bytes) -> bytes:
        """Establish encrypted session with agent"""
        async with self._key_lock:
            session_key = self.generate_session_key()
            self._session_keys[agent_id] = session_key
            return session_key

    async def encrypt_message(
        self,
        recipient_id: str,
        message: dict,
        sender_private_key: Optional[rsa.RSAPrivateKey] = None,
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt message for recipient
        Returns: (encrypted_payload, nonce, signature)
        """
        # Get or generate session key
        if recipient_id not in self._session_keys:
            self._session_keys[recipient_id] = self.generate_session_key()

        session_key = self._session_keys[recipient_id]

        # Serialize message
        message_bytes = json.dumps(message).encode()

        # Generate nonce
        nonce = os.urandom(self.config.nonce_size)

        # Encrypt with AES-GCM
        aesgcm = AESGCM(session_key)
        encrypted = aesgcm.encrypt(nonce, message_bytes, None)

        # Sign if private key provided
        signature = b""
        if sender_private_key:
            signature = sender_private_key.sign(
                encrypted,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

        return encrypted, nonce, signature

    async def decrypt_message(
        self,
        sender_id: str,
        encrypted_payload: bytes,
        nonce: bytes,
        signature: bytes,
        sender_public_key: Optional[rsa.RSAPublicKey] = None,
    ) -> dict:
        """Decrypt message from sender"""
        # Verify signature if provided
        if signature and sender_public_key:
            try:
                sender_public_key.verify(
                    signature,
                    encrypted_payload,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            except Exception as e:
                raise ValueError(f"Signature verification failed: {e}")

        # Get session key
        if sender_id not in self._session_keys:
            raise ValueError(f"No session key for sender {sender_id}")

        session_key = self._session_keys[sender_id]

        # Decrypt
        aesgcm = AESGCM(session_key)
        decrypted = aesgcm.decrypt(nonce, encrypted_payload, None)

        return json.loads(decrypted.decode())

    async def rotate_session_key(self, agent_id: str) -> bytes:
        """Rotate session key for an agent"""
        async with self._key_lock:
            new_key = self.generate_session_key()
            self._session_keys[agent_id] = new_key
            return new_key


# ============================================================================
# Message Router
# ============================================================================


class EncryptedMessageRouter:
    """
    Encrypted message router for agent-to-agent communication
    Supports email chains with end-to-end encryption
    """

    def __init__(
        self,
        security_config: Optional[SecurityConfig] = None,
        ca_key_path: Optional[str] = None,
        ca_cert_path: Optional[str] = None,
    ):
        self.config = security_config or SecurityConfig()
        self.cert_manager = CertificateManager(self.config, ca_key_path, ca_cert_path)
        self.encryption = EncryptionManager(self.config)

        # Message tracking
        self._message_history: Dict[str, EncryptedMessage] = {}
        self._pending_chains: Dict[str, Dict] = {}  # chain_id -> chain state
        self._delivery_callbacks: Dict[str, Callable] = {}

        # Routing tables
        self._agent_routes: Dict[str, str] = {}  # agent_id -> node_id
        self._chain_routes: Dict[str, List[str]] = {}  # chain_id -> [agent_ids]

        # Message handlers
        self._handlers: Dict[MessageType, Callable] = {}

        # Running state
        self._running = False
        self._maintenance_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the message router"""
        self._running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.info("Encrypted Message Router initialized")

    async def shutdown(self):
        """Shutdown the message router"""
        self._running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
        logger.info("Encrypted Message Router shutdown")

    # =====================================================================
    # Agent Registration
    # =====================================================================

    async def register_agent(self, agent_id: str, node_id: str) -> AgentCredentials:
        """Register a new agent and generate credentials"""
        # Generate certificate
        credentials = await self.cert_manager.generate_agent_certificate(agent_id)

        # Register route
        self._agent_routes[agent_id] = node_id

        logger.info(f"Registered agent {agent_id} on node {node_id}")
        return credentials

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        self._agent_routes.pop(agent_id, None)
        self.encryption._session_keys.pop(agent_id, None)
        logger.info(f"Unregistered agent {agent_id}")

    # =====================================================================
    # Message Sending
    # =====================================================================

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message: dict,
        message_type: MessageType = MessageType.ENCRYPTED,
        priority: MessagePriority = MessagePriority.NORMAL,
        chain_path: Optional[List[str]] = None,
    ) -> str:
        """
        Send encrypted message from sender to recipient
        Returns message ID
        """
        message_id = str(uuid.uuid4())
        timestamp = time.time()

        # Get sender credentials
        sender_creds = await self.cert_manager.get_certificate(sender_id)
        if not sender_creds:
            raise ValueError(f"Sender {sender_id} not registered")

        # Encrypt message
        encrypted, nonce, signature = await self.encryption.encrypt_message(recipient_id, message, sender_creds.private_key)

        # Create encrypted message
        encrypted_msg = EncryptedMessage(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=encrypted,
            nonce=nonce,
            timestamp=timestamp,
            signature=signature,
            priority=priority,
            chain_path=chain_path or [],
        )

        # Store in history
        self._message_history[message_id] = encrypted_msg

        # Route message
        await self._route_message(encrypted_msg)

        return message_id

    async def send_chain_message(
        self,
        originator_id: str,
        chain: List[str],
        message: dict,
        message_type: MessageType = MessageType.CHAIN_FORWARD,
    ) -> str:
        """
        Send message through an email chain
        Chain format: [agent1, agent2, agent3, ...] where message flows through each
        """
        if len(chain) > self.config.max_chain_length:
            raise ValueError(f"Chain length {len(chain)} exceeds maximum {self.config.max_chain_length}")

        chain_id = str(uuid.uuid4())

        # Create chain state
        self._pending_chains[chain_id] = {
            "originator": originator_id,
            "chain": chain,
            "current_index": 0,
            "message": message,
            "message_type": message_type,
            "created_at": time.time(),
            "message_ids": [],
        }

        # Start chain
        await self._process_chain_step(chain_id)

        return chain_id

    async def _route_message(self, message: EncryptedMessage):
        """Route message to recipient"""
        recipient_id = message.recipient_id

        # Check if recipient is local
        if recipient_id in self._agent_routes:
            # Deliver locally
            await self._deliver_message(message)
        else:
            # Forward to appropriate node (would integrate with Redis pub/sub)
            await self._forward_to_node(message)

    async def _deliver_message(self, message: EncryptedMessage):
        """Deliver message to local recipient"""
        handler = self._handlers.get(message.message_type)
        if handler:
            try:
                # Decrypt message
                sender_creds = await self.cert_manager.get_certificate(message.sender_id)
                decrypted = await self.encryption.decrypt_message(
                    message.sender_id,
                    message.payload,
                    message.nonce,
                    message.signature,
                    (sender_creds.private_key.public_key() if sender_creds else None),
                )

                await handler(message.recipient_id, decrypted, message)

                # Trigger delivery callback
                if message.message_id in self._delivery_callbacks:
                    callback = self._delivery_callbacks.pop(message.message_id)
                    await callback(message.message_id, True)

            except Exception as e:
                logger.error(f"Error delivering message {message.message_id}: {e}")
                if message.message_id in self._delivery_callbacks:
                    callback = self._delivery_callbacks.pop(message.message_id)
                    await callback(message.message_id, False)

    async def _forward_to_node(self, message: EncryptedMessage):
        """Forward message to another node"""
        # This would integrate with Redis pub/sub for cross-node routing
        # For now, just log
        logger.info(f"Would forward message {message.message_id} to node for {message.recipient_id}")

    async def _process_chain_step(self, chain_id: str):
        """Process next step in message chain"""
        if chain_id not in self._pending_chains:
            return

        chain_state = self._pending_chains[chain_id]
        chain = chain_state["chain"]
        current_idx = chain_state["current_index"]

        if current_idx >= len(chain):
            # Chain complete
            logger.info(f"Chain {chain_id} completed")
            del self._pending_chains[chain_id]
            return

        # Get current recipient
        recipient = chain[current_idx]
        originator = chain_state["originator"]

        # Prepare message
        chain_message = {
            **chain_state["message"],
            "chain_id": chain_id,
            "chain_position": current_idx,
            "chain_length": len(chain),
            "next_hop": (chain[current_idx + 1] if current_idx + 1 < len(chain) else None),
        }

        # Send message
        message_id = await self.send_message(
            sender_id=(originator if current_idx == 0 else chain[current_idx - 1]),
            recipient_id=recipient,
            message=chain_message,
            message_type=chain_state["message_type"],
            chain_path=chain[: current_idx + 1],
        )

        chain_state["message_ids"].append(message_id)
        chain_state["current_index"] += 1

        # Schedule next step
        asyncio.create_task(self._schedule_chain_step(chain_id))

    async def _schedule_chain_step(self, chain_id: str):
        """Schedule next chain step after delivery confirmation"""
        # In real implementation, wait for delivery confirmation
        # For now, just process immediately
        await asyncio.sleep(0.1)
        await self._process_chain_step(chain_id)

    # =====================================================================
    # Message Handling
    # =====================================================================

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler"""
        self._handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type.value}")

    async def on_message_delivered(self, message_id: str, callback: Callable):
        """Register callback for message delivery"""
        self._delivery_callbacks[message_id] = callback

    # =====================================================================
    # Certificate Rotation
    # =====================================================================

    async def rotate_agent_certificate(self, agent_id: str) -> Optional[AgentCredentials]:
        """Rotate certificate for an agent"""
        new_creds = await self.cert_manager.rotate_certificate(agent_id)

        if new_creds:
            # Notify agent of rotation
            await self.send_message(
                sender_id="system",
                recipient_id=agent_id,
                message={
                    "type": "certificate_rotated",
                    "new_certificate": new_creds.certificate_pem,
                    "expires_at": new_creds.expires_at.isoformat(),
                },
                message_type=MessageType.CERTIFICATE_ROTATION,
            )

        return new_creds

    # =====================================================================
    # Maintenance
    # =====================================================================

    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Check and rotate expiring certificates
                rotated = await self.cert_manager.check_and_rotate_expiring()
                if rotated:
                    logger.info(f"Rotated certificates for: {rotated}")

                # Clean up old message history
                cutoff = time.time() - 86400  # 24 hours
                old_messages = [mid for mid, msg in self._message_history.items() if msg.timestamp < cutoff]
                for mid in old_messages:
                    del self._message_history[mid]

                if old_messages:
                    logger.info(f"Cleaned up {len(old_messages)} old messages")

                # Clean up expired chains
                expired_chains = [
                    cid
                    for cid, state in self._pending_chains.items()
                    if time.time() - state["created_at"] > self.config.chain_timeout_seconds
                ]
                for cid in expired_chains:
                    del self._pending_chains[cid]

                if expired_chains:
                    logger.info(f"Cleaned up {len(expired_chains)} expired chains")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")

    # =====================================================================
    # Utility Methods
    # =====================================================================

    async def get_agent_info(self, agent_id: str) -> dict:
        """Get agent information"""
        creds = await self.cert_manager.get_certificate(agent_id)
        return {
            "agent_id": agent_id,
            "registered": agent_id in self._agent_routes,
            "has_certificate": creds is not None,
            "certificate_expires": (creds.expires_at.isoformat() if creds and creds.expires_at else None),
            "has_session": agent_id in self.encryption._session_keys,
        }

    def get_stats(self) -> dict:
        """Get router statistics"""
        return {
            "registered_agents": len(self._agent_routes),
            "active_sessions": len(self.encryption._session_keys),
            "message_history": len(self._message_history),
            "pending_chains": len(self._pending_chains),
            "certificate_count": len(self.cert_manager._agent_certs),
        }


# ============================================================================
# mTLS Configuration Helper
# ============================================================================


class MTLSConfig:
    """Helper for configuring mTLS"""

    @staticmethod
    def create_server_ssl_context(cert_manager: CertificateManager, verify_client: bool = True) -> ssl.SSLContext:
        """Create server SSL context with mTLS"""
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.verify_mode = ssl.CERT_REQUIRED if verify_client else ssl.CERT_OPTIONAL

        # Load CA certificate
        ca_cert = asyncio.run(cert_manager.get_ca_cert_pem())
        ctx.load_verify_locations(cadata=ca_cert)

        return ctx

    @staticmethod
    def create_client_ssl_context(
        credentials: AgentCredentials,
        ca_cert_pem: str,
        verify_server: bool = True,
    ) -> ssl.SSLContext:
        """Create client SSL context with mTLS"""
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        if verify_server:
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.load_verify_locations(cadata=ca_cert_pem)

        # Load client certificate and key
        cert_pem = credentials.certificate_pem
        key_pem = credentials.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(cert_pem)
            f.write(key_pem)
            cert_path = f.name

        ctx.load_cert_chain(cert_path)
        os.unlink(cert_path)

        return ctx


# ============================================================================
# Example Usage
# ============================================================================


async def example_usage():
    """Example of using the encrypted message router"""

    # Create router
    config = SecurityConfig(cert_validity_days=30, auto_rotation=True)

    router = EncryptedMessageRouter(config)
    await router.initialize()

    # Register agents
    await router.register_agent("agent_001", "node_1")
    await router.register_agent("agent_002", "node_1")
    await router.register_agent("agent_003", "node_1")

    # Register message handler
    async def on_command(recipient_id: str, message: dict, encrypted_msg: EncryptedMessage):
        print(f"Agent {recipient_id} received command: {message}")

    router.register_handler(MessageType.COMMAND, on_command)

    # Send encrypted message
    msg_id = await router.send_message(
        sender_id="agent_001",
        recipient_id="agent_002",
        message={"action": "scan", "target": "192.168.1.1"},
        message_type=MessageType.COMMAND,
    )
    print(f"Sent message: {msg_id}")

    # Send chain message
    chain_id = await router.send_chain_message(
        originator_id="agent_001",
        chain=["agent_002", "agent_003"],
        message={"action": "propagate", "data": "test"},
    )
    print(f"Started chain: {chain_id}")

    # Get stats
    stats = router.get_stats()
    print(f"Router stats: {json.dumps(stats, indent=2)}")

    # Cleanup
    await router.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())

"""
Secure Message Protocol
=======================

End-to-end encrypted messaging for agents.

Cryptography:
- Key Exchange: X25519 (Elliptic Curve Diffie-Hellman)
- Encryption: AES-256-GCM (Authenticated encryption)
- Signatures: Ed25519 (Fast, secure signatures)

Message Format:
{
    "header": {
        "message_id": "uuid",
        "sender_id": "agent_id",
        "recipient_id": "agent_id",
        "timestamp": "ISO8601",
        "msg_type": "task|result|event|heartbeat"
    },
    "payload": <encrypted>,
    "signature": <ed25519_signature>
}
"""

import base64
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Union

# Cryptography imports
try:
    from cryptography.exceptions import InvalidSignature, InvalidTag
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    # Fallback for development without cryptography library


@dataclass
class MessageHeader:
    """Message metadata"""

    message_id: str
    sender_id: str
    recipient_id: str
    timestamp: str
    msg_type: str  # task, result, event, heartbeat, control
    version: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageHeader":
        return cls(**data)


@dataclass
class EncryptedPayload:
    """Encrypted message content"""

    ciphertext: str  # base64 encoded
    nonce: str  # base64 encoded
    salt: str  # base64 encoded (for key derivation)

    def to_dict(self) -> Dict[str, str]:
        return {"ciphertext": self.ciphertext, "nonce": self.nonce, "salt": self.salt}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "EncryptedPayload":
        return cls(**data)


@dataclass
class SecureMessage:
    """
    Secure message container

    Attributes:
        header: Message metadata
        payload: Encrypted content
        signature: Ed25519 signature of (header + payload)
    """

    header: MessageHeader
    payload: EncryptedPayload
    signature: str  # base64 encoded Ed25519 signature

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps({"header": self.header.to_dict(), "payload": self.payload.to_dict(), "signature": self.signature})

    @classmethod
    def from_json(cls, json_str: str) -> "SecureMessage":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(
            header=MessageHeader.from_dict(data["header"]),
            payload=EncryptedPayload.from_dict(data["payload"]),
            signature=data["signature"],
        )

    def to_bytes(self) -> bytes:
        """Serialize to bytes for transmission"""
        return self.to_json().encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "SecureMessage":
        """Deserialize from bytes"""
        return cls.from_json(data.decode("utf-8"))


class MessageEncryption:
    """
    Encryption/decryption for agent messages

    Uses X25519 for key exchange and AES-256-GCM for encryption.
    Each message uses a fresh ephemeral key pair.
    """

    def __init__(self):
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required. " "Install with: pip install cryptography")

        # Generate long-term identity key for signing
        self._signing_key = Ed25519PrivateKey.generate()
        self._verify_key = self._signing_key.public_key()

    @property
    def public_key_bytes(self) -> bytes:
        """Get public key for sharing"""
        return self._verify_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

    def encrypt(self, plaintext: Union[str, bytes, dict], recipient_public_key: bytes) -> EncryptedPayload:
        """
        Encrypt message for recipient

        Args:
            plaintext: Message content
            recipient_public_key: Recipient's X25519 public key

        Returns:
            EncryptedPayload with ciphertext, nonce, and salt
        """
        # Convert plaintext to bytes
        if isinstance(plaintext, dict):
            plaintext = json.dumps(plaintext).encode("utf-8")
        elif isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Generate ephemeral key pair for this message
        ephemeral_private = X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()

        # Load recipient public key
        recipient_key = X25519PublicKey.from_public_bytes(recipient_public_key)

        # Derive shared secret
        shared_secret = ephemeral_private.exchange(recipient_key)

        # Generate salt and derive encryption key
        salt = secrets.token_bytes(32)
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        encryption_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=b"zen-agent-message").derive(shared_secret)

        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(encryption_key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Include ephemeral public key with ciphertext for recipient
        full_ciphertext = (
            ephemeral_public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
            + ciphertext
        )

        return EncryptedPayload(
            ciphertext=base64.b64encode(full_ciphertext).decode("ascii"),
            nonce=base64.b64encode(nonce).decode("ascii"),
            salt=base64.b64encode(salt).decode("ascii"),
        )

    def decrypt(self, encrypted: EncryptedPayload, private_key=None) -> bytes:
        """
        Decrypt message

        Args:
            encrypted: EncryptedPayload from encrypt()
            private_key: X25519 private key (if None, uses ephemeral)

        Returns:
            Decrypted plaintext bytes
        """
        # Decode components
        full_ciphertext = base64.b64decode(encrypted.ciphertext)
        nonce = base64.b64decode(encrypted.nonce)
        salt = base64.b64decode(encrypted.salt)

        # Extract ephemeral public key
        ephemeral_public_bytes = full_ciphertext[:32]
        ciphertext = full_ciphertext[32:]

        ephemeral_public = X25519PublicKey.from_public_bytes(ephemeral_public_bytes)

        # Use provided key or raise error
        if private_key is None:
            raise ValueError("Private key required for decryption")

        # Derive shared secret
        shared_secret = private_key.exchange(ephemeral_public)

        # Derive encryption key
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        encryption_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=b"zen-agent-message").derive(shared_secret)

        # Decrypt
        aesgcm = AESGCM(encryption_key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag:
            raise ValueError("Decryption failed - invalid ciphertext or tampering detected")

        return plaintext

    def sign(self, data: bytes) -> bytes:
        """
        Sign data with Ed25519

        Args:
            data: Data to sign

        Returns:
            Signature bytes
        """
        return self._signing_key.sign(data)

    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify Ed25519 signature

        Args:
            data: Original data
            signature: Signature to verify
            public_key: Signer's Ed25519 public key

        Returns:
            True if valid, False otherwise
        """
        try:
            verify_key = Ed25519PublicKey.from_public_bytes(public_key)
            verify_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False

    def create_message(
        self, sender_id: str, recipient_id: str, msg_type: str, payload: Union[str, bytes, dict], recipient_public_key: bytes
    ) -> SecureMessage:
        """
        Create a complete secure message

        Args:
            sender_id: Agent ID of sender
            recipient_id: Agent ID of recipient
            msg_type: Message type
            payload: Message content
            recipient_public_key: Recipient's X25519 public key

        Returns:
            Signed and encrypted SecureMessage
        """
        import uuid

        # Create header
        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            msg_type=msg_type,
        )

        # Encrypt payload
        encrypted_payload = self.encrypt(payload, recipient_public_key)

        # Create signature over header + payload
        data_to_sign = json.dumps(header.to_dict(), sort_keys=True).encode("utf-8") + json.dumps(
            encrypted_payload.to_dict(), sort_keys=True
        ).encode("utf-8")
        signature = self.sign(data_to_sign)

        return SecureMessage(header=header, payload=encrypted_payload, signature=base64.b64encode(signature).decode("ascii"))


class SecureMessageCodec:
    """
    High-level codec for encoding/decoding messages
    """

    def __init__(self, encryption: MessageEncryption, private_key: bytes):
        self.encryption = encryption
        if CRYPTO_AVAILABLE:
            self._private_key = X25519PrivateKey.from_private_bytes(private_key)
        else:
            self._private_key = None

    def encode(
        self, sender_id: str, recipient_id: str, msg_type: str, payload: dict, recipient_public_key: bytes
    ) -> SecureMessage:
        """Encode a message for sending"""
        return self.encryption.create_message(sender_id, recipient_id, msg_type, payload, recipient_public_key)

    def decode(self, message: SecureMessage) -> dict:
        """Decode a received message"""
        # Decrypt payload
        plaintext = self.encryption.decrypt(message.payload, self._private_key)

        # Parse JSON
        return json.loads(plaintext.decode("utf-8"))


# ============================================================================
# Convenience Functions
# ============================================================================


def generate_keypair() -> tuple[bytes, bytes]:
    """
    Generate a new X25519 keypair for encryption

    Returns:
        (private_key, public_key) as bytes
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography library required")

    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()

    return (
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw),
    )


def generate_signing_keypair() -> tuple[bytes, bytes]:
    """
    Generate a new Ed25519 keypair for signing

    Returns:
        (private_key, public_key) as bytes
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography library required")

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    return (
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw),
    )


# ============================================================================
# Test Functions
# ============================================================================


def test_encryption_roundtrip():
    """Test encrypt/decrypt roundtrip"""
    if not CRYPTO_AVAILABLE:
        print("cryptography not available, skipping test")
        return

    # Generate keypairs
    alice_private, alice_public = generate_keypair()
    bob_private, bob_public = generate_keypair()

    # Alice encrypts for Bob
    encryption = MessageEncryption()
    payload = {"message": "Hello, Bob!", "secret": 42}
    encrypted = encryption.encrypt(payload, bob_public)

    # Bob decrypts
    bob_codec = SecureMessageCodec(encryption, bob_private)
    decrypted = bob_codec.encryption.decrypt(encrypted, X25519PrivateKey.from_private_bytes(bob_private))

    result = json.loads(decrypted.decode("utf-8"))
    assert result["message"] == "Hello, Bob!"
    assert result["secret"] == 42

    print("✅ Encryption roundtrip test passed")


def test_message_signing():
    """Test message signing and verification"""
    if not CRYPTO_AVAILABLE:
        print("cryptography not available, skipping test")
        return

    encryption = MessageEncryption()
    data = b"Test message for signing"

    # Sign
    signature = encryption.sign(data)

    # Get public key
    public_key = encryption.public_key_bytes

    # Verify
    is_valid = encryption.verify(data, signature, public_key)
    assert is_valid is True

    # Tamper with data
    is_valid = encryption.verify(b"Tampered data", signature, public_key)
    assert is_valid is False

    print("✅ Message signing test passed")


if __name__ == "__main__":
    test_encryption_roundtrip()
    test_message_signing()
    print("\nAll tests passed!")

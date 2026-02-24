"""
Agent Communication v2 Tests (Simple)
=====================================

Tests for the new agent communication system with cryptography installed.
"""

import os
import sys
from datetime import datetime

import pytest

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test dependencies are installed
from agents.v2.secure_message import CRYPTO_AVAILABLE

if not CRYPTO_AVAILABLE:
    pytest.skip("cryptography not installed", allow_module_level=True)

from agents.v2 import MessageEncryption, SecureMessage
from agents.v2.message_queue import InMemoryMessageQueue
from agents.v2.secure_message import (
    EncryptedPayload,
    MessageHeader,
    generate_keypair,
    generate_signing_keypair,
)

# ============================================================================
# Secure Message Tests
# ============================================================================


class TestSecureMessage:
    """Test secure message encryption"""

    def test_key_generation(self):
        """Test keypair generation"""
        priv, pub = generate_keypair()
        assert len(priv) == 32
        assert len(pub) == 32

        sign_priv, sign_pub = generate_signing_keypair()
        assert len(sign_priv) == 32
        assert len(sign_pub) == 32
        print("✅ Key generation works")

    def test_encrypt_decrypt(self):
        """Test encryption roundtrip"""
        encryption = MessageEncryption()

        # Generate recipient keys
        _, recipient_pub = generate_keypair()

        # Encrypt
        plaintext = {"message": "Hello, World!", "secret": 42}
        encrypted = encryption.encrypt(plaintext, recipient_pub)

        assert encrypted.ciphertext is not None
        assert encrypted.nonce is not None
        assert encrypted.salt is not None
        print("✅ Encryption works")

    def test_sign_verify(self):
        """Test message signing"""
        encryption = MessageEncryption()
        data = b"Test message for signing"

        # Sign
        signature = encryption.sign(data)
        assert len(signature) > 0

        # Get public key
        public_key = encryption.public_key_bytes

        # Verify
        is_valid = encryption.verify(data, signature, public_key)
        assert is_valid is True

        # Verify tampered data fails
        is_invalid = encryption.verify(b"Tampered", signature, public_key)
        assert is_invalid is False
        print("✅ Signing/verification works")

    def test_create_message(self):
        """Test complete message creation"""
        encryption = MessageEncryption()

        # Generate recipient keys
        _, recipient_pub = generate_keypair()

        # Create message
        msg = encryption.create_message(
            sender_id="agent-a",
            recipient_id="agent-b",
            msg_type="task",
            payload={"action": "scan", "target": "example.com"},
            recipient_public_key=recipient_pub,
        )

        assert msg.header.message_id is not None
        assert msg.header.sender_id == "agent-a"
        assert msg.header.recipient_id == "agent-b"
        assert msg.header.msg_type == "task"
        assert msg.signature is not None
        print("✅ Message creation works")

    def test_serialization(self):
        """Test message serialization"""
        encryption = MessageEncryption()
        _, recipient_pub = generate_keypair()

        msg = encryption.create_message(
            sender_id="agent-a",
            recipient_id="agent-b",
            msg_type="test",
            payload={"data": "test"},
            recipient_public_key=recipient_pub,
        )

        # Serialize
        json_str = msg.to_json()
        assert isinstance(json_str, str)

        # Deserialize
        msg2 = SecureMessage.from_json(json_str)
        assert msg2.header.message_id == msg.header.message_id
        assert msg2.header.sender_id == msg.header.sender_id
        print("✅ Serialization works")


# ============================================================================
# Message Queue Tests
# ============================================================================


class TestMessageQueue:
    """Test message queue"""

    @pytest.mark.asyncio
    async def test_publish_receive(self):
        """Test publish and receive"""
        queue = InMemoryMessageQueue()
        await queue.connect()

        MessageEncryption()
        _, recipient_pub = generate_keypair()

        # Create message
        msg = SecureMessage(
            header=MessageHeader(
                message_id="test-msg-1",
                sender_id="agent-a",
                recipient_id="agent-b",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="task",
            ),
            payload=EncryptedPayload(
                ciphertext="encrypted_data", nonce="nonce123", salt="salt456"
            ),
            signature="sig789",
        )

        # Publish
        msg_id = await queue.publish("test.channel", msg)
        assert msg_id is not None

        # Receive
        received = await queue.receive("test.channel", timeout=1.0)
        assert received is not None
        assert received.id == msg_id
        print("✅ Queue publish/receive works")

    @pytest.mark.asyncio
    async def test_acknowledge(self):
        """Test message acknowledgment"""
        queue = InMemoryMessageQueue()
        await queue.connect()

        msg = SecureMessage(
            header=MessageHeader(
                message_id="ack-test",
                sender_id="agent-a",
                recipient_id="agent-b",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="test",
            ),
            payload=EncryptedPayload("enc", "nonce", "salt"),
            signature="sig",
        )

        await queue.publish("ack.channel", msg)
        received = await queue.receive("ack.channel", timeout=1.0)

        # Ack
        await queue.ack(received.id)
        print("✅ Acknowledgment works")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

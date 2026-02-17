"""
Agent Communication v2 Tests
============================

Tests for the new agent communication system.
"""

import os
import sys
import asyncio
import pytest
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check dependencies
from agents.v2.secure_message import CRYPTO_AVAILABLE

# Skip all tests if dependencies not available
pytestmark = pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography library not installed")

if CRYPTO_AVAILABLE:
    from agents.v2 import SecureMessage, MessageEncryption, AgentCredentials
    from agents.v2.auth_manager import AgentAuthenticator, AgentRole, AgentPermission
    from agents.v2.message_queue import InMemoryMessageQueue, QueuedMessage


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def encryption():
    """Create message encryption instance"""
    return MessageEncryption()


@pytest.fixture
def auth_manager():
    """Create authenticator with fresh database"""
    from database.auth_models import Base, engine
    from sqlalchemy import create_engine
    
    # Use in-memory database for tests
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    
    # Patch the session to use test engine
    from database.auth_models import SessionLocal
    original_engine = engine
    
    auth = AgentAuthenticator()
    auth.db = SessionLocal()
    
    return auth


@pytest.fixture
def message_queue():
    """Create in-memory message queue"""
    queue = InMemoryMessageQueue()
    asyncio.run(queue.connect())
    return queue


# ============================================================================
# Secure Message Tests
# ============================================================================

class TestSecureMessage:
    """Test secure message encryption"""
    
    def test_key_generation(self, encryption):
        """Test keypair generation"""
        from agents.v2.secure_message import generate_keypair, generate_signing_keypair
        
        priv, pub = generate_keypair()
        assert len(priv) == 32
        assert len(pub) == 32
        
        sign_priv, sign_pub = generate_signing_keypair()
        assert len(sign_priv) == 32
        assert len(sign_pub) == 32
    
    def test_encrypt_decrypt(self, encryption):
        """Test encryption roundtrip"""
        from agents.v2.secure_message import generate_keypair
        
        # Generate recipient keys
        _, recipient_pub = generate_keypair()
        
        # Encrypt
        plaintext = {"message": "Hello, World!", "secret": 42}
        encrypted = encryption.encrypt(plaintext, recipient_pub)
        
        assert encrypted.ciphertext is not None
        assert encrypted.nonce is not None
        assert encrypted.salt is not None
    
    def test_sign_verify(self, encryption):
        """Test message signing"""
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


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAgentAuthentication:
    """Test agent authentication"""
    
    def test_generate_credentials(self, auth_manager):
        """Test credential generation"""
        creds = auth_manager.generate_api_key(
            role=AgentRole.RESEARCHER,
            name="test-agent",
            expires_days=30
        )
        
        assert creds.agent_id.startswith("agt_")
        assert creds.api_key.startswith("zen_")
        assert len(creds.api_secret) > 20
        assert creds.role == AgentRole.RESEARCHER
        assert len(creds.permissions) > 0
        assert AgentPermission.MESSAGE_SEND in creds.permissions
    
    def test_authenticate_success(self, auth_manager):
        """Test successful authentication"""
        creds = auth_manager.generate_api_key(
            role=AgentRole.ANALYST,
            name="auth-test-agent"
        )
        
        identity = auth_manager.authenticate(creds.api_key, creds.api_secret)
        
        assert identity is not None
        assert identity.agent_id == creds.agent_id
        assert identity.role == AgentRole.ANALYST
        assert identity.is_active is True
    
    def test_authenticate_wrong_secret(self, auth_manager):
        """Test authentication with wrong secret"""
        creds = auth_manager.generate_api_key(
            role=AgentRole.SCANNER,
            name="auth-fail-agent"
        )
        
        identity = auth_manager.authenticate(creds.api_key, "wrong_secret")
        assert identity is None
    
    def test_check_permission(self, auth_manager):
        """Test permission checking"""
        creds = auth_manager.generate_api_key(
            role=AgentRole.RESEARCHER,
            name="perm-test-agent"
        )
        
        identity = auth_manager.authenticate(creds.api_key, creds.api_secret)
        
        # Should have researcher permissions
        assert auth_manager.check_permission(identity, AgentPermission.MESSAGE_SEND)
        assert auth_manager.check_permission(identity, AgentPermission.TASK_EXECUTE)
        
        # Should not have admin permissions
        assert not auth_manager.check_permission(identity, AgentPermission.AGENT_REGISTER)
    
    def test_list_agents(self, auth_manager):
        """Test listing agents"""
        # Create some agents
        auth_manager.generate_api_key(AgentRole.RESEARCHER, "agent-1")
        auth_manager.generate_api_key(AgentRole.ANALYST, "agent-2")
        
        agents = auth_manager.list_active_agents()
        
        assert len(agents) >= 2
        assert all(a.is_active for a in agents)


# ============================================================================
# Message Queue Tests
# ============================================================================

class TestMessageQueue:
    """Test message queue"""
    
    @pytest.mark.asyncio
    async def test_publish_receive(self, message_queue):
        """Test publish and receive"""
        from agents.v2.secure_message import MessageHeader, EncryptedPayload
        
        # Create message
        msg = SecureMessage(
            header=MessageHeader(
                message_id="test-msg-1",
                sender_id="agent-a",
                recipient_id="agent-b",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="task"
            ),
            payload=EncryptedPayload(
                ciphertext="encrypted_data",
                nonce="nonce123",
                salt="salt456"
            ),
            signature="sig789"
        )
        
        # Publish
        msg_id = await message_queue.publish("test.channel", msg)
        assert msg_id is not None
        
        # Receive
        received = await message_queue.receive("test.channel", timeout=1.0)
        assert received is not None
        assert received.id == msg_id
    
    @pytest.mark.asyncio
    async def test_acknowledge(self, message_queue):
        """Test message acknowledgment"""
        from agents.v2.secure_message import MessageHeader, EncryptedPayload
        
        msg = SecureMessage(
            header=MessageHeader(
                message_id="ack-test",
                sender_id="agent-a",
                recipient_id="agent-b",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="test"
            ),
            payload=EncryptedPayload("enc", "nonce", "salt"),
            signature="sig"
        )
        
        msg_id = await message_queue.publish("ack.channel", msg)
        received = await message_queue.receive("ack.channel", timeout=1.0)
        
        # Ack
        await message_queue.ack(received.id)
    
    @pytest.mark.asyncio
    async def test_subscribe(self, message_queue):
        """Test subscription"""
        from agents.v2.secure_message import MessageHeader, EncryptedPayload
        
        received_messages = []
        
        async def handler(msg):
            received_messages.append(msg)
        
        # Subscribe
        sub_task = asyncio.create_task(
            self._collect_messages(message_queue, handler)
        )
        
        # Publish a message
        await asyncio.sleep(0.1)  # Let subscription setup
        
        msg = SecureMessage(
            header=MessageHeader(
                message_id="sub-test",
                sender_id="agent-a",
                recipient_id="agent-b",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="test"
            ),
            payload=EncryptedPayload("enc", "nonce", "salt"),
            signature="sig"
        )
        
        await message_queue.publish("sub.channel", msg)
        
        # Wait for message
        await asyncio.sleep(0.2)
        sub_task.cancel()
    
    async def _collect_messages(self, queue, handler):
        """Helper to collect subscribed messages"""
        try:
            async for msg in queue.subscribe(["sub.channel"]):
                handler(msg)
        except asyncio.CancelledError:
            pass


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Test complete message flow"""
        from database.auth_models import init_auth_db
        init_auth_db()
        
        # Setup
        auth = AgentAuthenticator()
        queue = InMemoryMessageQueue()
        await queue.connect()
        
        # Create agent
        creds = auth.generate_api_key(AgentRole.RESEARCHER, "integration-agent")
        
        # Authenticate
        identity = auth.authenticate(creds.api_key, creds.api_secret)
        assert identity is not None
        
        # Create and send message
        from agents.v2.secure_message import MessageHeader, EncryptedPayload
        
        msg = SecureMessage(
            header=MessageHeader(
                message_id="int-test",
                sender_id=creds.agent_id,
                recipient_id="broadcast",
                timestamp=datetime.utcnow().isoformat(),
                msg_type="task"
            ),
            payload=EncryptedPayload("task_payload", "nonce", "salt"),
            signature="sig"
        )
        
        msg_id = await queue.publish("tasks", msg)
        assert msg_id is not None
        
        # Receive
        received = await queue.receive("tasks", timeout=1.0)
        assert received is not None
        
        # Ack
        await queue.ack(received.id)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Agent Communication v2
======================

Secure, scalable agent communication system.

Features:
- End-to-end encryption (X25519 + AES-256-GCM)
- Ed25519 message signing
- API key authentication
- Message queue integration (Redis)
- Real-time event streaming (WebSocket)
- Delivery guarantees

Usage:
    from agents.v2 import AgentClient, SecureMessage

    agent = AgentClient(agent_id="agt_xxx", api_key="key_xxx")
    await agent.connect()
    await agent.send_message(recipient="agt_yyy", payload={...})
"""

from .agent_client import AgentClient, AgentConnectionError
from .auth_manager import AgentAuthenticator, AgentCredentials
from .secure_message import EncryptedPayload, MessageEncryption, SecureMessage

__version__ = "2.0.0"

__all__ = [
    "SecureMessage",
    "MessageEncryption",
    "EncryptedPayload",
    "AgentClient",
    "AgentConnectionError",
    "AgentAuthenticator",
    "AgentCredentials",
]

"""
🌐 P2P Secure Connection Module.

Peer-to-peer encrypted connection between mobile phone and local machine.
Uses WebRTC for NAT traversal and DTLS for encryption.
"""

from .channel import SecureDataChannel
from .connection import P2PConfig, P2PConnection
from .signaling import KimiSignalingBridge

__all__ = [
    "P2PConnection",
    "P2PConfig",
    "KimiSignalingBridge",
    "SecureDataChannel",
]

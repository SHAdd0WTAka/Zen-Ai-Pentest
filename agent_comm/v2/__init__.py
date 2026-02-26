"""
gRPC Agent Communication Protocol v2.0

High-performance agent communication for Zen-AI-Pentest supporting 100+ agents.

Features:
- Protocol Buffers for efficient serialization
- Bidirectional streaming for real-time communication
- Backpressure and circuit breaker patterns
- End-to-end encryption (mTLS)
- Kubernetes deployment ready
"""

__version__ = "2.0.0"
__all__ = [
    "GRPCServer",
    "GRPCClient",
    "AgentRegistry",
    "MessageQueue",
    "CircuitBreaker",
    "BackpressureController",
]

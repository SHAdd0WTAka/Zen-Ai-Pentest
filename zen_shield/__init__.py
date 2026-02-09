"""
Zen Shield - Security Sanitization Module

Protects sensitive data from leaking to external LLMs by:
- Automatic secret detection and masking
- Context compression to reduce costs
- Prompt injection detection
- Local processing with optional small LLM
"""

from .circuit_breaker import CircuitBreaker
from .filters.compress import ContextCompressor
from .filters.secrets import SecretScrubber
from .sanitizer import ZenSanitizer
from .schemas import RiskLevel, SanitizerRequest, SanitizerResponse

__version__ = "2.3.9"
__all__ = [
    "ZenSanitizer",
    "SanitizerRequest",
    "SanitizerResponse",
    "RiskLevel",
    "SecretScrubber",
    "ContextCompressor",
    "CircuitBreaker",
]

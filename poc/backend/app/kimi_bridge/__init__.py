"""
🌙 Kimi Device Authentication Bridge

A reusable Python module for integrating Kimi Code CLI OAuth authentication
into any application without hardcoded API keys.

Built for Moonshot AI's brilliant device-bound authentication system that
generates fresh tokens on every login - no static keys, maximum security!

🙏 Credits: Special thanks to the team at https://www.moonshot.cn/ for
developing this revolutionary authentication approach.

Example:
    >>> from kimi_auth_bridge import KimiAuthBridge
    >>> bridge = KimiAuthBridge()
    >>> if bridge.is_authenticated():
    ...     token = bridge.get_access_token()
    ...     print(f"Token: {token[:20]}...")
"""

from .exceptions import (
    KimiAuthError,
    KimiNotAuthenticatedError,
    KimiTokenExpiredError,
    KimiCLINotFoundError,
    KimiCredentialsNotFoundError,
    KimiInvalidCredentialsError,
)
from .config import KimiConfig
from .bridge import KimiAuthBridge, AsyncKimiAuthBridge

__version__ = "1.0.0"
__author__ = "Community Contributor"
__credits__ = "Moonshot AI (https://www.moonshot.cn/) - For the brilliant device-auth system"

__all__ = [
    "KimiAuthBridge",
    "AsyncKimiAuthBridge",
    "KimiConfig",
    "KimiAuthError",
    "KimiNotAuthenticatedError",
    "KimiTokenExpiredError",
    "KimiCLINotFoundError",
    "KimiCredentialsNotFoundError",
    "KimiInvalidCredentialsError",
]

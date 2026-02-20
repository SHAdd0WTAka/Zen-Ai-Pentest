"""
VPN Decorators
==============

Decorators for VPN-aware functions.
Provides warnings and optional enforcement.
"""

import asyncio
import functools
import logging
from typing import Callable, Optional

from vpn.protonvpn import VPNManager, VPNStatus

logger = logging.getLogger("zen.vpn")


def recommend_vpn(message: Optional[str] = None, show_status: bool = True):
    """
    Decorator that recommends VPN usage but doesn't enforce it.

    Args:
        message: Custom warning message
        show_status: Whether to show VPN status

    Usage:
        @recommend_vpn()
        async def scan_target(target: str):
            # This will show warning if VPN not connected
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check VPN status
            vpn = VPNManager()
            status = vpn.check_before_scan(str(args[0]) if args else "unknown")

            # Show warning if not connected
            if status["warning"]:
                logger.warning(status["warning"])
            if status["recommendation"]:
                logger.info(status["recommendation"])

            # Execute function regardless
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check VPN status
            vpn = VPNManager()
            status = vpn.check_before_scan(str(args[0]) if args else "unknown")

            # Show warning if not connected
            if status["warning"]:
                logger.warning(status["warning"])
            if status["recommendation"]:
                logger.info(status["recommendation"])

            # Execute function regardless
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def require_vpn(message: str = "VPN connection required", allowed_networks: Optional[list] = None):
    """
    Decorator that requires VPN connection.

    Args:
        message: Error message when VPN not connected
        allowed_networks: List of networks that don't require VPN (e.g., ["127.0.0.1"])

    Usage:
        @require_vpn()
        async def scan_target(target: str):
            # This will raise error if VPN not connected
            pass
    """
    allowed = allowed_networks or ["127.0.0.1", "localhost", "::1"]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            target = str(args[0]) if args else ""

            # Check if target is in allowed networks
            if any(net in target for net in allowed):
                return await func(*args, **kwargs)

            # Check VPN status
            vpn = VPNManager()
            if not vpn.is_connected():
                raise PermissionError(f"{message}\n" f"Target: {target}\n" f"Please connect to a VPN before scanning.")

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            target = str(args[0]) if args else ""

            # Check if target is in allowed networks
            if any(net in target for net in allowed):
                return func(*args, **kwargs)

            # Check VPN status
            vpn = VPNManager()
            if not vpn.is_connected():
                raise PermissionError(f"{message}\n" f"Target: {target}\n" f"Please connect to a VPN before scanning.")

            return func(*args, **kwargs)

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_vpn_check(func: Callable) -> Callable:
    """
    Simple decorator that logs VPN status before execution.
    Non-blocking - just for logging.
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        vpn = VPNManager()
        status = vpn.get_status()

        if status.status == VPNStatus.CONNECTED:
            logger.debug(f"🔒 VPN active ({status.provider}) - executing {func.__name__}")
        else:
            logger.debug(f"🔓 No VPN - executing {func.__name__}")

        return await func(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        vpn = VPNManager()
        status = vpn.get_status()

        if status.status == VPNStatus.CONNECTED:
            logger.debug(f"🔒 VPN active ({status.provider}) - executing {func.__name__}")
        else:
            logger.debug(f"🔓 No VPN - executing {func.__name__}")

        return func(*args, **kwargs)

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

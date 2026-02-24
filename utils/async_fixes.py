#!/usr/bin/env python3
"""
AsyncIO Fixes for Windows/Python 3.13 compatibility
Handles ProactorEventLoop shutdown errors
Author: SHAdd0WTAka
"""

import asyncio
import platform
import sys
import warnings


def apply_windows_async_fixes():
    """
    Apply fixes for asyncio issues on Windows with Python 3.13+

    This fixes the _ProactorBasePipeTransport._call_connection_lost error
    that occurs when connections are closed during event loop shutdown.
    """
    if platform.system() != "Windows":
        return

    # Suppress the specific warning about unclosed transports
    warnings.filterwarnings("ignore", message="unclosed transport")

    # Python 3.13+ specific fixes
    if sys.version_info >= (3, 13):
        # Fix for ProactorEventLoop shutdown errors
        _patch_proactor_connection_lost()

    # Use SelectorEventLoop on Windows for better compatibility
    # (ProactorEventLoop is default on 3.8+ but has issues)
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass  # Not on Windows or older Python


def _patch_proactor_connection_lost():
    """
    Patch the ProactorBasePipeTransport to handle shutdown gracefully
    """
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport

        original_close = _ProactorBasePipeTransport.close

        def patched_close(self):
            """Patched close method that handles shutdown errors"""
            try:
                original_close(self)
            except (OSError, AttributeError):
                # Ignore errors during shutdown
                pass

        _ProactorBasePipeTransport.close = patched_close

        # Also patch _call_connection_lost
        original_call_connection_lost = (
            _ProactorBasePipeTransport._call_connection_lost
        )

        def patched_call_connection_lost(self, exc):
            """Patched _call_connection_lost that handles shutdown errors"""
            try:
                original_call_connection_lost(self, exc)
            except (OSError, AttributeError):
                # Silently ignore shutdown errors
                pass

        _ProactorBasePipeTransport._call_connection_lost = (
            patched_call_connection_lost
        )

    except ImportError:
        pass  # Not on Windows or different Python version


async def safe_close_session(session):
    """
    Safely close an aiohttp session

    Args:
        session: aiohttp ClientSession to close
    """
    if session is None:
        return

    try:
        await session.close()
        # Give the loop time to clean up
        await asyncio.sleep(0.1)
    except Exception:
        pass  # Ignore cleanup errors


def setup_event_loop():
    """
    Setup the event loop with proper Windows fixes

    Returns:
        asyncio.AbstractEventLoop: Configured event loop
    """
    apply_windows_async_fixes()

    # Get or create event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


class GracefulExit:
    """
    Context manager for graceful async shutdown

    Usage:
        async with GracefulExit() as exit_manager:
            # Your async code here
            pass
    """

    def __init__(self):
        self._sessions = []

    def register_session(self, session):
        """Register a session for cleanup"""
        if session:
            self._sessions.append(session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all registered sessions"""
        for session in self._sessions:
            await safe_close_session(session)
        # Small delay to let transports close
        await asyncio.sleep(0.25)


def silence_asyncio_warnings():
    """
    Silence common asyncio warnings that don't affect functionality
    """
    warnings.filterwarnings(
        "ignore",
        category=RuntimeWarning,
        message="coroutine.*was never awaited",
    )
    warnings.filterwarnings("ignore", message=r".*socket\.socket.*")
    warnings.filterwarnings("ignore", message=".*_ProactorBasePipeTransport.*")
    warnings.filterwarnings("ignore", message=".*unclosed.*")
    warnings.filterwarnings("ignore", message=".*Unclosed connector.*")

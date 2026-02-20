#!/usr/bin/env python3
"""
Test async fixes for Windows/Python 3.13 compatibility
Author: SHAdd0WTAka
"""

import asyncio
import os
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.async_fixes import apply_windows_async_fixes, safe_close_session, setup_event_loop, silence_asyncio_warnings


@pytest.mark.asyncio
async def test_basic_async():
    """Test basic async functionality"""
    print("[1] Testing basic async operations...")

    # Test simple async operation
    async def dummy_task():
        await asyncio.sleep(0.1)
        return "success"

    result = await dummy_task()
    assert result == "success", "Basic async failed"
    print("    ✓ Basic async works")


@pytest.mark.asyncio
async def test_session_cleanup():
    """Test session cleanup"""
    print("[2] Testing session cleanup...")

    try:
        import aiohttp

        session = aiohttp.ClientSession()
        await safe_close_session(session)
        print("    ✓ Session cleanup successful")

        # Test with None
        await safe_close_session(None)
        print("    ✓ None session handled correctly")

    except ImportError:
        print("    ⚠ aiohttp not installed, skipping")


def test_event_loop_setup():
    """Test event loop setup"""
    print("[3] Testing event loop setup...")

    loop = setup_event_loop()
    assert loop is not None, "Event loop setup failed"

    # Check if we can run a simple task
    async def check():
        return True

    result = loop.run_until_complete(check())
    assert result is True, "Event loop execution failed"
    print("    ✓ Event loop setup successful")


def test_windows_fixes():
    """Test Windows-specific fixes"""
    print("[4] Testing Windows-specific fixes...")

    # Apply fixes (should work on any platform)
    apply_windows_async_fixes()
    silence_asyncio_warnings()
    print("    ✓ Windows fixes applied successfully")

    # Check if we're on Windows
    if sys.platform == "win32":
        print("    ✓ Running on Windows - fixes active")
    else:
        print("    ⚠ Not on Windows - fixes applied but may not be needed")


@pytest.mark.asyncio
async def test_multiple_sessions():
    """Test multiple session cleanup"""
    print("[5] Testing multiple session cleanup...")

    try:
        import aiohttp

        sessions = [aiohttp.ClientSession() for _ in range(3)]

        for session in sessions:
            await safe_close_session(session)

        print("    ✓ Multiple sessions cleaned up")

    except ImportError:
        print("    ⚠ aiohttp not installed, skipping")


# Note: Tests can be run individually or via pytest

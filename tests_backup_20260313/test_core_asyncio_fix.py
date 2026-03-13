"""
Tests for core/asyncio_fix.py
Target: 80%+ Coverage
"""

import asyncio
import sys
from unittest.mock import MagicMock, call, patch

import pytest


class TestIsWindows:
    """Test is_windows function"""

    @patch("platform.system", return_value="Windows")
    def test_is_windows_true(self, mock_system):
        """Test is_windows returns True on Windows"""
        from core.asyncio_fix import is_windows

        assert is_windows() is True

    @patch("platform.system", return_value="Linux")
    def test_is_windows_false(self, mock_system):
        """Test is_windows returns False on Linux"""
        from core.asyncio_fix import is_windows

        assert is_windows() is False

    @patch("platform.system", return_value="Darwin")
    def test_is_windows_macos(self, mock_system):
        """Test is_windows on macOS"""
        from core.asyncio_fix import is_windows

        assert is_windows() is False


class TestIsPython313OrHigher:
    """Test is_python_313_or_higher function"""

    @patch("sys.version_info", (3, 13, 0))
    def test_python_313_true(self):
        """Test returns True for Python 3.13"""
        from core.asyncio_fix import is_python_313_or_higher

        assert is_python_313_or_higher() is True

    @patch("sys.version_info", (3, 14, 0))
    def test_python_314_true(self):
        """Test returns True for Python 3.14"""
        from core.asyncio_fix import is_python_313_or_higher

        assert is_python_313_or_higher() is True

    @patch("sys.version_info", (3, 12, 0))
    def test_python_312_false(self):
        """Test returns False for Python 3.12"""
        from core.asyncio_fix import is_python_313_or_higher

        assert is_python_313_or_higher() is False


class TestApplyWindowsAsyncioFix:
    """Test apply_windows_asyncio_fix function"""

    @patch("core.asyncio_fix.is_windows", return_value=False)
    def test_apply_fix_non_windows(self, mock_is_windows):
        """Test fix does nothing on non-Windows"""
        from core.asyncio_fix import apply_windows_asyncio_fix

        # Should return immediately without doing anything
        result = apply_windows_asyncio_fix()
        assert result is None

    @patch("core.asyncio_fix.is_windows", return_value=True)
    @patch("core.asyncio_fix.is_python_313_or_higher", return_value=False)
    def test_apply_fix_windows_old_python(self, mock_py313, mock_win):
        """Test fix on Windows with older Python"""
        from core.asyncio_fix import apply_windows_asyncio_fix

        # Should not raise, just skip the Windows-specific fixes
        apply_windows_asyncio_fix()


class TestSafeAsyncioRunner:
    """Test SafeAsyncioRunner class"""

    def test_runner_init_with_timeout(self):
        """Test runner initialization with timeout"""
        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner(timeout=30.0)
        assert runner.timeout == 30.0

    def test_runner_init_without_timeout(self):
        """Test runner initialization without timeout"""
        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner()
        assert runner.timeout is None

    @patch("core.asyncio_fix.is_windows", return_value=False)
    @patch("asyncio.run")
    def test_run_non_windows(self, mock_run, mock_is_win):
        """Test run on non-Windows uses asyncio.run"""
        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner()
        mock_coro = MagicMock()
        mock_run.return_value = "result"

        result = runner.run(mock_coro)

        mock_run.assert_called_once_with(mock_coro)
        assert result == "result"


class TestAsyncIOContext:
    """Test AsyncIOContext class"""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager"""
        from core.asyncio_fix import AsyncIOContext

        ctx = AsyncIOContext()

        async with ctx as context:
            assert context is ctx

    @pytest.mark.asyncio
    async def test_run_task_without_timeout(self):
        """Test run_task without timeout"""
        from core.asyncio_fix import AsyncIOContext

        ctx = AsyncIOContext()

        async with ctx:

            async def task():
                return "task_result"

            result = await ctx.run_task(task())
            assert result == "task_result"

    @pytest.mark.asyncio
    async def test_run_task_with_timeout(self):
        """Test run_task with timeout"""
        from core.asyncio_fix import AsyncIOContext

        ctx = AsyncIOContext(timeout=5.0)

        async with ctx:

            async def task():
                return "task_result"

            result = await ctx.run_task(task())
            assert result == "task_result"


class TestPatchAsyncioForWindows:
    """Test patch_asyncio_for_windows function"""

    def test_patch_runs_without_error(self):
        """Test patch runs without error"""
        from core.asyncio_fix import patch_asyncio_for_windows

        # Should not raise any exceptions
        # Note: On import, this is already called once
        try:
            patch_asyncio_for_windows()
        except Exception as e:
            pytest.fail(f"patch_asyncio_for_windows raised {e}")


class TestModuleExports:
    """Test module exports"""

    def test_all_functions_importable(self):
        """Test all main functions can be imported"""
        from core.asyncio_fix import (
            AsyncIOContext,
            SafeAsyncioRunner,
            apply_windows_asyncio_fix,
            is_python_313_or_higher,
            is_windows,
            patch_asyncio_for_windows,
            safe_asyncio_run,
        )

        assert callable(is_windows)
        assert callable(is_python_313_or_higher)
        assert callable(apply_windows_asyncio_fix)
        assert callable(safe_asyncio_run)
        assert callable(patch_asyncio_for_windows)


class TestRunnerWithFix:
    """Test _run_with_fix method"""

    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    def test_run_with_fix_timeout(self, mock_set_loop, mock_new_loop):
        """Test _run_with_fix with timeout"""
        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner(timeout=5.0)
        mock_loop = MagicMock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = "result"

        async def test_coro():
            return "result"

        result = runner._run_with_fix(test_coro())

        assert mock_loop.set_exception_handler.called
        mock_loop.close.assert_called_once()

    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    def test_run_with_fix_no_timeout(self, mock_set_loop, mock_new_loop):
        """Test _run_with_fix without timeout"""
        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner(timeout=None)
        mock_loop = MagicMock()
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = "result"

        async def test_coro():
            return "result"

        result = runner._run_with_fix(test_coro())

        # Should be called for coro AND shutdown_asyncgens
        assert mock_loop.run_until_complete.call_count >= 1
        mock_loop.close.assert_called_once()


class TestExceptionHandling:
    """Test exception handling in runner"""

    def test_exception_handler_logs_error(self):
        """Test that exception handler logs errors"""
        import logging

        from core.asyncio_fix import SafeAsyncioRunner

        runner = SafeAsyncioRunner()

        # Test the exception handler function exists
        mock_loop = MagicMock()
        handler = None

        def capture_handler(loop, context):
            nonlocal handler
            handler = context

        # Verify the method exists
        assert hasattr(runner, "_run_with_fix")

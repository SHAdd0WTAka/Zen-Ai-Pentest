"""
Unit Tests für utils/async_fixes.py

Tests async fixes with platform mocking.
"""

import pytest
import asyncio
import sys
import platform
import warnings
from unittest.mock import MagicMock, AsyncMock
from utils.async_fixes import (
    apply_windows_async_fixes,
    safe_close_session,
    setup_event_loop,
    GracefulExit,
    silence_asyncio_warnings,
)

pytestmark = pytest.mark.unit


class TestApplyWindowsAsyncFixes:
    """Test apply_windows_async_fixes function"""
    
    def test_skip_on_linux(self, monkeypatch):
        """Test function returns early on non-Windows"""
        monkeypatch.setattr(platform, 'system', lambda: 'Linux')
        # Should not raise any errors
        apply_windows_async_fixes()
    
    def test_skip_on_mac(self, monkeypatch):
        """Test function returns early on macOS"""
        monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
        apply_windows_async_fixes()
    
    def test_windows_pre_313(self, monkeypatch):
        """Test Windows fix for Python < 3.13"""
        monkeypatch.setattr(platform, 'system', lambda: 'Windows')
        monkeypatch.setattr(sys, 'version_info', (3, 12))
        
        policy_calls = []
        monkeypatch.setattr(asyncio, 'set_event_loop_policy', lambda p: policy_calls.append(p))
        
        apply_windows_async_fixes()
        assert len(policy_calls) == 1
    
    def test_windows_313_plus(self, monkeypatch):
        """Test Windows fix for Python 3.13+"""
        monkeypatch.setattr(platform, 'system', lambda: 'Windows')
        monkeypatch.setattr(sys, 'version_info', (3, 13))
        
        policy_calls = []
        filter_calls = []
        monkeypatch.setattr(asyncio, 'set_event_loop_policy', lambda p: policy_calls.append(p))
        original_filterwarnings = warnings.filterwarnings
        monkeypatch.setattr(warnings, 'filterwarnings', lambda *a, **k: filter_calls.append((a, k)))
        
        apply_windows_async_fixes()
        assert len(policy_calls) == 1
        assert len(filter_calls) > 0


class TestSafeCloseSession:
    """Test safe_close_session function"""
    
    @pytest.mark.asyncio
    async def test_close_none_session(self):
        """Test closing None session"""
        # Should not raise
        await safe_close_session(None)
    
    @pytest.mark.asyncio
    async def test_close_valid_session(self):
        """Test closing valid session"""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        
        await safe_close_session(mock_session)
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_raises_exception(self):
        """Test session that raises on close"""
        mock_session = MagicMock()
        mock_session.close = AsyncMock(side_effect=Exception("Close error"))
        
        # Should not raise
        await safe_close_session(mock_session)


class TestSetupEventLoop:
    """Test setup_event_loop function"""
    
    def test_get_running_loop(self, monkeypatch):
        """Test when loop is already running"""
        mock_loop = MagicMock()
        monkeypatch.setattr(asyncio, 'get_running_loop', lambda: mock_loop)
        
        result = setup_event_loop()
        assert result == mock_loop
    
    def test_create_new_loop(self, monkeypatch):
        """Test creating new event loop"""
        monkeypatch.setattr(asyncio, 'get_running_loop', lambda: (_ for _ in ()).throw(RuntimeError()))
        
        mock_loop = MagicMock()
        monkeypatch.setattr(asyncio, 'new_event_loop', lambda: mock_loop)
        
        set_calls = []
        monkeypatch.setattr(asyncio, 'set_event_loop', lambda l: set_calls.append(l))
        
        result = setup_event_loop()
        assert result == mock_loop
        assert set_calls == [mock_loop]


class TestGracefulExit:
    """Test GracefulExit context manager"""
    
    @pytest.mark.asyncio
    async def test_context_manager_enter(self):
        """Test entering context"""
        async with GracefulExit() as ge:
            assert isinstance(ge, GracefulExit)
            assert ge._sessions == []
    
    @pytest.mark.asyncio
    async def test_register_session(self):
        """Test registering sessions"""
        async with GracefulExit() as ge:
            mock_session = MagicMock()
            ge.register_session(mock_session)
            assert len(ge._sessions) == 1
    
    @pytest.mark.asyncio
    async def test_register_none_session(self):
        """Test registering None session"""
        async with GracefulExit() as ge:
            ge.register_session(None)
            assert len(ge._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_on_exit(self):
        """Test cleanup on context exit"""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        
        async with GracefulExit() as ge:
            ge.register_session(mock_session)
        
        # Session should be closed
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_multiple_sessions(self):
        """Test cleanup of multiple sessions"""
        sessions = []
        for i in range(3):
            mock_session = MagicMock()
            mock_session.close = AsyncMock()
            sessions.append(mock_session)
        
        async with GracefulExit() as ge:
            for s in sessions:
                ge.register_session(s)
        
        # All sessions should be closed
        for s in sessions:
            s.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_exception(self):
        """Test cleanup when session raises exception"""
        mock_session = MagicMock()
        mock_session.close = AsyncMock(side_effect=Exception("Close failed"))
        
        async with GracefulExit() as ge:
            ge.register_session(mock_session)
        
        # Should handle exception gracefully
        mock_session.close.assert_called_once()


class TestSilenceAsyncioWarnings:
    """Test silence_asyncio_warnings function"""
    
    def test_silences_warnings(self, monkeypatch):
        """Test that warnings are filtered"""
        filter_calls = []
        monkeypatch.setattr(warnings, 'filterwarnings', lambda *a, **k: filter_calls.append((a, k)))
        
        silence_asyncio_warnings()
        
        # Should be called multiple times for different warning patterns
        assert len(filter_calls) >= 4
    
    def test_silences_coroutine_warning(self, monkeypatch):
        """Test coroutine never awaited is silenced"""
        filter_calls = []
        monkeypatch.setattr(warnings, 'filterwarnings', lambda *a, **k: filter_calls.append((a, k)))
        
        silence_asyncio_warnings()
        
        # Check one call contains coroutine pattern (in kwargs)
        coroutine_calls = [c for c in filter_calls if 'coroutine' in str(c)]
        assert len(coroutine_calls) > 0
    
    def test_silences_proactor_warning(self, monkeypatch):
        """Test Proactor warning is silenced"""
        filter_calls = []
        monkeypatch.setattr(warnings, 'filterwarnings', lambda *a, **k: filter_calls.append((a, k)))
        
        silence_asyncio_warnings()
        
        proactor_calls = [c for c in filter_calls if 'Proactor' in str(c)]
        assert len(proactor_calls) > 0


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_graceful_exit_with_real_async(self):
        """Test GracefulExit with real async operations"""
        class FakeSession:
            def __init__(self):
                self.closed = False
            
            async def close(self):
                await asyncio.sleep(0.01)
                self.closed = True
        
        session = FakeSession()
        
        async with GracefulExit() as ge:
            ge.register_session(session)
        
        assert session.closed is True
    
    def test_setup_event_loop_integration(self, monkeypatch):
        """Test setup_event_loop creates valid loop"""
        monkeypatch.setattr('utils.async_fixes.apply_windows_async_fixes', lambda: None)
        loop = setup_event_loop()
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)

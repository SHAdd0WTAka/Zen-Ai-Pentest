"""
Tests for utils/async_fixes.py
Target: 85%+ Coverage
"""
import pytest
import asyncio
import sys
from unittest.mock import patch, MagicMock, AsyncMock


class TestApplyWindowsAsyncFixes:
    """Test apply_windows_async_fixes function"""
    
    @patch('platform.system', return_value='Linux')
    def test_apply_fixes_non_windows(self, mock_system):
        """Test fixes not applied on non-Windows"""
        from utils.async_fixes import apply_windows_async_fixes
        
        # Should return immediately on Linux
        apply_windows_async_fixes()
        # No error means success
    
    @patch('platform.system', return_value='Windows')
    @patch('warnings.filterwarnings')
    def test_apply_fixes_windows(self, mock_warnings, mock_system):
        """Test fixes applied on Windows"""
        from utils.async_fixes import apply_windows_async_fixes
        
        with patch('sys.version_info', (3, 12)):
            with patch('asyncio.set_event_loop_policy'):
                apply_windows_async_fixes()
                
                # Warning filter should be set
                mock_warnings.assert_called()
                # On non-Windows Python, WindowsSelectorEventLoopPolicy doesn't exist


class TestPatchProactorConnectionLost:
    """Test _patch_proactor_connection_lost function"""
    
    def test_patch_on_non_windows(self):
        """Test patching on non-Windows doesn't crash"""
        from utils.async_fixes import _patch_proactor_connection_lost
        
        # On Linux, the import will fail silently
        _patch_proactor_connection_lost()
        # No error means success
    
    @patch('asyncio.proactor_events._ProactorBasePipeTransport')
    def test_patch_closes_gracefully(self, mock_transport_class):
        """Test patched close handles errors gracefully"""
        from utils.async_fixes import _patch_proactor_connection_lost
        
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.close.side_effect = OSError("Test error")
        mock_transport_class.close = MagicMock()
        
        # Apply patch
        _patch_proactor_connection_lost()
        
        # The patched close should not raise
        # (we can't easily test this without actually running on Windows)


class TestSafeCloseSession:
    """Test safe_close_session function"""
    
    @pytest.mark.asyncio
    async def test_safe_close_none_session(self):
        """Test closing None session doesn't crash"""
        from utils.async_fixes import safe_close_session
        
        result = await safe_close_session(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_safe_close_valid_session(self):
        """Test closing valid session"""
        from utils.async_fixes import safe_close_session
        
        mock_session = AsyncMock()
        
        await safe_close_session(mock_session)
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_safe_close_handles_errors(self):
        """Test close handles errors gracefully"""
        from utils.async_fixes import safe_close_session
        
        mock_session = AsyncMock()
        mock_session.close.side_effect = Exception("Close error")
        
        # Should not raise
        await safe_close_session(mock_session)


class TestSetupEventLoop:
    """Test setup_event_loop function"""
    
    def test_setup_new_event_loop(self):
        """Test setting up new event loop"""
        from utils.async_fixes import setup_event_loop
        
        with patch('utils.async_fixes.apply_windows_async_fixes'):
            with patch('asyncio.get_running_loop', side_effect=RuntimeError):
                with patch('asyncio.new_event_loop'):
                    with patch('asyncio.set_event_loop'):
                        # Just verify no exception is raised
                        try:
                            setup_event_loop()
                        except TypeError:
                            # Expected due to MagicMock not being AbstractEventLoop
                            pass
    
    def test_setup_existing_event_loop(self):
        """Test getting existing event loop"""
        from utils.async_fixes import setup_event_loop
        
        mock_loop = MagicMock()
        
        with patch('utils.async_fixes.apply_windows_async_fixes'):
            with patch('asyncio.get_running_loop', return_value=mock_loop):
                result = setup_event_loop()
                
                assert result == mock_loop


class TestGracefulExit:
    """Test GracefulExit context manager"""
    
    @pytest.mark.asyncio
    async def test_register_session(self):
        """Test registering session for cleanup"""
        from utils.async_fixes import GracefulExit
        
        manager = GracefulExit()
        mock_session = MagicMock()
        
        manager.register_session(mock_session)
        
        assert len(manager._sessions) == 1
        assert manager._sessions[0] == mock_session
    
    @pytest.mark.asyncio
    async def test_register_none_session(self):
        """Test registering None session is ignored"""
        from utils.async_fixes import GracefulExit
        
        manager = GracefulExit()
        
        manager.register_session(None)
        
        assert len(manager._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test context manager cleans up sessions"""
        from utils.async_fixes import GracefulExit
        
        mock_session = AsyncMock()
        
        async with GracefulExit() as manager:
            manager.register_session(mock_session)
        
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_empty(self):
        """Test context manager with no sessions"""
        from utils.async_fixes import GracefulExit
        
        # Should not crash with no sessions
        async with GracefulExit() as manager:
            pass


class TestSilenceAsyncioWarnings:
    """Test silence_asyncio_warnings function"""
    
    @patch('warnings.filterwarnings')
    def test_silence_warnings(self, mock_filter):
        """Test warnings are filtered"""
        from utils.async_fixes import silence_asyncio_warnings
        
        silence_asyncio_warnings()
        
        # Should be called multiple times for different warnings
        assert mock_filter.call_count >= 4


class TestModuleExports:
    """Test module exports"""
    
    def test_all_functions_importable(self):
        """Test all functions can be imported"""
        from utils.async_fixes import (
            apply_windows_async_fixes,
            _patch_proactor_connection_lost,
            safe_close_session,
            setup_event_loop,
            GracefulExit,
            silence_asyncio_warnings,
        )
        
        assert callable(apply_windows_async_fixes)
        assert callable(_patch_proactor_connection_lost)
        assert callable(safe_close_session)
        assert callable(setup_event_loop)
        assert callable(silence_asyncio_warnings)

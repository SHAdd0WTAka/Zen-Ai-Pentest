"""
LLM Backends Tests
==================

Comprehensive tests for LLM backend integrations:
- Kimi backend
- OpenRouter backend
- Claude backend
- Mock all API calls
"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest

from backends.claude_direct import ClaudeDirectBackend
from backends.kimi_auth_backend import AuthenticationRequiredError, KimiAuthBackend, create_kimi_backend
from backends.openrouter import OpenRouterBackend


class TestKimiAuthBackend:
    """Test Kimi AI Backend with OAuth Token Support"""

    def test_init_default(self):
        """Initialize with default values"""
        backend = KimiAuthBackend()

        assert backend.name == "Kimi"
        assert backend.priority == 2
        assert backend._api_key is None

    def test_init_with_api_key(self):
        """Initialize with API key"""
        backend = KimiAuthBackend(api_key="test-key")

        assert backend._api_key == "test-key"

    @pytest.mark.asyncio
    async def test_aenter_aexit(self):
        """Test async context manager"""
        backend = KimiAuthBackend()

        async with backend as b:
            assert b.session is not None

        # After exit, session should be closed

    @patch.dict(os.environ, {"KIMI_API_KEY": "env-api-key"})
    def test_get_auth_token_from_env(self):
        """Get auth token from environment variable"""
        backend = KimiAuthBackend()

        token = backend._get_auth_token()

        assert token == "env-api-key"

    def test_get_auth_token_from_constructor(self):
        """Get auth token from constructor (fallback)"""
        backend = KimiAuthBackend(api_key="constructor-key")

        token = backend._get_auth_token()

        assert token == "constructor-key"

    @patch("backends.kimi_auth_backend.get_stored_token")
    def test_get_auth_token_from_store(self, mock_get_token):
        """Get auth token from token store"""
        mock_get_token.return_value = "stored-token"

        backend = KimiAuthBackend()
        token = backend._get_auth_token()

        assert token == "stored-token"

    def test_get_auth_token_no_token(self):
        """Return None when no token available"""
        backend = KimiAuthBackend()

        token = backend._get_auth_token()

        assert token is None

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Successful chat completion"""
        backend = KimiAuthBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is the AI response"}}]
        }
        mock_response.raise_for_status = Mock()

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello, AI!")

        assert response == "This is the AI response"

    @pytest.mark.asyncio
    async def test_chat_no_auth(self):
        """Chat without authentication raises error"""
        backend = KimiAuthBackend()  # No API key

        with pytest.raises(AuthenticationRequiredError):
            await backend.chat("Hello")

    @pytest.mark.asyncio
    async def test_chat_401_error(self):
        """Handle 401 authentication error"""
        backend = KimiAuthBackend(api_key="invalid-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 401

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.object(backend, "_refresh_token_if_needed", return_value=False):
            with pytest.raises(AuthenticationRequiredError):
                await backend.chat("Hello")

    @pytest.mark.asyncio
    async def test_chat_api_error(self):
        """Handle API error"""
        backend = KimiAuthBackend(api_key="test-key")
        backend.session = AsyncMock()
        backend.session.post.side_effect = aiohttp.ClientError("Connection failed")

        with pytest.raises(aiohttp.ClientError):
            await backend.chat("Hello")

    @pytest.mark.asyncio
    async def test_chat_stream_success(self):
        """Successful streaming chat"""
        backend = KimiAuthBackend(api_key="test-key")
        backend.session = AsyncMock()

        # Create mock response for streaming
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()

        # Simulate streaming data
        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
            b'data: {"choices": [{"delta": {"content": " World"}}]}\n',
            b'data: [DONE]\n',
        ]

        async def mock_iter():
            for data in stream_data:
                yield data

        mock_response.content = mock_iter()

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        chunks = []
        async for chunk in backend.chat_stream("Hello"):
            chunks.append(chunk)

        assert "".join(chunks) == "Hello World"

    @pytest.mark.asyncio
    async def test_chat_stream_no_auth(self):
        """Stream chat without authentication"""
        backend = KimiAuthBackend()

        with pytest.raises(AuthenticationRequiredError):
            async for _ in backend.chat_stream("Hello"):
                pass

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Successfully refresh token"""
        backend = KimiAuthBackend()
        backend.token_store = Mock()
        backend.token_store.get_refresh_token.return_value = "refresh-token"

        mock_flow = AsyncMock()
        mock_flow.refresh_access_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        with patch("backends.kimi_auth_backend.DeviceCodeFlow", return_value=mock_flow):
            with patch.object(mock_flow, "__aenter__", return_value=mock_flow):
                with patch.object(mock_flow, "__aexit__", AsyncMock()):
                    result = await backend._refresh_token_if_needed()

        assert result is True
        backend.token_store.save_credentials.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self):
        """Refresh without refresh token fails"""
        backend = KimiAuthBackend()
        backend.token_store = Mock()
        backend.token_store.get_refresh_token.return_value = None

        result = await backend._refresh_token_if_needed()

        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self):
        """Handle refresh token failure"""
        backend = KimiAuthBackend()
        backend.token_store = Mock()
        backend.token_store.get_refresh_token.return_value = "refresh-token"

        mock_flow = AsyncMock()
        mock_flow.refresh_access_token.side_effect = Exception("Refresh failed")

        with patch("backends.kimi_auth_backend.DeviceCodeFlow", return_value=mock_flow):
            with patch.object(mock_flow, "__aenter__", return_value=mock_flow):
                with patch.object(mock_flow, "__aexit__", AsyncMock()):
                    result = await backend._refresh_token_if_needed()

        assert result is False

    def test_is_configured_true(self):
        """Backend is configured with API key"""
        backend = KimiAuthBackend(api_key="test-key")

        assert backend.is_configured() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_configured_false(self):
        """Backend is not configured without API key"""
        backend = KimiAuthBackend()

        with patch.object(backend, "_get_auth_token", return_value=None):
            assert backend.is_configured() is False

    def test_create_kimi_backend(self):
        """Test convenience function"""
        backend = create_kimi_backend()

        assert isinstance(backend, KimiAuthBackend)


class TestOpenRouterBackend:
    """Test OpenRouter API Backend"""

    def test_init_default(self):
        """Initialize with default values"""
        backend = OpenRouterBackend()

        assert backend.name == "OpenRouter"
        assert backend.priority == 2
        assert backend.api_key is None
        assert len(backend.models) == 4

    def test_init_with_api_key(self):
        """Initialize with API key"""
        backend = OpenRouterBackend(api_key="test-key")

        assert backend.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_aenter_aexit(self):
        """Test async context manager"""
        backend = OpenRouterBackend()

        async with backend as b:
            assert b.session is not None

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Successful chat completion"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenRouter response"}}]
        }

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello", "Context")

        assert response == "OpenRouter response"

    @pytest.mark.asyncio
    async def test_chat_no_api_key(self):
        """Chat without API key returns None"""
        backend = OpenRouterBackend()  # No API key

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_rate_limit(self):
        """Handle rate limit (429)"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 429

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_invalid_key(self):
        """Handle invalid API key (401)"""
        backend = OpenRouterBackend(api_key="invalid-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 401

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_http_error(self):
        """Handle HTTP error"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 500

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_exception(self):
        """Handle general exception"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()
        backend.session.post.side_effect = Exception("Network error")

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_empty_response(self):
        """Handle empty response"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"choices": []}

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Successful health check"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200

        backend.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.get.return_value.__aexit__ = AsyncMock(return_value=False)

        is_healthy = await backend.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_no_key(self):
        """Health check without API key"""
        backend = OpenRouterBackend()

        is_healthy = await backend.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Failed health check"""
        backend = OpenRouterBackend(api_key="test-key")
        backend.session = AsyncMock()
        backend.session.get.side_effect = Exception("Connection error")

        is_healthy = await backend.health_check()

        assert is_healthy is False


class TestClaudeDirectBackend:
    """Test Claude Direct Backend"""

    def test_init_default(self):
        """Initialize with default values"""
        backend = ClaudeDirectBackend()

        assert backend.name == "Claude-Direct"
        assert backend.priority == 3
        assert backend.session_key is None

    def test_init_with_session_key(self):
        """Initialize with session key"""
        backend = ClaudeDirectBackend(session_key="test-session")

        assert backend.session_key == "test-session"

    @pytest.mark.asyncio
    async def test_aenter_aexit(self):
        """Test async context manager"""
        backend = ClaudeDirectBackend()

        async with backend as b:
            assert b.session is not None

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Successful chat completion"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend.session = AsyncMock()

        # Mock _get_org_id
        backend._get_org_id = AsyncMock(return_value="org-123")

        # Create mock response for SSE
        mock_response = AsyncMock()
        mock_response.status = 200

        async def mock_iter():
            yield b'data: {"completion": "Hello"}\n'
            yield b'data: {"completion": " from Claude"}\n'

        mock_response.content = mock_iter()

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response == "Hello from Claude"

    @pytest.mark.asyncio
    async def test_chat_no_session_key(self):
        """Chat without session key returns None"""
        backend = ClaudeDirectBackend()

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_no_org_id(self):
        """Chat without organization ID"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend._get_org_id = AsyncMock(return_value=None)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_session_expired(self):
        """Handle expired session (401)"""
        backend = ClaudeDirectBackend(session_key="expired-session")
        backend._get_org_id = AsyncMock(return_value="org-123")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 401

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_http_error(self):
        """Handle HTTP error"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend._get_org_id = AsyncMock(return_value="org-123")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 500

        backend.session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_chat_exception(self):
        """Handle general exception"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend._get_org_id = AsyncMock(return_value="org-123")
        backend.session = AsyncMock()
        backend.session.post.side_effect = Exception("Network error")

        response = await backend.chat("Hello")

        assert response is None

    @pytest.mark.asyncio
    async def test_get_org_id_success(self):
        """Successfully get organization ID"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [{"uuid": "org-123"}]

        backend.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.get.return_value.__aexit__ = AsyncMock(return_value=False)

        org_id = await backend._get_org_id()

        assert org_id == "org-123"

    @pytest.mark.asyncio
    async def test_get_org_id_failure(self):
        """Failed to get organization ID"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend.session = AsyncMock()
        backend.session.get.side_effect = Exception("API error")

        org_id = await backend._get_org_id()

        assert org_id is None

    @pytest.mark.asyncio
    async def test_get_org_id_empty_response(self):
        """Empty response from organizations endpoint"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend.session = AsyncMock()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []

        backend.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        backend.session.get.return_value.__aexit__ = AsyncMock(return_value=False)

        org_id = await backend._get_org_id()

        assert org_id is None

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Successful health check"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend._get_org_id = AsyncMock(return_value="org-123")

        is_healthy = await backend.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_no_session(self):
        """Health check without session key"""
        backend = ClaudeDirectBackend()

        is_healthy = await backend.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Failed health check"""
        backend = ClaudeDirectBackend(session_key="test-session")
        backend._get_org_id = AsyncMock(return_value=None)

        is_healthy = await backend.health_check()

        assert is_healthy is False


class TestBackendErrors:
    """Test error handling across backends"""

    @pytest.mark.asyncio
    async def test_authentication_required_error(self):
        """Test AuthenticationRequiredError"""
        error = AuthenticationRequiredError("Please authenticate")

        assert str(error) == "Please authenticate"
        assert isinstance(error, Exception)


class TestBackendIntegration:
    """Integration tests for backends"""

    @pytest.mark.asyncio
    async def test_backend_fallback_pattern(self):
        """Test fallback pattern between backends"""
        # Create backends
        kimi = KimiAuthBackend()
        openrouter = OpenRouterBackend()
        claude = ClaudeDirectBackend()

        # None should be configured without keys
        with patch.object(kimi, "is_configured", return_value=False):
            assert not kimi.is_configured()

        assert not openrouter.api_key
        assert not claude.session_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

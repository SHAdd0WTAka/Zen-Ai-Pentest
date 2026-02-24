#!/usr/bin/env python3
"""
Comprehensive tests for Kimi Auth Backend
Target: 80%+ coverage
"""

import json
import os
import sys
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.kimi_auth_backend import AuthenticationRequiredError, KimiAuthBackend


@pytest.fixture
def backend():
    """Create a backend instance for testing"""
    return KimiAuthBackend()


@pytest.fixture
def backend_with_key():
    """Create a backend instance with API key"""
    return KimiAuthBackend(api_key="test-api-key")


class TestKimiAuthBackendInitialization:
    """Test backend initialization and configuration"""

    def test_backend_initialization(self, backend):
        """Test basic backend initialization"""
        assert backend.name == "Kimi"
        assert backend.priority == 2
        assert backend.session is None
        assert backend._api_key is None

    def test_backend_with_api_key(self, backend_with_key):
        """Test backend initialization with API key"""
        assert backend_with_key._api_key == "test-api-key"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, backend):
        """Test async context manager entry and exit"""
        async with backend as b:
            assert b.session is not None
        # After exit, session should be closed
        assert backend.session is None or backend.session.closed

    @pytest.mark.asyncio
    async def test_async_exit_with_exception(self, backend):
        """Test async exit when session is None"""
        backend.session = None
        await backend.__aexit__(None, None, None)
        assert backend.session is None


class TestKimiAuthToken:
    """Test authentication token retrieval"""

    def test_get_auth_token_from_env(self, backend):
        """Test getting token from environment variable"""
        with patch.dict(os.environ, {"KIMI_API_KEY": "env-api-key"}):
            token = backend._get_auth_token()
            assert token == "env-api-key"

    def test_get_auth_token_from_constructor(self):
        """Test getting token from constructor"""
        backend = KimiAuthBackend(api_key="constructor-key")
        token = backend._get_auth_token()
        assert token == "constructor-key"

    def test_get_auth_token_priority_env_over_constructor(self):
        """Test env variable takes priority over constructor"""
        backend = KimiAuthBackend(api_key="constructor-key")
        with patch.dict(os.environ, {"KIMI_API_KEY": "env-api-key"}):
            token = backend._get_auth_token()
            assert token == "env-api-key"

    @patch("backends.kimi_auth_backend.get_stored_token")
    def test_get_auth_token_from_stored(self, mock_get_stored, backend):
        """Test getting token from stored credentials"""
        mock_get_stored.return_value = "stored-token"
        token = backend._get_auth_token()
        assert token == "stored-token"

    @patch("backends.kimi_auth_backend.get_stored_token")
    def test_get_auth_token_no_token(self, mock_get_stored, backend):
        """Test when no token is available"""
        mock_get_stored.return_value = None
        token = backend._get_auth_token()
        assert token is None


class TestKimiChat:
    """Test chat functionality"""

    def _create_mock_response(self, status=200, json_data=None, raise_for_status=None):
        """Helper to create a mock response that works as async context manager"""
        mock_response = AsyncMock()
        mock_response.status = status
        if json_data:
            mock_response.json = AsyncMock(return_value=json_data)
        if raise_for_status:
            mock_response.raise_for_status = raise_for_status
        else:
            mock_response.raise_for_status = Mock()
        return mock_response

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_success(self, mock_get_stored, backend):
        """Test successful chat completion"""
        mock_get_stored.return_value = "test-token"

        mock_response = self._create_mock_response(
            status=200, json_data={"choices": [{"message": {"content": "Hello, I am Kimi!"}}]}
        )

        # Create a mock post that works as async context manager
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        result = await backend.chat("Hello", model="kimi-k2-07132k-preview")

        assert result == "Hello, I am Kimi!"
        mock_post.assert_called_once()

        # Verify the call was made with correct headers
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_no_token(self, mock_get_stored, backend):
        """Test chat when no authentication token is available"""
        mock_get_stored.return_value = None
        backend._api_key = None

        backend.session = AsyncMock()

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await backend.chat("Hello")

        assert "Not authenticated" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_api_error(self, mock_get_stored, backend):
        """Test chat when API returns an error"""
        import aiohttp

        mock_get_stored.return_value = "test-token"

        mock_session = AsyncMock()
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = mock_post

        backend.session = mock_session

        with pytest.raises(aiohttp.ClientError):
            await backend.chat("Hello")

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_http_error(self, mock_get_stored, backend):
        """Test chat when HTTP error occurs"""
        import aiohttp

        mock_get_stored.return_value = "test-token"

        def mock_raise_for_status():
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500, message="Internal Server Error"
            )

        mock_response = AsyncMock()
        mock_response.raise_for_status = mock_raise_for_status

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with pytest.raises(aiohttp.ClientResponseError):
            await backend.chat("Hello")


class TestKimiTokenRefresh:
    """Test token refresh functionality"""

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    @patch.object(KimiAuthBackend, "_refresh_token_if_needed")
    async def test_chat_token_refresh_success(self, mock_refresh, mock_get_stored, backend):
        """Test successful token refresh on 401"""
        mock_get_stored.return_value = "expired-token"
        mock_refresh.return_value = True

        # First call returns 401, second returns success
        response_401 = AsyncMock()
        response_401.status = 401

        response_success = AsyncMock()
        response_success.status = 200
        response_success.json = AsyncMock(return_value={"choices": [{"message": {"content": "Refreshed response"}}]})
        response_success.raise_for_status = Mock()

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=[response_401, response_success])
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        result = await backend.chat("Hello")

        assert result == "Refreshed response"
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    @patch.object(KimiAuthBackend, "_refresh_token_if_needed")
    async def test_chat_token_refresh_failure(self, mock_refresh, mock_get_stored, backend):
        """Test failed token refresh on 401"""
        mock_get_stored.return_value = "expired-token"
        mock_refresh.return_value = False

        mock_response = AsyncMock()
        mock_response.status = 401

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await backend.chat("Hello")

        assert "Token expired" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.DeviceCodeFlow")
    async def test_refresh_token_success(self, mock_flow_class, backend):
        """Test successful token refresh"""
        # Setup token_store mock
        backend.token_store = MagicMock()
        backend.token_store.get_refresh_token.return_value = "refresh-token"

        mock_flow = AsyncMock()
        mock_flow.refresh_access_token = AsyncMock(
            return_value={"access_token": "new-access-token", "refresh_token": "new-refresh-token", "expires_in": 3600}
        )
        mock_flow.__aenter__ = AsyncMock(return_value=mock_flow)
        mock_flow.__aexit__ = AsyncMock(return_value=None)

        mock_flow_class.return_value = mock_flow

        result = await backend._refresh_token_if_needed()

        assert result is True
        backend.token_store.save_credentials.assert_called_once_with(
            access_token="new-access-token", refresh_token="new-refresh-token", expires_in=3600, provider="kimi"
        )

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self, backend):
        """Test refresh when no refresh token available"""
        backend.token_store = MagicMock()
        backend.token_store.get_refresh_token.return_value = None

        result = await backend._refresh_token_if_needed()

        assert result is False

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.DeviceCodeFlow")
    async def test_refresh_token_exception(self, mock_flow_class, backend):
        """Test refresh when exception occurs"""
        backend.token_store = MagicMock()
        backend.token_store.get_refresh_token.return_value = "refresh-token"

        mock_flow = AsyncMock()
        mock_flow.refresh_access_token.side_effect = Exception("Refresh failed")
        mock_flow.__aenter__ = AsyncMock(return_value=mock_flow)
        mock_flow.__aexit__ = AsyncMock(return_value=None)

        mock_flow_class.return_value = mock_flow

        result = await backend._refresh_token_if_needed()

        assert result is False


class TestKimiChatStream:
    """Test streaming chat functionality"""

    @staticmethod
    def _async_iterator(data):
        """Helper to create async iterator from list"""

        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_stream_success(self, mock_get_stored, backend):
        """Test successful streaming response"""
        mock_get_stored.return_value = "test-token"

        # Create mock stream data
        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
            b'data: {"choices": [{"delta": {"content": " World"}}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        chunks = []
        async for chunk in backend.chat_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Hello", " World"]

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_stream_no_token(self, mock_get_stored, backend):
        """Test stream when no authentication token"""
        mock_get_stored.return_value = None
        backend._api_key = None

        backend.session = AsyncMock()

        with pytest.raises(AuthenticationRequiredError):
            async for _ in backend.chat_stream("Hello"):
                pass

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_stream_invalid_json(self, mock_get_stored, backend):
        """Test stream with invalid JSON in response"""
        mock_get_stored.return_value = "test-token"

        stream_data = [
            b"data: invalid json\n",
            b'data: {"choices": [{"delta": {"content": "Valid"}}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        chunks = []
        async for chunk in backend.chat_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Valid"]

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_stream_missing_content(self, mock_get_stored, backend):
        """Test stream with missing content field"""
        mock_get_stored.return_value = "test-token"

        stream_data = [
            b'data: {"choices": [{"delta": {}}]}\n',
            b'data: {"choices": [{"delta": {"content": "Text"}}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        chunks = []
        async for chunk in backend.chat_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Text"]

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    @patch.object(KimiAuthBackend, "_refresh_token_if_needed")
    async def test_chat_stream_token_refresh(self, mock_refresh, mock_get_stored, backend):
        """Test stream token refresh on 401"""
        mock_get_stored.return_value = "expired-token"
        mock_refresh.return_value = True

        response_401 = AsyncMock()
        response_401.status = 401

        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Refreshed"}}]}\n',
            b"data: [DONE]\n",
        ]

        response_success = AsyncMock()
        response_success.status = 200
        response_success.raise_for_status = Mock()
        response_success.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=[response_401, response_success])
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        chunks = []
        async for chunk in backend.chat_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Refreshed"]


class TestKimiIsConfigured:
    """Test is_configured method"""

    def test_is_configured_with_api_key(self):
        """Test is_configured when API key is set"""
        backend = KimiAuthBackend(api_key="test-key")
        assert backend.is_configured() is True

    @patch.dict(os.environ, {"KIMI_API_KEY": "env-key"})
    def test_is_configured_with_env_var(self):
        """Test is_configured when env var is set"""
        backend = KimiAuthBackend()
        assert backend.is_configured() is True

    @patch("backends.kimi_auth_backend.get_stored_token")
    def test_is_configured_with_stored_token(self, mock_get_stored):
        """Test is_configured when stored token exists"""
        mock_get_stored.return_value = "stored-token"
        backend = KimiAuthBackend()
        assert backend.is_configured() is True

    def test_is_configured_not_configured(self):
        """Test is_configured when no auth available"""
        backend = KimiAuthBackend()
        assert backend.is_configured() is False


class TestKimiEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_with_custom_model(self, mock_get_stored, backend):
        """Test chat with custom model parameter"""
        mock_get_stored.return_value = "test-token"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response"}}]})
        mock_response.raise_for_status = Mock()

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        result = await backend.chat("Hello", model="custom-model-v1")

        assert result == "Response"

        # Verify the model was passed correctly
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "custom-model-v1"

    @pytest.mark.asyncio
    @patch("backends.kimi_auth_backend.get_stored_token")
    async def test_chat_stream_client_error(self, mock_get_stored, backend):
        """Test stream with client error"""
        import aiohttp

        mock_get_stored.return_value = "test-token"

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection error"))
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with pytest.raises(aiohttp.ClientError):
            async for _ in backend.chat_stream("Hello"):
                pass


class TestCreateKimiBackend:
    """Test convenience function"""

    def test_create_kimi_backend(self):
        """Test create_kimi_backend convenience function"""
        from backends.kimi_auth_backend import create_kimi_backend

        backend = create_kimi_backend()
        assert isinstance(backend, KimiAuthBackend)
        assert backend._api_key is None

#!/usr/bin/env python3
"""
Comprehensive tests for ChatGPT Direct Backend
Target: 80%+ coverage
"""

import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.chatgpt_direct import ChatGPTDirectBackend


@pytest.fixture
def backend():
    """Create a backend instance for testing"""
    return ChatGPTDirectBackend()


@pytest.fixture
def backend_with_token():
    """Create a backend instance with access token"""
    return ChatGPTDirectBackend(access_token="test-access-token")


class TestChatGPTBackendInitialization:
    """Test backend initialization"""

    def test_backend_initialization(self, backend):
        """Test basic backend initialization"""
        assert backend.name == "ChatGPT-Direct"
        assert backend.priority == 3
        assert backend.access_token is None
        assert backend.refresh_token is None
        assert backend.conversation_id is None
        assert backend.session is None

    def test_backend_with_access_token(self, backend_with_token):
        """Test backend initialization with access token"""
        assert backend_with_token.access_token == "test-access-token"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, backend):
        """Test async context manager"""
        async with backend as b:
            assert b.session is not None

    @pytest.mark.asyncio
    async def test_async_exit(self, backend_with_token):
        """Test async exit closes session"""
        async with backend_with_token as b:
            pass


class TestChatGPTChat:
    """Test chat functionality"""

    @pytest.mark.asyncio
    async def test_chat_no_access_token(self, backend, caplog):
        """Test chat when no access token provided"""
        import logging
        with caplog.at_level(logging.WARNING):
            result = await backend.chat("Hello")
        
        assert result is None
        assert "No access token provided" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_success(self, backend_with_token):
        """Test successful chat completion"""
        # Create stream-like response
        response_data = [
            'data: {"message": {"content": {"parts": ["Hello"]}}, "conversation_id": "conv-123"}\n',
            'data: {"message": {"content": {"parts": ["Hello there"]}}, "conversation_id": "conv-123"}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.chat("Hello")
        
        assert result == "Hello there"
        assert backend_with_token.conversation_id == "conv-123"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_context(self, backend_with_token):
        """Test chat with context parameter"""
        response_data = [
            'data: {"message": {"content": {"parts": ["Response"]}}, "conversation_id": "conv-456"}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        backend_with_token.conversation_id = "existing-conv"
        
        result = await backend_with_token.chat("Hello", context="Some context")
        
        assert result == "Response"

    @pytest.mark.asyncio
    async def test_chat_401_unauthorized(self, backend_with_token, caplog):
        """Test chat with 401 unauthorized"""
        import logging
        
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        with caplog.at_level(logging.ERROR):
            result = await backend_with_token.chat("Hello")
        
        assert result is None
        assert "Token expired" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_429_rate_limited(self, backend_with_token, caplog):
        """Test chat with 429 rate limit"""
        import logging
        
        mock_response = AsyncMock()
        mock_response.status = 429
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        with caplog.at_level(logging.WARNING):
            result = await backend_with_token.chat("Hello")
        
        assert result is None
        assert "Rate limited" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_500_server_error(self, backend_with_token, caplog):
        """Test chat with 500 server error"""
        import logging
        
        mock_response = AsyncMock()
        mock_response.status = 500
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        with caplog.at_level(logging.ERROR):
            result = await backend_with_token.chat("Hello")
        
        assert result is None
        assert "HTTP Error: 500" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_exception(self, backend_with_token, caplog):
        """Test chat when exception occurs"""
        import logging
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        with caplog.at_level(logging.ERROR):
            result = await backend_with_token.chat("Hello")
        
        assert result is None
        assert "Network error" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_invalid_json_in_stream(self, backend_with_token):
        """Test chat with invalid JSON in stream"""
        response_data = [
            'data: invalid json here\n',
            'data: {"message": {"content": {"parts": ["Valid response"]}}, "conversation_id": "conv-789"}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.chat("Hello")
        
        assert result == "Valid response"

    @pytest.mark.asyncio
    async def test_chat_no_conversation_id(self, backend_with_token):
        """Test chat response without conversation_id"""
        response_data = [
            'data: {"message": {"content": {"parts": ["Response without conv"]}}}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        backend_with_token.conversation_id = "existing"
        
        result = await backend_with_token.chat("Hello")
        
        assert result == "Response without conv"
        # Conversation ID should remain unchanged
        assert backend_with_token.conversation_id == "existing"

    @pytest.mark.asyncio
    async def test_chat_no_message_in_data(self, backend_with_token):
        """Test chat with data missing message field"""
        response_data = [
            'data: {"other_field": "value"}\n',
            'data: {"message": {"content": {"parts": ["Final response"]}}, "conversation_id": "conv-999"}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.chat("Hello")
        
        assert result == "Final response"


class TestChatGPTHeaders:
    """Test request headers and payload"""

    @pytest.mark.asyncio
    async def test_correct_headers_sent(self, backend_with_token):
        """Test that correct headers are sent with request"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='data: {"message": {"content": {"parts": ["Hi"]}}}\n')
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        await backend_with_token.chat("Hello")
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        
        assert headers["Authorization"] == "Bearer test-access-token"
        assert headers["Content-Type"] == "application/json"
        assert "Mozilla/5.0" in headers["User-Agent"]

    @pytest.mark.asyncio
    async def test_correct_payload_structure(self, backend_with_token):
        """Test that correct payload is sent"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='data: {"message": {"content": {"parts": ["Hi"]}}}\n')
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        await backend_with_token.chat("Test prompt")
        
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        
        assert payload["action"] == "next"
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["author"]["role"] == "user"
        assert payload["messages"][0]["content"]["parts"] == ["Test prompt"]
        assert payload["model"] == "text-davinci-002-render-sha"
        assert payload["timezone_offset_min"] == -120

    @pytest.mark.asyncio
    async def test_message_id_generation(self, backend_with_token):
        """Test that message IDs are generated"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='data: {"message": {"content": {"parts": ["Hi"]}}}\n')
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        await backend_with_token.chat("Hello")
        
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        
        # Message ID should be a string of digits
        msg_id = payload["messages"][0]["id"]
        assert msg_id.isdigit()
        assert len(msg_id) == 10
        
        # Parent message ID should also be digits
        parent_id = payload["parent_message_id"]
        assert parent_id.isdigit()
        assert len(parent_id) == 10


class TestChatGPTHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_no_token(self, backend):
        """Test health check without token"""
        result = await backend.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend_with_token):
        """Test successful health check"""
        mock_response = AsyncMock()
        mock_response.status = 200
        
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.health_check()
        
        assert result is True
        mock_get.assert_called_once_with(
            "https://chat.openai.com/backend-api/models",
            headers={"Authorization": "Bearer test-access-token"}
        )

    @pytest.mark.asyncio
    async def test_health_check_failure(self, backend_with_token):
        """Test failed health check"""
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.health_check()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, backend_with_token):
        """Test health check with exception"""
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = mock_get
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.health_check()
        
        assert result is False


class TestChatGPTEndpoint:
    """Test correct endpoint is called"""

    @pytest.mark.asyncio
    async def test_correct_endpoint(self, backend_with_token):
        """Test that correct endpoint is called"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='data: {"message": {"content": {"parts": ["Hi"]}}}\n')
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        await backend_with_token.chat("Hello")
        
        call_args = mock_post.call_args
        url = call_args[0][0]
        
        assert url == "https://chat.openai.com/backend-api/conversation"


class TestChatGPTTimeout:
    """Test timeout configuration"""

    @pytest.mark.asyncio
    async def test_timeout_set(self, backend_with_token):
        """Test that timeout is configured"""
        import aiohttp
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='data: {"message": {"content": {"parts": ["Hi"]}}}\n')
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        await backend_with_token.chat("Hello")
        
        call_args = mock_post.call_args
        timeout = call_args[1]["timeout"]
        
        assert isinstance(timeout, aiohttp.ClientTimeout)
        assert timeout.total == 60


class TestChatGPTEmptyResponse:
    """Test handling of empty responses"""

    @pytest.mark.asyncio
    async def test_empty_response(self, backend_with_token):
        """Test handling of empty response"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.chat("Hello")
        
        assert result == ""

    @pytest.mark.asyncio
    async def test_response_without_data_prefix(self, backend_with_token):
        """Test response lines without data: prefix"""
        response_data = [
            'event: message\n',
            'data: {"message": {"content": {"parts": ["Response"]}}, "conversation_id": "conv-001"}\n',
        ]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="\n".join(response_data))
        
        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.post = mock_post
        
        backend_with_token.session = mock_session
        
        result = await backend_with_token.chat("Hello")
        
        assert result == "Response"

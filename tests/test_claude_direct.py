#!/usr/bin/env python3
"""
Comprehensive tests for Claude Direct Backend
Target: 80%+ coverage
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.claude_direct import ClaudeDirectBackend


@pytest.fixture
def backend():
    """Create a backend instance for testing"""
    return ClaudeDirectBackend()


@pytest.fixture
def backend_with_key():
    """Create a backend instance with session key"""
    return ClaudeDirectBackend(session_key="test-session-key")


class TestClaudeBackendInitialization:
    """Test backend initialization"""

    def test_backend_initialization(self, backend):
        """Test basic backend initialization"""
        assert backend.name == "Claude-Direct"
        assert backend.priority == 3
        assert backend.session_key is None
        assert backend.session is None

    def test_backend_with_session_key(self, backend_with_key):
        """Test backend initialization with session key"""
        assert backend_with_key.session_key == "test-session-key"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, backend):
        """Test async context manager"""
        async with backend as b:
            assert b.session is not None

    @pytest.mark.asyncio
    async def test_async_exit(self, backend_with_key):
        """Test async exit closes session"""
        async with backend_with_key as b:
            pass


class TestClaudeChat:
    """Test chat functionality"""

    @staticmethod
    def _async_iterator(data):
        """Helper to create async iterator from list"""

        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    async def test_chat_no_session_key(self, backend, caplog):
        """Test chat when no session key provided"""
        import logging

        with caplog.at_level(logging.WARNING):
            result = await backend.chat("Hello")

        assert result is None
        assert "No session key provided" in caplog.text

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_success(self, mock_get_org_id, backend_with_key):
        """Test successful chat completion"""
        mock_get_org_id.return_value = "org-123-uuid"

        # Create SSE stream data
        stream_data = [
            b'data: {"completion": "Hello"}\n',
            b'data: {"completion": " there"}\n',
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == "Hello there"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_with_context(self, mock_get_org_id, backend_with_key):
        """Test chat with context parameter"""
        mock_get_org_id.return_value = "org-456"

        stream_data = [
            b'data: {"completion": "Response with context"}\n',
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat(
            "Hello", context="Previous context"
        )

        assert result == "Response with context"

    @pytest.mark.asyncio
    async def test_chat_no_org_id(self, backend_with_key, caplog):
        """Test chat when organization ID cannot be retrieved"""
        import logging

        with patch.object(backend_with_key, "_get_org_id", return_value=None):
            with caplog.at_level(logging.ERROR):
                result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Could not get organization ID" in caplog.text

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_401_unauthorized(
        self, mock_get_org_id, backend_with_key, caplog
    ):
        """Test chat with 401 unauthorized"""
        import logging

        mock_get_org_id.return_value = "org-123"

        mock_response = AsyncMock()
        mock_response.status = 401

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Session expired" in caplog.text

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_500_server_error(
        self, mock_get_org_id, backend_with_key, caplog
    ):
        """Test chat with 500 server error"""
        import logging

        mock_get_org_id.return_value = "org-123"

        mock_response = AsyncMock()
        mock_response.status = 500

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "HTTP Error: 500" in caplog.text

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_exception(
        self, mock_get_org_id, backend_with_key, caplog
    ):
        """Test chat when exception occurs"""
        import logging

        mock_get_org_id.return_value = "org-123"

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Network error" in caplog.text

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_invalid_json_in_stream(
        self, mock_get_org_id, backend_with_key
    ):
        """Test chat with invalid JSON in SSE stream"""
        mock_get_org_id.return_value = "org-123"

        stream_data = [
            b"data: invalid json\n",
            b'data: {"completion": "Valid response"}\n',
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == "Valid response"

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_empty_sse_data(
        self, mock_get_org_id, backend_with_key
    ):
        """Test chat with empty SSE data lines"""
        mock_get_org_id.return_value = "org-123"

        stream_data = [
            b"\n",
            b'data: {"completion": "Response"}\n',
            b"\n",
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == "Response"

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_chat_data_without_completion(
        self, mock_get_org_id, backend_with_key
    ):
        """Test chat with data missing completion field"""
        mock_get_org_id.return_value = "org-123"

        stream_data = [
            b'data: {"other_field": "value"}\n',
            b'data: {"completion": "Final response"}\n',
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == "Final response"


class TestClaudeGetOrgId:
    """Test organization ID retrieval"""

    @pytest.mark.asyncio
    async def test_get_org_id_success(self, backend_with_key):
        """Test successful organization ID retrieval"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[{"uuid": "org-uuid-123", "name": "Test Org"}]
        )

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key._get_org_id()

        assert result == "org-uuid-123"

    @pytest.mark.asyncio
    async def test_get_org_id_empty_list(self, backend_with_key):
        """Test get_org_id with empty organizations list"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key._get_org_id()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_org_id_no_uuid(self, backend_with_key):
        """Test get_org_id when org has no uuid field"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[{"name": "Test Org"}]
        )  # No uuid field

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key._get_org_id()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_org_id_401_error(self, backend_with_key):
        """Test get_org_id with 401 error"""
        mock_response = AsyncMock()
        mock_response.status = 401

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key._get_org_id()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_org_id_exception(self, backend_with_key):
        """Test get_org_id with exception"""
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key._get_org_id()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_org_id_correct_headers(self, backend_with_key):
        """Test correct headers are sent for org ID request"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"uuid": "org-123"}])

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        await backend_with_key._get_org_id()

        call_args = mock_get.call_args
        headers = call_args[1]["headers"]

        assert headers["Cookie"] == "sessionKey=test-session-key"
        assert "Mozilla/5.0" in headers["User-Agent"]


class TestClaudeHeaders:
    """Test request headers and payload"""

    @staticmethod
    def _async_iterator(data):
        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_correct_headers_sent(
        self, mock_get_org_id, backend_with_key
    ):
        """Test that correct headers are sent with request"""
        mock_get_org_id.return_value = "org-123"

        stream_data = [b'data: {"completion": "Hi"}\n']

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        assert headers["Cookie"] == "sessionKey=test-session-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "text/event-stream"
        assert "Mozilla/5.0" in headers["User-Agent"]

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_correct_payload_structure(
        self, mock_get_org_id, backend_with_key
    ):
        """Test that correct payload is sent"""
        mock_get_org_id.return_value = "org-123"

        stream_data = [b'data: {"completion": "Hi"}\n']

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Test prompt")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        assert payload["prompt"] == "Test prompt"
        assert payload["model"] == "claude-3-5-sonnet-20241022"
        assert payload["timezone"] == "Europe/Berlin"
        assert payload["attachments"] == []

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_correct_endpoint(self, mock_get_org_id, backend_with_key):
        """Test that correct endpoint is called"""
        mock_get_org_id.return_value = "org-456"

        stream_data = [b'data: {"completion": "Hi"}\n']

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        call_args = mock_post.call_args
        url = call_args[0][0]

        assert (
            url
            == "https://claude.ai/api/organizations/org-456/chat_conversations"
        )


class TestClaudeHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_no_session_key(self, backend):
        """Test health check without session key"""
        result = await backend.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend_with_key):
        """Test successful health check"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"uuid": "org-123"}])

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_no_org(self, backend_with_key):
        """Test health check when no org available"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key.health_check()

        assert result is False


class TestClaudeTimeout:
    """Test timeout configuration"""

    @staticmethod
    def _async_iterator(data):
        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_timeout_set(self, mock_get_org_id, backend_with_key):
        """Test that timeout is configured"""
        import aiohttp

        mock_get_org_id.return_value = "org-123"

        stream_data = [b'data: {"completion": "Hi"}\n']

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = self._async_iterator(stream_data)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        call_args = mock_post.call_args
        timeout = call_args[1]["timeout"]

        assert isinstance(timeout, aiohttp.ClientTimeout)
        assert timeout.total == 120


class TestClaudeEmptyResponse:
    """Test handling of empty responses"""

    @pytest.mark.asyncio
    @patch.object(ClaudeDirectBackend, "_get_org_id")
    async def test_empty_stream(self, mock_get_org_id, backend_with_key):
        """Test handling of empty stream"""
        mock_get_org_id.return_value = "org-123"

        stream_data = []

        async def empty_gen():
            return
            yield  # Make it a generator

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = empty_gen()

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == ""

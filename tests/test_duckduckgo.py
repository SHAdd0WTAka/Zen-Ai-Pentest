#!/usr/bin/env python3
"""
Comprehensive tests for DuckDuckGo Backend
Target: 80%+ coverage
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.duckduckgo import DuckDuckGoBackend


@pytest.fixture
def backend():
    """Create a backend instance for testing"""
    return DuckDuckGoBackend()


class TestDuckDuckGoInitialization:
    """Test backend initialization"""

    def test_backend_initialization(self, backend):
        """Test basic backend initialization"""
        assert backend.name == "DuckDuckGo"
        assert backend.priority == 1
        assert backend.vqd_token is None
        assert backend.session is None
        assert backend.current_model == 0
        assert len(backend.models) == 3

    def test_model_list(self, backend):
        """Test that models are properly configured"""
        expected_models = [
            "gpt-4o-mini",
            "claude-3-haiku",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        ]
        assert backend.models == expected_models

    @pytest.mark.asyncio
    async def test_async_context_manager(self, backend):
        """Test async context manager"""
        async with backend as b:
            assert b.session is not None

    @pytest.mark.asyncio
    async def test_async_exit(self, backend):
        """Test async exit closes session"""
        async with backend as b:
            pass


class TestDuckDuckGoGetVQDToken:
    """Test VQD token acquisition"""

    @pytest.mark.asyncio
    async def test_get_vqd_token_success(self, backend, caplog):
        """Test successful VQD token acquisition"""
        import logging

        html_response = '<html><body>vqd="abc123xyz"</body></html>'

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_response)

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        with caplog.at_level(logging.INFO):
            await backend._get_vqd_token()

        assert backend.vqd_token == "abc123xyz"
        assert "VQD Token acquired: abc123xyz" in caplog.text

    @pytest.mark.asyncio
    async def test_get_vqd_token_already_exists(self, backend):
        """Test VQD token acquisition when token already exists"""
        backend.vqd_token = "existing-token"

        mock_session = AsyncMock()
        mock_session.get = AsyncMock()

        backend.session = mock_session

        await backend._get_vqd_token()

        # Should not make HTTP request if token exists
        mock_session.get.assert_not_called()
        assert backend.vqd_token == "existing-token"

    @pytest.mark.asyncio
    async def test_get_vqd_token_not_in_response(self, backend):
        """Test VQD token acquisition when token not in response"""
        html_response = "<html><body>No token here</body></html>"

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_response)

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        await backend._get_vqd_token()

        assert backend.vqd_token is None

    @pytest.mark.asyncio
    async def test_get_vqd_token_exception(self, backend, caplog):
        """Test VQD token acquisition with exception"""
        import logging

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        with caplog.at_level(logging.ERROR):
            await backend._get_vqd_token()

        assert backend.vqd_token is None
        assert "Token acquisition failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_vqd_token_correct_headers(self, backend):
        """Test correct headers are sent for VQD token request"""
        html_response = '<html>vqd="test-token"</html>'

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_response)

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        await backend._get_vqd_token()

        call_args = mock_get.call_args
        headers = call_args[1]["headers"]

        assert "Mozilla/5.0" in headers["User-Agent"]
        assert "de-DE" in headers["Accept-Language"]
        assert "text/html" in headers["Accept"]


class TestDuckDuckGoChat:
    """Test chat functionality"""

    @staticmethod
    def _async_iterator(data):
        """Helper to create async iterator from list"""

        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_success(self, mock_get_vqd, backend):
        """Test successful chat completion"""
        backend.vqd_token = "test-vqd-token"

        stream_data = [
            b'data: {"message": "Hello"}\n',
            b'data: {"message": " from DDG"}\n',
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

        backend.session = mock_session

        result = await backend.chat("Hello")

        assert result == "Hello from DDG"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_no_vqd_token(self, mock_get_vqd, backend):
        """Test chat when VQD token cannot be acquired"""
        backend.vqd_token = None
        mock_get_vqd.return_value = None

        result = await backend.chat("Hello")

        assert result is None

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_429_rate_limited(self, mock_get_vqd, backend, caplog):
        """Test chat with 429 rate limit"""
        import logging

        backend.vqd_token = "test-token"
        backend.current_model = 0

        mock_response = AsyncMock()
        mock_response.status = 429

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with caplog.at_level(logging.WARNING):
            result = await backend.chat("Hello")

        assert result is None
        assert "Rate limited, rotating model" in caplog.text
        assert backend.current_model == 1  # Model should be rotated

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_418_teapot(self, mock_get_vqd, backend, caplog):
        """Test chat with 418 teapot error"""
        import logging

        backend.vqd_token = "test-token"

        mock_response = AsyncMock()
        mock_response.status = 418

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with caplog.at_level(logging.WARNING):
            result = await backend.chat("Hello")

        assert result is None
        assert "Teapot error" in caplog.text
        assert backend.vqd_token is None  # Token should be cleared

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_other_error(self, mock_get_vqd, backend, caplog):
        """Test chat with other HTTP error"""
        import logging

        backend.vqd_token = "test-token"

        mock_response = AsyncMock()
        mock_response.status = 503

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend.chat("Hello")

        assert result is None
        assert "HTTP Error: 503" in caplog.text

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_exception(self, mock_get_vqd, backend, caplog):
        """Test chat when exception occurs"""
        import logging

        backend.vqd_token = "test-token"

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend.chat("Hello")

        assert result is None
        assert "Network error" in caplog.text

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_invalid_json_in_stream(self, mock_get_vqd, backend):
        """Test chat with invalid JSON in stream"""
        backend.vqd_token = "test-token"

        stream_data = [
            b"data: invalid json\n",
            b'data: {"message": "Valid response"}\n',
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

        backend.session = mock_session

        result = await backend.chat("Hello")

        assert result == "Valid response"

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_empty_stream(self, mock_get_vqd, backend):
        """Test chat with empty stream"""
        backend.vqd_token = "test-token"

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

        backend.session = mock_session

        result = await backend.chat("Hello")

        assert result == ""


class TestDuckDuckGoHeaders:
    """Test request headers and payload"""

    @staticmethod
    def _async_iterator(data):
        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_correct_headers_sent(self, mock_get_vqd, backend):
        """Test that correct headers are sent with request"""
        backend.vqd_token = "test-vqd-token"

        stream_data = [b'data: {"message": "Hi"}\n']

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

        backend.session = mock_session

        await backend.chat("Hello")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        assert headers["X-Vqd-4"] == "test-vqd-token"
        assert headers["Content-Type"] == "application/json"
        assert "Mozilla/5.0" in headers["User-Agent"]
        assert headers["Referer"] == "https://duckduckgo.com/"

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_correct_payload_structure(self, mock_get_vqd, backend):
        """Test that correct payload is sent"""
        backend.vqd_token = "test-token"

        stream_data = [b'data: {"message": "Hi"}\n']

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

        backend.session = mock_session

        await backend.chat("Test prompt")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        assert payload["model"] == "gpt-4o-mini"  # First model
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "Test prompt"

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_correct_endpoint(self, mock_get_vqd, backend):
        """Test that correct endpoint is called"""
        backend.vqd_token = "test-token"

        stream_data = [b'data: {"message": "Hi"}\n']

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

        backend.session = mock_session

        await backend.chat("Hello")

        call_args = mock_post.call_args
        url = call_args[0][0]

        assert url == "https://duckduckgo.com/duckchat/v1/chat"


class TestDuckDuckGoModelRotation:
    """Test model rotation functionality"""

    @staticmethod
    def _async_iterator(data):
        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_model_selection(self, mock_get_vqd, backend):
        """Test that model is selected based on current_model counter"""
        backend.vqd_token = "test-token"
        backend.current_model = 1

        stream_data = [b'data: {"message": "Hi"}\n']

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

        backend.session = mock_session

        await backend.chat("Hello")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # current_model=1 should select second model (claude-3-haiku)
        assert payload["model"] == "claude-3-haiku"

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_model_rotation_wraps(self, mock_get_vqd, backend):
        """Test that model rotation wraps around"""
        backend.vqd_token = "test-token"
        backend.current_model = 3  # Past end of models list

        stream_data = [b'data: {"message": "Hi"}\n']

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

        backend.session = mock_session

        await backend.chat("Hello")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # 3 % 3 = 0, so should wrap to first model
        assert payload["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_rate_limit_rotates_model(self, mock_get_vqd, backend):
        """Test that rate limit rotates to next model"""
        backend.vqd_token = "test-token"
        backend.current_model = 0

        mock_response = AsyncMock()
        mock_response.status = 429

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend.session = mock_session

        await backend.chat("Hello")

        # After rate limit, model should be rotated
        assert backend.current_model == 1


class TestDuckDuckGoHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend):
        """Test successful health check"""
        html_response = '<html>vqd="health-token"</html>'

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_response)

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        result = await backend.health_check()

        assert result is True
        assert backend.vqd_token == "health-token"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, backend):
        """Test failed health check"""
        html_response = "<html>No token here</html>"

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_response)

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        result = await backend.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, backend):
        """Test health check with exception"""
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend.session = mock_session

        result = await backend.health_check()

        assert result is False


class TestDuckDuckGoEdgeCases:
    """Test edge cases"""

    @staticmethod
    def _async_iterator(data):
        async def gen():
            for item in data:
                yield item

        return gen()

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_with_empty_prompt(self, mock_get_vqd, backend):
        """Test chat with empty prompt"""
        backend.vqd_token = "test-token"

        stream_data = [b'data: {"message": "Response"}\n']

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

        backend.session = mock_session

        result = await backend.chat("")

        assert result == "Response"

        # Verify empty string was sent
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["messages"][0]["content"] == ""

    @pytest.mark.asyncio
    @patch.object(DuckDuckGoBackend, "_get_vqd_token")
    async def test_chat_all_models(self, mock_get_vqd, backend):
        """Test chat with each available model"""
        for i, model in enumerate(backend.models):
            backend.vqd_token = f"token-{i}"
            backend.current_model = i

            stream_data = [
                f'data: {{"message": "Response from {model}"}}\n'.encode()
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

            backend.session = mock_session

            result = await backend.chat("Hello")

            assert result == f"Response from {model}"

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["model"] == model

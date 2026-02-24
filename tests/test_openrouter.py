#!/usr/bin/env python3
"""
Comprehensive tests for OpenRouter Backend
Target: 80%+ coverage
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.openrouter import OpenRouterBackend


@pytest.fixture
def backend():
    """Create a backend instance for testing"""
    return OpenRouterBackend()


@pytest.fixture
def backend_with_key():
    """Create a backend instance with API key"""
    return OpenRouterBackend(api_key="test-api-key")


class TestOpenRouterInitialization:
    """Test backend initialization"""

    def test_backend_initialization(self, backend):
        """Test basic backend initialization"""
        assert backend.name == "OpenRouter"
        assert backend.priority == 2
        assert backend.api_key is None
        assert backend.session is None
        assert len(backend.models) == 4

    def test_backend_with_api_key(self, backend_with_key):
        """Test backend initialization with API key"""
        assert backend_with_key.api_key == "test-api-key"

    def test_model_list(self, backend):
        """Test that models are properly configured"""
        expected_models = [
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemini-flash-1.5:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "nvidia/llama-3.1-nemotron-70b-instruct:free",
        ]
        assert backend.models == expected_models

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


class TestOpenRouterChat:
    """Test chat functionality"""

    @pytest.mark.asyncio
    async def test_chat_no_api_key(self, backend, caplog):
        """Test chat when no API key provided"""
        import logging

        with caplog.at_level(logging.WARNING):
            result = await backend.chat("Hello")

        assert result is None
        assert "No API key provided" in caplog.text

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_success(self, mock_choice, backend_with_key):
        """Test successful chat completion"""
        mock_choice.return_value = "meta-llama/llama-3.2-3b-instruct:free"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hello from OpenRouter!"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result == "Hello from OpenRouter!"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_with_context(self, mock_choice, backend_with_key):
        """Test chat with context parameter"""
        mock_choice.return_value = "google/gemini-flash-1.5:free"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response with context"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello", context="Some context")

        assert result == "Response with context"

    @pytest.mark.asyncio
    async def test_chat_429_rate_limited(self, backend_with_key, caplog):
        """Test chat with 429 rate limit"""
        import logging

        mock_response = AsyncMock()
        mock_response.status = 429

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.WARNING):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Rate limit hit" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_401_invalid_key(self, backend_with_key, caplog):
        """Test chat with 401 invalid API key"""
        import logging

        mock_response = AsyncMock()
        mock_response.status = 401

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Invalid API key" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_500_server_error(self, backend_with_key, caplog):
        """Test chat with 500 server error"""
        import logging

        mock_response = AsyncMock()
        mock_response.status = 500

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "HTTP Error: 500" in caplog.text

    @pytest.mark.asyncio
    async def test_chat_exception(self, backend_with_key, caplog):
        """Test chat when exception occurs"""
        import logging

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.ERROR):
            result = await backend_with_key.chat("Hello")

        assert result is None
        assert "Network error" in caplog.text

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_empty_choices(self, mock_choice, backend_with_key):
        """Test chat with empty choices in response"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": []})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result is None

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_missing_choices(self, mock_choice, backend_with_key):
        """Test chat with missing choices field"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result is None


class TestOpenRouterHeaders:
    """Test request headers and payload"""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_correct_headers_sent(self, mock_choice, backend_with_key):
        """Test that correct headers are sent with request"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hi"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["HTTP-Referer"] == "https://localhost"
        assert headers["X-Title"] == "ZenAI-Pentest"

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_correct_payload_structure(self, mock_choice, backend_with_key):
        """Test that correct payload is sent"""
        mock_choice.return_value = "test-model-v1"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hi"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Test prompt")

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        assert payload["model"] == "test-model-v1"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert "cybersecurity expert" in payload["messages"][0]["content"]
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Test prompt"
        assert payload["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_correct_endpoint(self, backend_with_key):
        """Test that correct endpoint is called"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hi"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        call_args = mock_post.call_args
        url = call_args[0][0]

        assert url == "https://openrouter.ai/api/v1/chat/completions"


class TestOpenRouterHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self, backend):
        """Test health check without API key"""
        result = await backend.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend_with_key):
        """Test successful health check"""
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key.health_check()

        assert result is True
        mock_get.assert_called_once_with(
            "https://openrouter.ai/api/v1/auth/key", headers={"Authorization": "Bearer test-api-key"}
        )

    @pytest.mark.asyncio
    async def test_health_check_failure(self, backend_with_key):
        """Test failed health check"""
        mock_response = AsyncMock()
        mock_response.status = 401

        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, backend_with_key):
        """Test health check with exception"""
        mock_get = MagicMock()
        mock_get.return_value.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = mock_get

        backend_with_key.session = mock_session

        result = await backend_with_key.health_check()

        assert result is False


class TestOpenRouterModelRotation:
    """Test model rotation functionality"""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_model_selection(self, mock_choice, backend_with_key):
        """Test that a model is randomly selected"""
        mock_choice.return_value = "nvidia/llama-3.1-nemotron-70b-instruct:free"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hi"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        await backend_with_key.chat("Hello")

        mock_choice.assert_called_once_with(backend_with_key.models)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "nvidia/llama-3.1-nemotron-70b-instruct:free"

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_all_models_available(self, mock_choice, backend_with_key):
        """Test that all models can be selected"""
        for model in backend_with_key.models:
            mock_choice.return_value = model

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response"}}]})

            mock_post = MagicMock()
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = mock_post

            backend_with_key.session = mock_session

            result = await backend_with_key.chat("Hello")

            assert result == "Response"
            mock_choice.assert_called_with(backend_with_key.models)
            mock_choice.reset_mock()


class TestOpenRouterEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_with_empty_prompt(self, mock_choice, backend_with_key):
        """Test chat with empty prompt"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Response"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("")

        assert result == "Response"

        # Verify empty string was sent
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["messages"][1]["content"] == ""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_missing_message_content(self, mock_choice, backend_with_key):
        """Test response with missing message content"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {}}]})  # No content field

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        # Should handle missing content gracefully
        assert result is None

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_chat_null_content(self, mock_choice, backend_with_key):
        """Test response with null content"""
        mock_choice.return_value = "test-model"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": None}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result = await backend_with_key.chat("Hello")

        assert result is None


class TestOpenRouterLogging:
    """Test logging behavior"""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_model_logging(self, mock_choice, backend_with_key, caplog):
        """Test that selected model is logged"""
        import logging

        mock_choice.return_value = "meta-llama/llama-3.2-3b-instruct:free"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"message": {"content": "Hi"}}]})

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        with caplog.at_level(logging.INFO):
            await backend_with_key.chat("Hello")

        assert "Using meta-llama/llama-3.2-3b-instruct:free" in caplog.text


class TestOpenRouterMultipleCalls:
    """Test multiple sequential calls"""

    @pytest.mark.asyncio
    @patch("backends.openrouter.random.choice")
    async def test_multiple_chats(self, mock_choice, backend_with_key):
        """Test multiple sequential chat calls"""
        mock_choice.side_effect = ["model-1", "model-2", "model-3"]

        responses = [
            {"choices": [{"message": {"content": "Response 1"}}]},
            {"choices": [{"message": {"content": "Response 2"}}]},
            {"choices": [{"message": {"content": "Response 3"}}]},
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=responses)

        mock_post = MagicMock()
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = mock_post

        backend_with_key.session = mock_session

        result1 = await backend_with_key.chat("Hello 1")
        result2 = await backend_with_key.chat("Hello 2")
        result3 = await backend_with_key.chat("Hello 3")

        assert result1 == "Response 1"
        assert result2 == "Response 2"
        assert result3 == "Response 3"
        assert mock_post.call_count == 3

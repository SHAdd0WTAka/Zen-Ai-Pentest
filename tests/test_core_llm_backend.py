"""
Tests for core/llm_backend.py
Target: 100% Coverage
"""

import logging

import pytest


class TestLLMBackendInit:
    """Test LLMBackend initialization"""

    def test_init_with_defaults(self, caplog):
        """Test LLMBackend with default parameters"""
        from core.llm_backend import LLMBackend

        with caplog.at_level(logging.WARNING):
            backend = LLMBackend()

        assert backend.provider == "openai"
        assert backend.model == "gpt-4"
        assert "LLMBackend is a stub" in caplog.text

    def test_init_with_custom_provider(self, caplog):
        """Test LLMBackend with custom provider"""
        from core.llm_backend import LLMBackend

        with caplog.at_level(logging.WARNING):
            backend = LLMBackend(provider="anthropic")

        assert backend.provider == "anthropic"
        assert backend.model == "gpt-4"

    def test_init_with_custom_model(self, caplog):
        """Test LLMBackend with custom model"""
        from core.llm_backend import LLMBackend

        with caplog.at_level(logging.WARNING):
            backend = LLMBackend(model="claude-3")

        assert backend.provider == "openai"
        assert backend.model == "claude-3"

    def test_init_with_custom_both(self, caplog):
        """Test LLMBackend with both custom provider and model"""
        from core.llm_backend import LLMBackend

        with caplog.at_level(logging.WARNING):
            backend = LLMBackend(provider="cohere", model="command")

        assert backend.provider == "cohere"
        assert backend.model == "command"


class TestLLMBackendGenerate:
    """Test generate method"""

    @pytest.mark.asyncio
    async def test_generate_returns_string(self):
        """Test generate returns a string"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.generate("Hello world")

        assert isinstance(result, str)
        assert "Stub response for:" in result

    @pytest.mark.asyncio
    async def test_generate_includes_prompt(self):
        """Test generate includes truncated prompt"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.generate("Test prompt")

        assert "Test prompt" in result

    @pytest.mark.asyncio
    async def test_generate_truncates_long_prompt(self):
        """Test generate truncates long prompts to 50 chars"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        long_prompt = "a" * 100
        result = await backend.generate(long_prompt)

        # Should show only first 50 chars
        assert "a" * 50 in result
        assert "a" * 51 not in result

    @pytest.mark.asyncio
    async def test_generate_with_kwargs(self):
        """Test generate accepts kwargs (even if unused)"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.generate(
            "Hello", temperature=0.7, max_tokens=100
        )

        assert isinstance(result, str)


class TestLLMBackendChat:
    """Test chat method"""

    @pytest.mark.asyncio
    async def test_chat_returns_dict(self):
        """Test chat returns a dictionary"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.chat([{"role": "user", "content": "Hello"}])

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_chat_has_required_fields(self):
        """Test chat response has required fields"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        messages = [{"role": "user", "content": "Hello"}]
        result = await backend.chat(messages)

        assert "content" in result
        assert "model" in result
        assert "usage" in result

    @pytest.mark.asyncio
    async def test_chat_content_is_stub(self):
        """Test chat returns stub content"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.chat([])

        assert result["content"] == "Stub chat response"

    @pytest.mark.asyncio
    async def test_chat_model_matches_backend(self):
        """Test chat returns backend's model"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend(model="custom-model")
        result = await backend.chat([])

        assert result["model"] == "custom-model"

    @pytest.mark.asyncio
    async def test_chat_usage_format(self):
        """Test chat usage has expected format"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.chat([])

        assert "prompt_tokens" in result["usage"]
        assert "completion_tokens" in result["usage"]
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 10

    @pytest.mark.asyncio
    async def test_chat_with_kwargs(self):
        """Test chat accepts kwargs (even if unused)"""
        from core.llm_backend import LLMBackend

        backend = LLMBackend()
        result = await backend.chat([], temperature=0.5)

        assert isinstance(result, dict)


class TestModuleImport:
    """Test module-level imports"""

    def test_logger_exists(self):
        """Test logger is defined at module level"""
        import core.llm_backend as module

        assert hasattr(module, "logger")

    def test_llm_backend_class_exported(self):
        """Test LLMBackend class is importable"""
        from core.llm_backend import LLMBackend

        assert LLMBackend is not None

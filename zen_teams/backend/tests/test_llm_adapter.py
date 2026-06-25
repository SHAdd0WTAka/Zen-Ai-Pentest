"""Tests for LLM Adapter"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_adapter import (
    AnthropicProvider,
    GeminiProvider,
    LLMProviderFactory,
    OllamaProvider,
    OpenAIProvider,
    generate_with_agent,
    stream_with_agent,
)


class FakeAgent:
    llm_provider = "ollama"
    llm_model = "llama3.2"
    system_prompt = "You are a test agent"


class FakeAgentAnthropic:
    llm_provider = "anthropic"
    llm_model = "claude-3-5-sonnet-20241022"
    system_prompt = "You are a test agent"


class FakeAgentOpenAI:
    llm_provider = "openai"
    llm_model = "gpt-4o"
    system_prompt = "You are a test agent"


# ─── Factory ────────────────────────────────────────────────────────────────


def test_factory_list_providers():
    providers = LLMProviderFactory.list_providers()
    assert set(providers) == {"anthropic", "openai", "gemini", "ollama"}


def test_factory_get_provider():
    p = LLMProviderFactory.get_provider("ollama")
    assert isinstance(p, OllamaProvider)


def test_factory_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        LLMProviderFactory.get_provider("unknown")


# ─── Cost Estimation ────────────────────────────────────────────────────────


def test_anthropic_estimate_cost():
    p = AnthropicProvider(api_key="test")
    cost = p.estimate_cost(1_000_000, 1_000_000)
    assert cost == 3.0 + 15.0


def test_openai_estimate_cost():
    p = OpenAIProvider(api_key="test")
    cost = p.estimate_cost(1_000_000, 1_000_000)
    assert cost == 2.5 + 10.0


def test_gemini_estimate_cost():
    p = GeminiProvider(api_key="test")
    cost = p.estimate_cost(1_000_000, 1_000_000)
    assert cost == 1.25 + 5.0


def test_ollama_estimate_cost():
    p = OllamaProvider()
    cost = p.estimate_cost(1_000_000, 1_000_000)
    assert cost == 0.0


# ─── Ollama Provider (no external deps) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_generate():
    p = OllamaProvider(base_url="http://localhost:11434")
    with patch("aiohttp.ClientSession") as mock_session_cls:
        mock_session = MagicMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"response": "Hello from Ollama"}
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await p.generate("Say hello")
        assert result == "Hello from Ollama"


@pytest.mark.asyncio
async def test_ollama_stream():
    p = OllamaProvider(base_url="http://localhost:11434")
    with patch("aiohttp.ClientSession") as mock_session_cls:
        mock_session = MagicMock()
        mock_response = MagicMock()

        # Simulate streaming lines - content must be async iterable
        async def fake_content():
            for line in [b'{"response":"Hi"}\n', b'{"response":" there"}\n']:
                yield line

        mock_response.content = fake_content()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        chunks = []
        async for chunk in p.stream("Say hello"):
            chunks.append(chunk)
        assert chunks == ["Hi", " there"]


# ─── generate_with_agent / stream_with_agent ────────────────────────────────


@pytest.mark.asyncio
async def test_generate_with_agent():
    with patch.object(OllamaProvider, "generate", new_callable=AsyncMock, return_value="Generated!"):
        agent = FakeAgent()
        result = await generate_with_agent(agent, "Test prompt")
        assert result == "Generated!"


@pytest.mark.asyncio
async def test_stream_with_agent():
    async def fake_stream(*args, **kwargs):
        yield "chunk1"
        yield "chunk2"

    with patch.object(OllamaProvider, "stream", fake_stream):
        agent = FakeAgent()
        chunks = []
        async for chunk in stream_with_agent(agent, "Test prompt"):
            chunks.append(chunk)
        assert chunks == ["chunk1", "chunk2"]


# ─── Anthropic Provider (mocked client) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_anthropic_generate():
    p = AnthropicProvider(api_key="test-key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Claude says hi")]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch.object(p, "_get_client", return_value=mock_client):
        result = await p.generate("Hello")
        assert result == "Claude says hi"
        mock_client.messages.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_anthropic_stream():
    p = AnthropicProvider(api_key="test-key")

    class FakeTextStream:
        def __aiter__(self):
            self._idx = 0
            self._items = ["Hello", " world"]
            return self

        async def __anext__(self):
            if self._idx >= len(self._items):
                raise StopAsyncIteration
            item = self._items[self._idx]
            self._idx += 1
            return item

    class FakeStreamCtx:
        text_stream = FakeTextStream()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    mock_client = MagicMock()
    mock_client.messages.stream = MagicMock(return_value=FakeStreamCtx())

    with patch.object(p, "_get_client", return_value=mock_client):
        chunks = []
        async for chunk in p.stream("Hello"):
            chunks.append(chunk)
        assert chunks == ["Hello", " world"]


# ─── OpenAI Provider (mocked client) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_openai_generate():
    p = OpenAIProvider(api_key="test-key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="GPT says hi"))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(p, "_get_client", return_value=mock_client):
        result = await p.generate("Hello")
        assert result == "GPT says hi"


@pytest.mark.asyncio
async def test_openai_stream():
    p = OpenAIProvider(api_key="test-key")

    async def fake_chunks():
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))])
        yield MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))])

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_chunks())

    with patch.object(p, "_get_client", return_value=mock_client):
        chunks = []
        async for chunk in p.stream("Hello"):
            chunks.append(chunk)
        assert chunks == ["Hello", " world"]

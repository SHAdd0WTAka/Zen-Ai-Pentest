"""Test LLM backend"""

import pytest


class TestLLMBackend:
    """Test LLM backend"""

    def test_import(self):
        from core.llm_backend import LLMBackend

        assert LLMBackend is not None

    def test_has_generate(self):
        from core.llm_backend import LLMBackend

        assert hasattr(LLMBackend, "generate") or hasattr(LLMBackend, "chat")

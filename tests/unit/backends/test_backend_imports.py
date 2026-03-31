"""Test backend imports"""

import pytest


class TestBackendImports:
    """Test all LLM backends can be imported"""

    def test_kimi_backend_import(self):
        from backends.kimi_auth_backend import KimiAuthBackend

        assert KimiAuthBackend is not None

    def test_openrouter_backend_import(self):
        from backends.openrouter import OpenRouterBackend

        assert OpenRouterBackend is not None

    def test_chatgpt_backend_import(self):
        from backends.chatgpt_direct import ChatGPTDirectBackend

        assert ChatGPTDirectBackend is not None

    def test_claude_backend_import(self):
        from backends.claude_direct import ClaudeDirectBackend

        assert ClaudeDirectBackend is not None

    def test_duckduckgo_backend_import(self):
        from backends.duckduckgo import DuckDuckGoBackend

        assert DuckDuckGoBackend is not None

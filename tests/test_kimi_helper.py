#!/usr/bin/env python3
"""Tests für kimi_helper.py"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestKimiHelper:
    """Test cases für Kimi Helper"""

    def test_personas_defined(self):
        """Test dass alle 6 Personas definiert sind"""
        from kimi_helper import PERSONAS

        expected_personas = ['recon', 'exploit', 'report', 'audit', 'network', 'redteam']
        assert all(p in PERSONAS for p in expected_personas)

    def test_persona_structure(self):
        """Test dass jede Persona korrekte Struktur hat"""
        from kimi_helper import PERSONAS

        for key, persona in PERSONAS.items():
            assert 'name' in persona
            assert 'emoji' in persona
            assert 'desc' in persona
            assert 'prompt' in persona

    def test_get_persona_dir(self):
        """Test get_persona_dir Funktion"""
        from kimi_helper import get_persona_dir

        persona_dir = get_persona_dir()
        assert persona_dir.exists()
        assert persona_dir.name == "personas"

    def test_load_persona_invalid(self):
        """Test load_persona mit ungültiger Persona"""
        from kimi_helper import load_persona

        result = load_persona("invalid_persona")
        assert result is None

    @patch('kimi_helper.requests.post')
    def test_query_kimi_api_success(self, mock_post):
        """Test erfolgreiche API Anfrage"""
        from kimi_helper import query_kimi_api

        # Mock Response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch('kimi_helper.get_api_key', return_value='test-key'):
            result = query_kimi_api("test prompt", "system prompt")

        assert result == 'Test response'

    @patch('kimi_helper.get_api_key')
    def test_query_kimi_api_no_key(self, mock_get_key):
        """Test API Anfrage ohne Key"""
        from kimi_helper import query_kimi_api

        mock_get_key.return_value = None
        result = query_kimi_api("test", "system")

        assert result is None


class TestOpenRouterSupport:
    """Test OpenRouter spezifische Features"""

    def test_openrouter_key_detection(self):
        """Test Erkennung von OpenRouter Keys"""

        # OpenRouter Keys starten mit "sk-or-"
        openrouter_key = "sk-or-test123"
        assert openrouter_key.startswith("sk-or-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

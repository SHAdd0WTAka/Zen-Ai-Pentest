#!/usr/bin/env python3
"""Tests für switch_model.py"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestSwitchModel:
    """Test cases für Model Switcher"""

    def test_backends_defined(self):
        """Test dass alle Backends definiert sind"""
        from switch_model import BACKENDS

        expected = ['kimi', 'openrouter', 'openai']
        assert all(b in BACKENDS for b in expected)

    def test_parse_env_empty(self):
        """Test parse_env ohne existierende .env"""
        from switch_model import parse_env

        with patch('pathlib.Path.exists', return_value=False):
            result = parse_env(Path('/fake/.env'))

        assert result['current_backend'] is None
        assert result['current_model'] is None
        assert result['available'] == {}

    def test_parse_env_with_content(self):
        """Test parse_env mit Inhalt"""
        from switch_model import parse_env

        env_content = '''export DEFAULT_BACKEND="kimi"
export DEFAULT_MODEL="kimi-k2.5"
export KIMI_API_KEY="sk-test123"
'''

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=env_content)):
                result = parse_env(Path('/fake/.env'))

        assert result['current_backend'] == 'kimi'
        assert result['current_model'] == 'kimi-k2.5'
        assert 'kimi' in result['available']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

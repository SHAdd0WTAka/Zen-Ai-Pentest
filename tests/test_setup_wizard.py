#!/usr/bin/env python3
"""Tests für setup_wizard.py"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestSetupWizard:
    """Test cases für Setup Wizard"""

    def test_backends_defined(self):
        """Test dass alle Backends definiert sind"""
        from setup_wizard import BACKENDS

        expected = ['kimi', 'openrouter', 'openai']
        assert all(b in BACKENDS for b in expected)

    def test_backend_structure(self):
        """Test Backend Konfiguration"""
        from setup_wizard import BACKENDS

        for key, backend in BACKENDS.items():
            assert 'name' in backend
            assert 'env_var' in backend
            assert 'url' in backend
            assert 'models' in backend
            assert isinstance(backend['models'], list)

    def test_test_api_key_openrouter(self):
        """Test OpenRouter API Key Validierung"""
        from setup_wizard import test_api_key

        with patch('setup_wizard.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = test_api_key('openrouter', 'sk-or-test')
            assert result is True

    def test_test_api_key_invalid(self):
        """Test ungültiger API Key"""
        from setup_wizard import test_api_key

        with patch('setup_wizard.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = test_api_key('kimi', 'invalid-key')
            assert result is False


class TestEnvGeneration:
    """Test .env Datei Generierung"""

    def test_save_config_content(self):
        """Test Inhalt der generierten .env"""
        from setup_wizard import save_config

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('pathlib.Path.exists', return_value=False):
                save_config('kimi', 'kimi-k2.5', 'sk-test-key')

                # Prüfe dass open aufgerufen wurde
                mock_file.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

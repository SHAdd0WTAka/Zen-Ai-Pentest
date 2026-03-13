"""
Tests for api/core/config.py
Target: 100% Coverage
"""

import os
from unittest.mock import patch

import pytest


class TestSettingsImport:
    """Test basic settings import"""

    def test_settings_import(self):
        """Test that settings can be imported"""
        from api.core.config import settings

        assert settings is not None

    def test_settings_is_settings_class(self):
        """Test that settings is Settings instance"""
        from api.core.config import Settings, settings

        assert isinstance(settings, Settings)

    def test_jwt_algorithm(self):
        """Test JWT algorithm is HS256"""
        from api.core.config import settings

        assert settings.JWT_ALGORITHM == "HS256"

    def test_app_name(self):
        """Test app name"""
        from api.core.config import settings

        assert settings.APP_NAME == "ZEN-AI Pentest"

    def test_version(self):
        """Test version"""
        from api.core.config import settings

        assert settings.VERSION == "1.0.0"


class TestSettingsWithEnvVars:
    """Test settings with environment variables"""

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "test-secret-123"}, clear=True)
    def test_secret_key_from_env(self):
        """Test SECRET_KEY from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == "test-secret-123"

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "60"}, clear=True)
    def test_access_token_expire_from_env(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "14"}, clear=True)
    def test_refresh_token_expire_from_env(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == 14

    @patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://localhost/db"}, clear=True
    )
    def test_database_url_from_env(self):
        """Test DATABASE_URL from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert (
            config_module.settings.DATABASE_URL == "postgresql://localhost/db"
        )

    @patch.dict(os.environ, {"DEBUG": "true"}, clear=True)
    def test_debug_true_from_env(self):
        """Test DEBUG=true from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {"DEBUG": "True"}, clear=True)
    def test_debug_true_capitalized(self):
        """Test DEBUG=True (capitalized) from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {"DEBUG": "false"}, clear=True)
    def test_debug_false_from_env(self):
        """Test DEBUG=false from environment"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False


class TestSettingsDefaultsWithClearEnv:
    """Test settings defaults with cleared environment"""

    @patch.dict(os.environ, {}, clear=True)
    def test_defaults_with_clear_env(self):
        """Test all defaults when env is cleared"""
        import importlib

        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "dev-secret-key-change-in-production"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.DATABASE_URL is None
        assert settings.DEBUG is False
        assert settings.JWT_ALGORITHM == "HS256"

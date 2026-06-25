"""
Comprehensive unit tests for api/core/config.py
Target: 100% Coverage

Tests cover:
- Settings class initialization
- Environment variable loading (mock env vars)
- Default values
- Validation (invalid values)
- All config properties
"""

import importlib
import os
from unittest.mock import patch

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_config_module():
    """Reset config module after each test to ensure clean state."""
    yield
    # Cleanup: reimport with default environment
    with patch.dict(os.environ, {}, clear=True):
        import api.core.config as config_module

        importlib.reload(config_module)


@pytest.fixture
def clean_env():
    """Provide a clean environment with no config-related variables."""
    env_vars_to_clear = [
        "JWT_SECRET_KEY",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "DATABASE_URL",
        "DEBUG",
    ]
    patched_env = {k: "" for k in env_vars_to_clear}
    with patch.dict(os.environ, patched_env, clear=True):
        yield


# =============================================================================
# Test Settings Class Initialization
# =============================================================================


class TestSettingsInitialization:
    """Test Settings class initialization and basic properties."""

    def test_settings_class_exists(self):
        """Test that Settings class can be imported."""
        from api.core.config import Settings

        assert Settings is not None
        assert isinstance(Settings, type)

    def test_settings_instance_creation(self):
        """Test that Settings instance can be created."""
        from api.core.config import Settings

        settings = Settings()
        assert isinstance(settings, Settings)

    def test_settings_singleton(self):
        """Test that module-level settings instance exists."""
        from api.core.config import Settings, settings

        assert isinstance(settings, Settings)

    def test_settings_has_all_attributes(self):
        """Test that settings has all expected attributes."""
        from api.core.config import Settings

        settings = Settings()

        # JWT Settings
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "JWT_ALGORITHM")
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert hasattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS")

        # Database
        assert hasattr(settings, "DATABASE_URL")

        # App Settings
        assert hasattr(settings, "DEBUG")
        assert hasattr(settings, "APP_NAME")
        assert hasattr(settings, "VERSION")


# =============================================================================
# Test Default Values
# =============================================================================


class TestDefaultValues:
    """Test default values when no environment variables are set."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_secret_key(self):
        """Test default SECRET_KEY value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == "dev-secret-key-change-in-production"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_jwt_algorithm(self):
        """Test default JWT_ALGORITHM value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.JWT_ALGORITHM == "HS256"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_access_token_expire_minutes(self):
        """Test default ACCESS_TOKEN_EXPIRE_MINUTES value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert isinstance(config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_refresh_token_expire_days(self):
        """Test default REFRESH_TOKEN_EXPIRE_DAYS value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert isinstance(config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS, int)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_database_url(self):
        """Test default DATABASE_URL value (None)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DATABASE_URL is None

    @patch.dict(os.environ, {}, clear=True)
    def test_default_debug(self):
        """Test default DEBUG value (False)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False
        assert isinstance(config_module.settings.DEBUG, bool)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_app_name(self):
        """Test default APP_NAME value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.APP_NAME == "ZEN-AI Pentest"

    @patch.dict(os.environ, {}, clear=True)
    def test_default_version(self):
        """Test default VERSION value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.VERSION == "1.0.0"

    @patch.dict(os.environ, {}, clear=True)
    def test_all_defaults_together(self):
        """Test all default values together."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "dev-secret-key-change-in-production"
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.DATABASE_URL is None
        assert settings.DEBUG is False
        assert settings.APP_NAME == "ZEN-AI Pentest"
        assert settings.VERSION == "1.0.0"


# =============================================================================
# Test Environment Variable Loading
# =============================================================================


class TestEnvironmentVariableLoading:
    """Test loading settings from environment variables."""

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "custom-secret-key-123"}, clear=True)
    def test_secret_key_from_env(self):
        """Test SECRET_KEY loaded from environment."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == "custom-secret-key-123"

    @patch.dict(os.environ, {"JWT_SECRET_KEY": ""}, clear=True)
    def test_secret_key_empty_string(self):
        """Test SECRET_KEY with empty string."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == ""

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "60"}, clear=True)
    def test_access_token_expire_from_env(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES loaded from environment."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert isinstance(config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "0"}, clear=True)
    def test_access_token_expire_zero(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with zero."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 0

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "1440"}, clear=True)
    def test_access_token_expire_large_value(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with large value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "14"}, clear=True)
    def test_refresh_token_expire_from_env(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS loaded from environment."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == 14
        assert isinstance(config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS, int)

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "0"}, clear=True)
    def test_refresh_token_expire_zero(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS with zero."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == 0

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "365"}, clear=True)
    def test_refresh_token_expire_large_value(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS with large value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == 365

    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:pass@localhost/db"},
        clear=True,
    )
    def test_database_url_from_env(self):
        """Test DATABASE_URL loaded from environment."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DATABASE_URL == "postgresql://user:pass@localhost/db"

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./app.db"}, clear=True)
    def test_database_url_sqlite(self):
        """Test DATABASE_URL with SQLite."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DATABASE_URL == "sqlite:///./app.db"

    @patch.dict(os.environ, {"DEBUG": "true"}, clear=True)
    def test_debug_true_lowercase(self):
        """Test DEBUG=true (lowercase)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {"DEBUG": "True"}, clear=True)
    def test_debug_true_capitalized(self):
        """Test DEBUG=True (capitalized)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {"DEBUG": "TRUE"}, clear=True)
    def test_debug_true_uppercase(self):
        """Test DEBUG=TRUE (uppercase)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {"DEBUG": "false"}, clear=True)
    def test_debug_false_lowercase(self):
        """Test DEBUG=false (lowercase)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False

    @patch.dict(os.environ, {"DEBUG": "False"}, clear=True)
    def test_debug_false_capitalized(self):
        """Test DEBUG=False (capitalized)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False

    @patch.dict(os.environ, {"DEBUG": "FALSE"}, clear=True)
    def test_debug_false_uppercase(self):
        """Test DEBUG=FALSE (uppercase)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False

    @patch.dict(os.environ, {"DEBUG": "1"}, clear=True)
    def test_debug_numeric_one(self):
        """Test DEBUG=1 (should be False, not 'true')."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False

    @patch.dict(os.environ, {"DEBUG": "yes"}, clear=True)
    def test_debug_yes(self):
        """Test DEBUG=yes (should be False)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False

    @patch.dict(os.environ, {"DEBUG": ""}, clear=True)
    def test_debug_empty(self):
        """Test DEBUG='' (should be False)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DEBUG is False


# =============================================================================
# Test Multiple Environment Variables
# =============================================================================


class TestMultipleEnvironmentVariables:
    """Test loading multiple environment variables together."""

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-secret",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "120",
            "REFRESH_TOKEN_EXPIRE_DAYS": "30",
            "DATABASE_URL": "postgresql://localhost/test",
            "DEBUG": "true",
        },
        clear=True,
    )
    def test_all_env_vars_set(self):
        """Test all environment variables set together."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "test-secret"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30
        assert settings.DATABASE_URL == "postgresql://localhost/test"
        assert settings.DEBUG is True
        # Constants should remain unchanged
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.APP_NAME == "ZEN-AI Pentest"
        assert settings.VERSION == "1.0.0"

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "prod-secret",
            "DEBUG": "false",
        },
        clear=True,
    )
    def test_partial_env_vars(self):
        """Test partial environment variables with defaults."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "prod-secret"
        assert settings.DEBUG is False
        # Defaults should apply
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.DATABASE_URL is None


# =============================================================================
# Test Validation and Edge Cases
# =============================================================================


class TestValidationAndEdgeCases:
    """Test validation and edge cases for configuration values."""

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "not-a-number"}, clear=True)
    def test_access_token_expire_invalid_value(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with invalid value raises error."""
        import api.core.config as config_module

        with pytest.raises(ValueError):
            importlib.reload(config_module)

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "invalid"}, clear=True)
    def test_refresh_token_expire_invalid_value(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS with invalid value raises error."""
        import api.core.config as config_module

        with pytest.raises(ValueError):
            importlib.reload(config_module)

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "-10"}, clear=True)
    def test_access_token_expire_negative(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with negative value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        # Negative values are technically valid integers
        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == -10

    @patch.dict(os.environ, {"REFRESH_TOKEN_EXPIRE_DAYS": "-5"}, clear=True)
    def test_refresh_token_expire_negative(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS with negative value."""
        import api.core.config as config_module

        importlib.reload(config_module)

        # Negative values are technically valid integers
        assert config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS == -5

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "  60  "}, clear=True)
    def test_access_token_expire_with_whitespace(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with whitespace (Python handles gracefully)."""
        import api.core.config as config_module

        # Python's int() handles whitespace gracefully
        importlib.reload(config_module)
        assert config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "60.5"}, clear=True)
    def test_access_token_expire_float_string(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES with float string (should fail)."""
        import api.core.config as config_module

        with pytest.raises(ValueError):
            importlib.reload(config_module)


# =============================================================================
# Test Settings Instance Attributes
# =============================================================================


class TestSettingsInstanceAttributes:
    """Test accessing settings instance attributes."""

    def test_settings_are_class_attributes(self):
        """Test that settings are class-level attributes."""
        from api.core.config import Settings

        # Check class has attributes before instantiation
        assert hasattr(Settings, "SECRET_KEY") or "SECRET_KEY" in Settings.__dict__
        assert hasattr(Settings, "JWT_ALGORITHM")
        assert hasattr(Settings, "APP_NAME")
        assert hasattr(Settings, "VERSION")

    def test_settings_instance_shares_class_defaults(self):
        """Test that instance shares class default values."""
        from api.core.config import Settings

        instance1 = Settings()
        instance2 = Settings()

        assert instance1.JWT_ALGORITHM == instance2.JWT_ALGORITHM
        assert instance1.APP_NAME == instance2.APP_NAME
        assert instance1.VERSION == instance2.VERSION

    def test_module_settings_is_singleton(self):
        """Test that module-level settings is a singleton-like instance."""
        from api.core.config import Settings, settings

        # Should be the same instance type
        assert isinstance(settings, Settings)


# =============================================================================
# Test Type Validation
# =============================================================================


class TestTypeValidation:
    """Test types of configuration values."""

    @patch.dict(os.environ, {}, clear=True)
    def test_secret_key_is_string(self):
        """Test SECRET_KEY is string type."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.SECRET_KEY, str)

    @patch.dict(os.environ, {}, clear=True)
    def test_jwt_algorithm_is_string(self):
        """Test JWT_ALGORITHM is string type."""
        from api.core.config import settings

        assert isinstance(settings.JWT_ALGORITHM, str)

    @patch.dict(os.environ, {}, clear=True)
    def test_access_token_expire_is_int(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES is int type."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)

    @patch.dict(os.environ, {}, clear=True)
    def test_refresh_token_expire_is_int(self):
        """Test REFRESH_TOKEN_EXPIRE_DAYS is int type."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.REFRESH_TOKEN_EXPIRE_DAYS, int)

    @patch.dict(os.environ, {}, clear=True)
    def test_database_url_is_optional_string_or_none(self):
        """Test DATABASE_URL is either string or None."""
        import api.core.config as config_module

        importlib.reload(config_module)

        url = config_module.settings.DATABASE_URL
        assert url is None or isinstance(url, str)

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/db"}, clear=True)
    def test_database_url_with_value_is_string(self):
        """Test DATABASE_URL is string when set."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.DATABASE_URL, str)

    @patch.dict(os.environ, {}, clear=True)
    def test_debug_is_bool(self):
        """Test DEBUG is bool type."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.DEBUG, bool)

    @patch.dict(os.environ, {"DEBUG": "true"}, clear=True)
    def test_debug_true_is_bool(self):
        """Test DEBUG is bool when true."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert isinstance(config_module.settings.DEBUG, bool)
        assert config_module.settings.DEBUG is True

    @patch.dict(os.environ, {}, clear=True)
    def test_app_name_is_string(self):
        """Test APP_NAME is string type."""
        from api.core.config import settings

        assert isinstance(settings.APP_NAME, str)

    @patch.dict(os.environ, {}, clear=True)
    def test_version_is_string(self):
        """Test VERSION is string type."""
        from api.core.config import settings

        assert isinstance(settings.VERSION, str)


# =============================================================================
# Test Special Characters and Unicode
# =============================================================================


class TestSpecialCharactersAndUnicode:
    """Test handling of special characters in environment variables."""

    @patch.dict(
        os.environ,
        {"JWT_SECRET_KEY": "key-with-special-chars-!@#$%"},
        clear=True,
    )
    def test_secret_key_with_special_chars(self):
        """Test SECRET_KEY with special characters."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == "key-with-special-chars-!@#$%"

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "ключ-с-юникодом-日本語"}, clear=True)
    def test_secret_key_with_unicode(self):
        """Test SECRET_KEY with unicode characters."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.SECRET_KEY == "ключ-с-юникодом-日本語"

    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:p%40ss@localhost/db"},
        clear=True,
    )
    def test_database_url_with_encoded_chars(self):
        """Test DATABASE_URL with URL-encoded characters."""
        import api.core.config as config_module

        importlib.reload(config_module)

        assert config_module.settings.DATABASE_URL == "postgresql://user:p%40ss@localhost/db"


# =============================================================================
# Test Whitespace Handling
# =============================================================================


class TestWhitespaceHandling:
    """Test handling of whitespace in environment variables."""

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "  spaced-key  "}, clear=True)
    def test_secret_key_with_whitespace(self):
        """Test SECRET_KEY preserves whitespace."""
        import api.core.config as config_module

        importlib.reload(config_module)

        # Whitespace is preserved as-is
        assert config_module.settings.SECRET_KEY == "  spaced-key  "

    @patch.dict(os.environ, {"APP_NAME": "Test App"}, clear=True)
    def test_app_name_not_from_env(self):
        """Test APP_NAME is not affected by environment (it's hardcoded)."""
        import api.core.config as config_module

        importlib.reload(config_module)

        # APP_NAME is hardcoded, not from env
        assert config_module.settings.APP_NAME == "ZEN-AI Pentest"


# =============================================================================
# Test Module Import Side Effects
# =============================================================================


class TestModuleImport:
    """Test module import behavior."""

    def test_module_imports_settings_instance(self):
        """Test that importing module creates settings instance."""
        import api.core.config as config_module

        assert hasattr(config_module, "settings")
        assert config_module.settings is not None

    def test_settings_is_settings_class_instance(self):
        """Test that settings is instance of Settings class."""
        from api.core.config import Settings, settings

        assert isinstance(settings, Settings)

    def test_multiple_imports_same_instance(self):
        """Test that multiple imports reference the same module."""
        import api.core.config as config1
        import api.core.config as config2

        # Same module object
        assert config1 is config2
        assert config1.settings is config2.settings


# =============================================================================
# Test Documentation String
# =============================================================================


class TestDocumentation:
    """Test module and class documentation."""

    def test_module_has_docstring(self):
        """Test module has docstring."""
        import api.core.config as config_module

        assert config_module.__doc__ is not None
        assert "Configuration" in config_module.__doc__

    def test_settings_class_has_docstring(self):
        """Test Settings class has docstring."""
        from api.core.config import Settings

        assert Settings.__doc__ is not None
        assert "settings" in Settings.__doc__.lower()


# =============================================================================
# Integration-like Tests
# =============================================================================


class TestIntegrationScenarios:
    """Test realistic configuration scenarios."""

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "production-secret-key-min-32-chars",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "REFRESH_TOKEN_EXPIRE_DAYS": "1",
            "DATABASE_URL": "postgresql://prod_user:secure_pass@db.example.com:5432/pentest_prod",
            "DEBUG": "false",
        },
        clear=True,
    )
    def test_production_configuration(self):
        """Test production-like configuration."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "production-secret-key-min-32-chars"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 1
        assert settings.DATABASE_URL == "postgresql://prod_user:secure_pass@db.example.com:5432/pentest_prod"
        assert settings.DEBUG is False
        assert settings.JWT_ALGORITHM == "HS256"

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "dev-key",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
            "REFRESH_TOKEN_EXPIRE_DAYS": "30",
            "DATABASE_URL": "sqlite:///./dev.db",
            "DEBUG": "true",
        },
        clear=True,
    )
    def test_development_configuration(self):
        """Test development-like configuration."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "dev-key"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440  # 24 hours
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30
        assert settings.DATABASE_URL == "sqlite:///./dev.db"
        assert settings.DEBUG is True

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-secret",
            "DATABASE_URL": "sqlite:///./test.db",
        },
        clear=True,
    )
    def test_ci_cd_configuration(self):
        """Test CI/CD configuration with minimal env vars."""
        import api.core.config as config_module

        importlib.reload(config_module)
        settings = config_module.settings

        assert settings.SECRET_KEY == "test-secret"
        assert settings.DATABASE_URL == "sqlite:///./test.db"
        # Use defaults
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.DEBUG is False

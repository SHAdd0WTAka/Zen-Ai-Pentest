"""
Unit Tests für utils/helpers.py

Tests helper functions without file system dependencies.
"""

import json
import os
import tempfile

import pytest

from utils.helpers import (
    load_config,
    load_session,
    save_config,
    save_session,
    validate_target,
)

pytestmark = pytest.mark.unit


class TestLoadConfig:
    """Test load_config function"""

    def test_load_existing_config(self):
        """Test loading existing config file"""
        test_config = {
            "backends": {"openrouter_api_key": "test_key"},
            "custom_key": "custom_value",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(test_config, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["backends"]["openrouter_api_key"] == "test_key"
            assert config["custom_key"] == "custom_value"
            # Check defaults are merged
            assert "rate_limits" in config
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_config(self):
        """Test loading when file doesn't exist"""
        config = load_config("nonexistent_config_xyz.json")

        # Should return defaults
        assert "backends" in config
        assert "rate_limits" in config
        assert "stealth" in config
        assert "output" in config

    def test_load_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Should return defaults on error
            assert "backends" in config
        finally:
            os.unlink(temp_path)

    def test_config_merge_deep(self):
        """Test deep merging of nested config"""
        test_config = {
            "backends": {"openrouter_api_key": "test"},
            "rate_limits": {"requests_per_minute": 20},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(test_config, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Custom values
            assert config["backends"]["openrouter_api_key"] == "test"
            assert config["rate_limits"]["requests_per_minute"] == 20
            # Default values for missing keys
            assert config["backends"]["chatgpt_token"] is None
            assert config["rate_limits"]["backoff_seconds"] == 60
        finally:
            os.unlink(temp_path)


class TestSaveConfig:
    """Test save_config function"""

    def test_save_config(self):
        """Test saving config to file"""
        test_config = {"key": "value", "nested": {"key": "value"}}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_config(test_config, temp_path)

            # Verify file was written
            with open(temp_path, "r") as f:
                loaded = json.load(f)
                assert loaded == test_config
        finally:
            os.unlink(temp_path)


class TestSessionManagement:
    """Test session save/load functions"""

    def test_save_and_load_session(self):
        """Test saving and loading session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_data = {"token": "abc123", "user": "test"}

            # Save
            save_session("test_backend", session_data, tmpdir)

            # Load
            loaded = load_session("test_backend", tmpdir)
            assert loaded == session_data

    def test_load_nonexistent_session(self):
        """Test loading non-existent session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_session("nonexistent", tmpdir)
            assert result is None

    def test_load_invalid_session(self):
        """Test loading invalid session file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON file
            filepath = os.path.join(tmpdir, "invalid_session.json")
            with open(filepath, "w") as f:
                f.write("invalid json")

            result = load_session("invalid", tmpdir)
            assert result is None


class TestValidateTarget:
    """Test validate_target function"""

    def test_validate_ip_v4(self):
        """Test validating IPv4 address"""
        result = validate_target("192.168.1.1")
        assert result["valid"] is True
        assert result["is_ip"] is True
        assert result["is_domain"] is False
        assert result["is_url"] is False
        assert result["type"] == "ip"

    def test_validate_ip_v6(self):
        """Test validating IPv6 address"""
        result = validate_target("2001:db8::1")
        assert result["valid"] is True
        assert result["is_ip"] is True
        assert result["type"] == "ip"

    def test_validate_domain(self):
        """Test validating domain name"""
        result = validate_target("example.com")
        assert result["valid"] is True
        assert result["is_ip"] is False
        assert result["is_domain"] is True
        assert result["is_url"] is False
        assert result["type"] == "domain"

    def test_validate_subdomain(self):
        """Test validating subdomain"""
        result = validate_target("sub.domain.example.com")
        assert result["valid"] is True
        assert result["is_domain"] is True

    def test_validate_url_http(self):
        """Test validating HTTP URL"""
        result = validate_target("http://example.com")
        assert result["valid"] is True
        assert result["is_url"] is True
        assert result["type"] == "url"

    def test_validate_url_https(self):
        """Test validating HTTPS URL"""
        result = validate_target("https://example.com")
        assert result["valid"] is True
        assert result["is_url"] is True
        assert result["type"] == "url"

    def test_validate_url_with_path(self):
        """Test validating URL with path"""
        result = validate_target("https://example.com/path/to/page")
        assert result["valid"] is True
        assert result["is_url"] is True

    def test_validate_empty(self):
        """Test validating empty string"""
        result = validate_target("")
        assert result["valid"] is False
        assert result["type"] is None

    def test_validate_none(self):
        """Test validating None"""
        result = validate_target(None)
        assert result["valid"] is False

    def test_validate_invalid(self):
        """Test validating invalid target"""
        result = validate_target("not a valid target!!!")
        assert result["valid"] is False
        assert result["type"] is None

    def test_validate_localhost(self):
        """Test validating localhost - special case"""
        result = validate_target("localhost")
        # localhost is a special case - may be valid or invalid depending on implementation
        # We just check it doesn't crash
        assert "valid" in result

    def test_validate_private_ip(self):
        """Test validating private IP"""
        result = validate_target("10.0.0.1")
        assert result["valid"] is True
        assert result["is_ip"] is True

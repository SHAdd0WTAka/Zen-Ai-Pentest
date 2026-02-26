"""
Tests for utils/helpers.py
Target: 90%+ Coverage
"""

import json
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest


class TestLoadConfig:
    """Test load_config function"""

    def test_load_config_defaults(self):
        """Test load_config returns defaults when file doesn't exist"""
        from utils.helpers import load_config

        # Use non-existent path
        config = load_config("/nonexistent/config.json")

        assert "backends" in config
        assert "rate_limits" in config
        assert "stealth" in config
        assert "output" in config
        assert config["stealth"]["delay_min"] == 1

    def test_load_config_from_file(self):
        """Test load_config loads from file"""
        from utils.helpers import load_config

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"custom_key": "value"}, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["custom_key"] == "value"
            # Should merge with defaults
            assert "backends" in config
        finally:
            os.unlink(temp_path)

    def test_load_config_merges_nested(self):
        """Test load_config merges nested dicts"""
        from utils.helpers import load_config

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"stealth": {"delay_min": 5}}, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Custom value preserved
            assert config["stealth"]["delay_min"] == 5
            # Default value merged
            assert config["stealth"]["delay_max"] == 3
        finally:
            os.unlink(temp_path)

    def test_load_config_invalid_json(self):
        """Test load_config handles invalid JSON"""
        from utils.helpers import load_config

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Should return defaults
            assert "backends" in config
        finally:
            os.unlink(temp_path)


class TestSaveConfig:
    """Test save_config function"""

    def test_save_config_creates_file(self):
        """Test save_config creates file"""
        from utils.helpers import save_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            test_config = {"key": "value", "nested": {"a": 1}}

            save_config(test_config, config_path)

            assert os.path.exists(config_path)
            with open(config_path, "r") as f:
                loaded = json.load(f)
            assert loaded == test_config


class TestSaveSession:
    """Test save_session function"""

    def test_save_session_creates_dir(self):
        """Test save_session creates session directory"""
        from utils.helpers import save_session

        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = os.path.join(tmpdir, "sessions")

            save_session("test_backend", {"token": "abc123"}, session_dir)

            assert os.path.exists(session_dir)
            expected_file = os.path.join(
                session_dir, "test_backend_session.json"
            )
            assert os.path.exists(expected_file)

    def test_save_session_saves_data(self, capsys):
        """Test save_session saves correct data"""
        from utils.helpers import save_session

        with tempfile.TemporaryDirectory() as tmpdir:
            session_data = {"token": "abc123", "expires": 12345}
            save_session("my_backend", session_data, tmpdir)

            filepath = os.path.join(tmpdir, "my_backend_session.json")
            with open(filepath, "r") as f:
                loaded = json.load(f)
            assert loaded == session_data

            captured = capsys.readouterr()
            assert "Saved my_backend session" in captured.out


class TestLoadSession:
    """Test load_session function"""

    def test_load_session_existing(self):
        """Test load_session loads existing session"""
        from utils.helpers import load_session

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "my_backend_session.json")
            with open(filepath, "w") as f:
                json.dump({"token": "xyz789"}, f)

            result = load_session("my_backend", tmpdir)

            assert result == {"token": "xyz789"}

    def test_load_session_not_found(self):
        """Test load_session returns None for missing session"""
        from utils.helpers import load_session

        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_session("nonexistent", tmpdir)
            assert result is None

    def test_load_session_invalid_json(self, capsys):
        """Test load_session handles invalid JSON"""
        from utils.helpers import load_session

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "bad_session.json")
            with open(filepath, "w") as f:
                f.write("invalid json")

            result = load_session("bad", tmpdir)

            assert result is None
            captured = capsys.readouterr()
            assert "Error loading" in captured.out


class TestValidateTarget:
    """Test validate_target function"""

    def test_validate_empty_target(self):
        """Test validation with empty target"""
        from utils.helpers import validate_target

        result = validate_target("")
        assert result["valid"] is False
        assert result["type"] is None

    def test_validate_valid_ip(self):
        """Test validation with valid IP"""
        from utils.helpers import validate_target

        result = validate_target("192.168.1.1")
        assert result["valid"] is True
        assert result["is_ip"] is True
        assert result["type"] == "ip"

    def test_validate_valid_ipv6(self):
        """Test validation with valid IPv6"""
        from utils.helpers import validate_target

        result = validate_target("::1")
        assert result["valid"] is True
        assert result["is_ip"] is True

    def test_validate_valid_domain(self):
        """Test validation with valid domain"""
        from utils.helpers import validate_target

        result = validate_target("example.com")
        assert result["valid"] is True
        assert result["is_domain"] is True
        assert result["type"] == "domain"

    def test_validate_valid_url_http(self):
        """Test validation with HTTP URL"""
        from utils.helpers import validate_target

        result = validate_target("http://example.com")
        assert result["valid"] is True
        assert result["is_url"] is True
        assert result["type"] == "url"

    def test_validate_valid_url_https(self):
        """Test validation with HTTPS URL"""
        from utils.helpers import validate_target

        result = validate_target("https://example.com/path?query=1")
        assert result["valid"] is True
        assert result["is_url"] is True

    def test_validate_url_with_port(self):
        """Test validation with URL containing port"""
        from utils.helpers import validate_target

        result = validate_target("http://localhost:8080")
        assert result["valid"] is True

    def test_validate_invalid_target(self):
        """Test validation with invalid target"""
        from utils.helpers import validate_target

        result = validate_target("not a valid target!!!")
        assert result["valid"] is False

    def test_validate_single_label_domain(self):
        """Test validation with single label (no dot)"""
        from utils.helpers import validate_target

        result = validate_target("localhost")
        # localhost needs URL format to be valid
        assert result["valid"] is False


class TestSanitizeFilename:
    """Test sanitize_filename function"""

    def test_sanitize_removes_invalid_chars(self):
        """Test removal of invalid filename characters"""
        from utils.helpers import sanitize_filename

        result = sanitize_filename('file<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result

    def test_sanitize_limits_length(self):
        """Test filename length limit"""
        from utils.helpers import sanitize_filename

        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_sanitize_keeps_valid_chars(self):
        """Test valid characters are preserved"""
        from utils.helpers import sanitize_filename

        result = sanitize_filename("valid_filename-123.txt")
        assert result == "valid_filename-123.txt"


class TestFormatDuration:
    """Test format_duration function"""

    def test_format_seconds(self):
        """Test formatting seconds"""
        from utils.helpers import format_duration

        assert format_duration(45) == "45.0s"
        assert format_duration(59.5) == "59.5s"

    def test_format_minutes(self):
        """Test formatting minutes"""
        from utils.helpers import format_duration

        assert format_duration(120) == "2.0m"
        assert format_duration(90) == "1.5m"

    def test_format_hours(self):
        """Test formatting hours"""
        from utils.helpers import format_duration

        assert format_duration(7200) == "2.0h"
        assert format_duration(5400) == "1.5h"


class TestTruncateString:
    """Test truncate_string function"""

    def test_truncate_short_string(self):
        """Test short string not truncated"""
        from utils.helpers import truncate_string

        assert truncate_string("short") == "short"

    def test_truncate_long_string(self):
        """Test long string truncated"""
        from utils.helpers import truncate_string

        long_str = "a" * 200
        result = truncate_string(long_str, max_length=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_truncate_custom_suffix(self):
        """Test custom suffix"""
        from utils.helpers import truncate_string

        long_str = "a" * 200
        result = truncate_string(long_str, max_length=50, suffix="[more]")
        assert result.endswith("[more]")


class TestBanner:
    """Test banner function"""

    def test_banner_contains_text(self):
        """Test banner contains expected text"""
        from utils.helpers import banner

        result = banner()
        assert "ZEN AI PENTEST" in result
        assert "SHAdd0WTAka" in result
        assert "Version: 1.0.0" in result


class TestColorize:
    """Test colorize function"""

    def test_colorize_red(self):
        """Test red color"""
        from utils.helpers import colorize

        result = colorize("text", "red")
        assert "\033[91m" in result
        assert "\033[0m" in result

    def test_colorize_green(self):
        """Test green color"""
        from utils.helpers import colorize

        result = colorize("text", "green")
        assert "\033[92m" in result

    def test_colorize_unknown_color(self):
        """Test unknown color defaults to no color code"""
        from utils.helpers import colorize

        result = colorize("text", "unknown")
        # Should still have reset code
        assert "\033[0m" in result

    def test_colorize_all_colors(self):
        """Test all defined colors"""
        from utils.helpers import colorize

        colors = [
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
            "bold",
        ]
        for color in colors:
            result = colorize("test", color)
            assert "\033[" in result
            assert "\033[0m" in result


class TestGetSeverityColor:
    """Test get_severity_color function"""

    def test_get_severity_critical(self):
        """Test Critical severity"""
        from utils.helpers import get_severity_color

        assert get_severity_color("Critical") == "red"

    def test_get_severity_high(self):
        """Test High severity"""
        from utils.helpers import get_severity_color

        assert get_severity_color("High") == "magenta"

    def test_get_severity_medium(self):
        """Test Medium severity"""
        from utils.helpers import get_severity_color

        assert get_severity_color("Medium") == "yellow"

    def test_get_severity_low(self):
        """Test Low severity"""
        from utils.helpers import get_severity_color

        assert get_severity_color("Low") == "blue"

    def test_get_severity_info(self):
        """Test Info severity"""
        from utils.helpers import get_severity_color

        assert get_severity_color("Info") == "white"

    def test_get_severity_unknown(self):
        """Test unknown severity defaults to white"""
        from utils.helpers import get_severity_color

        assert get_severity_color("Unknown") == "white"

"""Tests for utils.helpers module."""

import json
import os

import pytest


@pytest.fixture
def sample_config():
    return {
        "backends": {"openrouter_api_key": "test-key"},
        "rate_limits": {"requests_per_minute": 5},
    }


class TestValidateTarget:
    def test_valid_ipv4(self):
        from utils.helpers import validate_target

        result = validate_target("192.168.1.1")
        assert result["valid"] is True
        assert result["is_ip"] is True
        assert result["type"] == "ip"

    def test_valid_ipv6(self):
        from utils.helpers import validate_target

        result = validate_target("::1")
        assert result["valid"] is True
        assert result["is_ip"] is True

    def test_valid_domain(self):
        from utils.helpers import validate_target

        result = validate_target("example.com")
        assert result["valid"] is True
        assert result["is_domain"] is True
        assert result["type"] == "domain"

    def test_valid_url(self):
        from utils.helpers import validate_target

        result = validate_target("https://example.com")
        assert result["valid"] is True
        assert result["is_url"] is True
        assert result["type"] == "url"

    def test_valid_url_with_port(self):
        from utils.helpers import validate_target

        result = validate_target("http://localhost:8080")
        assert result["valid"] is True
        assert result["is_url"] is True

    def test_empty_target(self):
        from utils.helpers import validate_target

        result = validate_target("")
        assert result["valid"] is False
        assert result["type"] is None

    def test_none_target(self):
        from utils.helpers import validate_target

        result = validate_target("not a target at all")
        assert result["valid"] is False
        assert result["type"] is None


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        from utils.helpers import sanitize_filename

        assert sanitize_filename('foo<>:"/\\|?*bar') == "foo_________bar"

    def test_preserves_valid_chars(self):
        from utils.helpers import sanitize_filename

        assert sanitize_filename("hello-world.txt") == "hello-world.txt"

    def test_truncates_long_names(self):
        from utils.helpers import sanitize_filename

        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) == 100

    def test_empty_string(self):
        from utils.helpers import sanitize_filename

        assert sanitize_filename("") == ""


class TestFormatDuration:
    def test_seconds(self):
        from utils.helpers import format_duration

        assert format_duration(30) == "30.0s"

    def test_minutes(self):
        from utils.helpers import format_duration

        assert format_duration(90) == "1.5m"
        assert format_duration(3540) == "59.0m"

    def test_hours(self):
        from utils.helpers import format_duration

        assert format_duration(7200) == "2.0h"
        assert format_duration(36000) == "10.0h"

    def test_zero(self):
        from utils.helpers import format_duration

        assert format_duration(0) == "0.0s"


class TestTruncateString:
    def test_no_truncation_needed(self):
        from utils.helpers import truncate_string

        assert truncate_string("hello") == "hello"

    def test_truncates_with_suffix(self):
        from utils.helpers import truncate_string

        result = truncate_string("hello world this is long", max_length=10)
        assert result == "hello w..."

    def test_exact_length(self):
        from utils.helpers import truncate_string

        assert truncate_string("hello", max_length=5) == "hello"

    def test_custom_suffix(self):
        from utils.helpers import truncate_string

        result = truncate_string("hello world", max_length=7, suffix="!!")
        assert result == "hello!!"

    def test_empty_string(self):
        from utils.helpers import truncate_string

        assert truncate_string("") == ""


class TestBanner:
    def test_returns_banner_string(self):
        from utils.helpers import banner

        result = banner()
        assert "ZEN AI PENTEST" in result
        assert "SHAdd0WTAka" in result

    def test_contains_separator(self):
        from utils.helpers import banner

        result = banner()
        assert "=" in result


class TestColorize:
    def test_red_color(self):
        from utils.helpers import colorize

        result = colorize("error", "red")
        assert "\033[91m" in result
        assert "error" in result
        assert "\033[0m" in result

    def test_green_color(self):
        from utils.helpers import colorize

        result = colorize("ok", "green")
        assert "\033[92m" in result
        assert "ok" in result

    def test_unknown_color_falls_back(self):
        from utils.helpers import colorize

        result = colorize("test", "nonexistent")
        assert "\033[0m" in result
        assert "test" in result

    def test_bold(self):
        from utils.helpers import colorize

        result = colorize("bold text", "bold")
        assert "\033[1m" in result


class TestGetSeverityColor:
    def test_critical_is_red(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("Critical") == "red"

    def test_high_is_magenta(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("High") == "magenta"

    def test_medium_is_yellow(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("Medium") == "yellow"

    def test_low_is_blue(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("Low") == "blue"

    def test_info_is_white(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("Info") == "white"

    def test_unknown_severity_defaults_to_white(self):
        from utils.helpers import get_severity_color

        assert get_severity_color("Unknown") == "white"


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self, tmp_path):
        from utils.helpers import load_config

        config_path = str(tmp_path / "nonexistent.json")
        result = load_config(config_path)
        assert "backends" in result
        assert "rate_limits" in result

    def test_loads_existing_config(self, tmp_path):
        from utils.helpers import load_config

        config = {"backends": {"openrouter_api_key": "test"}}
        config_path = str(tmp_path / "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        result = load_config(config_path)
        assert result["backends"]["openrouter_api_key"] == "test"

    def test_merges_with_defaults(self, tmp_path):
        from utils.helpers import load_config

        config = {"backends": {"openrouter_api_key": "test"}}
        config_path = str(tmp_path / "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        result = load_config(config_path)
        assert result["rate_limits"]["requests_per_minute"] == 10

    def test_handles_corrupted_file(self, tmp_path):
        from utils.helpers import load_config

        config_path = str(tmp_path / "bad.json")
        with open(config_path, "w") as f:
            f.write("not json")

        result = load_config(config_path)
        assert "backends" in result


class TestSaveConfig:
    def test_saves_config(self, tmp_path):
        from utils.helpers import save_config

        config = {"key": "value"}
        config_path = str(tmp_path / "out.json")
        save_config(config, config_path)

        with open(config_path) as f:
            loaded = json.load(f)
        assert loaded == {"key": "value"}


class TestSaveLoadSession:
    def test_save_and_load_session(self, tmp_path):
        from utils.helpers import load_session, save_session

        session_dir = str(tmp_path / "sessions")
        data = {"token": "abc123", "expires": 12345}
        save_session("openai", data, session_dir)

        loaded = load_session("openai", session_dir)
        assert loaded == data

    def test_load_missing_session(self, tmp_path):
        from utils.helpers import load_session

        result = load_session("nonexistent", str(tmp_path / "sessions"))
        assert result is None

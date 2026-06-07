"""
Comprehensive unit tests for utils/helpers.py, zen_ai_pentest/cli.py,
and selected __init__.py files.
"""

import json
import sys

import pytest

from utils.helpers import (
    banner,
    colorize,
    format_duration,
    get_severity_color,
    load_config,
    load_session,
    sanitize_filename,
    save_config,
    save_session,
    truncate_string,
    validate_target,
)
from zen_ai_pentest.cli import main as cli_main

pytestmark = pytest.mark.unit


class TestLoadConfig:
    def test_missing_file_returns_defaults(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "missing.json"
        config = load_config(str(missing))
        assert config["backends"]["openrouter_api_key"] is None
        assert config["rate_limits"]["requests_per_minute"] == 10
        assert config["stealth"]["delay_min"] == 1
        assert config["output"]["log_level"] == "INFO"

    def test_valid_file_loads_and_merges(self, tmp_path):
        config_path = tmp_path / "config.json"
        payload = {"backends": {"openrouter_api_key": "secret"}, "custom": True}
        config_path.write_text(json.dumps(payload))

        config = load_config(str(config_path))
        assert config["backends"]["openrouter_api_key"] == "secret"
        assert config["custom"] is True
        # Missing nested default merged
        assert config["backends"]["chatgpt_token"] is None
        assert config["rate_limits"]["backoff_seconds"] == 60

    def test_partial_config_merges_defaults(self, tmp_path):
        config_path = tmp_path / "partial.json"
        payload = {"rate_limits": {"requests_per_minute": 99}}
        config_path.write_text(json.dumps(payload))

        config = load_config(str(config_path))
        assert config["rate_limits"]["requests_per_minute"] == 99
        assert config["rate_limits"]["backoff_seconds"] == 60
        assert config["backends"]["openrouter_api_key"] is None

    def test_invalid_json_returns_defaults_and_prints(self, tmp_path, capsys):
        config_path = tmp_path / "bad.json"
        config_path.write_text("not json")

        config = load_config(str(config_path))
        assert config["backends"]["openrouter_api_key"] is None
        captured = capsys.readouterr()
        assert "Error loading config" in captured.out

    def test_full_config_preserves_existing_nested_values(self, tmp_path):
        config_path = tmp_path / "full.json"
        payload = {
            "backends": {
                "openrouter_api_key": "k1",
                "chatgpt_token": "k2",
                "claude_session": "k3",
            },
            "rate_limits": {"requests_per_minute": 1, "backoff_seconds": 2},
            "stealth": {"delay_min": 0, "delay_max": 1, "random_user_agent": False},
            "output": {"save_logs": False, "log_level": "DEBUG", "report_format": "json"},
        }
        config_path.write_text(json.dumps(payload))

        config = load_config(str(config_path))
        assert config == payload


class TestSaveConfig:
    def test_save_config_writes_valid_json(self, tmp_path):
        config_path = tmp_path / "out.json"
        payload = {"a": 1, "nested": {"b": "c"}}
        save_config(payload, str(config_path))

        assert config_path.exists()
        loaded = json.loads(config_path.read_text())
        assert loaded == payload


class TestSessionManagement:
    def test_save_session_creates_directory_and_file(self, tmp_path, capsys):
        session_dir = tmp_path / "sessions"
        data = {"token": "abc", "user": "me"}
        save_session("backend1", data, str(session_dir))

        expected = session_dir / "backend1_session.json"
        assert expected.exists()
        assert json.loads(expected.read_text()) == data
        captured = capsys.readouterr()
        assert "Saved backend1 session" in captured.out

    def test_load_session_missing_returns_none(self, tmp_path):
        assert load_session("missing", str(tmp_path)) is None

    def test_load_session_valid_returns_data(self, tmp_path):
        data = {"key": [1, 2, 3]}
        path = tmp_path / "backend2_session.json"
        path.write_text(json.dumps(data))
        assert load_session("backend2", str(tmp_path)) == data

    def test_load_session_invalid_json_returns_none_and_prints(self, tmp_path, capsys):
        path = tmp_path / "bad_session.json"
        path.write_text("{invalid")
        assert load_session("bad", str(tmp_path)) is None
        captured = capsys.readouterr()
        assert "Error loading bad session" in captured.out


class TestValidateTarget:
    def test_valid_ipv4(self):
        r = validate_target("192.168.1.1")
        assert r["valid"] is True
        assert r["is_ip"] is True
        assert r["type"] == "ip"

    def test_valid_ipv6(self):
        r = validate_target("2001:db8::1")
        assert r["valid"] is True
        assert r["is_ip"] is True
        assert r["type"] == "ip"

    def test_valid_url(self):
        r = validate_target("https://example.com/path?x=1")
        assert r["valid"] is True
        assert r["is_url"] is True
        assert r["type"] == "url"

    def test_valid_domain(self):
        r = validate_target("example.com")
        assert r["valid"] is True
        assert r["is_domain"] is True
        assert r["type"] == "domain"

    def test_valid_subdomain(self):
        r = validate_target("sub.example.co.uk")
        assert r["valid"] is True
        assert r["is_domain"] is True

    def test_invalid_inputs(self):
        assert validate_target("")["valid"] is False
        assert validate_target(None)["valid"] is False
        assert validate_target("not valid!!!")["valid"] is False
        assert validate_target(" spaces ")["valid"] is False


class TestSanitizeFilename:
    def test_removes_invalid_characters(self):
        assert sanitize_filename("a<b>c:d/e\\f|g?h*i") == "a_b_c_d_e_f_g_h_i"

    def test_limits_length(self):
        long_name = "a" * 150
        assert len(sanitize_filename(long_name)) == 100

    def test_normal_name_unchanged(self):
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(45.0) == "45.0s"

    def test_minutes(self):
        assert format_duration(120.0) == "2.0m"

    def test_hours(self):
        assert format_duration(7200.0) == "2.0h"

    def test_boundary_seconds_to_minutes(self):
        assert format_duration(59.9) == "59.9s"
        assert format_duration(60.0) == "1.0m"

    def test_boundary_minutes_to_hours(self):
        assert format_duration(3599.0) == "60.0m"
        assert format_duration(3600.0) == "1.0h"


class TestTruncateString:
    def test_short_string_unchanged(self):
        assert truncate_string("hello", max_length=10) == "hello"

    def test_long_string_truncated_with_suffix(self):
        s = "a" * 100
        result = truncate_string(s, max_length=10)
        assert result == "aaaaaaa..."
        assert len(result) == 10

    def test_exact_length_unchanged(self):
        s = "a" * 10
        assert truncate_string(s, max_length=10) == s


class TestBanner:
    def test_contains_project_name(self):
        text = banner()
        assert "ZEN AI PENTEST" in text


class TestColorize:
    def test_all_colors(self):
        text = "X"
        for color in ("red", "green", "yellow", "blue", "magenta", "cyan", "white", "bold"):
            result = colorize(text, color)
            assert result.startswith("\033[")
            assert result.endswith("\033[0m")
            assert text in result

    def test_invalid_color_returns_reset_only(self):
        result = colorize("X", "octarine")
        assert result == "X\033[0m"


class TestGetSeverityColor:
    def test_all_severities(self):
        assert get_severity_color("Critical") == "red"
        assert get_severity_color("High") == "magenta"
        assert get_severity_color("Medium") == "yellow"
        assert get_severity_color("Low") == "blue"
        assert get_severity_color("Info") == "white"

    def test_invalid_returns_white(self):
        assert get_severity_color("Unknown") == "white"


class TestCli:
    def test_main_runs_and_prints_banner(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["zen_ai_pentest"])
        cli_main()
        captured = capsys.readouterr()
        assert "Zen AI Pentest v2.3.9" in captured.out
        assert "Available modules:" in captured.out
        assert "core" in captured.out


class TestZenAiPentestInit:
    def test_version_and_author_and_license(self):
        import zen_ai_pentest

        assert zen_ai_pentest.__version__ == "1.0.0"
        assert zen_ai_pentest.__author__ == "Zen-AI-Pentest Team"
        assert zen_ai_pentest.__license__ == "MIT"

    def test_all_exports(self):
        import zen_ai_pentest

        expected = [
            "__version__",
            "__author__",
            "__license__",
            "BaseTool",
            "PluginRegistry",
            "ToolMetadata",
            "ToolResult",
            "ToolCategory",
            "ToolRiskLevel",
            "get_registry",
            "AIToolSelector",
            "ExecutionContext",
            "ToolRecommendation",
            "SelectionStrategy",
            "LLMVotingEngine",
            "ContextMatcher",
            "PerformanceTracker",
            "SecureToolWrapper",
            "SandboxConfig",
            "ExecutionOptions",
            "ResourceMonitor",
            "NetworkIsolator",
            "PentestAgent",
            "MultiAgentOrchestrator",
            "AgentConfig",
            "AgentResult",
        ]
        for name in expected:
            assert name in zen_ai_pentest.__all__


class TestPluginsInit:
    def test_builtin_plugins_and_accessors(self):
        import zen_ai_pentest.plugins as plugins

        assert "NmapPlugin" in plugins.__all__
        assert "SQLMapPlugin" in plugins.__all__
        assert "NucleiPlugin" in plugins.__all__
        assert "SubfinderPlugin" in plugins.__all__
        assert "TrivyPlugin" in plugins.__all__

        names = plugins.list_builtin_plugins()
        assert set(names) == {"nmap", "sqlmap", "nuclei", "subfinder", "trivy"}

        assert plugins.get_builtin_plugin("nmap") is plugins.NmapPlugin
        assert plugins.get_builtin_plugin("missing") is None


class TestExamplesInit:
    def test_all_exports_exist(self):
        import zen_ai_pentest.examples as examples

        for name in examples.__all__:
            assert hasattr(examples, name)
            assert callable(getattr(examples, name))

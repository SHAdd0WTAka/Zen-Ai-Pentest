"""Smoke tests for tools/gobuster_integration.py"""

import pytest

from tools.gobuster_integration import TOOL_REGISTRY, GobusterResult, GobusterScanner, GobusterTool


class TestGobusterResult:
    def test_creation(self):
        result = GobusterResult(
            target="http://example.com/admin",
            found_paths=[{"path": "/admin", "status": 200, "url": "http://example.com/admin"}],
            status_codes={200: 1},
            total_requests=1,
            duration=1.5,
            success=True,
        )
        assert result.target == "http://example.com/admin"
        assert len(result.found_paths) == 1
        assert result.status_codes == {200: 1}
        assert result.success is True
        assert result.error_message is None


class TestGobusterScanner:
    def test_init_defaults(self):
        scanner = GobusterScanner()
        assert scanner.timeout == 300

    def test_init_custom(self):
        scanner = GobusterScanner(timeout=60)
        assert scanner.timeout == 60

    def test_validate_missing_target(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({})
        assert not valid

    def test_validate_valid(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({"target": "http://example.com"})
        assert valid
        assert error is None

    def test_parse_output(self):
        scanner = GobusterScanner()
        output = "/admin (Status: 200) [Size: 1234]\n/login (Status: 301) [Size: 567]\n"
        result = scanner._parse_output(output, "http://example.com")
        assert len(result.found_paths) == 2
        assert result.target == "http://example.com"
        assert result.found_paths[0]["path"] == "/admin"
        assert result.found_paths[1]["status"] == 301

    def test_parse_output_empty(self):
        scanner = GobusterScanner()
        result = scanner._parse_output("", "http://example.com")
        assert result.found_paths == []
        assert result.status_codes == {}
        assert result.total_requests == 0

    def test_build_command(self):
        scanner = GobusterScanner()
        cmd = scanner._build_command("http://example.com", {"extensions": "php"})
        cmd_str = " ".join(cmd)
        assert "http://example.com" in cmd_str
        assert "php" in cmd_str


class TestGobusterTool:
    def test_name_and_description(self):
        tool = GobusterTool()
        assert tool.name == "gobuster"
        assert len(tool.description) > 0

    def test_get_parameters(self):
        tool = GobusterTool()
        params = tool.get_parameters()
        assert "target" in params
        assert params["target"]["type"] == "string"
        assert params["target"]["required"] is True


class TestRegistry:
    def test_tool_registry_contains_gobuster(self):
        assert "gobuster" in TOOL_REGISTRY
        assert TOOL_REGISTRY["gobuster"] == GobusterTool

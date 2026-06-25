"""Unit tests for tools/gobuster_integration.py"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.gobuster_integration import (
    TOOL_REGISTRY,
    GobusterResult,
    GobusterScanner,
    GobusterTool,
)


class TestGobusterResult:
    def test_creation_with_all_fields(self):
        result = GobusterResult(
            target="http://example.com",
            found_paths=[{"path": "/admin", "status": 200, "url": "http://example.com/admin"}],
            status_codes={200: 1},
            total_requests=1,
            duration=2.5,
            success=True,
            error_message=None,
        )
        assert result.target == "http://example.com"
        assert result.found_paths[0]["path"] == "/admin"
        assert result.status_codes == {200: 1}
        assert result.success is True
        assert result.error_message is None

    def test_creation_with_error(self):
        result = GobusterResult(
            target="http://example.com",
            found_paths=[],
            status_codes={},
            total_requests=0,
            duration=0.0,
            success=False,
            error_message="Target unreachable",
        )
        assert result.success is False
        assert result.error_message == "Target unreachable"

    def test_empty_paths_list(self):
        result = GobusterResult(
            target="http://example.com",
            found_paths=[],
            status_codes={},
            total_requests=0,
            duration=0.0,
            success=True,
        )
        assert result.found_paths == []
        assert result.total_requests == 0


class TestGobusterScanner:
    def test_init_defaults(self):
        scanner = GobusterScanner()
        assert scanner.timeout == 300
        assert scanner.default_wordlist == "/usr/share/wordlists/dirb/common.txt"

    def test_init_custom_timeout(self):
        scanner = GobusterScanner(timeout=120)
        assert scanner.timeout == 120

    def test_init_custom_wordlist(self):
        scanner = GobusterScanner(wordlist="/custom/wordlist.txt")
        assert scanner.default_wordlist == "/custom/wordlist.txt"

    def test_validate_missing_target(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({})
        assert valid is False
        assert error == "Target URL is required"

    def test_validate_empty_target(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({"target": ""})
        assert valid is False
        assert error == "Target URL is required"

    def test_validate_invalid_url_no_scheme(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({"target": "example.com"})
        assert valid is False
        assert "must be a valid URL" in error

    def test_validate_valid_http(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({"target": "http://example.com"})
        assert valid is True
        assert error is None

    def test_validate_valid_https(self):
        scanner = GobusterScanner()
        valid, error = scanner.validate_parameters({"target": "https://example.com"})
        assert valid is True
        assert error is None

    def test_parse_output_single_line(self):
        scanner = GobusterScanner()
        output = "/admin (Status: 200) [Size: 1234]\n"
        result = scanner._parse_output(output, "http://example.com")
        assert len(result.found_paths) == 1
        assert result.found_paths[0]["path"] == "/admin"
        assert result.found_paths[0]["status"] == 200
        assert result.found_paths[0]["url"] == "http://example.com/admin"

    def test_parse_output_multiple_lines(self):
        scanner = GobusterScanner()
        output = "/admin (Status: 200) [Size: 1234]\n/login (Status: 301) [Size: 567]\n/hidden (Status: 403) [Size: 89]\n"
        result = scanner._parse_output(output, "http://example.com")
        assert len(result.found_paths) == 3
        assert result.status_codes == {200: 1, 301: 1, 403: 1}

    def test_parse_output_empty(self):
        scanner = GobusterScanner()
        result = scanner._parse_output("", "http://example.com")
        assert result.found_paths == []
        assert result.status_codes == {}
        assert result.total_requests == 0

    def test_parse_output_malformed_lines_skipped(self):
        scanner = GobusterScanner()
        output = "not a path line\n/admin (Status: 200) [Size: 1234]\nrandom noise\n"
        result = scanner._parse_output(output, "http://example.com")
        assert len(result.found_paths) == 1

    def test_build_command_defaults(self):
        scanner = GobusterScanner()
        cmd = scanner._build_command("http://example.com", {})
        assert scanner.tool_path in cmd
        assert "dir" in cmd
        assert "-u" in cmd
        assert "http://example.com" in cmd
        assert "-w" in cmd
        assert scanner.default_wordlist in cmd
        assert "-t" in cmd
        assert "10" in cmd

    def test_build_command_with_extensions(self):
        scanner = GobusterScanner()
        cmd = scanner._build_command("http://example.com", {"extensions": "php,txt,html"})
        cmd_str = " ".join(cmd)
        assert "-x" in cmd_str
        assert "php,txt,html" in cmd_str

    def test_build_command_custom_threads(self):
        scanner = GobusterScanner()
        cmd = scanner._build_command("http://example.com", {"threads": 25})
        cmd_str = " ".join(cmd)
        assert "25" in cmd_str

    @patch("tools.gobuster_integration.subprocess.run")
    def test_find_gobuster_found(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.strip.return_value = "/usr/bin/gobuster"
        mock_run.return_value = mock_result
        scanner = GobusterScanner()
        assert scanner.tool_path == "/usr/bin/gobuster"

    @patch("tools.gobuster_integration.subprocess.run")
    def test_find_gobuster_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        scanner = GobusterScanner()
        assert scanner.tool_path == "gobuster"

    @pytest.mark.asyncio
    @patch("tools.gobuster_integration.asyncio.create_subprocess_exec")
    async def test_execute_success(self, mock_create_subprocess):
        scanner = GobusterScanner(timeout=300)
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"/admin (Status: 200) [Size: 1234]\n",
            b"",
        )
        mock_create_subprocess.return_value = mock_process

        result = await scanner.execute({"target": "http://example.com"})
        assert result.success is True
        assert len(result.found_paths) == 1
        assert result.found_paths[0]["path"] == "/admin"

    @pytest.mark.asyncio
    async def test_execute_validation_failure(self):
        scanner = GobusterScanner()
        result = await scanner.execute({})
        assert result.success is False
        assert result.error_message == "Target URL is required"

    @pytest.mark.asyncio
    @patch("tools.gobuster_integration.asyncio.create_subprocess_exec")
    async def test_execute_timeout(self, mock_create_subprocess):
        scanner = GobusterScanner(timeout=1)
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_create_subprocess.return_value = mock_process

        result = await scanner.execute({"target": "http://example.com"})
        assert result.success is False
        assert result.error_message == "Scan timed out"

    @pytest.mark.asyncio
    @patch("tools.gobuster_integration.asyncio.create_subprocess_exec")
    async def test_execute_exception(self, mock_create_subprocess):
        scanner = GobusterScanner()
        mock_create_subprocess.side_effect = RuntimeError("Process crashed")

        result = await scanner.execute({"target": "http://example.com"})
        assert result.success is False
        assert "Process crashed" in result.error_message


class TestGobusterTool:
    def test_init(self):
        tool = GobusterTool()
        assert tool.name == "gobuster"
        assert tool.description == "Directory and file brute-forcing"
        assert tool.version == "1.0.0"

    def test_get_parameters(self):
        tool = GobusterTool()
        params = tool.get_parameters()
        assert "target" in params
        assert params["target"]["required"] is True
        assert params["target"]["type"] == "string"
        assert "wordlist" in params
        assert "threads" in params
        assert "extensions" in params
        assert params["threads"]["default"] == 10
        assert params["threads"]["minimum"] == 1
        assert params["threads"]["maximum"] == 50

    @pytest.mark.asyncio
    async def test_run_success(self):
        tool = GobusterTool()

        async def fake_execute(self, params):
            return GobusterResult(
                target="http://example.com",
                found_paths=[{"path": "/admin", "status": 200, "url": "http://example.com/admin"}],
                status_codes={200: 1},
                total_requests=1,
                duration=1.5,
                success=True,
            )

        with patch.object(GobusterScanner, "execute", new=fake_execute):
            result = await tool.run({"target": "http://example.com"})
            assert result["success"] is True
            assert len(result["found_paths"]) == 1
            assert result["error"] is None

    def test_registry_contains_gobuster(self):
        assert "gobuster" in TOOL_REGISTRY
        assert TOOL_REGISTRY["gobuster"] == GobusterTool

"""Tests for TruffleHog Integration Module

This module contains comprehensive tests for the trufflehog_integration module,
including unit tests with mocked subprocess calls.
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

# Import the module under test
from tools.trufflehog_integration import (
    TruffleHogFinding,
    TruffleHogResult,
    TruffleHogScanner,
    trufflehog_scan_git,
    trufflehog_scan_local_repo,
    trufflehog_scan_path,
)

# Sample TruffleHog JSON output for testing
SAMPLE_TRUFFLEHOG_OUTPUT = """\
{"SourceMetadata":{"Data":{"Git":{"commit":"abc123","file":"config.py",\
"email":"test@example.com","repository":"https://github.com/test/repo",\
"timestamp":"2023-01-01T00:00:00Z","line":10}}},"SourceID":0,"SourceType":15,\
"SourceName":"trufflehog - git","DetectorType":17,"DetectorName":"AWS",\
"DecoderName":"PLAIN","Verified":true,"Raw":"AKIAIOSFODNN7EXAMPLE",\
"Redacted":"AKIAIOSFODNN7EXAMPLE","ExtraData":null,"StructuredData":null}
{"SourceMetadata":{"Data":{"Git":{"commit":"def456","file":".env",\
"email":"dev@example.com","repository":"https://github.com/test/repo",\
"timestamp":"2023-01-02T00:00:00Z","line":5}}},"SourceID":1,"SourceType":15,\
"SourceName":"trufflehog - git","DetectorType":1,"DetectorName":"GitHub",\
"DecoderName":"PLAIN","Verified":false,"Raw":"ghp_xxxxxxxxxxxxxxxxxxxx",\
"Redacted":"ghp_xxxxxxxx...","ExtraData":null,"StructuredData":null}
"""

SAMPLE_FILESYSTEM_OUTPUT = """\
{"SourceMetadata":{"Data":{"Filesystem":{"file":"/path/to/secrets.txt",\
"line":1}}},"SourceID":0,"SourceType":0,"SourceName":"trufflehog - filesystem",\
"DetectorType":17,"DetectorName":"AWS","DecoderName":"PLAIN","Verified":false,\
"Raw":"AKIAIOSFODNN7EXAMPLE","Redacted":"AKIAIOSFODNN7EXAMPLE",\
"ExtraData":null,"StructuredData":null}
"""


class TestTruffleHogScannerInit:
    """Test TruffleHogScanner initialization"""

    @patch("shutil.which")
    def test_init_default(self, mock_which):
        """Test initialization with defaults"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner.verified_only is False
        assert scanner.custom_regexes == {}
        assert scanner.exclude_paths == []
        assert scanner.max_depth == 0

    @patch("shutil.which")
    def test_init_with_options(self, mock_which):
        """Test initialization with custom options"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner(
            verified_only=True,
            custom_regexes={"custom_key": "CUSTOM_[A-Z]+"},
            exclude_paths=["node_modules", "vendor"],
            max_depth=100,
            since_commit="abc123",
            branch="main",
        )
        assert scanner.verified_only is True
        assert scanner.custom_regexes == {"custom_key": "CUSTOM_[A-Z]+"}
        assert scanner.exclude_paths == ["node_modules", "vendor"]
        assert scanner.max_depth == 100
        assert scanner.since_commit == "abc123"
        assert scanner.branch == "main"

    @patch("shutil.which")
    def test_init_trufflehog_not_found(self, mock_which):
        """Test error when trufflehog is not found"""
        mock_which.return_value = None
        with pytest.raises(RuntimeError) as exc_info:
            TruffleHogScanner(trufflehog_path="nonexistent")
        assert "trufflehog not found" in str(exc_info.value)


class TestTruffleHogFinding:
    """Test TruffleHogFinding dataclass"""

    def test_finding_creation(self):
        """Test creating TruffleHogFinding object"""
        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="AKIAIOSFODNN7EXAMPLE",
            redacted="AKIAIOSFODNN7EXAMPLE",
            source="git",
            source_metadata={"commit": "abc123", "file": "config.py"},
            severity="critical",
            confidence="high",
        )
        assert finding.detector_name == "AWS"
        assert finding.verified is True
        assert finding.severity == "critical"

    def test_finding_default_values(self):
        """Test TruffleHogFinding with default values"""
        finding = TruffleHogFinding(
            detector_name="GitHub",
            detector_type="1",
            verified=False,
            raw="secret",
            redacted="secret...",
            source="filesystem",
        )
        assert finding.severity == "high"  # Default
        assert finding.confidence == "high"  # Default
        assert finding.source_metadata == {}


class TestTruffleHogResult:
    """Test TruffleHogResult dataclass"""

    def test_result_success(self):
        """Test successful result"""
        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="secret",
            redacted="secret",
            source="git",
        )
        result = TruffleHogResult(
            success=True,
            target="https://github.com/test/repo",
            scan_type="git",
            findings=[finding],
            scan_time=15.5,
        )
        assert result.success is True
        assert len(result.findings) == 1
        assert result.verified_only is False

    def test_result_failure(self):
        """Test failed result"""
        result = TruffleHogResult(
            success=False,
            target="/path/to/code",
            scan_type="filesystem",
            error="Path does not exist",
            scan_time=0.0,
        )
        assert result.success is False
        assert result.error == "Path does not exist"


class TestSeverityClassification:
    """Test severity classification"""

    @patch("shutil.which")
    def test_classify_aws_severity(self, mock_which):
        """Test AWS detector severity classification"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner._classify_severity("AWS", True) == "critical"
        assert scanner._classify_severity("AWS", False) == "critical"

    @patch("shutil.which")
    def test_classify_github_severity(self, mock_which):
        """Test GitHub detector severity classification"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner._classify_severity("GitHub", True) == "critical"
        assert scanner._classify_severity("GitHub", False) == "critical"

    @patch("shutil.which")
    def test_classify_private_key_severity(self, mock_which):
        """Test PrivateKey detector severity classification"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner._classify_severity("PrivateKey", False) == "critical"

    @patch("shutil.which")
    def test_classify_verified_upgrade(self, mock_which):
        """Test that verified secrets upgrade severity"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        # Medium severity detector becomes high when verified
        assert scanner._classify_severity("GenericApiKey", True) == "high"

    @patch("shutil.which")
    def test_classify_unknown_detector(self, mock_which):
        """Test unknown detector defaults to medium"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner._classify_severity("UnknownDetector", False) == "medium"

    @patch("shutil.which")
    def test_classify_password_detector(self, mock_which):
        """Test Password detector severity"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        assert scanner._classify_severity("Password", False) == "low"


class TestJSONParsing:
    """Test JSON output parsing"""

    @patch("shutil.which")
    def test_parse_git_output(self, mock_which):
        """Test parsing git scan JSON output"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        findings = scanner._parse_json_output(SAMPLE_TRUFFLEHOG_OUTPUT, "git")

        assert len(findings) == 2
        assert findings[0].detector_name == "AWS"
        assert findings[0].verified is True
        assert findings[1].detector_name == "GitHub"
        assert findings[1].verified is False

    @patch("shutil.which")
    def test_parse_filesystem_output(self, mock_which):
        """Test parsing filesystem scan JSON output"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        findings = scanner._parse_json_output(
            SAMPLE_FILESYSTEM_OUTPUT, "filesystem"
        )

        assert len(findings) == 1
        assert findings[0].source == "filesystem"

    @patch("shutil.which")
    def test_parse_empty_output(self, mock_which):
        """Test parsing empty output"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        findings = scanner._parse_json_output("", "git")
        assert len(findings) == 0

    @patch("shutil.which")
    def test_parse_malformed_json(self, mock_which):
        """Test parsing malformed JSON"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        malformed = '{"invalid": json}\n{"valid": "json"}'
        findings = scanner._parse_json_output(malformed, "git")
        # Should handle gracefully and skip invalid lines
        assert isinstance(findings, list)

    @patch("shutil.which")
    def test_parse_with_source_metadata(self, mock_which):
        """Test parsing with source metadata extraction"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        findings = scanner._parse_json_output(SAMPLE_TRUFFLEHOG_OUTPUT, "git")

        # Verify source metadata is parsed from Git data
        assert (
            "Git" in findings[0].source_metadata
            or "Data" in findings[0].source_metadata
        )
        # The metadata should contain git-related info
        metadata = findings[0].source_metadata
        if "Git" in metadata:
            git_data = metadata["Git"]
            assert git_data.get("commit") == "abc123"
            assert git_data.get("file") == "config.py"


class TestCommandBuilding:
    """Test command building"""

    @patch("shutil.which")
    def test_build_git_command_basic(self, mock_which):
        """Test basic git command building"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()
        cmd = scanner._build_git_command("https://github.com/test/repo")

        assert cmd[0] == "/usr/bin/trufflehog"
        assert "git" in cmd
        assert "https://github.com/test/repo" in cmd
        assert "--json" in cmd

    @patch("shutil.which")
    def test_build_git_command_verified_only(self, mock_which):
        """Test git command with verified only flag"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner(verified_only=True)
        cmd = scanner._build_git_command("https://github.com/test/repo")

        assert "--only-verified" in cmd

    @patch("shutil.which")
    def test_build_git_command_with_depth(self, mock_which):
        """Test git command with max depth"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner(max_depth=100)
        cmd = scanner._build_git_command("https://github.com/test/repo")

        assert "--max-depth" in cmd
        assert "100" in cmd

    @patch("shutil.which")
    def test_build_git_command_with_since_commit(self, mock_which):
        """Test git command with since commit"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner(since_commit="abc123")
        cmd = scanner._build_git_command("https://github.com/test/repo")

        assert "--since-commit" in cmd
        assert "abc123" in cmd

    @patch("shutil.which")
    def test_build_filesystem_command(self, mock_which):
        """Test filesystem command building"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner(exclude_paths=["node_modules"])
        cmd = scanner._build_filesystem_command("/path/to/code")

        assert "filesystem" in cmd
        assert "/path/to/code" in cmd
        assert "--exclude-paths" in cmd
        assert "node_modules" in cmd


class TestAsyncScanning:
    """Test async scanning functionality"""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_git_success(self, mock_which):
        """Test successful git scan"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        mock_result = Mock()
        mock_result.stdout = SAMPLE_TRUFFLEHOG_OUTPUT
        mock_result.stderr = ""

        with patch.object(
            scanner, "_run_subprocess", return_value=mock_result
        ):
            result = await scanner.scan_git("https://github.com/test/repo")

            assert result.success is True
            assert result.scan_type == "git"
            assert len(result.findings) == 2

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_git_timeout(self, mock_which):
        """Test git scan timeout handling"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        with patch.object(
            scanner, "_run_subprocess", side_effect=asyncio.TimeoutError
        ):
            result = await scanner.scan_git(
                "https://github.com/test/repo", timeout=1
            )

            assert result.success is False
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_filesystem_success(self, mock_which):
        """Test successful filesystem scan"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        mock_result = Mock()
        mock_result.stdout = SAMPLE_FILESYSTEM_OUTPUT
        mock_result.stderr = ""

        with patch.object(
            scanner, "_run_subprocess", return_value=mock_result
        ):
            with patch("pathlib.Path.exists", return_value=True):
                result = await scanner.scan_filesystem("/path/to/code")

                assert result.success is True
                assert result.scan_type == "filesystem"

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_filesystem_nonexistent_path(self, mock_which):
        """Test filesystem scan with nonexistent path"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        with patch("pathlib.Path.exists", return_value=False):
            result = await scanner.scan_filesystem("/nonexistent/path")

            assert result.success is False
            assert "does not exist" in result.error


class TestOutputParsing:
    """Test output parsing methods"""

    @patch("shutil.which")
    def test_parse_output(self, mock_which):
        """Test parse_output method"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="AKIAIOSFODNN7EXAMPLE",
            redacted="AKIAIOSFODNN7EXAMPLE",
            source="git",
            source_metadata={"commit": "abc123", "file": "config.py"},
            severity="critical",
        )
        result = TruffleHogResult(
            success=True,
            target="https://github.com/test/repo",
            scan_type="git",
            findings=[finding],
        )

        parsed = scanner.parse_output(result)

        assert len(parsed) == 1
        assert parsed[0]["tool"] == "trufflehog"
        assert parsed[0]["detector"] == "AWS"
        assert parsed[0]["verified"] is True
        assert parsed[0]["severity"] == "critical"

    @patch("shutil.which")
    def test_normalize_findings(self, mock_which):
        """Test normalize_findings method"""
        mock_which.return_value = "/usr/bin/trufflehog"
        scanner = TruffleHogScanner()

        findings = [
            {
                "tool": "trufflehog",
                "detector": "AWS",
                "type": "17",
                "severity": "critical",
                "verified": True,
                "source": "git",
                "source_metadata": {"commit": "abc123", "file": "config.py"},
                "redacted_secret": "AKIAIOS...",
            }
        ]

        normalized = scanner.normalize_findings(findings)

        assert len(normalized) == 1
        assert normalized[0]["tool"] == "trufflehog"
        assert normalized[0]["severity"] == "critical"
        assert "Secret Found: AWS" in normalized[0]["title"]
        assert "VERIFIED" in normalized[0]["description"]


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    @patch("asyncio.run")
    def test_trufflehog_scan_git_tool(self, mock_run):
        """Test trufflehog_scan_git tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "https://github.com/test/repo"
        mock_result.scan_time = 10.0
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = trufflehog_scan_git("https://github.com/test/repo")
        assert isinstance(result, str)
        assert "completed" in result.lower() or "Repository" in result

    @patch("asyncio.run")
    def test_trufflehog_scan_path_tool(self, mock_run):
        """Test trufflehog_scan_path tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "/path/to/code"
        mock_result.scan_time = 5.0
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = trufflehog_scan_path("/path/to/code")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_trufflehog_scan_local_repo_tool(self, mock_run):
        """Test trufflehog_scan_local_repo tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "/path/to/repo"
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = trufflehog_scan_local_repo("/path/to/repo")
        assert isinstance(result, str)


class TestVersion:
    """Test version retrieval"""

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_get_version_success(self, mock_run, mock_which):
        """Test successful version retrieval"""
        mock_which.return_value = "/usr/bin/trufflehog"
        mock_run.return_value = Mock(returncode=0, stdout="3.0.0\n", stderr="")

        scanner = TruffleHogScanner()
        version = scanner.get_version()
        assert version == "3.0.0"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_get_version_failure(self, mock_run, mock_which):
        """Test version retrieval failure"""
        mock_which.return_value = "/usr/bin/trufflehog"
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")

        scanner = TruffleHogScanner()
        version = scanner.get_version()
        assert version == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

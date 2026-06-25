"""Comprehensive unit tests for TruffleHog Integration Module.

Target: 95%+ coverage of tools/trufflehog_integration.py with all
external calls mocked (subprocess, filesystem, registry, langchain).
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# The module under test imports langchain_core.tools if available and tries
# to import .tool_registry.  Both are already resolved by conftest import
# health check; the module-level auto-registration has already run.
from tools import trufflehog_integration as th_mod
from tools.trufflehog_integration import (
    LANGCHAIN_AVAILABLE,
    TOOL_REGISTRY_AVAILABLE,
    TruffleHogFinding,
    TruffleHogResult,
    TruffleHogScanner,
    register_trufflehog_tools,
    trufflehog_scan,
    trufflehog_scan_git,
    trufflehog_scan_local_repo,
    trufflehog_scan_path,
)

# ============================================================================
# Constants / fixtures
# ============================================================================

VALID_TRUFFLEHOG_PATH = "/usr/local/bin/trufflehog"


@pytest.fixture(autouse=True)
def _patch_shutil_which():
    """Ensure every test sees a valid trufflehog binary."""
    with patch("tools.trufflehog_integration.shutil.which", return_value=VALID_TRUFFLEHOG_PATH):
        yield


@pytest.fixture
def scanner() -> TruffleHogScanner:
    """Return a default scanner with a validated mock path."""
    return TruffleHogScanner()


# Sample JSON outputs mimicking real TruffleHog output (JSON-lines).
SAMPLE_GIT_OUTPUT = """\
{"SourceMetadata":{"Data":{"Git":{"commit":"abc123","file":"config.py","email":"test@example.com","repository":"https://github.com/test/repo","timestamp":"2023-01-01T00:00:00Z","line":10}}},"SourceID":0,"SourceType":15,"SourceName":"trufflehog - git","DetectorType":17,"DetectorName":"AWS","DecoderName":"PLAIN","Verified":true,"Raw":"AKIAIOSFODNN7EXAMPLE","Redacted":"AKIAIOSFODNN7EXAMPLE","ExtraData":null,"StructuredData":null}
{"SourceMetadata":{"Data":{"Git":{"commit":"def456","file":".env","email":"dev@example.com","repository":"https://github.com/test/repo","timestamp":"2023-01-02T00:00:00Z","line":5}}},"SourceID":1,"SourceType":15,"SourceName":"trufflehog - git","DetectorType":1,"DetectorName":"GitHub","DecoderName":"PLAIN","Verified":false,"Raw":"ghp_xxxxxxxxxxxxxxxxxxxx","Redacted":"ghp_xxxxxxxx...","ExtraData":null,"StructuredData":null}
"""

SAMPLE_FILESYSTEM_OUTPUT = """\
{"SourceMetadata":{"Data":{"Filesystem":{"file":"/path/to/secrets.txt","line":1}}},"SourceID":0,"SourceType":0,"SourceName":"trufflehog - filesystem","DetectorType":17,"DetectorName":"AWS","DecoderName":"PLAIN","Verified":false,"Raw":"AKIAIOSFODNN7EXAMPLE","Redacted":"AKIAIOSFODNN7EXAMPLE","ExtraData":null,"StructuredData":null}
"""

SAMPLE_OUTPUT_NO_DATA_KEY = json.dumps(
    {
        "SourceMetadata": {"Filesystem": {"file": "/flat/meta.txt", "line": 42}},
        "DetectorName": "Password",
        "DetectorType": 999,
        "Verified": False,
        "Raw": "passw0rd",
        "Redacted": "pass...",
    }
)


# ============================================================================
# Dataclasses
# ============================================================================


class TestTruffleHogFinding:
    """TruffleHogFinding construction and defaults."""

    def test_all_fields_set(self):
        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="secret",
            redacted="s...",
            source="git",
            source_metadata={"commit": "abc"},
            severity="critical",
            confidence="high",
        )
        assert finding.detector_name == "AWS"
        assert finding.detector_type == "17"
        assert finding.verified is True
        assert finding.raw == "secret"
        assert finding.redacted == "s..."
        assert finding.source == "git"
        assert finding.source_metadata == {"commit": "abc"}
        assert finding.severity == "critical"
        assert finding.confidence == "high"

    def test_default_fields(self):
        finding = TruffleHogFinding(
            detector_name="GitHub",
            detector_type="1",
            verified=False,
            raw="x",
            redacted="x",
            source="filesystem",
        )
        assert finding.source_metadata == {}
        assert finding.severity == "high"
        assert finding.confidence == "high"

    def test_dataclass_fields_complete(self):
        names = {f.name for f in fields(TruffleHogFinding)}
        expected = {
            "detector_name",
            "detector_type",
            "verified",
            "raw",
            "redacted",
            "source",
            "source_metadata",
            "severity",
            "confidence",
        }
        assert names == expected


class TestTruffleHogResult:
    """TruffleHogResult construction and defaults."""

    def test_success_result_defaults(self):
        result = TruffleHogResult(success=True, target="repo", scan_type="git")
        assert result.findings == []
        assert result.scan_time == 0.0
        assert result.error is None
        assert result.raw_output == ""
        assert result.verified_only is False

    def test_failure_result(self):
        result = TruffleHogResult(
            success=False,
            target="/bad",
            scan_type="filesystem",
            error="Path does not exist",
        )
        assert result.success is False
        assert result.error == "Path does not exist"

    def test_with_findings(self):
        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="r",
            redacted="r",
            source="git",
        )
        result = TruffleHogResult(
            success=True,
            target="repo",
            scan_type="git",
            findings=[finding],
            scan_time=12.34,
            raw_output=SAMPLE_GIT_OUTPUT,
            verified_only=True,
        )
        assert len(result.findings) == 1
        assert result.scan_time == pytest.approx(12.34)
        assert result.verified_only is True


# ============================================================================
# Scanner initialization and installation validation
# ============================================================================


class TestTruffleHogScannerInit:
    """TruffleHogScanner.__init__ and _validate_installation coverage."""

    def test_init_defaults(self):
        scanner = TruffleHogScanner()
        assert scanner.trufflehog_path == VALID_TRUFFLEHOG_PATH
        assert scanner.verified_only is False
        assert scanner.custom_regexes == {}
        assert scanner.exclude_paths == []
        assert scanner.include_paths == []
        assert scanner.max_depth == 0
        assert scanner.since_commit is None
        assert scanner.branch is None

    def test_init_all_options(self):
        scanner = TruffleHogScanner(
            trufflehog_path="/custom/trufflehog",
            verified_only=True,
            custom_regexes={"RGX": "[A-Z]+"},
            exclude_paths=["node_modules"],
            include_paths=["src"],
            max_depth=50,
            since_commit="deadbeef",
            branch="develop",
        )
        assert scanner.trufflehog_path == VALID_TRUFFLEHOG_PATH
        assert scanner.verified_only is True
        assert scanner.custom_regexes == {"RGX": "[A-Z]+"}
        assert scanner.exclude_paths == ["node_modules"]
        assert scanner.include_paths == ["src"]
        assert scanner.max_depth == 50
        assert scanner.since_commit == "deadbeef"
        assert scanner.branch == "develop"

    def test_validate_installation_not_found(self):
        with patch("tools.trufflehog_integration.shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="trufflehog not found"):
                TruffleHogScanner(trufflehog_path="missing")


# ============================================================================
# Version retrieval
# ============================================================================


class TestGetVersion:
    """TruffleHogScanner._get_version / get_version."""

    def test_get_version_success(self, scanner):
        mock_proc = Mock(returncode=0, stdout="3.82.0\n", stderr="")
        with patch("tools.trufflehog_integration.subprocess.run", return_value=mock_proc):
            assert scanner.get_version() == "3.82.0"

    def test_get_version_non_zero_exit(self, scanner):
        mock_proc = Mock(returncode=1, stdout="", stderr="boom")
        with patch("tools.trufflehog_integration.subprocess.run", return_value=mock_proc):
            assert scanner.get_version() == "unknown"

    def test_get_version_exception(self, scanner):
        with patch("tools.trufflehog_integration.subprocess.run", side_effect=OSError("no exec")):
            assert scanner.get_version() == "unknown"

    def test_get_version_delegates(self, scanner):
        with patch.object(scanner, "_get_version", return_value="1.2.3"):
            assert scanner.get_version() == "1.2.3"


# ============================================================================
# Severity map & classification
# ============================================================================


class TestSeverityMap:
    """The SEVERITY_MAP contents and classification logic."""

    def test_severity_map_has_expected_keys(self):
        sm = TruffleHogScanner.SEVERITY_MAP
        assert sm["AWS"] == "critical"
        assert sm["GitHub"] == "critical"
        assert sm["PrivateKey"] == "critical"
        assert sm["Heroku"] == "high"
        assert sm["GenericApiKey"] == "high"
        assert sm["Mailgun"] == "medium"
        assert sm["Password"] == "low"
        assert sm["Url"] == "info"

    def test_classify_exact_match(self, scanner):
        assert scanner._classify_severity("AWS", False) == "critical"
        assert scanner._classify_severity("Password", False) == "low"
        assert scanner._classify_severity("Url", False) == "info"

    def test_classify_partial_match(self, scanner):
        # "MyAWSKey" contains "AWS" -> critical
        assert scanner._classify_severity("MyAWSKey", False) == "critical"
        # "CustomPasswordDetector" contains "Password" -> low
        assert scanner._classify_severity("CustomPasswordDetector", False) == "low"

    def test_classify_unknown_defaults_medium(self, scanner):
        assert scanner._classify_severity("TotallyUnknownDetector", False) == "medium"

    def test_classify_verified_upgrades_medium_to_high(self, scanner):
        assert scanner._classify_severity("Mailgun", False) == "medium"
        assert scanner._classify_severity("Mailgun", True) == "high"

    def test_classify_verified_upgrades_low_to_high(self, scanner):
        assert scanner._classify_severity("Password", False) == "low"
        assert scanner._classify_severity("Password", True) == "high"

    def test_classify_verified_does_not_change_critical(self, scanner):
        assert scanner._classify_severity("AWS", True) == "critical"

    def test_classify_verified_does_not_change_info(self, scanner):
        # info is not in [medium, low] so stays info even when verified
        assert scanner._classify_severity("Url", True) == "info"

    def test_classify_case_insensitive_partial_match(self, scanner):
        assert scanner._classify_severity("myawskey", False) == "critical"
        assert scanner._classify_severity("GITHUB_APP", False) == "critical"


# ============================================================================
# Command building
# ============================================================================


class TestCommandBuilding:
    """TruffleHogScanner._build_git_command and _build_filesystem_command."""

    def test_build_git_command_basic(self, scanner):
        cmd = scanner._build_git_command("https://github.com/test/repo")
        assert cmd == [VALID_TRUFFLEHOG_PATH, "git", "https://github.com/test/repo", "--json"]

    def test_build_git_command_verified_only(self):
        scanner = TruffleHogScanner(verified_only=True)
        cmd = scanner._build_git_command("https://github.com/test/repo")
        assert "--only-verified" in cmd

    def test_build_git_command_max_depth(self):
        scanner = TruffleHogScanner(max_depth=100)
        cmd = scanner._build_git_command("https://github.com/test/repo")
        assert "--max-depth" in cmd
        assert cmd[cmd.index("--max-depth") + 1] == "100"

    def test_build_git_command_since_commit(self):
        scanner = TruffleHogScanner(since_commit="abc123")
        cmd = scanner._build_git_command("https://github.com/test/repo")
        assert "--since-commit" in cmd
        assert cmd[cmd.index("--since-commit") + 1] == "abc123"

    def test_build_git_command_branch(self):
        scanner = TruffleHogScanner(branch="main")
        cmd = scanner._build_git_command("https://github.com/test/repo")
        assert "--branch" in cmd
        assert cmd[cmd.index("--branch") + 1] == "main"

    def test_build_git_command_excludes(self):
        scanner = TruffleHogScanner(exclude_paths=["vendor", "node_modules"])
        cmd = scanner._build_git_command("https://github.com/test/repo")
        # Each exclude path gets a --exclude-paths flag
        idxs = [i for i, v in enumerate(cmd) if v == "--exclude-paths"]
        assert len(idxs) == 2
        assert cmd[idxs[0] + 1] == "vendor"
        assert cmd[idxs[1] + 1] == "node_modules"

    def test_build_filesystem_command_basic(self, scanner):
        cmd = scanner._build_filesystem_command("/path/to/code")
        assert cmd == [VALID_TRUFFLEHOG_PATH, "filesystem", "/path/to/code", "--json"]

    def test_build_filesystem_command_verified_only(self):
        scanner = TruffleHogScanner(verified_only=True)
        cmd = scanner._build_filesystem_command("/path/to/code")
        assert "--only-verified" in cmd

    def test_build_filesystem_command_excludes(self):
        scanner = TruffleHogScanner(exclude_paths=["dist"])
        cmd = scanner._build_filesystem_command("/path/to/code")
        assert "--exclude-paths" in cmd
        assert cmd[cmd.index("--exclude-paths") + 1] == "dist"

    def test_build_filesystem_command_logs_custom_regexes(self, scanner, caplog):
        scanner.custom_regexes = {"KEY": "[A-Z]+"}
        with caplog.at_level("INFO", logger="tools.trufflehog_integration"):
            scanner._build_filesystem_command("/path/to/code")
        assert "Custom regexes configured" in caplog.text
        assert "KEY" in caplog.text


# ============================================================================
# JSON output parsing
# ============================================================================


class TestJSONParsing:
    """TruffleHogScanner._parse_json_output."""

    def test_parse_git_findings(self, scanner):
        findings = scanner._parse_json_output(SAMPLE_GIT_OUTPUT, "git")
        assert len(findings) == 2
        assert findings[0].detector_name == "AWS"
        assert findings[0].verified is True
        assert findings[0].severity == "critical"
        assert findings[0].confidence == "high"
        assert findings[0].source == "git"

        assert findings[1].detector_name == "GitHub"
        assert findings[1].verified is False
        assert findings[1].severity == "critical"
        assert findings[1].confidence == "medium"

    def test_parse_filesystem_findings(self, scanner):
        findings = scanner._parse_json_output(SAMPLE_FILESYSTEM_OUTPUT, "filesystem")
        assert len(findings) == 1
        assert findings[0].source == "filesystem"
        assert findings[0].verified is False

    def test_parse_empty_output(self, scanner):
        assert scanner._parse_json_output("", "git") == []
        assert scanner._parse_json_output("   \n  \n", "git") == []

    def test_parse_malformed_json_skipped(self, scanner, caplog):
        bad = '{"bad": json}\n{"DetectorName":"AWS","DetectorType":1,"Verified":false,"Raw":"x","Redacted":"x"}'
        with caplog.at_level("WARNING", logger="tools.trufflehog_integration"):
            findings = scanner._parse_json_output(bad, "git")
        assert len(findings) == 1
        assert findings[0].detector_name == "AWS"
        assert "Failed to parse JSON line" in caplog.text

    def test_parse_source_metadata_with_data_key(self, scanner):
        findings = scanner._parse_json_output(SAMPLE_GIT_OUTPUT, "git")
        meta = findings[0].source_metadata
        # The Git data is under SourceMetadata.Data, so it gets unwrapped
        assert "Git" in meta
        assert meta["Git"]["commit"] == "abc123"

    def test_parse_source_metadata_without_data_key(self, scanner):
        findings = scanner._parse_json_output(SAMPLE_OUTPUT_NO_DATA_KEY, "filesystem")
        assert len(findings) == 1
        meta = findings[0].source_metadata
        assert "Filesystem" in meta
        assert meta["Filesystem"]["file"] == "/flat/meta.txt"

    def test_parse_missing_fields_use_defaults(self, scanner):
        minimal = json.dumps({"Verified": True})
        findings = scanner._parse_json_output(minimal, "git")
        assert len(findings) == 1
        assert findings[0].detector_name == "Unknown"
        assert findings[0].detector_type == "Unknown"
        assert findings[0].verified is True
        assert findings[0].raw == ""
        assert findings[0].redacted == ""


# ============================================================================
# Async scanning methods
# ============================================================================


@pytest.mark.asyncio
class TestScanGit:
    """TruffleHogScanner.scan_git."""

    async def test_scan_git_success(self, scanner):
        mock_proc = Mock(stdout=SAMPLE_GIT_OUTPUT, stderr="")
        with patch.object(scanner, "_run_subprocess", return_value=mock_proc):
            result = await scanner.scan_git("https://github.com/test/repo")
        assert result.success is True
        assert result.target == "https://github.com/test/repo"
        assert result.scan_type == "git"
        assert len(result.findings) == 2
        assert result.raw_output == SAMPLE_GIT_OUTPUT
        assert result.verified_only is False
        assert result.scan_time >= 0.0

    async def test_scan_git_timeout(self, scanner):
        with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
            result = await scanner.scan_git("https://github.com/test/repo", timeout=1)
        assert result.success is False
        assert "timed out" in result.error.lower()
        assert result.scan_time >= 0.0

    async def test_scan_git_generic_exception(self, scanner):
        with patch.object(scanner, "_run_subprocess", side_effect=RuntimeError("boom")):
            result = await scanner.scan_git("https://github.com/test/repo")
        assert result.success is False
        assert result.error == "boom"

    async def test_scan_git_verified_only_flagged(self):
        scanner = TruffleHogScanner(verified_only=True)
        mock_proc = Mock(stdout=SAMPLE_GIT_OUTPUT, stderr="")
        with patch.object(scanner, "_run_subprocess", return_value=mock_proc):
            result = await scanner.scan_git("https://github.com/test/repo")
        assert result.verified_only is True


@pytest.mark.asyncio
class TestScanFilesystem:
    """TruffleHogScanner.scan_filesystem."""

    async def test_scan_filesystem_success(self, scanner):
        mock_proc = Mock(stdout=SAMPLE_FILESYSTEM_OUTPUT, stderr="")
        with patch.object(scanner, "_run_subprocess", return_value=mock_proc):
            with patch.object(Path, "exists", return_value=True):
                result = await scanner.scan_filesystem("/path/to/code")
        assert result.success is True
        assert result.scan_type == "filesystem"
        assert len(result.findings) == 1

    async def test_scan_filesystem_path_does_not_exist(self, scanner):
        with patch.object(Path, "exists", return_value=False):
            result = await scanner.scan_filesystem("/nonexistent/path")
        assert result.success is False
        assert "does not exist" in result.error
        assert result.verified_only is False

    async def test_scan_filesystem_timeout(self, scanner):
        with patch.object(Path, "exists", return_value=True):
            with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
                result = await scanner.scan_filesystem("/path/to/code", timeout=1)
        assert result.success is False
        assert "timed out" in result.error.lower()

    async def test_scan_filesystem_generic_exception(self, scanner):
        with patch.object(Path, "exists", return_value=True):
            with patch.object(scanner, "_run_subprocess", side_effect=ValueError("bad")):
                result = await scanner.scan_filesystem("/path/to/code")
        assert result.success is False
        assert result.error == "bad"

    async def test_scan_filesystem_verified_only(self):
        scanner = TruffleHogScanner(verified_only=True)
        mock_proc = Mock(stdout=SAMPLE_FILESYSTEM_OUTPUT, stderr="")
        with patch.object(scanner, "_run_subprocess", return_value=mock_proc):
            with patch.object(Path, "exists", return_value=True):
                result = await scanner.scan_filesystem("/path/to/code")
        assert result.verified_only is True


# ============================================================================
# Subprocess runner
# ============================================================================


class TestRunSubprocess:
    """TruffleHogScanner._run_subprocess."""

    def test_run_subprocess_calls_subprocess_run(self, scanner):
        mock_proc = Mock(stdout="out", stderr="err")
        with patch("tools.trufflehog_integration.subprocess.run", return_value=mock_proc) as mock_run:
            result = scanner._run_subprocess(["trufflehog", "git", "url", "--json"])
        mock_run.assert_called_once_with(["trufflehog", "git", "url", "--json"], capture_output=True, text=True)
        assert result == mock_proc


# ============================================================================
# Output helpers
# ============================================================================


class TestParseOutput:
    """TruffleHogScanner.parse_output."""

    def test_parse_output_complete_metadata(self, scanner):
        finding = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="raw",
            redacted="redacted",
            source="git",
            source_metadata={
                "File": "config.py",
                "Commit": "abc123",
                "Email": "test@example.com",
                "Timestamp": "2023-01-01T00:00:00Z",
            },
            severity="critical",
            confidence="high",
        )
        result = TruffleHogResult(success=True, target="repo", scan_type="git", findings=[finding])
        parsed = scanner.parse_output(result)
        assert len(parsed) == 1
        p = parsed[0]
        assert p["tool"] == "trufflehog"
        assert p["detector"] == "AWS"
        assert p["type"] == "17"
        assert p["severity"] == "critical"
        assert p["verified"] is True
        assert p["confidence"] == "high"
        assert p["source"] == "git"
        assert p["file"] == "config.py"
        assert p["commit"] == "abc123"
        assert p["email"] == "test@example.com"
        assert p["timestamp"] == "2023-01-01T00:00:00Z"
        assert p["redacted_secret"] == "redacted"

    def test_parse_output_empty_metadata(self, scanner):
        finding = TruffleHogFinding(
            detector_name="GitHub",
            detector_type="1",
            verified=False,
            raw="r",
            redacted="r",
            source="filesystem",
        )
        result = TruffleHogResult(success=True, target="/code", scan_type="filesystem", findings=[finding])
        parsed = scanner.parse_output(result)
        assert parsed[0]["file"] == ""
        assert parsed[0]["commit"] == ""


class TestNormalizeFindings:
    """TruffleHogScanner.normalize_findings."""

    def test_normalize_verified_finding(self, scanner):
        # normalize_findings consumes the dict format produced by parse_output,
        # where file/commit/timestamp are promoted to top-level keys.
        findings: List[Dict[str, Any]] = [
            {
                "tool": "trufflehog",
                "detector": "AWS",
                "type": "17",
                "severity": "critical",
                "verified": True,
                "confidence": "high",
                "source": "git",
                "source_metadata": {"File": "config.py", "Commit": "abc123", "Timestamp": "2023-01-01T00:00:00Z"},
                "redacted_secret": "AKIA...",
                "file": "config.py",
                "commit": "abc123",
                "timestamp": "2023-01-01T00:00:00Z",
            }
        ]
        norm = scanner.normalize_findings(findings)
        assert len(norm) == 1
        n = norm[0]
        assert n["tool"] == "trufflehog"
        assert n["target"] == "git"
        assert n["severity"] == "critical"
        assert n["title"] == "Secret Found: AWS"
        assert "VERIFIED" in n["description"]
        assert n["evidence"]["file"] == "config.py"
        assert n["evidence"]["commit"] == "abc123"
        assert n["evidence"]["timestamp"] == "2023-01-01T00:00:00Z"
        assert "remediation" in n
        assert "references" in n
        assert n["confidence"] == "high"
        assert n["verified"] is True

    def test_normalize_unverified_finding(self, scanner):
        findings: List[Dict[str, Any]] = [
            {
                "tool": "trufflehog",
                "detector": "Password",
                "type": "999",
                "severity": "low",
                "verified": False,
                "confidence": "medium",
                "source": "filesystem",
                "source_metadata": {},
                "redacted_secret": "pass...",
            }
        ]
        norm = scanner.normalize_findings(findings)
        assert "VERIFIED" not in norm[0]["description"]
        assert norm[0]["severity"] == "low"

    def test_normalize_no_optional_metadata(self, scanner):
        findings: List[Dict[str, Any]] = [
            {
                "tool": "trufflehog",
                "detector": "Generic",
                "severity": "medium",
                "verified": False,
                "source": "git",
                "redacted_secret": "xxx",
            }
        ]
        norm = scanner.normalize_findings(findings)
        evidence = norm[0]["evidence"]
        assert "file" not in evidence
        assert "commit" not in evidence
        assert "timestamp" not in evidence


# ============================================================================
# LangChain tool wrappers
# ============================================================================


class TestLangChainTools:
    """trufflehog_scan_git, trufflehog_scan_path, trufflehog_scan_local_repo."""

    @pytest.fixture(autouse=True)
    def _patch_shutil_for_tools(self):
        """The tool functions create new scanners; ensure they find a binary."""
        with patch("tools.trufflehog_integration.shutil.which", return_value=VALID_TRUFFLEHOG_PATH):
            yield

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_git_success_no_findings(self, mock_run):
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "https://github.com/test/repo"
        mock_result.scan_time = 1.23
        mock_result.findings = []
        mock_result.verified_only = False
        mock_run.return_value = mock_result

        result = trufflehog_scan_git("https://github.com/test/repo")
        assert isinstance(result, str)
        assert "TruffleHog Git Scan completed in 1.23s" in result
        assert "Repository: https://github.com/test/repo" in result
        assert "Secrets Found: 0" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_git_with_findings(self, mock_run):
        f1 = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="r",
            redacted="redacted",
            source="git",
            severity="critical",
        )
        f2 = TruffleHogFinding(
            detector_name="GitHub",
            detector_type="1",
            verified=False,
            raw="r",
            redacted="redacted2",
            source="git",
            severity="high",
        )
        f3 = TruffleHogFinding(
            detector_name="Mailgun",
            detector_type="2",
            verified=False,
            raw="r",
            redacted="redacted3",
            source="git",
            severity="medium",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "repo"
        mock_result.scan_time = 5.0
        mock_result.findings = [f1, f2, f3]
        mock_run.return_value = mock_result

        result = trufflehog_scan_git("repo")
        assert "CRITICAL Severity (1):" in result
        assert "HIGH Severity (1):" in result
        assert "MEDIUM Severity (1):" in result
        assert "AWS" in result
        assert "GitHub" in result
        assert "Mailgun" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_git_with_info_severity_ignored(self, mock_run):
        """Severity 'info' is not in severity_groups and should be skipped in output."""
        f1 = TruffleHogFinding(
            detector_name="Url",
            detector_type="99",
            verified=False,
            raw="r",
            redacted="http://example.com",
            source="git",
            severity="info",
        )
        f2 = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="r",
            redacted="r",
            source="git",
            severity="critical",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "repo"
        mock_result.scan_time = 1.0
        mock_result.findings = [f1, f2]
        mock_run.return_value = mock_result

        result = trufflehog_scan_git("repo")
        assert "CRITICAL Severity (1):" in result
        assert "Url" not in result
        assert "INFO" not in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_git_failure(self, mock_run):
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "something failed"
        mock_run.return_value = mock_result

        result = trufflehog_scan_git("bad_repo")
        assert "TruffleHog scan failed" in result
        assert "something failed" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_filesystem", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_path_success(self, mock_run):
        f1 = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="r",
            redacted="r",
            source="filesystem",
            severity="critical",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "/path/to/code"
        mock_result.scan_time = 2.0
        mock_result.findings = [f1]
        mock_run.return_value = mock_result

        result = trufflehog_scan_path("/path/to/code")
        assert "Filesystem Scan Results for /path/to/code" in result
        assert "Total Secrets: 1" in result
        assert "Verified: 1" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_filesystem", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_path_failure(self, mock_run):
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "no such path"
        mock_run.return_value = mock_result

        result = trufflehog_scan_path("/missing")
        assert "TruffleHog scan failed" in result
        assert "no such path" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_local_repo_success(self, mock_run):
        f1 = TruffleHogFinding(
            detector_name="AWS",
            detector_type="17",
            verified=True,
            raw="r",
            redacted="r",
            source="git",
            severity="critical",
        )
        f2 = TruffleHogFinding(
            detector_name="GitHub",
            detector_type="1",
            verified=False,
            raw="r",
            redacted="r",
            source="git",
            severity="high",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "/local/repo"
        mock_result.findings = [f1, f2]
        mock_run.return_value = mock_result

        result = trufflehog_scan_local_repo("/local/repo", since_commit="abc", branch="main")
        assert "Local Repository Scan Complete" in result
        assert "Path: /local/repo" in result
        assert "High/Critical Secrets: 2" in result
        assert "Total Secrets: 2" in result

    @patch("tools.trufflehog_integration.TruffleHogScanner.scan_git", new=Mock())
    @patch("asyncio.run")
    def test_trufflehog_scan_local_repo_failure(self, mock_run):
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "git error"
        mock_run.return_value = mock_result

        result = trufflehog_scan_local_repo("/local/repo")
        assert "Local repo scan failed" in result
        assert "git error" in result

    def test_trufflehog_scan_alias(self):
        assert trufflehog_scan is trufflehog_scan_git


# ============================================================================
# Tool registry integration
# ============================================================================


class TestToolRegistryIntegration:
    """register_trufflehog_tools and import fallbacks."""

    def test_register_success_when_available(self):
        mock_registry = Mock()
        with patch.multiple(
            th_mod,
            TOOL_REGISTRY_AVAILABLE=True,
            LANGCHAIN_AVAILABLE=True,
            registry=mock_registry,
        ):
            register_trufflehog_tools()

        assert mock_registry.register.call_count == 3
        calls = [c.kwargs["tool"] for c in mock_registry.register.call_args_list]
        assert trufflehog_scan_git in calls
        assert trufflehog_scan_path in calls
        assert trufflehog_scan_local_repo in calls

    def test_register_skips_when_langchain_unavailable(self):
        mock_registry = Mock()
        with patch.multiple(
            th_mod,
            TOOL_REGISTRY_AVAILABLE=True,
            LANGCHAIN_AVAILABLE=False,
            registry=mock_registry,
        ):
            register_trufflehog_tools()
        mock_registry.register.assert_not_called()

    def test_register_skips_when_registry_unavailable(self):
        with patch.multiple(
            th_mod,
            TOOL_REGISTRY_AVAILABLE=False,
            LANGCHAIN_AVAILABLE=True,
        ):
            # Should return early without error even if registry is None
            register_trufflehog_tools()

    def test_register_handles_registry_exception(self):
        mock_registry = Mock()
        mock_registry.register.side_effect = RuntimeError("registry down")
        with patch.multiple(
            th_mod,
            TOOL_REGISTRY_AVAILABLE=True,
            LANGCHAIN_AVAILABLE=True,
            registry=mock_registry,
        ):
            # Must not raise
            register_trufflehog_tools()


# ============================================================================
# Import fallbacks (simulate missing langchain_core.tools / tool_registry)
# ============================================================================


class TestImportFallbacks:
    """Coverage for the module-level try/except import blocks."""

    def test_tool_decorator_fallback_with_func(self):
        """When langchain is unavailable, the fallback @tool should pass through."""

        def sample():
            return 42

        with patch.object(th_mod, "LANGCHAIN_AVAILABLE", False):
            # Re-import the fallback decorator by forcing the module to re-evaluate
            # the except branch.  We call the local fallback directly.
            decorated = th_mod.tool(sample)
            assert decorated is sample
            assert decorated() == 42

    def test_tool_decorator_fallback_without_func(self):
        with patch.object(th_mod, "LANGCHAIN_AVAILABLE", False):
            decorator = th_mod.tool(some_kwarg=True)

            def sample2():
                return 1

            decorated = decorator(sample2)
            assert decorated is sample2
            assert decorated() == 1

    def test_registry_import_fallback_values(self):
        # When the relative import fails, the module sets registry=None and
        # the category/level constants to None.
        assert hasattr(th_mod, "registry")
        assert hasattr(th_mod, "ToolCategory")
        assert hasattr(th_mod, "ToolSafetyLevel")
        # The boolean flag reflects whether the import succeeded in this env.
        assert isinstance(TOOL_REGISTRY_AVAILABLE, bool)


# ============================================================================
# Module exports
# ============================================================================


class TestModuleExports:
    """__all__ contains expected names."""

    def test_all_exports_present(self):
        expected = {
            "TruffleHogScanner",
            "TruffleHogFinding",
            "TruffleHogResult",
            "trufflehog_scan_git",
            "trufflehog_scan",
            "trufflehog_scan_path",
            "trufflehog_scan_local_repo",
            "register_trufflehog_tools",
        }
        assert set(th_mod.__all__) == expected

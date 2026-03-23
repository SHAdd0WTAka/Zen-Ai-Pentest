"""Tests for Semgrep Integration Module

This module contains comprehensive tests for the semgrep_integration module,
including unit tests with mocked subprocess calls.
"""

import asyncio
import json
from unittest.mock import Mock, patch

import pytest

# Import the module under test
from tools.semgrep_integration import (
    SemgrepConfidence,
    SemgrepFinding,
    SemgrepResult,
    SemgrepScanner,
    SemgrepSeverity,
    semgrep_scan_ci,
    semgrep_scan_code,
    semgrep_scan_owasp,
    semgrep_scan_secrets,
)

# Sample Semgrep JSON output for testing
SAMPLE_SEMGREP_OUTPUT = {
    "version": "1.0.0",
    "results": [
        {
            "check_id": "python.lang.security.audit.dangerous-eval-string",
            "path": "app.py",
            "start": {"line": 15, "col": 10},
            "end": {"line": 15, "col": 30},
            "extra": {
                "message": "Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content.",
                "severity": "ERROR",
                "confidence": "HIGH",
                "lines": "result = eval(user_input)",
                "metadata": {
                    "cwe": [
                        "CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code ('Eval Injection')"
                    ],
                    "owasp": ["A03:2021 - Injection"],
                    "references": [
                        "https://owasp.org/Top10/A03_2021-Injection",
                    ],
                    "category": "security",
                    "technology": ["python"],
                    "confidence": "HIGH",
                    "likelihood": "HIGH",
                    "impact": "HIGH",
                },
                "fix": "# Use safer alternatives like ast.literal_eval()\nimport ast\nresult = ast.literal_eval(user_input)",
            },
        },
        {
            "check_id": "javascript.lang.security.audit.path-traversal.path-join-resolve-traversal",
            "path": "server.js",
            "start": {"line": 42, "col": 20},
            "end": {"line": 42, "col": 50},
            "extra": {
                "message": "Path traversal vulnerability detected",
                "severity": "WARNING",
                "confidence": "MEDIUM",
                "lines": "const file = path.join(__dirname, req.query.file);",
                "metadata": {
                    "cwe": [
                        "CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')"
                    ],
                    "owasp": ["A01:2021 - Broken Access Control"],
                    "category": "security",
                    "technology": ["javascript"],
                    "confidence": "MEDIUM",
                },
            },
        },
    ],
    "errors": [],
    "paths": {"scanned": ["app.py", "server.js"]},
    "interfile_languages_used": [],
    "stats": {
        "okfiles": 2,
        "errorfiles": 0,
    },
}

SAMPLE_SEMGREP_WITH_ERRORS = {
    "version": "1.0.0",
    "results": [],
    "errors": [
        {
            "code": 3,
            "level": "warn",
            "message": "Syntax error in file",
            "path": "broken.py",
            "type": "Syntax error",
        },
    ],
    "paths": {"scanned": []},
}


class TestSemgrepScannerInit:
    """Test SemgrepScanner initialization"""

    @patch("shutil.which")
    def test_init_default(self, mock_which):
        """Test initialization with defaults"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        assert scanner.config == scanner.DEFAULT_RULES
        assert scanner.num_jobs == 4
        assert scanner.timeout == 300
        assert scanner.autofix is False
        assert scanner.dry_run is True

    @patch("shutil.which")
    def test_init_with_options(self, mock_which):
        """Test initialization with custom options"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(
            config=["p/owasp-top-ten"],
            exclude_patterns=["tests", "node_modules"],
            include_patterns=["*.py"],
            num_jobs=8,
            timeout=600,
            autofix=True,
            dry_run=False,
            verbose=True,
        )
        assert scanner.config == ["p/owasp-top-ten"]
        assert scanner.exclude_patterns == ["tests", "node_modules"]
        assert scanner.include_patterns == ["*.py"]
        assert scanner.num_jobs == 8
        assert scanner.timeout == 600
        assert scanner.autofix is True
        assert scanner.dry_run is False
        assert scanner.verbose is True

    @patch("shutil.which")
    def test_init_semgrep_not_found(self, mock_which):
        """Test error when semgrep is not found"""
        mock_which.return_value = None
        with pytest.raises(RuntimeError) as exc_info:
            SemgrepScanner(semgrep_path="nonexistent")
        assert "semgrep not found" in str(exc_info.value)


class TestSemgrepFinding:
    """Test SemgrepFinding dataclass"""

    def test_finding_creation(self):
        """Test creating SemgrepFinding"""
        finding = SemgrepFinding(
            check_id="python.lang.security.eval",
            path="app.py",
            start_line=10,
            end_line=10,
            start_col=5,
            end_col=20,
            message="Dangerous eval detected",
            severity="ERROR",
            confidence="HIGH",
            code_snippet="eval(user_input)",
            fix="ast.literal_eval(user_input)",
        )
        assert finding.check_id == "python.lang.security.eval"
        assert finding.severity == "ERROR"
        assert finding.fix == "ast.literal_eval(user_input)"

    def test_finding_default_metadata(self):
        """Test finding with default metadata"""
        finding = SemgrepFinding(
            check_id="test.rule",
            path="test.py",
            start_line=1,
            end_line=1,
            start_col=1,
            end_col=10,
            message="Test",
            severity="WARNING",
            confidence="MEDIUM",
        )
        assert finding.metadata == {}
        assert finding.fix == ""
        assert finding.fix_regex == {}


class TestSemgrepResult:
    """Test SemgrepResult dataclass"""

    def test_result_success(self):
        """Test successful result"""
        finding = SemgrepFinding(
            check_id="test.rule",
            path="test.py",
            start_line=1,
            end_line=1,
            start_col=1,
            end_col=10,
            message="Test finding",
            severity="ERROR",
            confidence="HIGH",
        )
        result = SemgrepResult(
            success=True,
            target="/path/to/code",
            findings=[finding],
            scan_time=30.5,
            stats={"files_scanned": 10},
        )
        assert result.success is True
        assert len(result.findings) == 1

    def test_result_with_errors(self):
        """Test result with errors"""
        result = SemgrepResult(
            success=False,
            target="/path/to/code",
            errors=["Syntax error in file.py"],
            scan_time=5.0,
        )
        assert result.success is False
        assert result.errors == ["Syntax error in file.py"]


class TestSeverityMapping:
    """Test severity mapping"""

    @patch("shutil.which")
    def test_error_severity(self, mock_which):
        """Test ERROR severity maps to high"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        assert scanner.SEVERITY_MAP["ERROR"] == "high"

    @patch("shutil.which")
    def test_warning_severity(self, mock_which):
        """Test WARNING severity maps to medium"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        assert scanner.SEVERITY_MAP["WARNING"] == "medium"

    @patch("shutil.which")
    def test_info_severity(self, mock_which):
        """Test INFO severity maps to low"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        assert scanner.SEVERITY_MAP["INFO"] == "low"


class TestCommandBuilding:
    """Test command building"""

    @patch("shutil.which")
    def test_build_command_basic(self, mock_which):
        """Test basic command building"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        cmd = scanner._build_command("/path/to/code")

        assert cmd[0] == "/usr/bin/semgrep"
        assert "--json" in cmd
        assert "/path/to/code" in cmd

    @patch("shutil.which")
    def test_build_command_with_configs(self, mock_which):
        """Test command with multiple configs"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(
            config=["p/security-audit", "p/owasp-top-ten"]
        )
        cmd = scanner._build_command("/path/to/code")

        assert "--config" in cmd
        assert "p/security-audit" in cmd
        assert "p/owasp-top-ten" in cmd

    @patch("shutil.which")
    def test_build_command_with_exclude(self, mock_which):
        """Test command with exclude patterns"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(exclude_patterns=["node_modules", "tests"])
        cmd = scanner._build_command("/path/to/code")

        assert "--exclude" in cmd
        assert "node_modules" in cmd
        assert "tests" in cmd

    @patch("shutil.which")
    def test_build_command_performance_options(self, mock_which):
        """Test command with performance options"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(
            max_memory=4096,
            max_target_bytes=500000,
            num_jobs=8,
            timeout=600,
        )
        cmd = scanner._build_command("/path/to/code")

        assert "--max-memory" in cmd
        assert "4096" in cmd
        assert "--jobs" in cmd
        assert "8" in cmd

    @patch("shutil.which")
    def test_build_command_behavior_options(self, mock_which):
        """Test command with behavior options"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(
            autofix=True,
            strict=True,
            verbose=True,
        )
        cmd = scanner._build_command("/path/to/code")

        assert "--autofix" in cmd
        assert "--strict" in cmd
        assert "--verbose" in cmd


class TestFindingParsing:
    """Test finding parsing"""

    @patch("shutil.which")
    def test_parse_findings(self, mock_which):
        """Test parsing findings from JSON"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        findings = scanner._parse_findings(SAMPLE_SEMGREP_OUTPUT)

        assert len(findings) == 2
        assert (
            findings[0].check_id
            == "python.lang.security.audit.dangerous-eval-string"
        )
        assert findings[0].severity == "ERROR"
        assert findings[0].metadata.get("cwe") is not None

    @patch("shutil.which")
    def test_parse_finding_with_fix(self, mock_which):
        """Test parsing finding with fix"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        findings = scanner._parse_findings(SAMPLE_SEMGREP_OUTPUT)

        assert findings[0].fix is not None
        assert "ast.literal_eval" in findings[0].fix

    @patch("shutil.which")
    def test_parse_empty_findings(self, mock_which):
        """Test parsing empty findings"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        empty_data = {"results": []}
        findings = scanner._parse_findings(empty_data)
        assert len(findings) == 0

    @patch("shutil.which")
    def test_extract_errors(self, mock_which):
        """Test extracting errors"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        errors = scanner._extract_errors(SAMPLE_SEMGREP_WITH_ERRORS)
        assert len(errors) == 1
        assert "Syntax error" in errors[0]

    @patch("shutil.which")
    def test_extract_stats(self, mock_which):
        """Test extracting statistics"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        stats = scanner._extract_stats(SAMPLE_SEMGREP_OUTPUT)
        assert stats["version"] == "1.0.0"
        assert stats["severity_counts"]["ERROR"] == 1
        assert stats["severity_counts"]["WARNING"] == 1


class TestAsyncScanning:
    """Test async scanning"""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_success(self, mock_which):
        """Test successful scan"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(SAMPLE_SEMGREP_OUTPUT)
        mock_result.stderr = ""

        with patch.object(
            scanner, "_run_subprocess", return_value=mock_result
        ):
            with patch("pathlib.Path.exists", return_value=True):
                result = await scanner.scan("/path/to/code")

                assert result.success is True
                assert len(result.findings) == 2
                assert result.stats["severity_counts"]["ERROR"] == 1

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_nonexistent_target(self, mock_which):
        """Test scan with nonexistent target"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        with patch("pathlib.Path.exists", return_value=False):
            result = await scanner.scan("/nonexistent/path")

            assert result.success is False
            assert "does not exist" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_timeout(self, mock_which):
        """Test scan timeout handling"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        with patch.object(
            scanner, "_run_subprocess", side_effect=asyncio.TimeoutError
        ):
            with patch("pathlib.Path.exists", return_value=True):
                result = await scanner.scan("/path/to/code")

                assert result.success is False
                assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_with_custom_config(self, mock_which):
        """Test scan with custom config"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(SAMPLE_SEMGREP_OUTPUT)
        mock_result.stderr = ""

        with patch.object(
            scanner, "_run_subprocess", return_value=mock_result
        ):
            with patch("pathlib.Path.exists", return_value=True):
                result = await scanner.scan(
                    "/path/to/code", custom_config=["p/owasp-top-ten"]
                )

                assert result.success is True


class TestOutputParsing:
    """Test output parsing methods"""

    @patch("shutil.which")
    def test_parse_output(self, mock_which):
        """Test parse_output method"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        finding = SemgrepFinding(
            check_id="python.lang.security.eval",
            path="app.py",
            start_line=10,
            end_line=10,
            start_col=5,
            end_col=20,
            message="Dangerous eval",
            severity="ERROR",
            confidence="HIGH",
            metadata={
                "cwe": ["CWE-95"],
                "owasp": ["A03:2021"],
                "references": ["https://owasp.org"],
                "category": "security",
                "technology": ["python"],
            },
            code_snippet="eval(user_input)",
            fix="ast.literal_eval(user_input)",
        )
        result = SemgrepResult(
            success=True,
            target="/path/to/code",
            findings=[finding],
        )

        parsed = scanner.parse_output(result)

        assert len(parsed) == 1
        assert parsed[0]["tool"] == "semgrep"
        assert parsed[0]["check_id"] == "python.lang.security.eval"
        assert parsed[0]["cwe_ids"] == ["CWE-95"]
        assert parsed[0]["owasp"] == ["A03:2021"]

    @patch("shutil.which")
    def test_normalize_findings(self, mock_which):
        """Test normalize_findings method"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        findings = [
            {
                "tool": "semgrep",
                "check_id": "python.lang.security.eval",
                "path": "app.py",
                "line": 10,
                "column": 5,
                "message": "Dangerous eval usage",
                "severity": "high",
                "confidence": "high",
                "cwe_ids": ["CWE-95"],
                "owasp": ["A03:2021"],
                "references": ["https://owasp.org"],
                "code": "eval(user_input)",
                "fix": "ast.literal_eval(user_input)",
            }
        ]

        normalized = scanner.normalize_findings(findings)

        assert len(normalized) == 1
        assert normalized[0]["tool"] == "semgrep"
        assert normalized[0]["severity"] == "high"
        assert "Dangerous eval usage" in normalized[0]["title"]
        assert normalized[0]["cwe_ids"] == ["CWE-95"]


class TestRuleConfiguration:
    """Test rule configuration methods"""

    @patch("shutil.which")
    def test_add_owasp_rules(self, mock_which):
        """Test adding OWASP rules"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(config=[])
        scanner.add_owasp_rules()
        assert "p/owasp-top-ten" in scanner.config

    @patch("shutil.which")
    def test_add_cwe_rules(self, mock_which):
        """Test adding CWE rules"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(config=[])
        scanner.add_cwe_rules()
        assert "p/cwe-top-25" in scanner.config

    @patch("shutil.which")
    def test_add_security_audit_rules(self, mock_which):
        """Test adding security audit rules"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(config=[])
        scanner.add_security_audit_rules()
        assert "p/security-audit" in scanner.config

    @patch("shutil.which")
    def test_add_secrets_rules(self, mock_which):
        """Test adding secrets rules"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner(config=[])
        scanner.add_secrets_rules()
        assert "p/secrets" in scanner.config


class TestFalsePositiveFiltering:
    """Test false positive filtering"""

    @patch("shutil.which")
    def test_filter_test_files(self, mock_which):
        """Test filtering test files"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        findings = [
            SemgrepFinding(
                check_id="test.rule",
                path="test_security.py",
                start_line=1,
                end_line=1,
                start_col=1,
                end_col=10,
                message="Test",
                severity="WARNING",
                confidence="MEDIUM",
            ),
            SemgrepFinding(
                check_id="test.rule",
                path="app.py",
                start_line=1,
                end_line=1,
                start_col=1,
                end_col=10,
                message="Test",
                severity="WARNING",
                confidence="MEDIUM",
            ),
        ]

        filtered = scanner.filter_false_positives(findings)
        assert len(filtered) == 1
        assert filtered[0].path == "app.py"

    @patch("shutil.which")
    def test_filter_with_custom_patterns(self, mock_which):
        """Test filtering with custom patterns"""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()

        findings = [
            SemgrepFinding(
                check_id="test.rule",
                path="my_custom_file.py",
                start_line=1,
                end_line=1,
                start_col=1,
                end_col=10,
                message="Test",
                severity="WARNING",
                confidence="MEDIUM",
            ),
        ]

        filtered = scanner.filter_false_positives(findings, ["custom"])
        assert len(filtered) == 0


class TestEnums:
    """Test enumeration classes"""

    def test_severity_enum_values(self):
        """Test SemgrepSeverity enum values"""
        assert SemgrepSeverity.ERROR.value == "ERROR"
        assert SemgrepSeverity.WARNING.value == "WARNING"
        assert SemgrepSeverity.INFO.value == "INFO"

    def test_confidence_enum_values(self):
        """Test SemgrepConfidence enum values"""
        assert SemgrepConfidence.HIGH.value == "HIGH"
        assert SemgrepConfidence.MEDIUM.value == "MEDIUM"
        assert SemgrepConfidence.LOW.value == "LOW"


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    @patch("asyncio.run")
    def test_semgrep_scan_code_tool(self, mock_run):
        """Test semgrep_scan_code tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.scan_time = 30.0
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = semgrep_scan_code("/path/to/code")
        assert isinstance(result, str)
        assert "Semgrep" in result

    @patch("asyncio.run")
    def test_semgrep_scan_owasp_tool(self, mock_run):
        """Test semgrep_scan_owasp tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = semgrep_scan_owasp("/path/to/code")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_semgrep_scan_secrets_tool(self, mock_run):
        """Test semgrep_scan_secrets tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = semgrep_scan_secrets("/path/to/code")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_semgrep_scan_ci_tool(self, mock_run):
        """Test semgrep_scan_ci tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = semgrep_scan_ci("/path/to/code")
        assert isinstance(result, str)
        assert "CI" in result or "PASS" in result or "FAIL" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

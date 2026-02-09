"""Tests for Trivy Integration Module

This module contains comprehensive tests for the trivy_integration module,
including unit tests with mocked subprocess calls.
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the module under test
from tools.trivy_integration import (
    TrivyScanner,
    TrivyVulnerability,
    TrivyMisconfiguration,
    TrivySecret,
    TrivyResult,
    TrivyScanTarget,
    TrivyScannerType,
    trivy_scan_image,
    trivy_scan_filesystem,
    trivy_scan_dockerfile,
    trivy_generate_sbom,
)


# Sample Trivy JSON output for testing
SAMPLE_TRIVY_VULN_OUTPUT = {
    "SchemaVersion": 2,
    "ArtifactName": "nginx:latest",
    "ArtifactType": "container_image",
    "Metadata": {
        "OS": {
            "Family": "debian",
            "Name": "11.1",
        },
    },
    "Results": [
        {
            "Target": "nginx:latest (debian 11.1)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2021-1234",
                    "PkgName": "openssl",
                    "InstalledVersion": "1.1.1n-0+deb11u1",
                    "FixedVersion": "1.1.1n-0+deb11u2",
                    "Severity": "HIGH",
                    "Title": "openssl: Buffer overflow",
                    "Description": "A buffer overflow vulnerability in OpenSSL",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2021-1234",
                    "References": [
                        "https://openssl.org/news/secadv/20210325.txt",
                    ],
                    "CVSS": {
                        "nvd": {
                            "V3Score": 7.5,
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                        },
                    },
                    "PublishedDate": "2021-03-25T00:00:00Z",
                    "LastModifiedDate": "2021-04-01T00:00:00Z",
                },
                {
                    "VulnerabilityID": "CVE-2022-5678",
                    "PkgName": "curl",
                    "InstalledVersion": "7.74.0-1.3+deb11u1",
                    "FixedVersion": "7.74.0-1.3+deb11u7",
                    "Severity": "CRITICAL",
                    "Title": "curl: Heap buffer overflow",
                    "Description": "A heap buffer overflow in curl",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2022-5678",
                    "References": [],
                    "CVSS": {
                        "redhat": {
                            "V3Score": 9.8,
                        },
                    },
                },
            ],
        },
    ],
}

SAMPLE_TRIVY_MISCONFIG_OUTPUT = {
    "SchemaVersion": 2,
    "ArtifactName": ".",
    "ArtifactType": "filesystem",
    "Results": [
        {
            "Target": "Dockerfile",
            "Class": "config",
            "Type": "dockerfile",
            "Misconfigurations": [
                {
                    "Type": "Dockerfile Security Check",
                    "ID": "DS002",
                    "Title": "Image user should not be 'root'",
                    "Description": "Running containers with 'root' user can lead to security issues",
                    "Message": "Specify at least 1 USER command in Dockerfile",
                    "Resolution": "Add 'USER nonroot' to Dockerfile",
                    "Severity": "HIGH",
                    "References": [
                        "https://docs.docker.com/develop/develop-images/dockerfile_best-practices/",
                    ],
                },
            ],
        },
    ],
}

SAMPLE_TRIVY_SECRET_OUTPUT = {
    "SchemaVersion": 2,
    "ArtifactName": ".",
    "ArtifactType": "filesystem",
    "Results": [
        {
            "Target": "config.py",
            "Class": "secret",
            "Secrets": [
                {
                    "RuleID": "aws-access-key-id",
                    "Category": "AWS",
                    "Severity": "CRITICAL",
                    "Title": "AWS Access Key ID",
                    "Match": "AKIAIOSFODNN7EXAMPLE",
                },
            ],
        },
    ],
}


class TestTrivyScannerInit:
    """Test TrivyScanner initialization"""

    @patch("shutil.which")
    def test_init_default(self, mock_which):
        """Test initialization with defaults"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        assert scanner.cache_dir is None
        assert scanner.severity == ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert scanner.scanners == [TrivyScannerType.VULNERABILITY]
        assert scanner.skip_db_update is False

    @patch("shutil.which")
    def test_init_with_options(self, mock_which):
        """Test initialization with custom options"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner(
            cache_dir="/tmp/trivy-cache",
            severity=["HIGH", "CRITICAL"],
            scanners=[TrivyScannerType.VULNERABILITY, TrivyScannerType.MISCONFIGURATION],
            skip_db_update=True,
            offline_scan=True,
            timeout=1800,
        )
        assert scanner.cache_dir == "/tmp/trivy-cache"
        assert scanner.severity == ["HIGH", "CRITICAL"]
        assert TrivyScannerType.VULNERABILITY in scanner.scanners
        assert TrivyScannerType.MISCONFIGURATION in scanner.scanners
        assert scanner.skip_db_update is True
        assert scanner.offline_scan is True
        assert scanner.timeout == 1800

    @patch("shutil.which")
    def test_init_trivy_not_found(self, mock_which):
        """Test error when trivy is not found"""
        mock_which.return_value = None
        with pytest.raises(RuntimeError) as exc_info:
            TrivyScanner(trivy_path="nonexistent")
        assert "trivy not found" in str(exc_info.value)


class TestTrivyDataClasses:
    """Test Trivy dataclasses"""

    def test_vulnerability_creation(self):
        """Test creating TrivyVulnerability"""
        vuln = TrivyVulnerability(
            vulnerability_id="CVE-2021-1234",
            pkg_name="openssl",
            installed_version="1.1.1n",
            fixed_version="1.1.1n-1",
            severity="HIGH",
            title="Buffer overflow",
            description="A buffer overflow vulnerability",
            cvss_score=7.5,
            primary_url="https://example.com",
        )
        assert vuln.vulnerability_id == "CVE-2021-1234"
        assert vuln.cvss_score == 7.5

    def test_misconfiguration_creation(self):
        """Test creating TrivyMisconfiguration"""
        misconf = TrivyMisconfiguration(
            id="DS002",
            type="Dockerfile",
            title="Root user",
            description="Should not use root",
            severity="HIGH",
            message="No USER specified",
            resolution="Add USER directive",
            file_path="Dockerfile",
        )
        assert misconf.id == "DS002"
        assert misconf.file_path == "Dockerfile"

    def test_secret_creation(self):
        """Test creating TrivySecret"""
        secret = TrivySecret(
            rule_id="aws-access-key-id",
            category="AWS",
            severity="CRITICAL",
            title="AWS Key",
            match="AKIA...",
            file_path="config.py",
            start_line=10,
        )
        assert secret.rule_id == "aws-access-key-id"
        assert secret.start_line == 10


class TestTrivyResult:
    """Test TrivyResult dataclass"""

    def test_result_success(self):
        """Test successful result"""
        vuln = TrivyVulnerability(
            vulnerability_id="CVE-2021-1234",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="1.1",
            severity="HIGH",
            title="Test",
            description="Test",
        )
        result = TrivyResult(
            success=True,
            target="nginx:latest",
            scan_type="image",
            vulnerabilities=[vuln],
            scan_time=30.5,
            artifact_name="nginx:latest",
        )
        assert result.success is True
        assert result.artifact_name == "nginx:latest"

    def test_result_failure(self):
        """Test failed result"""
        result = TrivyResult(
            success=False,
            target="invalid:image",
            scan_type="image",
            error="Image not found",
        )
        assert result.success is False
        assert result.error == "Image not found"


class TestSeverityOrder:
    """Test severity ordering"""

    @patch("shutil.which")
    def test_severity_order_list(self, mock_which):
        """Test severity order list is correct"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        assert scanner.SEVERITY_ORDER == ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


class TestCVSSExtraction:
    """Test CVSS score extraction"""

    @patch("shutil.which")
    def test_extract_nvd_cvss(self, mock_which):
        """Test extracting NVD CVSS score"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        cvss_data = {"nvd": {"V3Score": 7.5}}
        score = scanner._extract_cvss_score(cvss_data)
        assert score == 7.5

    @patch("shutil.which")
    def test_extract_vendor_cvss(self, mock_which):
        """Test extracting vendor CVSS score"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        cvss_data = {"redhat": {"V3Score": 8.1}}
        score = scanner._extract_cvss_score(cvss_data)
        assert score == 8.1

    @patch("shutil.which")
    def test_extract_no_cvss(self, mock_which):
        """Test extracting CVSS when none available"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        score = scanner._extract_cvss_score({})
        assert score is None


class TestVulnerabilityParsing:
    """Test vulnerability parsing"""

    @patch("shutil.which")
    def test_parse_vulnerabilities(self, mock_which):
        """Test parsing vulnerabilities from output"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        vulns = scanner._parse_vulnerabilities(SAMPLE_TRIVY_VULN_OUTPUT["Results"])

        assert len(vulns) == 2
        assert vulns[0].vulnerability_id == "CVE-2021-1234"
        assert vulns[0].cvss_score == 7.5
        assert vulns[1].vulnerability_id == "CVE-2022-5678"
        assert vulns[1].cvss_score == 9.8

    @patch("shutil.which")
    def test_parse_empty_vulnerabilities(self, mock_which):
        """Test parsing empty vulnerabilities"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        vulns = scanner._parse_vulnerabilities([{"Vulnerabilities": []}])
        assert len(vulns) == 0


class TestMisconfigurationParsing:
    """Test misconfiguration parsing"""

    @patch("shutil.which")
    def test_parse_misconfigurations(self, mock_which):
        """Test parsing misconfigurations"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        misconfs = scanner._parse_misconfigurations(SAMPLE_TRIVY_MISCONFIG_OUTPUT["Results"])

        assert len(misconfs) == 1
        assert misconfs[0].id == "DS002"
        assert misconfs[0].severity == "HIGH"


class TestSecretParsing:
    """Test secret parsing"""

    @patch("shutil.which")
    def test_parse_secrets(self, mock_which):
        """Test parsing secrets"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        secrets = scanner._parse_secrets(SAMPLE_TRIVY_SECRET_OUTPUT["Results"])

        assert len(secrets) == 1
        assert secrets[0].rule_id == "aws-access-key-id"
        assert secrets[0].category == "AWS"


class TestCommandBuilding:
    """Test command building"""

    @patch("shutil.which")
    def test_build_image_command(self, mock_which):
        """Test building image scan command"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()
        cmd = scanner._build_command(TrivyScanTarget.IMAGE, "nginx:latest")

        assert cmd[0] == "/usr/bin/trivy"
        assert "image" in cmd
        assert "nginx:latest" in cmd
        assert "--format" in cmd
        assert "json" in cmd

    @patch("shutil.which")
    def test_build_command_with_severity(self, mock_which):
        """Test command with severity filter"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner(severity=["HIGH", "CRITICAL"])
        cmd = scanner._build_command(TrivyScanTarget.IMAGE, "nginx:latest")

        assert "--severity" in cmd
        assert "HIGH,CRITICAL" in cmd

    @patch("shutil.which")
    def test_build_command_with_scanners(self, mock_which):
        """Test command with multiple scanners"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner(
            scanners=[TrivyScannerType.VULNERABILITY, TrivyScannerType.MISCONFIGURATION]
        )
        cmd = scanner._build_command(TrivyScanTarget.FILESYSTEM, ".")

        assert "--scanners" in cmd
        assert "vuln,config" in cmd

    @patch("shutil.which")
    def test_build_command_with_cache(self, mock_which):
        """Test command with cache directory"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner(cache_dir="/tmp/trivy-cache")
        cmd = scanner._build_command(TrivyScanTarget.IMAGE, "nginx:latest")

        assert "--cache-dir" in cmd
        assert "/tmp/trivy-cache" in cmd


class TestAsyncScanning:
    """Test async scanning"""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_image_success(self, mock_which):
        """Test successful image scan"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(SAMPLE_TRIVY_VULN_OUTPUT)
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan_image("nginx:latest")

            assert result.success is True
            assert result.scan_type == "image"
            assert len(result.vulnerabilities) == 2
            assert result.os_info["Family"] == "debian"

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_filesystem_nonexistent(self, mock_which):
        """Test scanning nonexistent path"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        with patch("pathlib.Path.exists", return_value=False):
            result = await scanner.scan_filesystem("/nonexistent/path")

            assert result.success is False
            assert "does not exist" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_timeout(self, mock_which):
        """Test scan timeout handling"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
            result = await scanner.scan_image("nginx:latest", timeout=1)

            assert result.success is False
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_json_error(self, mock_which):
        """Test handling invalid JSON output"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan_image("nginx:latest")

            assert result.success is False
            assert "parse" in result.error.lower()


class TestOutputParsing:
    """Test output parsing methods"""

    @patch("shutil.which")
    def test_parse_output(self, mock_which):
        """Test parse_output method"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        vuln = TrivyVulnerability(
            vulnerability_id="CVE-2021-1234",
            pkg_name="openssl",
            installed_version="1.0",
            fixed_version="1.1",
            severity="HIGH",
            title="Test",
            description="Test",
            cvss_score=7.5,
            primary_url="https://example.com",
        )
        result = TrivyResult(
            success=True,
            target="nginx:latest",
            scan_type="image",
            vulnerabilities=[vuln],
        )

        parsed = scanner.parse_output(result)

        assert len(parsed["vulnerabilities"]) == 1
        assert parsed["vulnerabilities"][0]["id"] == "CVE-2021-1234"
        assert parsed["vulnerabilities"][0]["cvss_score"] == 7.5

    @patch("shutil.which")
    def test_normalize_findings(self, mock_which):
        """Test normalize_findings method"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        vuln = TrivyVulnerability(
            vulnerability_id="CVE-2021-1234",
            pkg_name="openssl",
            installed_version="1.0",
            fixed_version="1.1",
            severity="HIGH",
            title="Buffer overflow",
            description="A buffer overflow",
            references=["https://example.com"],
        )
        result = TrivyResult(
            success=True,
            target="nginx:latest",
            scan_type="image",
            vulnerabilities=[vuln],
        )

        normalized = scanner.normalize_findings(result)

        assert len(normalized) == 1
        assert normalized[0]["tool"] == "trivy"
        assert normalized[0]["severity"] == "high"
        assert "Update openssl to version 1.1" in normalized[0]["remediation"]


class TestSBOMGeneration:
    """Test SBOM generation"""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_generate_sbom(self, mock_which):
        """Test SBOM generation"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"components": []}'

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            sbom = await scanner.generate_sbom("nginx:latest")
            assert '{"components": []}' in sbom

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_generate_sbom_failure(self, mock_which):
        """Test SBOM generation failure"""
        mock_which.return_value = "/usr/bin/trivy"
        scanner = TrivyScanner()

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error generating SBOM"

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            sbom = await scanner.generate_sbom("nginx:latest")
            assert "failed" in sbom.lower()


class TestEnums:
    """Test enumeration classes"""

    def test_scan_target_values(self):
        """Test scan target enum values"""
        assert TrivyScanTarget.IMAGE.value == "image"
        assert TrivyScanTarget.FILESYSTEM.value == "filesystem"
        assert TrivyScanTarget.REPOSITORY.value == "repository"

    def test_scanner_type_values(self):
        """Test scanner type enum values"""
        assert TrivyScannerType.VULNERABILITY.value == "vuln"
        assert TrivyScannerType.MISCONFIGURATION.value == "config"
        assert TrivyScannerType.SECRET.value == "secret"


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    @patch("asyncio.run")
    def test_trivy_scan_image_tool(self, mock_run):
        """Test trivy_scan_image tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.scan_time = 30.0
        mock_result.os_info = {"Family": "debian", "Name": "11"}
        mock_result.vulnerabilities = []

        mock_run.return_value = mock_result

        result = trivy_scan_image("nginx:latest")
        assert isinstance(result, str)
        assert "Trivy" in result or "nginx" in result

    @patch("asyncio.run")
    def test_trivy_scan_filesystem_tool(self, mock_run):
        """Test trivy_scan_filesystem tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.scan_time = 10.0
        mock_result.vulnerabilities = []
        mock_result.misconfigurations = []

        mock_run.return_value = mock_result

        result = trivy_scan_filesystem("/path/to/code")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_trivy_scan_dockerfile_tool(self, mock_run):
        """Test trivy_scan_dockerfile tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.misconfigurations = []

        mock_run.return_value = mock_result

        result = trivy_scan_dockerfile("Dockerfile")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_trivy_generate_sbom_tool(self, mock_run):
        """Test trivy_generate_sbom tool function"""
        mock_run.return_value = '{"components": []}'

        result = trivy_generate_sbom("nginx:latest")
        assert isinstance(result, str)
        assert "SBOM" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for ScoutSuite Integration Module

This module contains comprehensive tests for the scout_integration module,
including unit tests with mocked subprocess calls and cloud credential checks.
"""

import asyncio
import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the module under test
from tools.scout_integration import (
    ScoutSuiteScanner,
    ScoutFinding,
    ScoutResult,
    CloudProvider,
    scoutsuite_scan_aws,
    scoutsuite_scan_azure,
    scoutsuite_scan_gcp,
    scoutsuite_quick_scan,
)


# Sample ScoutSuite report data for testing
SAMPLE_SCOUTSUITE_REPORT = {
    "provider_code": "aws",
    "provider_name": "Amazon Web Services",
    "account_id": "123456789012",
    "last_run": {
        "time": "2023-01-01T00:00:00Z",
        "services": ["iam", "s3", "ec2"],
    },
    "services": {
        "iam": {
            "findings": {
                "password-policy-not-set": {
                    "description": "No password policy set for IAM users",
                    "level": "danger",
                    "id_suffix": "password-policy-not-set",
                    "path": "iam.password_policy.password-policy-not-set",
                    "display_path": "iam.password_policy",
                    "resource_type": "password-policy",
                    "service": "iam",
                    "checked_items": 1,
                    "flagged_items": 1,
                    "compliance": ["cis", "pci-dss"],
                    "references": ["https://docs.aws.amazon.com/IAM"],
                    "remediation": "Set a strong password policy",
                },
                "root-account-mfa-not-enabled": {
                    "description": "Root account MFA is not enabled",
                    "level": "danger",
                    "id_suffix": "root-account-mfa-not-enabled",
                    "resource_type": "root-account",
                    "service": "iam",
                    "checked_items": 1,
                    "flagged_items": 1,
                    "compliance": ["cis"],
                    "references": [],
                    "remediation": "Enable MFA for root account",
                },
            },
        },
        "s3": {
            "findings": {
                "bucket-public-access": {
                    "description": "S3 bucket has public access enabled",
                    "level": "warning",
                    "id_suffix": "bucket-public-access",
                    "resource_type": "s3-bucket",
                    "service": "s3",
                    "checked_items": 5,
                    "flagged_items": 2,
                    "compliance": [],
                    "references": [],
                    "remediation": "Remove public access from S3 bucket",
                },
            },
        },
    },
    "metadata": {
        "version": "5.0.0",
    },
}


class TestScoutSuiteScannerInit:
    """Test ScoutSuiteScanner initialization"""

    @patch("shutil.which")
    def test_init_with_aws_provider(self, mock_which):
        """Test initialization with AWS provider"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner.provider == "aws"

    @patch("shutil.which")
    def test_init_with_azure_provider(self, mock_which):
        """Test initialization with Azure provider"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AZURE)
        assert scanner.provider == "azure"

    @patch("shutil.which")
    def test_init_with_gcp_provider(self, mock_which):
        """Test initialization with GCP provider"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.GCP)
        assert scanner.provider == "gcp"

    @patch("shutil.which")
    def test_init_with_string_provider(self, mock_which):
        """Test initialization with string provider"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider="aws")
        assert scanner.provider == "aws"

    @patch("shutil.which")
    def test_init_with_options(self, mock_which):
        """Test initialization with custom options"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(
            provider=CloudProvider.AWS,
            profile="production",
            regions=["us-east-1", "eu-west-1"],
            services=["iam", "s3"],
            compliance=["cis", "pci-dss"],
            output_dir="/tmp/scout-reports",
        )
        assert scanner.profile == "production"
        assert scanner.regions == ["us-east-1", "eu-west-1"]
        assert scanner.services == ["iam", "s3"]
        assert scanner.compliance == ["cis", "pci-dss"]
        assert scanner.output_dir == "/tmp/scout-reports"

    @patch("shutil.which")
    def test_init_scoutsuite_not_found(self, mock_which):
        """Test error when ScoutSuite is not found"""
        mock_which.return_value = None
        with pytest.raises(RuntimeError) as exc_info:
            ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert "ScoutSuite not found" in str(exc_info.value)


class TestScoutFinding:
    """Test ScoutFinding dataclass"""

    def test_finding_creation(self):
        """Test creating ScoutFinding object"""
        finding = ScoutFinding(
            rule_id="password-policy-not-set",
            description="No password policy set",
            severity="critical",
            provider="aws",
            service="iam",
            resource_type="password-policy",
            resource_path="iam.password_policy",
            remediation="Set a password policy",
            compliance=["cis"],
            flagged_items=1,
            checked_items=1,
        )
        assert finding.rule_id == "password-policy-not-set"
        assert finding.severity == "critical"
        assert finding.provider == "aws"

    def test_finding_default_values(self):
        """Test ScoutFinding with default values"""
        finding = ScoutFinding(
            rule_id="test-rule",
            description="Test description",
            severity="high",
            provider="aws",
            service="ec2",
            resource_type="instance",
            resource_path="ec2.instances",
            remediation="Fix it",
        )
        assert finding.compliance == []
        assert finding.references == []
        assert finding.enabled is True
        assert finding.flagged_items == 0


class TestScoutResult:
    """Test ScoutResult dataclass"""

    def test_result_success(self):
        """Test successful result"""
        finding = ScoutFinding(
            rule_id="test-rule",
            description="Test",
            severity="high",
            provider="aws",
            service="iam",
            resource_type="policy",
            resource_path="iam",
            remediation="Fix",
        )
        result = ScoutResult(
            success=True,
            provider="aws",
            findings=[finding],
            scan_time=120.5,
            report_path="/tmp/report.json",
        )
        assert result.success is True
        assert result.provider == "aws"
        assert len(result.findings) == 1

    def test_result_failure(self):
        """Test failed result"""
        result = ScoutResult(
            success=False,
            provider="azure",
            error="No credentials found",
            scan_time=0.0,
        )
        assert result.success is False
        assert result.error == "No credentials found"


class TestSeverityMapping:
    """Test severity level mapping"""

    @patch("shutil.which")
    def test_danger_severity(self, mock_which):
        """Test danger level maps to critical"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner.SEVERITY_MAP["danger"] == "critical"

    @patch("shutil.which")
    def test_critical_severity(self, mock_which):
        """Test critical level"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner.SEVERITY_MAP["critical"] == "critical"

    @patch("shutil.which")
    def test_warning_severity(self, mock_which):
        """Test warning level maps to medium"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner.SEVERITY_MAP["warning"] == "medium"

    @patch("shutil.which")
    def test_unknown_severity(self, mock_which):
        """Test unknown level maps to info"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner.SEVERITY_MAP.get("unknown", "info") == "info"


class TestReportParsing:
    """Test report parsing"""

    @patch("shutil.which")
    def test_parse_report(self, mock_which):
        """Test report JSON parsing"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                SAMPLE_SCOUTSUITE_REPORT
            )
            data = scanner._parse_report("/tmp/report.json")
            assert data["provider_code"] == "aws"

    @patch("shutil.which")
    def test_extract_findings(self, mock_which):
        """Test extracting findings from report"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        findings = scanner._extract_findings(SAMPLE_SCOUTSUITE_REPORT)

        assert len(findings) == 3
        # Check that danger level finding is critical
        danger_finding = next(f for f in findings if f.severity == "critical")
        assert danger_finding.severity == "critical"

    @patch("shutil.which")
    def test_generate_summary(self, mock_which):
        """Test summary generation"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        findings = [
            ScoutFinding(
                rule_id="critical-1",
                description="Critical",
                severity="critical",
                provider="aws",
                service="iam",
                resource_type="policy",
                resource_path="iam",
                remediation="Fix",
                flagged_items=1,
                checked_items=1,
            ),
            ScoutFinding(
                rule_id="high-1",
                description="High",
                severity="high",
                provider="aws",
                service="s3",
                resource_type="bucket",
                resource_path="s3",
                remediation="Fix",
                flagged_items=2,
                checked_items=5,
            ),
        ]

        summary = scanner._generate_summary(findings)
        assert summary["total_findings"] == 2
        assert summary["severity_counts"]["critical"] == 1
        assert summary["severity_counts"]["high"] == 1
        assert summary["total_flagged_items"] == 3
        assert summary["total_checked_items"] == 6


class TestCredentialChecks:
    """Test cloud credential checking"""

    @patch("shutil.which")
    @patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "test"})
    def test_check_aws_credentials_env(self, mock_which):
        """Test AWS credentials from environment"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert scanner._check_aws_credentials() is True

    @patch("shutil.which")
    @patch.dict(os.environ, {}, clear=True)
    def test_check_aws_credentials_no_creds(self, mock_which):
        """Test AWS credentials check without creds"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        with patch("pathlib.Path.exists", return_value=False):
            with patch("subprocess.run", return_value=Mock(returncode=1)):
                assert scanner._check_aws_credentials() is False

    @patch("shutil.which")
    @patch.dict(os.environ, {"AZURE_CLIENT_ID": "test", "AZURE_CLIENT_SECRET": "test"})
    def test_check_azure_credentials_env(self, mock_which):
        """Test Azure credentials from environment"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AZURE)
        assert scanner._check_azure_credentials() is True

    @patch("shutil.which")
    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"})
    def test_check_gcp_credentials_env(self, mock_which):
        """Test GCP credentials from environment"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.GCP)
        assert scanner._check_gcp_credentials() is True


class TestCommandBuilding:
    """Test command building"""

    @patch("shutil.which")
    def test_build_command_basic(self, mock_which):
        """Test basic command building"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        cmd = scanner._build_command()

        assert cmd[0] == "/usr/bin/scout"
        assert "aws" in cmd
        assert "--report-dir" in cmd
        assert "--no-browser" in cmd

    @patch("shutil.which")
    def test_build_command_with_profile(self, mock_which):
        """Test command with AWS profile"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS, profile="production")
        cmd = scanner._build_command()

        assert "--profile" in cmd
        assert "production" in cmd

    @patch("shutil.which")
    def test_build_command_with_regions(self, mock_which):
        """Test command with regions"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(
            provider=CloudProvider.AWS,
            regions=["us-east-1", "eu-west-1"],
        )
        cmd = scanner._build_command()

        assert "--regions" in cmd
        assert "us-east-1,eu-west-1" in cmd

    @patch("shutil.which")
    def test_build_command_with_services(self, mock_which):
        """Test command with services"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(
            provider=CloudProvider.AWS,
            services=["iam", "s3", "ec2"],
        )
        cmd = scanner._build_command()

        assert "--services" in cmd
        assert "iam,s3,ec2" in cmd


class TestAsyncScanning:
    """Test async scanning functionality"""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_success(self, mock_which):
        """Test successful scan"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch.object(scanner, "_check_credentials", return_value=True):
            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                with patch.object(scanner, "_find_latest_report", return_value="/tmp/report.json"):
                    with patch.object(scanner, "_parse_report", return_value=SAMPLE_SCOUTSUITE_REPORT):
                        result = await scanner.scan()

                        assert result.success is True
                        assert result.provider == "aws"

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_no_credentials(self, mock_which):
        """Test scan without credentials"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        with patch.object(scanner, "_check_credentials", return_value=False):
            result = await scanner.scan()

            assert result.success is False
            assert "credentials" in result.error.lower()

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_scan_timeout(self, mock_which):
        """Test scan timeout handling"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        with patch.object(scanner, "_check_credentials", return_value=True):
            with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
                result = await scanner.scan(timeout=1)

                assert result.success is False
                assert "timed out" in result.error.lower()


class TestOutputParsing:
    """Test output parsing methods"""

    @patch("shutil.which")
    def test_parse_output(self, mock_which):
        """Test parse_output method"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        finding = ScoutFinding(
            rule_id="password-policy-not-set",
            description="No password policy",
            severity="critical",
            provider="aws",
            service="iam",
            resource_type="password-policy",
            resource_path="iam.password_policy",
            remediation="Set policy",
            compliance=["cis", "pci-dss"],
            flagged_items=1,
            checked_items=1,
        )
        result = ScoutResult(
            success=True,
            provider="aws",
            findings=[finding],
        )

        parsed = scanner.parse_output(result)

        assert len(parsed) == 1
        assert parsed[0]["tool"] == "scoutsuite"
        assert parsed[0]["rule_id"] == "password-policy-not-set"
        assert parsed[0]["compliance"] == ["cis", "pci-dss"]

    @patch("shutil.which")
    def test_normalize_findings(self, mock_which):
        """Test normalize_findings method"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)

        findings = [
            {
                "tool": "scoutsuite",
                "rule_id": "test-rule",
                "description": "Test description",
                "severity": "high",
                "provider": "aws",
                "service": "s3",
                "resource_type": "bucket",
                "remediation": "Fix it",
                "compliance": ["cis"],
                "references": ["https://example.com"],
                "flagged_items": 2,
                "checked_items": 5,
            }
        ]

        normalized = scanner.normalize_findings(findings)

        assert len(normalized) == 1
        assert normalized[0]["tool"] == "scoutsuite"
        assert normalized[0]["target"] == "aws:s3"
        assert normalized[0]["severity"] == "high"
        assert normalized[0]["compliance"] == ["cis"]


class TestCloudProviderEnum:
    """Test CloudProvider enum"""

    def test_provider_values(self):
        """Test provider enum values"""
        assert CloudProvider.AWS.value == "aws"
        assert CloudProvider.AZURE.value == "azure"
        assert CloudProvider.GCP.value == "gcp"
        assert CloudProvider.ALIBABA.value == "aliyun"
        assert CloudProvider.ORACLE.value == "oracle"


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    @patch("asyncio.run")
    def test_scoutsuite_scan_aws_tool(self, mock_run):
        """Test scoutsuite_scan_aws tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.provider = "aws"
        mock_result.scan_time = 120.0
        mock_result.report_path = "/tmp/report.json"
        mock_result.summary = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 3},
            "total_findings": 6,
        }

        mock_run.return_value = mock_result

        result = scoutsuite_scan_aws(profile="default")
        assert isinstance(result, str)
        assert "ScoutSuite" in result or "Scan" in result

    @patch("asyncio.run")
    def test_scoutsuite_scan_azure_tool(self, mock_run):
        """Test scoutsuite_scan_azure tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.report_path = "/tmp/azure_report.json"

        mock_run.return_value = mock_result

        result = scoutsuite_scan_azure()
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_scoutsuite_scan_gcp_tool(self, mock_run):
        """Test scoutsuite_scan_gcp tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.report_path = "/tmp/gcp_report.json"

        mock_run.return_value = mock_result

        result = scoutsuite_scan_gcp(project_id="test-project")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_scoutsuite_quick_scan_tool(self, mock_run):
        """Test scoutsuite_quick_scan tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.findings = []

        mock_run.return_value = mock_result

        result = scoutsuite_quick_scan("aws")
        assert isinstance(result, str)


class TestComplianceFrameworks:
    """Test compliance framework configuration"""

    @patch("shutil.which")
    def test_aws_compliance_frameworks(self, mock_which):
        """Test AWS compliance frameworks"""
        mock_which.return_value = "/usr/bin/scout"
        scanner = ScoutSuiteScanner(provider=CloudProvider.AWS)
        assert "cis" in scanner.COMPLIANCE_FRAMEWORKS["aws"]
        assert "pci-dss" in scanner.COMPLIANCE_FRAMEWORKS["aws"]
        assert "hipaa" in scanner.COMPLIANCE_FRAMEWORKS["aws"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

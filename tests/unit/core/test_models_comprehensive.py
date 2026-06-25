"""Comprehensive tests for core.models"""

from datetime import datetime

import pytest


class TestSeverity:
    """Test Severity enum"""

    def test_severity_values(self):
        from core.models import Severity

        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_from_string(self):
        from core.models import Severity

        assert Severity("critical") == Severity.CRITICAL
        assert Severity("high") == Severity.HIGH


class TestScanStatus:
    """Test ScanStatus enum"""

    def test_scan_status_values(self):
        from core.models import ScanStatus

        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"
        assert ScanStatus.CANCELLED.value == "cancelled"


class TestFinding:
    """Test Finding model"""

    def test_finding_creation(self):
        from core.models import Finding, Severity

        f = Finding(title="SQL Injection", severity=Severity.CRITICAL, description="SQL injection found", host="example.com")
        assert f.title == "SQL Injection"
        assert f.severity == Severity.CRITICAL

    def test_finding_with_port(self):
        from core.models import Finding, Severity

        f = Finding(title="Open Port", severity=Severity.MEDIUM, description="Port 80 open", host="example.com", port=80)
        assert f.port == 80

    def test_finding_with_cvss(self):
        from core.models import Finding, Severity

        f = Finding(title="Vuln", severity=Severity.HIGH, description="High severity vuln", host="example.com", cvss_score=8.5)
        assert f.cvss_score == 8.5

    def test_finding_with_cve(self):
        from core.models import Finding, Severity

        f = Finding(
            title="Known CVE",
            severity=Severity.CRITICAL,
            description="CVE found",
            host="example.com",
            cve_ids=["CVE-2024-1234"],
        )
        assert "CVE-2024-1234" in f.cve_ids

    def test_finding_with_remediation(self):
        from core.models import Finding, Severity

        f = Finding(
            title="Fixable",
            severity=Severity.LOW,
            description="Can be fixed",
            host="example.com",
            remediation="Update the package",
        )
        assert "Update" in f.remediation

    def test_finding_confidence_levels(self):
        from core.models import Finding, Severity

        f1 = Finding(title="T1", severity=Severity.LOW, description="D", host="h", confidence="confirmed")
        f2 = Finding(title="T2", severity=Severity.LOW, description="D", host="h", confidence="likely")
        f3 = Finding(title="T3", severity=Severity.LOW, description="D", host="h", confidence="possible")
        assert f1.confidence == "confirmed"
        assert f2.confidence == "likely"
        assert f3.confidence == "possible"

    def test_finding_with_tags(self):
        from core.models import Finding, Severity

        f = Finding(title="Tagged", severity=Severity.MEDIUM, description="Has tags", host="example.com", tags=["web", "sql"])
        assert "web" in f.tags

    def test_finding_with_service(self):
        from core.models import Finding, Severity

        f = Finding(
            title="Service Vuln", severity=Severity.HIGH, description="Service issue", host="example.com", service="nginx"
        )
        assert f.service == "nginx"


class TestScanResult:
    """Test ScanResult model"""

    def test_scan_result_creation(self):
        from core.models import ScanResult, ScanStatus

        r = ScanResult(scan_id="scan-001", target="example.com", status=ScanStatus.PENDING, started_at=datetime.now())
        assert r.scan_id == "scan-001"
        assert r.target == "example.com"

    def test_scan_result_with_findings(self):
        from core.models import Finding, ScanResult, ScanStatus, Severity

        f = Finding(title="Test", severity=Severity.LOW, description="Test", host="example.com")
        r = ScanResult(
            scan_id="scan-002", target="example.com", status=ScanStatus.COMPLETED, started_at=datetime.now(), findings=[f]
        )
        assert len(r.findings) == 1

    def test_scan_result_completed(self):
        from core.models import ScanResult, ScanStatus

        now = datetime.now()
        r = ScanResult(scan_id="scan-003", target="example.com", status=ScanStatus.COMPLETED, started_at=now, completed_at=now)
        assert r.completed_at is not None

    def test_scan_result_with_stats(self):
        from core.models import ScanResult, ScanStatus

        r = ScanResult(
            scan_id="scan-004",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=datetime.now(),
            stats={"ports_scanned": 1000, "hosts_scanned": 1},
        )
        assert r.stats["ports_scanned"] == 1000

    def test_scan_result_with_error(self):
        from core.models import ScanResult, ScanStatus

        r = ScanResult(
            scan_id="scan-005",
            target="example.com",
            status=ScanStatus.FAILED,
            started_at=datetime.now(),
            error_message="Connection timeout",
        )
        assert r.error_message == "Connection timeout"

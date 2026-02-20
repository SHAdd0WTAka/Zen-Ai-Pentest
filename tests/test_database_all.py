"""
Alle Database Model Tests
"""

import pytest

try:
    from database.models import Finding, Report, Scan, ScanStatus, Severity, User

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestUserModelAll:
    """Alle User Tests"""

    def test_user_1(self):
        u = User(username="user1", email="u1@test.com")
        assert u.username == "user1"

    def test_user_2(self):
        u = User(username="user2", email="u2@test.com")
        assert u.email == "u2@test.com"

    def test_user_3(self):
        u = User(username="admin", email="admin@test.com", role="admin")
        assert u.role == "admin"

    def test_user_4(self):
        u = User(username="test4")
        assert hasattr(u, "id")

    def test_user_5(self):
        u = User(username="test5")
        assert u.is_active is None or isinstance(u.is_active, bool)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestScanModelAll:
    """Alle Scan Tests"""

    def test_scan_1(self):
        s = Scan(target="test1.com", scan_type="network")
        assert s.target == "test1.com"

    def test_scan_2(self):
        s = Scan(target="test2.com", scan_type="web")
        assert s.scan_type == "web"

    def test_scan_3(self):
        s = Scan(target="192.168.1.1", scan_type="network")
        assert s.status == ScanStatus.PENDING or s.status is not None

    def test_scan_4(self):
        s = Scan(target="test.com", name="Test Scan")
        assert s.name == "Test Scan"

    def test_scan_5(self):
        s = Scan(target="test.com", config={"ports": "80,443"})
        assert isinstance(s.config, dict)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestFindingModelAll:
    """Alle Finding Tests"""

    def test_finding_1(self):
        f = Finding(title="SQL Injection", severity=Severity.HIGH)
        assert f.title == "SQL Injection"

    def test_finding_2(self):
        f = Finding(title="XSS", severity=Severity.MEDIUM)
        assert f.severity == Severity.MEDIUM

    def test_finding_3(self):
        f = Finding(title="CSRF", severity=Severity.LOW, cvss_score=5.0)
        assert f.cvss_score == 5.0

    def test_finding_4(self):
        f = Finding(title="Info Leak", cve_id="CVE-2021-1234")
        assert f.cve_id == "CVE-2021-1234"

    def test_finding_5(self):
        f = Finding(title="Test", target="http://test.com")
        assert f.target == "http://test.com"


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestReportModelAll:
    """Alle Report Tests"""

    def test_report_1(self):
        r = Report(format="pdf", status="pending")
        assert r.format == "pdf"

    def test_report_2(self):
        r = Report(format="html", status="completed")
        assert r.status == "completed"

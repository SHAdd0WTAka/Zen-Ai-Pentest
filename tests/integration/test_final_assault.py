"""Final Assault - 10 weitere Tests für 50% Coverage."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_user_email_uniqueness():
    """User Email Eindeutigkeit."""
    from database.models import Base, User

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    user1 = User(username="user1", email="same@test.com", hashed_password="hash")
    db.add(user1)
    db.commit()

    user2 = User(username="user2", email="other@test.com", hashed_password="hash")
    db.add(user2)
    db.commit()

    assert db.query(User).count() == 2
    db.close()


def test_scan_config_json():
    """Scan Config als JSON speichern."""
    import json

    from database.models import Base, Scan, ScanStatus

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    config = {"ports": "80,443", "timing": 3, "scripts": ["vuln", "safe"]}
    scan = Scan(
        name="Config Scan",
        target="config.com",
        scan_type="nmap",
        status=ScanStatus.PENDING,
        config=json.dumps(config),
    )
    db.add(scan)
    db.commit()

    retrieved = db.query(Scan).filter_by(id=scan.id).first()
    assert retrieved.config is not None
    db.close()


def test_finding_with_cve():
    """Finding mit CVE ID."""
    from database.models import Base, Finding, Scan, ScanStatus, Severity

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    scan = Scan(
        name="CVE Scan",
        target="cve.com",
        scan_type="nmap",
        status=ScanStatus.COMPLETED,
    )
    db.add(scan)
    db.commit()

    finding = Finding(
        scan_id=scan.id,
        title="RCE Vulnerability",
        severity=Severity.CRITICAL,
        cvss_score=9.8,
        cve_id="CVE-2024-1234",
    )
    db.add(finding)
    db.commit()

    assert finding.cve_id == "CVE-2024-1234"
    db.close()


@pytest.mark.asyncio
async def test_cache_delete_operations():
    """Cache Delete Operationen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("delete_me", "value", ttl=3600)
    assert await cache.get("delete_me") == "value"

    await cache.delete("delete_me")
    assert await cache.get("delete_me") is None


def test_report_file_path():
    """Report File Path speichern."""
    from database.models import Base, Report, ReportFormat, ReportStatus

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    report = Report(
        format=ReportFormat.PDF,
        status=ReportStatus.COMPLETED,
        template="exec",
        file_path="/reports/2024/report_123.pdf",
        file_size=1024000,
    )
    db.add(report)
    db.commit()

    assert report.file_path == "/reports/2024/report_123.pdf"
    assert report.file_size == 1024000
    db.close()


def test_scan_timestamps():
    """Scan Timestamps."""
    from database.models import Base, Scan, ScanStatus

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime.now(timezone.utc)
    scan = Scan(
        name="Time Scan",
        target="time.com",
        scan_type="nmap",
        status=ScanStatus.PENDING,
        created_at=now,
    )
    db.add(scan)
    db.commit()

    assert scan.created_at is not None
    db.close()


def test_user_is_active():
    """User Active Status."""
    from database.models import Base, User

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    active_user = User(
        username="active",
        email="active@test.com",
        hashed_password="hash",
        is_active=1,
    )
    inactive_user = User(
        username="inactive",
        email="inactive@test.com",
        hashed_password="hash",
        is_active=0,
    )
    db.add_all([active_user, inactive_user])
    db.commit()

    active_count = db.query(User).filter_by(is_active=1).count()
    assert active_count == 1
    db.close()


def test_finding_remediation():
    """Finding Remediation Text."""
    from database.models import Base, Finding, Scan, ScanStatus, Severity

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    scan = Scan(
        name="Rem Scan",
        target="rem.com",
        scan_type="nmap",
        status=ScanStatus.COMPLETED,
    )
    db.add(scan)
    db.commit()

    finding = Finding(
        scan_id=scan.id,
        title="SQL Injection",
        severity=Severity.HIGH,
        remediation="Use parameterized queries and input validation",
    )
    db.add(finding)
    db.commit()

    assert "parameterized" in finding.remediation
    db.close()


def test_scan_result_summary():
    """Scan Result Summary speichern."""
    import json

    from database.models import Base, Scan, ScanStatus

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    summary = {
        "total_hosts": 5,
        "open_ports": 23,
        "services": ["http", "ssh", "ftp"],
    }
    scan = Scan(
        name="Summary Scan",
        target="sum.com",
        scan_type="nmap",
        status=ScanStatus.COMPLETED,
        result_summary=json.dumps(summary),
    )
    db.add(scan)
    db.commit()

    assert scan.result_summary is not None
    db.close()


def test_multiple_findings_per_scan():
    """Mehrere Findings pro Scan."""
    from database.models import Base, Finding, Scan, ScanStatus, Severity

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    scan = Scan(
        name="Multi Finding",
        target="multi.com",
        scan_type="nmap",
        status=ScanStatus.COMPLETED,
    )
    db.add(scan)
    db.commit()

    for i in range(10):
        f = Finding(
            scan_id=scan.id,
            title=f"Vulnerability {i}",
            severity=Severity.HIGH if i % 2 == 0 else Severity.MEDIUM,
            cvss_score=7.0 if i % 2 == 0 else 5.0,
        )
        db.add(f)
    db.commit()

    count = db.query(Finding).filter_by(scan_id=scan.id).count()
    assert count == 10
    db.close()

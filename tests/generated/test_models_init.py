"""Generated Model Init Tests - Auto-generated."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database.auth_models import Base as AuthBase

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    AuthBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session()


def test_user_init(db_session):
    """Test User init."""
    from database.models import User
    obj = User(username="test", email="test@test.com", hashed_password="pass")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_scan_init(db_session):
    """Test Scan init."""
    from database.models import Scan
    obj = Scan(name="Test", target="test.com", scan_type="network", status="pending")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_finding_init(db_session):
    """Test Finding init."""
    from database.models import Finding
    obj = Finding(scan_id=1, title="Test", severity="high", target="test.com")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_report_init(db_session):
    """Test Report init."""
    from database.models import Report
    obj = Report(name="Test", format="pdf", status="pending")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_asset_init(db_session):
    """Test Asset init."""
    from database.models import Asset
    obj = Asset(name="Test", asset_type="domain")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_notification_init(db_session):
    """Test Notification init."""
    from database.models import Notification
    obj = Notification(user_id=1, type="info", message="Test")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_toolconfig_init(db_session):
    """Test ToolConfig init."""
    from database.models import ToolConfig
    obj = ToolConfig(tool_name="nmap", config={})
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_auditlog_init(db_session):
    """Test AuditLog init."""
    from database.models import AuditLog
    obj = AuditLog(action="CREATE", user_id=1)
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_vulnerabilitydb_init(db_session):
    """Test VulnerabilityDB init."""
    from database.models import VulnerabilityDB
    obj = VulnerabilityDB(cve_id="CVE-2021-1234", description="Test")
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

def test_apikey_init(db_session):
    """Test APIKey init."""
    from database.auth_models import APIKey
    obj = APIKey(name="Test", user_id=1)
    db_session.add(obj)
    db_session.commit()
    assert obj.id is not None

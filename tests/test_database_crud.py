"""Database CRUD Tests - SQLite In-Memory.

Target: +10% Coverage durch DB-Operationen.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Scan, Finding, User, Report, Asset, AuditLog
from database.auth_models import Base as AuthBase, APIKey


# Create in-memory test database
@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    AuthBase.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)
    AuthBase.metadata.drop_all(engine)


class TestUserCRUD:
    """Tests for User CRUD operations."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_pass_123",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"

    def test_read_user(self, db_session):
        """Test reading a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_pass_123",
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved is not None
        assert retrieved.email == "test@example.com"

    def test_update_user(self, db_session):
        """Test updating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_pass_123",
        )
        db_session.add(user)
        db_session.commit()
        
        user.is_active = False
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved.is_active is False

    def test_delete_user(self, db_session):
        """Test deleting a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_pass_123",
        )
        db_session.add(user)
        db_session.commit()
        
        db_session.delete(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved is None


class TestScanCRUD:
    """Tests for Scan CRUD operations."""

    def test_create_scan(self, db_session):
        """Test creating a scan."""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="network",
            status="pending",
        )
        db_session.add(scan)
        db_session.commit()
        
        assert scan.id is not None
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"

    def test_read_scan(self, db_session):
        """Test reading a scan."""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="network",
            status="pending",
        )
        db_session.add(scan)
        db_session.commit()
        
        retrieved = db_session.query(Scan).filter_by(name="Test Scan").first()
        assert retrieved is not None
        assert retrieved.target == "example.com"

    def test_update_scan_status(self, db_session):
        """Test updating scan status."""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="network",
            status="pending",
        )
        db_session.add(scan)
        db_session.commit()
        
        scan.status = "completed"
        db_session.commit()
        
        retrieved = db_session.query(Scan).filter_by(name="Test Scan").first()
        assert retrieved.status == "completed"

    def test_delete_scan(self, db_session):
        """Test deleting a scan."""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="network",
        )
        db_session.add(scan)
        db_session.commit()
        
        db_session.delete(scan)
        db_session.commit()
        
        retrieved = db_session.query(Scan).filter_by(name="Test Scan").first()
        assert retrieved is None


class TestFindingCRUD:
    """Tests for Finding CRUD operations."""

    def test_create_finding(self, db_session):
        """Test creating a finding."""
        finding = Finding(
            title="XSS Vulnerability",
            severity="high",
            description="Cross-site scripting found",
            target="example.com",
        )
        db_session.add(finding)
        db_session.commit()
        
        assert finding.id is not None
        assert finding.title == "XSS Vulnerability"
        assert finding.severity == "high"

    def test_read_finding(self, db_session):
        """Test reading a finding."""
        finding = Finding(
            title="SQL Injection",
            severity="critical",
            target="example.com",
        )
        db_session.add(finding)
        db_session.commit()
        
        retrieved = db_session.query(Finding).filter_by(title="SQL Injection").first()
        assert retrieved is not None
        assert retrieved.severity == "critical"


class TestAssetCRUD:
    """Tests for Asset CRUD operations."""

    def test_create_asset(self, db_session):
        """Test creating an asset."""
        asset = Asset(
            name="Example Asset",
            asset_type="domain",
            value="example.com",
        )
        db_session.add(asset)
        db_session.commit()
        
        assert asset.id is not None
        assert asset.name == "Example Asset"


class TestReportCRUD:
    """Tests for Report CRUD operations."""

    def test_create_report(self, db_session):
        """Test creating a report."""
        report = Report(
            name="Test Report",
            format="pdf",
            status="pending",
        )
        db_session.add(report)
        db_session.commit()
        
        assert report.id is not None
        assert report.name == "Test Report"


class TestAuditLogCRUD:
    """Tests for AuditLog CRUD operations."""

    def test_create_audit_log(self, db_session):
        """Test creating an audit log."""
        log = AuditLog(
            action="CREATE",
            entity_type="Scan",
            entity_id=1,
            user_id=1,
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.action == "CREATE"


class TestAPIKeyCRUD:
    """Tests for APIKey CRUD operations."""

    def test_create_api_key(self, db_session):
        """Test creating an API key."""
        key = APIKey(
            key="test_api_key_12345",
            name="Test Key",
            user_id=1,
        )
        db_session.add(key)
        db_session.commit()
        
        assert key.id is not None
        assert key.key == "test_api_key_12345"

    def test_read_api_key(self, db_session):
        """Test reading an API key."""
        key = APIKey(
            key="secret_key_123",
            name="Production Key",
            user_id=1,
        )
        db_session.add(key)
        db_session.commit()
        
        retrieved = db_session.query(APIKey).filter_by(key="secret_key_123").first()
        assert retrieved is not None
        assert retrieved.name == "Production Key"

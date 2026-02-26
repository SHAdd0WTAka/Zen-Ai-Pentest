"""Simple Database Tests - SQLite In-Memory.

Target: +5% Coverage durch grundlegende DB-Operationen.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Scan, Finding, User


@pytest.fixture
def db_session():
    """Create a fresh database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pass",
        )
        db_session.add(user)
        db_session.commit()
        assert user.id is not None
        assert user.email == "test@example.com"

    def test_user_query(self, db_session):
        """Test querying a user."""
        user = User(username="queryuser", email="query@test.com", hashed_password="pass")
        db_session.add(user)
        db_session.commit()
        
        result = db_session.query(User).filter_by(email="query@test.com").first()
        assert result is not None
        assert result.email == "query@test.com"


class TestScanModel:
    """Tests for Scan model."""

    def test_scan_creation(self, db_session):
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

    def test_scan_update_status(self, db_session):
        """Test updating scan status."""
        scan = Scan(
            name="Status Test",
            target="test.com",
            scan_type="web",
            status="pending",
        )
        db_session.add(scan)
        db_session.commit()
        
        scan.status = "running"
        db_session.commit()
        
        result = db_session.query(Scan).filter_by(name="Status Test").first()
        assert result.status == "running"


class TestFindingModel:
    """Tests for Finding model."""

    def test_finding_with_scan(self, db_session):
        """Test creating a finding with scan relationship."""
        scan = Scan(
            name="Finding Test Scan",
            target="example.com",
            scan_type="network",
            status="completed",
        )
        db_session.add(scan)
        db_session.commit()
        
        finding = Finding(
            scan_id=scan.id,
            title="Critical Vulnerability",
            severity="critical",
            target="example.com",
        )
        db_session.add(finding)
        db_session.commit()
        
        assert finding.id is not None
        assert finding.scan_id == scan.id
        assert finding.title == "Critical Vulnerability"

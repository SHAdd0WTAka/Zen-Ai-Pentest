"""Vertical Slice: Database Models - CRUD Operations.

Tests the complete CRUD cycle:
1. Create: Insert new records
2. Read: Query existing records
3. Update: Modify records
4. Delete: Remove records

Uses in-memory SQLite for fast, isolated tests.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    from database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.mark.asyncio
async def test_scan_model_crud_cycle(db_session):
    """Erstellt, liest, updated, löscht Scan in DB.

    Vertical slice covering:
    - database.models.Scan
    - database.models.ScanStatus
    """
    from database.models import Scan, ScanStatus

    # Create
    scan = Scan(
        name="Test Scan",
        target="example.com",
        scan_type="nmap",
        status=ScanStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        config={"ports": "80,443"},
    )
    db_session.add(scan)
    db_session.commit()

    scan_id = scan.id
    assert scan_id is not None

    # Read
    retrieved = db_session.query(Scan).filter_by(id=scan_id).first()
    assert retrieved is not None
    assert retrieved.target == "example.com"
    assert retrieved.status == ScanStatus.PENDING
    assert retrieved.name == "Test Scan"

    # Update
    retrieved.status = ScanStatus.RUNNING
    db_session.commit()

    # Verify Update
    updated = db_session.query(Scan).filter_by(id=scan_id).first()
    assert updated.status == ScanStatus.RUNNING

    # Delete
    db_session.delete(updated)
    db_session.commit()

    # Verify Delete
    deleted = db_session.query(Scan).filter_by(id=scan_id).first()
    assert deleted is None


@pytest.mark.asyncio
async def test_user_model_crud_with_relationships(db_session):
    """Testet User CRUD mit Scan-Beziehungen."""
    from database.models import Scan, ScanStatus, User

    # Create User
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_hash",
        role="operator",
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()

    user_id = user.id
    assert user_id is not None

    # Create Scan for User
    scan = Scan(
        name="User Test Scan",
        target="test.com",
        scan_type="nmap",
        status=ScanStatus.COMPLETED,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(scan)
    db_session.commit()

    # Verify relationship
    retrieved_user = db_session.query(User).filter_by(id=user_id).first()
    assert retrieved_user.username == "testuser"

    # Check scan association
    user_scans = db_session.query(Scan).filter_by(user_id=user_id).all()
    assert len(user_scans) == 1
    assert user_scans[0].target == "test.com"

    # Cleanup
    db_session.delete(scan)
    db_session.delete(retrieved_user)
    db_session.commit()


@pytest.mark.asyncio
async def test_finding_crud(db_session):
    """Testet Finding (Vulnerability) CRUD.

    Uses Finding model for vulnerability storage.
    """
    from database.models import Finding, Scan, ScanStatus, Severity

    # Create parent scan
    scan = Scan(
        name="Vulnerability Scan",
        target="vulnerable.com",
        scan_type="sqlmap",
        status=ScanStatus.COMPLETED,
    )
    db_session.add(scan)
    db_session.commit()

    # Create finding (use JSON string for SQLite compatibility)
    import json

    finding = Finding(
        scan_id=scan.id,
        title="SQL Injection",
        description="Parameter vulnerable to SQL injection",
        severity=Severity.CRITICAL,
        evidence=json.dumps({"payload": "' OR 1=1--"}),
        remediation="Use parameterized queries",
        cvss_score=9.8,
        cve_id="CVE-2023-1234",
        tool="sqlmap",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(finding)
    db_session.commit()

    finding_id = finding.id
    assert finding_id is not None

    # Verify
    retrieved = db_session.query(Finding).filter_by(id=finding_id).first()
    assert retrieved.severity == Severity.CRITICAL
    assert retrieved.cvss_score == 9.8
    assert retrieved.evidence is not None

    # Cleanup
    db_session.delete(retrieved)
    db_session.delete(scan)
    db_session.commit()


@pytest.mark.asyncio
async def test_database_indexes_performance(db_session):
    """Prüft dass Indizes für Performance-Queries existieren."""
    from sqlalchemy import inspect

    from database.models import User

    inspector = inspect(db_session.bind)

    # Check users table indexes
    user_indexes = inspector.get_indexes("users")
    index_names = [idx["name"] for idx in user_indexes]

    # Verify expected indexes
    assert any("username" in name for name in index_names)
    assert any("email" in name for name in index_names)

    # Check scans table
    scan_indexes = inspector.get_indexes("scans")
    assert len(scan_indexes) > 0

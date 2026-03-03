"""Vertical Slice 1: Database CRUD - Scan Model Lifecycle"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """In-memory DB für isolierte Tests."""
    from database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_scan_create_read(db_session):
    """Create & Read: Scan in DB speichern und lesen."""
    from database.models import Scan, ScanStatus

    # CREATE
    scan = Scan(
        name="Port Scan Test",
        target="example.com",
        scan_type="nmap",
        status=ScanStatus.PENDING,
        config={"ports": "80,443"},
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(scan)
    db_session.commit()

    scan_id = scan.id
    assert scan_id is not None

    # READ
    retrieved = db_session.query(Scan).filter_by(id=scan_id).first()
    assert retrieved.name == "Port Scan Test"
    assert retrieved.target == "example.com"
    assert retrieved.status == ScanStatus.PENDING


def test_scan_update_delete(db_session):
    """Update & Delete: Scan ändern und löschen."""
    from database.models import Scan, ScanStatus

    # Setup
    scan = Scan(
        name="Update Test",
        target="test.com",
        scan_type="nikto",
        status=ScanStatus.PENDING,
    )
    db_session.add(scan)
    db_session.commit()
    scan_id = scan.id

    # UPDATE
    scan.status = ScanStatus.RUNNING
    db_session.commit()

    updated = db_session.query(Scan).filter_by(id=scan_id).first()
    assert updated.status == ScanStatus.RUNNING

    # DELETE
    db_session.delete(updated)
    db_session.commit()

    deleted = db_session.query(Scan).filter_by(id=scan_id).first()
    assert deleted is None

"""Database Module Tests"""

from datetime import datetime

import pytest

from database.models import Finding, Scan, User


def test_scan_model():
    """Test Scan model."""
    scan = Scan(
        name="Test Scan",
        target="example.com",
        scan_type="network",
        status="pending",
    )
    assert scan.target == "example.com"
    assert scan.status == "pending"


def test_finding_model():
    """Test Finding model."""
    finding = Finding(
        title="XSS Vulnerability",
        severity="high",
        description="Found XSS",
        target="example.com",
    )
    assert finding.title == "XSS Vulnerability"
    assert finding.severity == "high"


def test_user_model():
    """Test User model."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_pass",
        is_active=True,
    )
    assert user.email == "test@example.com"
    assert user.is_active is True

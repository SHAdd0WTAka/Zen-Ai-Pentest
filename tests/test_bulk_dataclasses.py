"""Dataclass tests - Auto-generated."""

import pytest


def test_scan_create_dataclass():
    """Test ScanCreate dataclass."""
    from api.schemas import ScanCreate
    scan = ScanCreate(name="Test", target="example.com", scan_type="network")
    assert scan.name == "Test"
    assert scan.target == "example.com"


def test_scan_response_dataclass():
    """Test ScanResponse dataclass."""
    from api.schemas import ScanResponse
    scan = ScanResponse(id=1, name="Test", target="example.com", scan_type="network", status="pending")
    assert scan.id == 1
    assert scan.name == "Test"


def test_finding_response_dataclass():
    """Test FindingResponse dataclass."""
    from api.schemas import FindingResponse
    finding = FindingResponse(id=1, title="Test Finding", severity="high", target="example.com")
    assert finding.id == 1
    assert finding.title == "Test Finding"

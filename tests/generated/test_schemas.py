"""Generated Schema Tests - Auto-generated."""

import pytest
from api.schemas import *


def test_scancreate_create():
    """Test ScanCreate schema."""
    obj = ScanCreate(name="Test", target="test.com", scan_type="network")
    assert obj.name == "Test"
    assert obj.target == "test.com"
    assert obj.scan_type == "network"

def test_scanupdate_create():
    """Test ScanUpdate schema."""
    obj = ScanUpdate(status="running")
    assert obj.status == "running"

def test_findingcreate_create():
    """Test FindingCreate schema."""
    obj = FindingCreate(title="Test", severity="high", target="test.com")
    assert obj.title == "Test"
    assert obj.severity == "high"
    assert obj.target == "test.com"

def test_findingupdate_create():
    """Test FindingUpdate schema."""
    obj = FindingUpdate(severity="critical")
    assert obj.severity == "critical"

def test_usercreate_create():
    """Test UserCreate schema."""
    obj = UserCreate(username="test", email="test@test.com", password="pass")
    assert obj.username == "test"
    assert obj.email == "test@test.com"
    assert obj.password == "pass"

def test_userupdate_create():
    """Test UserUpdate schema."""
    obj = UserUpdate(email="new@test.com")
    assert obj.email == "new@test.com"

def test_reportcreate_create():
    """Test ReportCreate schema."""
    obj = ReportCreate(name="Test", format="pdf")
    assert obj.name == "Test"
    assert obj.format == "pdf"

def test_targetcreate_create():
    """Test TargetCreate schema."""
    obj = TargetCreate(name="Test", type="domain", value="test.com")
    assert obj.name == "Test"
    assert obj.type == "domain"
    assert obj.value == "test.com"

def test_toolexecute_create():
    """Test ToolExecute schema."""
    obj = ToolExecute(tool="nmap", target="test.com")
    assert obj.tool == "nmap"
    assert obj.target == "test.com"

def test_notificationcreate_create():
    """Test NotificationCreate schema."""
    obj = NotificationCreate(type="info", message="Test")
    assert obj.type == "info"
    assert obj.message == "Test"

def test_configupdate_create():
    """Test ConfigUpdate schema."""
    obj = ConfigUpdate(key="timeout", value="30")
    assert obj.key == "timeout"
    assert obj.value == "30"

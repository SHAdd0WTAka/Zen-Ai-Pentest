"""
Comprehensive tests for api/models/finding.py
Target: 90-100% coverage for Finding model, severity levels, and status tracking.

Tests cover:
- FindingSeverity enum (all 5 levels)
- FindingStatus enum (all 5 statuses)
- Finding class initialization with various parameters
- Finding methods: find_one, find_many, save, update, to_response
- Status transitions and edge cases
- Evidence attachments
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.models.finding import Finding, FindingSeverity, FindingStatus

# ============================================================================
# FindingSeverity Enum Tests
# ============================================================================


class TestFindingSeverity:
    """Test suite for FindingSeverity enum - all severity levels."""

    def test_severity_info(self):
        """Test INFO severity level."""
        assert FindingSeverity.INFO.value == "info"
        assert FindingSeverity.INFO.name == "INFO"

    def test_severity_low(self):
        """Test LOW severity level."""
        assert FindingSeverity.LOW.value == "low"
        assert FindingSeverity.LOW.name == "LOW"

    def test_severity_medium(self):
        """Test MEDIUM severity level."""
        assert FindingSeverity.MEDIUM.value == "medium"
        assert FindingSeverity.MEDIUM.name == "MEDIUM"

    def test_severity_high(self):
        """Test HIGH severity level."""
        assert FindingSeverity.HIGH.value == "high"
        assert FindingSeverity.HIGH.name == "HIGH"

    def test_severity_critical(self):
        """Test CRITICAL severity level."""
        assert FindingSeverity.CRITICAL.value == "critical"
        assert FindingSeverity.CRITICAL.name == "CRITICAL"

    def test_severity_enum_count(self):
        """Test that all 5 severity levels exist."""
        assert len(FindingSeverity) == 5
        severities = list(FindingSeverity)
        assert FindingSeverity.INFO in severities
        assert FindingSeverity.LOW in severities
        assert FindingSeverity.MEDIUM in severities
        assert FindingSeverity.HIGH in severities
        assert FindingSeverity.CRITICAL in severities

    def test_severity_from_value(self):
        """Test creating severity from string value."""
        assert FindingSeverity("info") == FindingSeverity.INFO
        assert FindingSeverity("low") == FindingSeverity.LOW
        assert FindingSeverity("medium") == FindingSeverity.MEDIUM
        assert FindingSeverity("high") == FindingSeverity.HIGH
        assert FindingSeverity("critical") == FindingSeverity.CRITICAL

    def test_severity_comparison_by_value(self):
        """Test severity level comparison by value."""
        severities = [
            FindingSeverity.INFO,
            FindingSeverity.LOW,
            FindingSeverity.MEDIUM,
            FindingSeverity.HIGH,
            FindingSeverity.CRITICAL,
        ]
        values = [s.value for s in severities]
        assert values == ["info", "low", "medium", "high", "critical"]

    def test_severity_invalid_value_raises_error(self):
        """Test that invalid severity value raises ValueError."""
        with pytest.raises(ValueError):
            FindingSeverity("invalid")


# ============================================================================
# FindingStatus Enum Tests
# ============================================================================


class TestFindingStatus:
    """Test suite for FindingStatus enum - all status values."""

    def test_status_open(self):
        """Test OPEN status."""
        assert FindingStatus.OPEN.value == "open"
        assert FindingStatus.OPEN.name == "OPEN"

    def test_status_in_progress(self):
        """Test IN_PROGRESS status."""
        assert FindingStatus.IN_PROGRESS.value == "in_progress"
        assert FindingStatus.IN_PROGRESS.name == "IN_PROGRESS"

    def test_status_resolved(self):
        """Test RESOLVED status."""
        assert FindingStatus.RESOLVED.value == "resolved"
        assert FindingStatus.RESOLVED.name == "RESOLVED"

    def test_status_false_positive(self):
        """Test FALSE_POSITIVE status."""
        assert FindingStatus.FALSE_POSITIVE.value == "false_positive"
        assert FindingStatus.FALSE_POSITIVE.name == "FALSE_POSITIVE"

    def test_status_risk_accepted(self):
        """Test RISK_ACCEPTED status."""
        assert FindingStatus.RISK_ACCEPTED.value == "risk_accepted"
        assert FindingStatus.RISK_ACCEPTED.name == "RISK_ACCEPTED"

    def test_status_enum_count(self):
        """Test that all 5 status values exist."""
        assert len(FindingStatus) == 5
        statuses = list(FindingStatus)
        assert FindingStatus.OPEN in statuses
        assert FindingStatus.IN_PROGRESS in statuses
        assert FindingStatus.RESOLVED in statuses
        assert FindingStatus.FALSE_POSITIVE in statuses
        assert FindingStatus.RISK_ACCEPTED in statuses

    def test_status_from_value(self):
        """Test creating status from string value."""
        assert FindingStatus("open") == FindingStatus.OPEN
        assert FindingStatus("in_progress") == FindingStatus.IN_PROGRESS
        assert FindingStatus("resolved") == FindingStatus.RESOLVED
        assert FindingStatus("false_positive") == FindingStatus.FALSE_POSITIVE
        assert FindingStatus("risk_accepted") == FindingStatus.RISK_ACCEPTED

    def test_status_invalid_value_raises_error(self):
        """Test that invalid status value raises ValueError."""
        with pytest.raises(ValueError):
            FindingStatus("invalid_status")


# ============================================================================
# Finding Class Initialization Tests
# ============================================================================


class TestFindingInitialization:
    """Test suite for Finding class initialization."""

    def test_basic_finding_creation(self):
        """Test creating a finding with minimal required fields."""
        finding = Finding(
            title="Test Finding",
            description="This is a test finding description",
        )
        assert finding.title == "Test Finding"
        assert finding.description == "This is a test finding description"
        assert finding.id == "finding-stub-id"
        assert finding.severity == FindingSeverity.MEDIUM  # default
        assert finding.status == FindingStatus.OPEN  # default

    def test_finding_with_all_severity_levels(self):
        """Test creating findings with all severity levels."""
        for severity in FindingSeverity:
            finding = Finding(
                title=f"Test {severity.name}",
                description=f"Finding with {severity.value} severity",
                severity=severity,
            )
            assert finding.severity == severity
            assert finding.title == f"Test {severity.name}"

    def test_finding_with_all_status_values(self):
        """Test creating findings with all status values."""
        for status in FindingStatus:
            finding = Finding(
                title=f"Test {status.name}",
                description=f"Finding with {status.value} status",
                status=status,
            )
            assert finding.status == status
            assert finding.title == f"Test {status.name}"

    def test_finding_with_scan_id(self):
        """Test creating a finding with scan_id."""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            scan_id="scan-12345",
        )
        assert finding.scan_id == "scan-12345"

    def test_finding_with_target(self):
        """Test creating a finding with target."""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            target="example.com",
        )
        assert finding.target == "example.com"

    def test_finding_with_tool(self):
        """Test creating a finding with tool name."""
        finding = Finding(title="Test Finding", description="Test description", tool="nmap")
        assert finding.tool == "nmap"

    def test_finding_with_cvss_score(self):
        """Test creating a finding with CVSS score."""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            cvss_score=7.5,
        )
        assert finding.cvss_score == 7.5

    def test_finding_with_zero_cvss_score(self):
        """Test creating a finding with zero CVSS score."""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            cvss_score=0.0,
        )
        assert finding.cvss_score == 0.0

    def test_finding_with_max_cvss_score(self):
        """Test creating a finding with maximum CVSS score."""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            cvss_score=10.0,
        )
        assert finding.cvss_score == 10.0

    def test_finding_with_remediation(self):
        """Test creating a finding with remediation advice."""
        remediation = "Update to the latest version of the software"
        finding = Finding(
            title="Test Finding",
            description="Test description",
            remediation=remediation,
        )
        assert finding.remediation == remediation

    def test_finding_full_initialization(self):
        """Test creating a finding with all parameters."""
        evidence = {"request": "GET /test", "response": "200 OK"}
        cwe_ids = ["CWE-79", "CWE-89"]
        cve_ids = ["CVE-2024-1234"]
        references = ["https://example.com/ref1", "https://example.com/ref2"]

        finding = Finding(
            title="Full Test Finding",
            description="Complete finding with all fields",
            severity=FindingSeverity.HIGH,
            status=FindingStatus.IN_PROGRESS,
            scan_id="scan-abc-123",
            target="192.168.1.1",
            tool="sqlmap",
            evidence=evidence,
            remediation="Apply security patch",
            cvss_score=8.5,
            cwe_ids=cwe_ids,
            cve_ids=cve_ids,
            references=references,
        )

        assert finding.title == "Full Test Finding"
        assert finding.description == "Complete finding with all fields"
        assert finding.severity == FindingSeverity.HIGH
        assert finding.status == FindingStatus.IN_PROGRESS
        assert finding.scan_id == "scan-abc-123"
        assert finding.target == "192.168.1.1"
        assert finding.tool == "sqlmap"
        assert finding.evidence == evidence
        assert finding.remediation == "Apply security patch"
        assert finding.cvss_score == 8.5
        assert finding.cwe_ids == cwe_ids
        assert finding.cve_ids == cve_ids
        assert finding.references == references

    def test_finding_timestamps_created(self):
        """Test that finding has created_at and updated_at timestamps."""
        before = datetime.now(timezone.utc)
        finding = Finding(title="Test", description="Test")
        after = datetime.now(timezone.utc)

        assert isinstance(finding.created_at, datetime)
        assert isinstance(finding.updated_at, datetime)
        assert before <= finding.created_at <= after
        assert before <= finding.updated_at <= after

    def test_finding_resolved_fields_default_none(self):
        """Test that resolved_at and resolved_by default to None."""
        finding = Finding(title="Test", description="Test")
        assert finding.resolved_at is None
        assert finding.resolved_by is None


# ============================================================================
# Finding Evidence Tests
# ============================================================================


class TestFindingEvidence:
    """Test suite for finding evidence attachments."""

    def test_finding_with_empty_evidence_dict(self):
        """Test creating finding with empty evidence dict."""
        finding = Finding(title="Test", description="Test", evidence={})
        assert finding.evidence == {}

    def test_finding_with_evidence_none_defaults_to_empty_dict(self):
        """Test that evidence defaults to empty dict when None."""
        finding = Finding(title="Test", description="Test", evidence=None)
        assert finding.evidence == {}

    def test_finding_with_http_evidence(self):
        """Test creating finding with HTTP request/response evidence."""
        evidence = {
            "request": "GET /api/users HTTP/1.1\nHost: example.com",
            "response": "HTTP/1.1 200 OK\nContent-Type: application/json",
            "screenshot": "base64encoded...",
        }
        finding = Finding(
            title="XSS Vulnerability",
            description="Reflected XSS found",
            evidence=evidence,
        )
        assert finding.evidence["request"] == evidence["request"]
        assert finding.evidence["response"] == evidence["response"]
        assert finding.evidence["screenshot"] == evidence["screenshot"]

    def test_finding_with_command_output_evidence(self):
        """Test creating finding with command output evidence."""
        evidence = {
            "command": "nmap -sV 192.168.1.1",
            "output": "22/tcp open  ssh\n80/tcp open  http",
            "exit_code": 0,
        }
        finding = Finding(
            title="Open Ports",
            description="Multiple open ports detected",
            evidence=evidence,
        )
        assert finding.evidence["command"] == "nmap -sV 192.168.1.1"
        assert finding.evidence["exit_code"] == 0

    def test_finding_with_nested_evidence(self):
        """Test creating finding with nested evidence structure."""
        evidence = {
            "vulnerability": {
                "type": "SQL Injection",
                "parameter": "id",
                "payload": "' OR '1'='1",
            },
            "database": {
                "version": "MySQL 8.0",
                "tables": ["users", "accounts"],
            },
        }
        finding = Finding(
            title="SQL Injection",
            description="SQLi in id parameter",
            evidence=evidence,
        )
        assert finding.evidence["vulnerability"]["type"] == "SQL Injection"
        assert finding.evidence["database"]["tables"] == ["users", "accounts"]


# ============================================================================
# Finding List Fields Tests
# ============================================================================


class TestFindingListFields:
    """Test suite for list fields in Finding (cwe_ids, cve_ids, references)."""

    def test_finding_cwe_ids_default_empty_list(self):
        """Test that cwe_ids defaults to empty list."""
        finding = Finding(title="Test", description="Test")
        assert finding.cwe_ids == []

    def test_finding_cwe_ids_default_empty_when_none(self):
        """Test that cwe_ids defaults to empty list when None passed."""
        finding = Finding(title="Test", description="Test", cwe_ids=None)
        assert finding.cwe_ids == []

    def test_finding_cwe_ids_with_values(self):
        """Test creating finding with CWE IDs."""
        finding = Finding(
            title="XSS",
            description="Cross-site scripting",
            cwe_ids=["CWE-79", "CWE-80"],
        )
        assert finding.cwe_ids == ["CWE-79", "CWE-80"]

    def test_finding_cve_ids_default_empty_list(self):
        """Test that cve_ids defaults to empty list."""
        finding = Finding(title="Test", description="Test")
        assert finding.cve_ids == []

    def test_finding_cve_ids_default_empty_when_none(self):
        """Test that cve_ids defaults to empty list when None passed."""
        finding = Finding(title="Test", description="Test", cve_ids=None)
        assert finding.cve_ids == []

    def test_finding_cve_ids_with_values(self):
        """Test creating finding with CVE IDs."""
        finding = Finding(
            title="Known Vulnerability",
            description="Known CVE",
            cve_ids=["CVE-2024-1234", "CVE-2024-5678"],
        )
        assert finding.cve_ids == ["CVE-2024-1234", "CVE-2024-5678"]

    def test_finding_references_default_empty_list(self):
        """Test that references defaults to empty list."""
        finding = Finding(title="Test", description="Test")
        assert finding.references == []

    def test_finding_references_default_empty_when_none(self):
        """Test that references defaults to empty list when None passed."""
        finding = Finding(title="Test", description="Test", references=None)
        assert finding.references == []

    def test_finding_references_with_urls(self):
        """Test creating finding with reference URLs."""
        refs = [
            "https://owasp.org/www-community/attacks/xss/",
            "https://cwe.mitre.org/data/definitions/79.html",
        ]
        finding = Finding(title="XSS", description="XSS vulnerability", references=refs)
        assert finding.references == refs


# ============================================================================
# Finding Async Methods Tests
# ============================================================================


class TestFindingAsyncMethods:
    """Test suite for Finding async class methods."""

    @pytest.mark.asyncio
    async def test_find_one_returns_none(self):
        """Test that find_one returns None (stub behavior)."""
        result = await Finding.find_one(id="some-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_one_with_various_kwargs(self):
        """Test find_one with various keyword arguments."""
        result = await Finding.find_one(scan_id="scan-123")
        assert result is None

        result = await Finding.find_one(title="Test", severity="high")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_many_returns_empty_list(self):
        """Test that find_many returns empty list (stub behavior)."""
        result = await Finding.find_many()
        assert result == []

    @pytest.mark.asyncio
    async def test_find_many_with_filters_returns_empty_list(self):
        """Test find_many with filters returns empty list."""
        result = await Finding.find_many(severity="high", status="open")
        assert result == []

    @pytest.mark.asyncio
    async def test_find_many_returns_list_type(self):
        """Test that find_many returns a list type."""
        result = await Finding.find_many()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_save_does_nothing(self):
        """Test that save method completes without error."""
        finding = Finding(title="Test", description="Test")
        await finding.save()  # Should not raise

    @pytest.mark.asyncio
    async def test_save_preserves_attributes(self):
        """Test that save doesn't modify finding attributes."""
        finding = Finding(title="Test", description="Test", severity=FindingSeverity.HIGH)
        await finding.save()
        assert finding.title == "Test"
        assert finding.severity == FindingSeverity.HIGH


# ============================================================================
# Finding Update Tests
# ============================================================================


class TestFindingUpdate:
    """Test suite for Finding update method."""

    @pytest.mark.asyncio
    async def test_update_single_field(self):
        """Test updating a single field."""
        finding = Finding(title="Old Title", description="Test")
        await finding.update(title="New Title")
        assert finding.title == "New Title"
        assert finding.description == "Test"  # unchanged

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        finding = Finding(title="Old", description="Old desc", severity=FindingSeverity.LOW)
        await finding.update(title="New", description="New desc", severity=FindingSeverity.HIGH)
        assert finding.title == "New"
        assert finding.description == "New desc"
        assert finding.severity == FindingSeverity.HIGH

    @pytest.mark.asyncio
    async def test_update_status_transition_open_to_resolved(self):
        """Test status transition from OPEN to RESOLVED."""
        finding = Finding(title="Test", description="Test", status=FindingStatus.OPEN)
        await finding.update(status=FindingStatus.RESOLVED)
        assert finding.status == FindingStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_update_status_transition_open_to_in_progress(self):
        """Test status transition from OPEN to IN_PROGRESS."""
        finding = Finding(title="Test", description="Test", status=FindingStatus.OPEN)
        await finding.update(status=FindingStatus.IN_PROGRESS)
        assert finding.status == FindingStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_status_to_false_positive(self):
        """Test marking finding as false positive."""
        finding = Finding(title="Test", description="Test")
        await finding.update(status=FindingStatus.FALSE_POSITIVE)
        assert finding.status == FindingStatus.FALSE_POSITIVE

    @pytest.mark.asyncio
    async def test_update_status_to_risk_accepted(self):
        """Test marking finding as risk accepted."""
        finding = Finding(title="Test", description="Test")
        await finding.update(status=FindingStatus.RISK_ACCEPTED)
        assert finding.status == FindingStatus.RISK_ACCEPTED

    @pytest.mark.asyncio
    async def test_update_all_status_transitions(self):
        """Test all possible status transitions."""
        for initial_status in FindingStatus:
            for new_status in FindingStatus:
                finding = Finding(title="Test", description="Test", status=initial_status)
                await finding.update(status=new_status)
                assert finding.status == new_status, f"Failed transition from {initial_status} to {new_status}"

    @pytest.mark.asyncio
    async def test_update_severity_levels(self):
        """Test updating severity to all levels."""
        finding = Finding(title="Test", description="Test")

        for severity in FindingSeverity:
            await finding.update(severity=severity)
            assert finding.severity == severity

    @pytest.mark.asyncio
    async def test_update_cvss_score(self):
        """Test updating CVSS score."""
        finding = Finding(title="Test", description="Test", cvss_score=5.0)
        await finding.update(cvss_score=9.0)
        assert finding.cvss_score == 9.0

    @pytest.mark.asyncio
    async def test_update_remediation(self):
        """Test updating remediation field."""
        finding = Finding(title="Test", description="Test")
        await finding.update(remediation="Apply patch immediately")
        assert finding.remediation == "Apply patch immediately"

    @pytest.mark.asyncio
    async def test_update_evidence(self):
        """Test updating evidence."""
        finding = Finding(title="Test", description="Test", evidence={"old": "data"})
        new_evidence = {"new": "evidence", "screenshot": "base64"}
        await finding.update(evidence=new_evidence)
        assert finding.evidence == new_evidence

    @pytest.mark.asyncio
    async def test_update_cwe_ids(self):
        """Test updating CWE IDs."""
        finding = Finding(title="Test", description="Test", cwe_ids=["CWE-79"])
        await finding.update(cwe_ids=["CWE-79", "CWE-80", "CWE-81"])
        assert finding.cwe_ids == ["CWE-79", "CWE-80", "CWE-81"]

    @pytest.mark.asyncio
    async def test_update_cve_ids(self):
        """Test updating CVE IDs."""
        finding = Finding(title="Test", description="Test")
        await finding.update(cve_ids=["CVE-2024-9999"])
        assert finding.cve_ids == ["CVE-2024-9999"]

    @pytest.mark.asyncio
    async def test_update_references(self):
        """Test updating references."""
        finding = Finding(title="Test", description="Test")
        new_refs = ["https://example.com/1", "https://example.com/2"]
        await finding.update(references=new_refs)
        assert finding.references == new_refs

    @pytest.mark.asyncio
    async def test_update_updates_timestamp(self):
        """Test that update modifies the updated_at timestamp."""
        finding = Finding(title="Test", description="Test")
        original_updated_at = finding.updated_at

        # Small delay to ensure timestamp difference
        import asyncio

        await asyncio.sleep(0.01)

        await finding.update(title="New Title")
        assert finding.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_nonexistent_attribute(self):
        """Test updating an attribute that doesn't exist creates it."""
        finding = Finding(title="Test", description="Test")
        await finding.update(new_field="new value")
        assert finding.new_field == "new value"

    @pytest.mark.asyncio
    async def test_update_resolved_fields(self):
        """Test updating resolved fields."""
        from datetime import datetime, timezone

        resolved_time = datetime.now(timezone.utc)
        finding = Finding(title="Test", description="Test")

        await finding.update(resolved_at=resolved_time, resolved_by="admin@example.com")
        assert finding.resolved_at == resolved_time
        assert finding.resolved_by == "admin@example.com"


# ============================================================================
# Finding to_response Tests
# ============================================================================


class TestFindingToResponse:
    """Test suite for Finding to_response method."""

    def test_to_response_basic(self):
        """Test basic to_response conversion."""
        finding = Finding(title="Test", description="Test desc")
        response = finding.to_response()

        assert isinstance(response, dict)
        assert response["id"] == "finding-stub-id"
        assert response["title"] == "Test"
        assert response["description"] == "Test desc"
        assert response["severity"] == "medium"
        assert response["status"] == "open"

    def test_to_response_all_severities(self):
        """Test to_response with all severity levels."""
        for severity in FindingSeverity:
            finding = Finding(title="Test", description="Test", severity=severity)
            response = finding.to_response()
            assert response["severity"] == severity.value

    def test_to_response_all_statuses(self):
        """Test to_response with all status values."""
        for status in FindingStatus:
            finding = Finding(title="Test", description="Test", status=status)
            response = finding.to_response()
            assert response["status"] == status.value

    def test_to_response_with_all_fields(self):
        """Test to_response with all fields populated."""
        evidence = {"request": "GET /", "response": "200 OK"}
        finding = Finding(
            title="Full Finding",
            description="Complete description",
            severity=FindingSeverity.CRITICAL,
            status=FindingStatus.IN_PROGRESS,
            scan_id="scan-123",
            target="target.example.com",
            tool="custom-scanner",
            evidence=evidence,
            remediation="Fix immediately",
            cvss_score=9.8,
            cwe_ids=["CWE-89"],
            cve_ids=["CVE-2024-1234"],
            references=["https://example.com"],
        )

        response = finding.to_response()

        assert response["title"] == "Full Finding"
        assert response["description"] == "Complete description"
        assert response["severity"] == "critical"
        assert response["status"] == "in_progress"
        assert response["scan_id"] == "scan-123"
        assert response["target"] == "target.example.com"
        assert response["tool"] == "custom-scanner"
        assert response["evidence"] == evidence
        assert response["remediation"] == "Fix immediately"
        assert response["cvss_score"] == 9.8
        assert response["cwe_ids"] == ["CWE-89"]
        assert response["cve_ids"] == ["CVE-2024-1234"]
        assert response["references"] == ["https://example.com"]

    def test_to_response_timestamps_isoformat(self):
        """Test that timestamps are in ISO format."""
        finding = Finding(title="Test", description="Test")
        response = finding.to_response()

        # Should be string in ISO format, not datetime object
        assert isinstance(response["created_at"], str)
        assert isinstance(response["updated_at"], str)

        # Verify it can be parsed back to datetime
        parsed = datetime.fromisoformat(response["created_at"])
        assert isinstance(parsed, datetime)

    def test_to_response_id_is_string(self):
        """Test that id in response is a string."""
        finding = Finding(title="Test", description="Test")
        response = finding.to_response()
        assert isinstance(response["id"], str)
        assert response["id"] == "finding-stub-id"

    def test_to_response_with_none_values(self):
        """Test to_response handles None values correctly."""
        finding = Finding(
            title="Test",
            description="Test",
            scan_id=None,
            target=None,
            tool=None,
            remediation=None,
            cvss_score=None,
        )
        response = finding.to_response()

        assert response["scan_id"] is None
        assert response["target"] is None
        assert response["tool"] is None
        assert response["remediation"] is None
        assert response["cvss_score"] is None

    def test_to_response_empty_lists(self):
        """Test to_response with empty lists."""
        finding = Finding(title="Test", description="Test")
        response = finding.to_response()

        assert response["cwe_ids"] == []
        assert response["cve_ids"] == []
        assert response["references"] == []

    def test_to_response_evidence_empty_dict(self):
        """Test to_response with empty evidence dict."""
        finding = Finding(title="Test", description="Test")
        response = finding.to_response()
        assert response["evidence"] == {}


# ============================================================================
# Finding Edge Cases Tests
# ============================================================================


class TestFindingEdgeCases:
    """Test suite for Finding edge cases."""

    def test_finding_with_empty_title(self):
        """Test finding with empty title."""
        finding = Finding(title="", description="Test")
        assert finding.title == ""

    def test_finding_with_empty_description(self):
        """Test finding with empty description."""
        finding = Finding(title="Test", description="")
        assert finding.description == ""

    def test_finding_with_long_title(self):
        """Test finding with very long title."""
        long_title = "A" * 1000
        finding = Finding(title=long_title, description="Test")
        assert finding.title == long_title

    def test_finding_with_long_description(self):
        """Test finding with very long description."""
        long_desc = "B" * 5000
        finding = Finding(title="Test", description=long_desc)
        assert finding.description == long_desc

    def test_finding_with_special_characters(self):
        """Test finding with special characters in fields."""
        finding = Finding(
            title="<script>alert('XSS')</script>",
            description="Description with unicode: 你好世界 🌍 émojis",
            target="https://example.com/path?param=value&other=test",
        )
        assert "<script>" in finding.title
        assert "你好世界" in finding.description

    def test_finding_with_unicode(self):
        """Test finding with unicode characters."""
        finding = Finding(
            title="日本語タイトル",
            description="中文描述",
            target="ドメイン.example.com",
        )
        assert finding.title == "日本語タイトル"
        assert finding.description == "中文描述"

    def test_finding_evidence_with_complex_nested_structure(self):
        """Test finding with deeply nested evidence."""
        evidence = {"level1": {"level2": {"level3": {"data": [1, 2, 3], "nested": {"key": "value"}}}}}
        finding = Finding(title="Test", description="Test", evidence=evidence)
        assert finding.evidence["level1"]["level2"]["level3"]["data"] == [
            1,
            2,
            3,
        ]

    def test_finding_with_negative_cvss(self):
        """Test finding with negative CVSS score (edge case)."""
        finding = Finding(title="Test", description="Test", cvss_score=-1.0)
        assert finding.cvss_score == -1.0

    def test_finding_with_very_high_cvss(self):
        """Test finding with CVSS score above 10 (edge case)."""
        finding = Finding(title="Test", description="Test", cvss_score=15.0)
        assert finding.cvss_score == 15.0

    @pytest.mark.asyncio
    async def test_multiple_updates_same_field(self):
        """Test multiple updates to the same field."""
        finding = Finding(title="Original", description="Test")

        await finding.update(title="First")
        assert finding.title == "First"

        await finding.update(title="Second")
        assert finding.title == "Second"

        await finding.update(title="Third")
        assert finding.title == "Third"

    @pytest.mark.asyncio
    async def test_update_preserves_unmodified_fields(self):
        """Test that update preserves fields not being modified."""
        finding = Finding(
            title="Title",
            description="Description",
            severity=FindingSeverity.HIGH,
            status=FindingStatus.OPEN,
            target="example.com",
        )

        await finding.update(title="New Title")

        assert finding.description == "Description"
        assert finding.severity == FindingSeverity.HIGH
        assert finding.status == FindingStatus.OPEN
        assert finding.target == "example.com"


# ============================================================================
# Finding Integration Tests
# ============================================================================


class TestFindingIntegration:
    """Integration-style tests for Finding workflows."""

    @pytest.mark.asyncio
    async def test_full_finding_lifecycle(self):
        """Test complete finding lifecycle from creation to resolution."""
        # Create new finding
        finding = Finding(
            title="SQL Injection",
            description="SQL injection in login form",
            severity=FindingSeverity.HIGH,
            target="example.com/login",
            tool="sqlmap",
        )

        assert finding.status == FindingStatus.OPEN

        # Move to in progress
        await finding.update(status=FindingStatus.IN_PROGRESS)
        assert finding.status == FindingStatus.IN_PROGRESS

        # Add remediation
        await finding.update(
            remediation="Use parameterized queries",
            cvss_score=8.5,
            cwe_ids=["CWE-89"],
            cve_ids=["CVE-2024-1234"],
        )

        # Mark as resolved
        from datetime import datetime, timezone

        resolved_time = datetime.now(timezone.utc)
        await finding.update(
            status=FindingStatus.RESOLVED,
            resolved_at=resolved_time,
            resolved_by="security@example.com",
        )

        assert finding.status == FindingStatus.RESOLVED
        assert finding.resolved_at == resolved_time
        assert finding.resolved_by == "security@example.com"

        # Verify response format
        response = finding.to_response()
        assert response["status"] == "resolved"
        assert response["severity"] == "high"
        assert response["cvss_score"] == 8.5

    @pytest.mark.asyncio
    async def test_false_positive_workflow(self):
        """Test marking finding as false positive."""
        finding = Finding(
            title="Potential Vulnerability",
            description="May be a vulnerability",
            severity=FindingSeverity.MEDIUM,
        )

        await finding.update(
            status=FindingStatus.FALSE_POSITIVE,
            evidence={"analysis": "Verified as not exploitable"},
        )

        assert finding.status == FindingStatus.FALSE_POSITIVE
        assert finding.evidence["analysis"] == "Verified as not exploitable"

    @pytest.mark.asyncio
    async def test_risk_acceptance_workflow(self):
        """Test risk acceptance workflow."""
        finding = Finding(
            title="Low Priority Issue",
            description="Low impact issue",
            severity=FindingSeverity.LOW,
        )

        await finding.update(
            status=FindingStatus.RISK_ACCEPTED,
            remediation="Risk accepted due to low impact",
        )

        assert finding.status == FindingStatus.RISK_ACCEPTED
        response = finding.to_response()
        assert response["status"] == "risk_accepted"

    def test_finding_types_variations(self):
        """Test different types of security findings."""
        findings = [
            {
                "title": "XSS Vulnerability",
                "description": "Reflected XSS in search parameter",
                "severity": FindingSeverity.HIGH,
                "cwe_ids": ["CWE-79"],
            },
            {
                "title": "Missing Security Headers",
                "description": "X-Frame-Options header not set",
                "severity": FindingSeverity.MEDIUM,
                "cwe_ids": ["CWE-693"],
            },
            {
                "title": "Information Disclosure",
                "description": "Server version exposed in headers",
                "severity": FindingSeverity.LOW,
                "cwe_ids": ["CWE-200"],
            },
            {
                "title": "Remote Code Execution",
                "description": "Unauthenticated RCE vulnerability",
                "severity": FindingSeverity.CRITICAL,
                "cwe_ids": ["CWE-94"],
                "cvss_score": 9.8,
            },
            {
                "title": "SSL Certificate Info",
                "description": "Certificate expires in 30 days",
                "severity": FindingSeverity.INFO,
                "cwe_ids": [],
            },
        ]

        for finding_data in findings:
            finding = Finding(**finding_data)
            response = finding.to_response()
            assert response["title"] == finding_data["title"]
            assert response["severity"] == finding_data["severity"].value


# ============================================================================
# Module Import Tests
# ============================================================================


class TestModuleImports:
    """Test suite for module imports."""

    def test_import_finding_class(self):
        """Test that Finding class can be imported."""
        from api.models.finding import Finding

        assert Finding is not None
        assert callable(Finding)

    def test_import_finding_severity(self):
        """Test that FindingSeverity enum can be imported."""
        from api.models.finding import FindingSeverity

        assert FindingSeverity is not None

    def test_import_finding_status(self):
        """Test that FindingStatus enum can be imported."""
        from api.models.finding import FindingStatus

        assert FindingStatus is not None

    def test_import_all_from_module(self):
        """Test that all exports can be imported."""
        from api.models.finding import Finding, FindingSeverity, FindingStatus

        assert all([Finding, FindingSeverity, FindingStatus])

    def test_module_docstring(self):
        """Test that module has docstring."""
        import api.models.finding as finding_module

        assert finding_module.__doc__ is not None
        assert "Finding model" in finding_module.__doc__

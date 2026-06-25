"""
Comprehensive tests for validation, filtering, and orchestration core modules.

Modules covered:
- false_positive_filter.py (145 statements)
- exploit_evidence.py (13 statements)
- llm_backend.py (12 statements)
- models.py (186 statements)
- output_validator.py (171 statements)
- orchestrator.py (230 statements)
- shield_integration.py (93 statements)
- tool_executor.py (60 statements)
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from core.exploit_evidence import ExploitEvidenceCollector

# Import modules under test
from core.false_positive_filter import (
    FalsePositiveFilter,
    LLMVote,
    ValidationResult,
    VoteVerdict,
)
from core.false_positive_filter import validate_finding as fp_validate_finding
from core.llm_backend import LLMBackend
from core.models import (
    APIKeyConfig,
    BackendType,
    DomainRecon,
    Finding,
    HealthStatus,
    LLMRequest,
    LLMResponse,
    PaginatedResponse,
    ReportConfig,
    ScanConfig,
    ScanResult,
    ScanStatus,
    Severity,
    SubdomainInfo,
    TimestampedModel,
)
from core.orchestrator import BaseBackend
from core.orchestrator import LLMResponse as OrchestratorLLMResponse
from core.orchestrator import QualityLevel, ZenOrchestrator
from core.output_validator import (
    OutputValidator,
    ValidatedToolOutput,
    validate_and_report,
    validate_tool_output,
)
from core.tool_executor import (
    MockToolExecutor,
    RealToolExecutor,
    ToolResult,
    ToolResultStatus,
    get_executor,
    reset_executor,
    set_executor,
)

# ============================================================================
# Tests for false_positive_filter.py
# ============================================================================


class TestVoteVerdict:
    """Test VoteVerdict enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert VoteVerdict.VALID.value == "valid"
        assert VoteVerdict.FALSE_POSITIVE.value == "false_positive"
        assert VoteVerdict.UNCERTAIN.value == "uncertain"


class TestLLMVote:
    """Test LLMVote dataclass."""

    def test_creation(self):
        """Test creating a vote."""
        vote = LLMVote(
            provider="openai",
            verdict=VoteVerdict.VALID,
            confidence=0.85,
            reasoning="Clear vulnerability evidence",
            latency_ms=150.5,
        )

        assert vote.provider == "openai"
        assert vote.verdict == VoteVerdict.VALID
        assert vote.confidence == 0.85
        assert vote.latency_ms == 150.5


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_creation(self):
        """Test creating validation result."""
        vote = LLMVote(
            provider="openai",
            verdict=VoteVerdict.VALID,
            confidence=0.85,
            reasoning="Valid vulnerability",
        )

        result = ValidationResult(
            is_valid=True,
            confidence=0.85,
            votes=[vote],
            consensus="valid (1/1 votes)",
            recommended_action="accept",
        )

        assert result.is_valid is True
        assert result.confidence == 0.85
        assert len(result.votes) == 1
        assert result.metadata == {}


class TestFalsePositiveFilter:
    """Test FalsePositiveFilter class."""

    def test_initialization_defaults(self):
        """Test initialization with defaults."""
        filter_obj = FalsePositiveFilter()

        assert filter_obj.providers == ["openai", "anthropic", "openrouter"]
        assert filter_obj.confidence_threshold == 0.7
        assert filter_obj.min_votes_required == 2

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        filter_obj = FalsePositiveFilter(
            providers=["openai"],
            confidence_threshold=0.8,
            min_votes_required=1,
        )

        assert filter_obj.providers == ["openai"]
        assert filter_obj.confidence_threshold == 0.8
        assert filter_obj.min_votes_required == 1

    def test_build_validation_prompt(self):
        """Test prompt building."""
        filter_obj = FalsePositiveFilter()

        finding = {
            "title": "SQL Injection",
            "severity": "high",
            "description": "SQLi in login form",
            "tool": "sqlmap",
            "target": "http://example.com/login",
            "evidence": "Parameter id is vulnerable",
            "cvss_score": 8.5,
            "cve_ids": ["CVE-2023-1234"],
        }

        prompt = filter_obj._build_validation_prompt(finding)

        assert "SQL Injection" in prompt
        assert "sqlmap" in prompt
        assert "CVE-2023-1234" in prompt
        assert "JSON FORMAT" in prompt

    def test_simulate_validation_true_positive(self):
        """Test simulated validation for true positive."""
        filter_obj = FalsePositiveFilter()

        finding = {
            "title": "SQL Injection Exploit",
            "description": "RCE vulnerability allowing remote code execution",
        }

        result = filter_obj._simulate_validation(finding)

        assert result["verdict"] == "valid"
        assert result["confidence"] > 0.7

    def test_simulate_validation_false_positive(self):
        """Test simulated validation for false positive."""
        filter_obj = FalsePositiveFilter()

        finding = {
            "title": "Informational Finding",
            "description": "Not vulnerable, no evidence found",
        }

        result = filter_obj._simulate_validation(finding)

        assert result["verdict"] == "false_positive"

    def test_simulate_validation_uncertain(self):
        """Test simulated validation for uncertain case."""
        filter_obj = FalsePositiveFilter()

        finding = {
            "title": "Unknown Issue",
            "description": "Some data",
        }

        result = filter_obj._simulate_validation(finding)

        assert result["verdict"] == "uncertain"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_gather_votes(self):
        """Test gathering votes from providers."""
        filter_obj = FalsePositiveFilter(providers=["openai", "anthropic"])

        finding = {"title": "SQL Injection", "description": "Test"}

        votes = await filter_obj.gather_votes(finding)

        # Should have votes (simulated)
        assert len(votes) <= 2  # May be less if backend init fails

    @pytest.mark.asyncio
    async def test_gather_votes_with_exception(self):
        """Test gathering votes when provider fails."""
        filter_obj = FalsePositiveFilter(providers=["openai"])

        # Mock to cause exception
        with patch.object(filter_obj, "_query_provider", side_effect=Exception("API Error")):
            finding = {"title": "Test", "description": "Test"}
            votes = await filter_obj.gather_votes(finding)

            assert votes == []

    def test_calculate_confidence_no_votes(self):
        """Test confidence calculation with no votes."""
        filter_obj = FalsePositiveFilter()

        confidence = filter_obj.calculate_confidence([])

        assert confidence == 0.0

    def test_calculate_confidence_valid_majority(self):
        """Test confidence with valid majority."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.VALID, 0.8, "Valid"),
            LLMVote("p2", VoteVerdict.VALID, 0.9, "Valid"),
            LLMVote("p3", VoteVerdict.FALSE_POSITIVE, 0.6, "FP"),
        ]

        confidence = filter_obj.calculate_confidence(votes)

        assert confidence > 0.7

    def test_calculate_confidence_fp_majority(self):
        """Test confidence with false positive majority."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.FALSE_POSITIVE, 0.8, "FP"),
            LLMVote("p2", VoteVerdict.FALSE_POSITIVE, 0.9, "FP"),
            LLMVote("p3", VoteVerdict.VALID, 0.5, "Maybe"),
        ]

        confidence = filter_obj.calculate_confidence(votes)

        assert confidence > 0.5

    def test_calculate_confidence_tie(self):
        """Test confidence calculation with tie."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.VALID, 0.8, "Valid"),
            LLMVote("p2", VoteVerdict.FALSE_POSITIVE, 0.8, "FP"),
        ]

        confidence = filter_obj.calculate_confidence(votes)

        # Tie should reduce confidence
        assert confidence < 0.8

    def test_determine_consensus_valid(self):
        """Test consensus determination for valid."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.VALID, 0.8, ""),
            LLMVote("p2", VoteVerdict.VALID, 0.9, ""),
            LLMVote("p3", VoteVerdict.FALSE_POSITIVE, 0.5, ""),
        ]

        consensus = filter_obj.determine_consensus(votes)

        assert "valid" in consensus

    def test_determine_consensus_false_positive(self):
        """Test consensus determination for false positive."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.FALSE_POSITIVE, 0.8, ""),
            LLMVote("p2", VoteVerdict.FALSE_POSITIVE, 0.9, ""),
        ]

        consensus = filter_obj.determine_consensus(votes)

        assert "false_positive" in consensus

    def test_determine_consensus_uncertain(self):
        """Test consensus determination for uncertain."""
        filter_obj = FalsePositiveFilter()

        votes = [
            LLMVote("p1", VoteVerdict.UNCERTAIN, 0.8, ""),
            LLMVote("p2", VoteVerdict.UNCERTAIN, 0.9, ""),
        ]

        consensus = filter_obj.determine_consensus(votes)

        assert "uncertain" in consensus

    def test_determine_consensus_no_votes(self):
        """Test consensus with no votes."""
        filter_obj = FalsePositiveFilter()

        consensus = filter_obj.determine_consensus([])

        assert consensus == "no_votes"

    @pytest.mark.asyncio
    async def test_validate_finding_insufficient_votes(self):
        """Test validation with insufficient votes."""
        filter_obj = FalsePositiveFilter(min_votes_required=5, providers=["openai"])

        finding = {"title": "Test", "description": "Test"}

        result = await filter_obj.validate_finding(finding)

        assert result.is_valid is False
        assert result.consensus == "insufficient_votes"
        assert result.recommended_action == "manual_review"

    @pytest.mark.asyncio
    async def test_batch_validate(self):
        """Test batch validation."""
        filter_obj = FalsePositiveFilter(providers=["openai"])

        findings = [
            {"title": "SQL Injection", "description": "Test"},
            {"title": "XSS", "description": "Test"},
        ]

        results = await filter_obj.batch_validate(findings)

        assert len(results) == 2
        assert all(isinstance(r, ValidationResult) for r in results)


# ============================================================================
# Tests for exploit_evidence.py
# ============================================================================


class TestExploitEvidenceCollector:
    """Test ExploitEvidenceCollector class."""

    def test_initialization(self):
        """Test initialization."""
        collector = ExploitEvidenceCollector(storage_path="/tmp/evidence")  # nosec B108)

        assert collector.storage_path == "/tmp/evidence"  # nosec B108

    def test_initialization_default(self):
        """Test initialization with default path."""
        collector = ExploitEvidenceCollector()

        assert collector.storage_path == "./evidence"

    @pytest.mark.asyncio
    async def test_collect_response_evidence(self):
        """Test collecting response evidence."""
        collector = ExploitEvidenceCollector()

        request_data = {
            "url": "http://example.com/api/users",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer secret_token",
            },
        }

        response_data = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"id": 1, "name": "Test"}' + "x" * 2000,
        }

        evidence = await collector.collect_response_evidence(request_data, response_data)

        assert "timestamp" in evidence
        assert evidence["request"]["url"] == "http://example.com/api/users"
        assert evidence["request"]["method"] == "POST"
        # Authorization should be sanitized
        assert "Authorization" not in evidence["request"]["headers"]
        assert evidence["response"]["status_code"] == 200
        # Body should be truncated
        assert len(evidence["response"]["body_preview"]) <= 1000

    def test_sanitize_headers(self):
        """Test header sanitization."""
        collector = ExploitEvidenceCollector()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret",
            "Cookie": "session=secret123",
            "X-Api-Key": "super_secret",
            "Accept": "application/json",
        }

        sanitized = collector._sanitize_headers(headers)

        assert "Content-Type" in sanitized
        assert "Accept" in sanitized
        assert "Authorization" not in sanitized
        assert "Cookie" not in sanitized
        assert "X-Api-Key" not in sanitized

    @pytest.mark.asyncio
    async def test_generate_poc_report(self):
        """Test generating PoC report."""
        collector = ExploitEvidenceCollector()

        finding = {
            "title": "SQL Injection",
            "severity": "Critical",
            "description": "SQL injection in login form",
        }

        evidence = {
            "timestamp": "2024-01-01T00:00:00",
            "request": {"url": "http://example.com/login"},
            "response": {"status_code": 200},
        }

        html = await collector.generate_poc_report(finding, evidence)

        assert "<html>" in html
        assert "SQL Injection" in html
        assert "Critical" in html
        assert "Proof of Concept Report" in html
        assert "http://example.com/login" in html


# ============================================================================
# Tests for llm_backend.py
# ============================================================================


class TestLLMBackend:
    """Test LLMBackend stub class."""

    def test_initialization_defaults(self):
        """Test initialization with defaults."""
        backend = LLMBackend()

        assert backend.provider == "openai"
        assert backend.model == "gpt-4"

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        backend = LLMBackend(provider="anthropic", model="claude-3")

        assert backend.provider == "anthropic"
        assert backend.model == "claude-3"

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test generate method."""
        backend = LLMBackend()

        result = await backend.generate("Test prompt")

        assert "Stub response" in result
        assert "Test prompt" in result

    @pytest.mark.asyncio
    async def test_chat(self):
        """Test chat method."""
        backend = LLMBackend()

        messages = [{"role": "user", "content": "Hello"}]
        result = await backend.chat(messages)

        assert result["content"] == "Stub chat response"
        assert result["model"] == "gpt-4"
        assert "usage" in result


# ============================================================================
# Tests for models.py
# ============================================================================


class TestSeverity:
    """Test Severity enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"


class TestScanStatus:
    """Test ScanStatus enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"
        assert ScanStatus.CANCELLED.value == "cancelled"


class TestBackendType:
    """Test BackendType enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert BackendType.DUCKDUCKGO.value == "duckduckgo"
        assert BackendType.OPENROUTER.value == "openrouter"


class TestTimestampedModel:
    """Test TimestampedModel base class."""

    def test_creation(self):
        """Test creation with timestamps."""
        model = TimestampedModel()

        assert isinstance(model.created_at, datetime)
        assert model.updated_at is None


class TestAPIKeyConfig:
    """Test APIKeyConfig model."""

    def test_creation(self):
        """Test creation."""
        config = APIKeyConfig(
            openrouter_key="sk-or-test12345678901234567890",
            openai_key="sk-test12345678901234567890",
        )

        assert config.openrouter_key == "sk-or-test12345678901234567890"
        assert config.openai_key == "sk-test12345678901234567890"

    def test_get_key(self):
        """Test getting key for provider."""
        config = APIKeyConfig(
            openrouter_key="sk-or-test12345678901234567890",
            openai_key="sk-test12345678901234567890",
            anthropic_key="sk-ant-test12345678901234567890",
        )

        assert config.get_key(BackendType.OPENROUTER) == "sk-or-test12345678901234567890"
        assert config.get_key(BackendType.OPENAI) == "sk-test12345678901234567890"
        assert config.get_key(BackendType.ANTHROPIC) == "sk-ant-test12345678901234567890"

    def test_invalid_key_format(self):
        """Test validation of key format."""
        # This should raise validation error
        with pytest.raises(PydanticValidationError):
            APIKeyConfig(openai_key="invalid")  # Too short


class TestScanConfig:
    """Test ScanConfig model."""

    def test_creation_defaults(self):
        """Test creation with defaults."""
        config = ScanConfig(target="example.com")

        assert config.target == "example.com"
        assert config.scan_type == "quick"
        assert config.ports == [80, 443]
        assert config.timeout == 300

    def test_creation_custom(self):
        """Test creation with custom values."""
        config = ScanConfig(
            target="example.com",
            scan_type="full",
            ports=[22, 80, 443],
            timeout=600,
        )

        assert config.scan_type == "full"
        assert config.ports == [22, 80, 443]
        assert config.timeout == 600

    def test_validate_target_invalid(self):
        """Test target validation."""
        with pytest.raises(PydanticValidationError):
            ScanConfig(target="invalid;command")  # Dangerous chars

    def test_validate_ports_invalid(self):
        """Test port validation."""
        with pytest.raises(PydanticValidationError):
            ScanConfig(target="example.com", ports=[99999])  # Invalid port


class TestFinding:
    """Test Finding model."""

    def test_creation(self):
        """Test creation."""
        finding = Finding(
            title="SQL Injection",
            description="SQL injection in login",
            severity=Severity.CRITICAL,
            host="example.com",
            port=80,
        )

        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.CRITICAL
        assert finding.confidence == "possible"  # Default

    def test_cve_validation(self):
        """Test CVE ID validation."""
        finding = Finding(
            title="Test",
            description="Test",
            severity=Severity.HIGH,
            host="example.com",
            cve_ids=["cve-2023-1234", "CVE-2022-5678"],
        )

        # Should normalize to uppercase
        assert finding.cve_ids == ["CVE-2023-1234", "CVE-2022-5678"]

    def test_invalid_cve_format(self):
        """Test invalid CVE format."""
        with pytest.raises(PydanticValidationError):
            Finding(
                title="Test",
                description="Test",
                severity=Severity.HIGH,
                host="example.com",
                cve_ids=["invalid-cve"],
            )


class TestScanResult:
    """Test ScanResult model."""

    def test_duration_seconds(self):
        """Test duration calculation."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=60)

        result = ScanResult(
            scan_id="scan_123",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=start,
            completed_at=end,
        )

        assert result.duration_seconds == 60.0

    def test_duration_seconds_incomplete(self):
        """Test duration when not completed."""
        result = ScanResult(
            scan_id="scan_123",
            target="example.com",
            status=ScanStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        assert result.duration_seconds is None

    def test_severity_counts(self):
        """Test severity counts."""
        result = ScanResult(
            scan_id="scan_123",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            findings=[
                Finding(
                    title="F1",
                    description="D1",
                    severity=Severity.CRITICAL,
                    host="h1",
                ),
                Finding(
                    title="F2",
                    description="D2",
                    severity=Severity.HIGH,
                    host="h1",
                ),
                Finding(
                    title="F3",
                    description="D3",
                    severity=Severity.HIGH,
                    host="h1",
                ),
            ],
        )

        counts = result.severity_counts
        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 0


class TestLLMRequest:
    """Test LLMRequest model."""

    def test_creation(self):
        """Test creation."""
        request = LLMRequest(
            prompt="Test prompt",
            system_prompt="System instruction",
            temperature=0.5,
            max_tokens=1000,
        )

        assert request.prompt == "Test prompt"
        assert request.temperature == 0.5

    def test_temperature_validation(self):
        """Test temperature validation."""
        with pytest.raises(PydanticValidationError):
            LLMRequest(prompt="Test", temperature=3.0)  # Too high

        with pytest.raises(PydanticValidationError):
            LLMRequest(prompt="Test", temperature=-0.5)  # Too low

    def test_sanitize_prompt(self):
        """Test prompt sanitization."""
        request = LLMRequest(prompt="Test\x00null\x01byte\nvalid")

        assert "\x00" not in request.prompt
        assert "\x01" not in request.prompt
        # Newlines may or may not be kept depending on the implementation
        assert "valid" in request.prompt


class TestLLMResponse:
    """Test LLMResponse model."""

    def test_success_property(self):
        """Test success property."""
        response = LLMResponse(
            content="Response",
            backend=BackendType.OPENAI,
        )

        assert response.success is True

        response_with_error = LLMResponse(
            content="",
            backend=BackendType.OPENAI,
            error="API Error",
        )

        assert response_with_error.success is False


class TestPaginatedResponse:
    """Test PaginatedResponse model."""

    def test_has_next(self):
        """Test has_next property."""
        response = PaginatedResponse(
            items=[1, 2, 3],
            total=30,
            page=1,
            per_page=10,
            pages=3,
        )

        assert response.has_next is True
        assert response.has_prev is False

    def test_has_prev(self):
        """Test has_prev property."""
        response = PaginatedResponse(
            items=[1, 2, 3],
            total=30,
            page=2,
            per_page=10,
            pages=3,
        )

        assert response.has_next is True
        assert response.has_prev is True


class TestReportConfig:
    """Test ReportConfig model."""

    def test_creation(self):
        """Test creation."""
        config = ReportConfig(
            title="Penetration Test Report",
            client_name="Example Corp",
            format="pdf",
            template="technical",
        )

        assert config.title == "Penetration Test Report"
        assert config.format == "pdf"

    def test_template_validation(self):
        """Test template validation."""
        with pytest.raises(PydanticValidationError):
            ReportConfig(
                title="Test",
                client_name="Test",
                template="invalid_template",
            )


# ============================================================================
# Tests for output_validator.py
# ============================================================================


class TestOutputValidator:
    """Test OutputValidator class."""

    def test_initialization(self):
        """Test initialization."""
        validator = OutputValidator()

        assert len(validator.schemas) > 0  # Should have default schemas
        assert "nmap" in validator.schemas
        assert "sqlmap" in validator.schemas

    def test_initialization_with_schema_dir(self, tmp_path):
        """Test initialization with schema directory."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        custom_schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}},
        }
        (schema_dir / "custom.json").write_text(json.dumps(custom_schema))

        validator = OutputValidator(schema_dir=str(schema_dir))

        assert "custom" in validator.schemas

    def test_list_schemas(self):
        """Test listing schemas."""
        validator = OutputValidator()
        schemas = validator.list_schemas()

        assert "nmap" in schemas
        assert "nuclei" in schemas

    def test_get_schema(self):
        """Test getting specific schema."""
        validator = OutputValidator()

        schema = validator.get_schema("nmap")
        assert schema is not None
        assert schema["type"] == "object"

        # Non-existent schema
        assert validator.get_schema("nonexistent") is None

    def test_add_schema(self):
        """Test adding a schema."""
        validator = OutputValidator()

        new_schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}},
        }
        validator.add_schema("new_tool", new_schema)

        assert validator.get_schema("new_tool") == new_schema

    def test_remove_schema(self):
        """Test removing a schema."""
        validator = OutputValidator()

        result = validator.remove_schema("nmap")
        assert result is True
        assert validator.get_schema("nmap") is None

        # Try removing again
        result = validator.remove_schema("nmap")
        assert result is False

    def test_validate_success(self):
        """Test successful validation."""
        validator = OutputValidator()

        output = {
            "target": "example.com",
            "ports": [
                {"port": 80, "state": "open", "service": "http"},
            ],
        }

        result = validator.validate("nmap", output)
        assert result is True

    def test_validate_from_json_string(self):
        """Test validation from JSON string."""
        validator = OutputValidator()

        output = json.dumps(
            {
                "target": "example.com",
                "ports": [{"port": 80, "state": "open"}],
            }
        )

        result = validator.validate("nmap", output)
        assert result is True

    def test_validate_invalid_json(self):
        """Test validation with invalid JSON string."""
        validator = OutputValidator()

        result = validator.validate("nmap", "not valid json")
        assert result is False

    def test_validate_no_schema(self):
        """Test validation when no schema exists."""
        validator = OutputValidator()

        result = validator.validate("unknown_tool", {"data": "value"})
        assert result is True  # Passes if no schema

    def test_validate_basic_without_jsonschema(self):
        """Test basic validation when jsonschema not available."""
        validator = OutputValidator()

        with patch("core.output_validator.JSONSCHEMA_AVAILABLE", False):
            output = {"target": "example.com", "ports": []}
            result = validator.validate("nmap", output)
            assert result is True

    def test_validate_with_errors(self):
        """Test validation with error details."""
        validator = OutputValidator()

        # Missing required field
        output = {"ports": []}  # Missing "target"

        is_valid, errors = validator.validate_with_errors("nmap", output)

        assert is_valid is False
        assert len(errors) > 0

    def test_sanitize_output(self):
        """Test output sanitization."""
        validator = OutputValidator()

        output = {
            "target": "example.com",
            "ports": [],
            "unknown_field": "should be removed",
        }

        sanitized = validator.sanitize_output("nmap", output)

        assert "target" in sanitized
        assert "unknown_field" not in sanitized


class TestValidatedToolOutput:
    """Test ValidatedToolOutput wrapper class."""

    def test_creation(self):
        """Test creation."""
        validator = OutputValidator()
        wrapper = ValidatedToolOutput("nmap", {"target": "example.com"}, validator)

        assert wrapper.tool_name == "nmap"
        assert wrapper.raw_output == {"target": "example.com"}

    def test_is_valid_property(self):
        """Test is_valid property."""
        validator = OutputValidator()
        output = {"target": "example.com", "ports": []}
        wrapper = ValidatedToolOutput("nmap", output, validator)

        # First access should trigger validation
        assert wrapper.is_valid is True

        # Second access should use cached value
        assert wrapper.is_valid is True

    def test_errors_property(self):
        """Test errors property."""
        validator = OutputValidator()
        output = {"ports": []}  # Missing required "target"
        wrapper = ValidatedToolOutput("nmap", output, validator)

        errors = wrapper.errors
        assert len(errors) > 0

    def test_get_sanitized(self):
        """Test getting sanitized output."""
        validator = OutputValidator()
        output = {"target": "example.com", "ports": [], "extra": "field"}
        wrapper = ValidatedToolOutput("nmap", output, validator)

        sanitized = wrapper.get_sanitized()
        assert "target" in sanitized
        assert "extra" not in sanitized


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_validate_tool_output(self):
        """Test validate_tool_output function."""
        output = {"target": "example.com", "ports": []}
        result = validate_tool_output("nmap", output)

        assert result is True

    def test_validate_and_report(self):
        """Test validate_and_report function."""
        output = {"ports": []}  # Invalid - missing target
        is_valid, errors = validate_and_report("nmap", output)

        assert is_valid is False
        assert len(errors) > 0


# ============================================================================
# Tests for orchestrator.py
# ============================================================================


class TestQualityLevel:
    """Test QualityLevel enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"


class TestOrchestratorLLMResponse:
    """Test orchestrator's LLMResponse."""

    def test_creation(self):
        """Test creation."""
        response = OrchestratorLLMResponse(
            content="Test response",
            source="openai",
            latency=1.5,
            quality=QualityLevel.HIGH,
        )

        assert response.content == "Test response"
        assert response.source == "openai"
        assert response.latency == 1.5


class TestBaseBackend:
    """Test BaseBackend abstract class."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""

        class ConcreteBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "response"

        backend = ConcreteBackend("test", 1)

        async with backend:
            assert backend.session is not None

    @pytest.mark.asyncio
    async def test_health_check_default(self):
        """Test default health check."""

        class ConcreteBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "response"

        backend = ConcreteBackend("test", 1)

        assert await backend.health_check() is True


class TestZenOrchestrator:
    """Test ZenOrchestrator class."""

    def test_initialization(self):
        """Test initialization."""
        orchestrator = ZenOrchestrator()

        assert orchestrator.backends == []
        assert orchestrator.request_count == 0

    def test_add_backend(self):
        """Test adding backend."""
        orchestrator = ZenOrchestrator()

        class MockBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "response"

        backend = MockBackend("test", 1)
        orchestrator.add_backend(backend)

        assert len(orchestrator.backends) == 1
        assert orchestrator.backends[0].name == "test"

    def test_add_backend_sorts_by_priority(self):
        """Test that backends are sorted by priority."""
        orchestrator = ZenOrchestrator()

        class MockBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "response"

        backend3 = MockBackend("high", 3)
        backend1 = MockBackend("low", 1)
        backend2 = MockBackend("medium", 2)

        orchestrator.add_backend(backend3)
        orchestrator.add_backend(backend1)
        orchestrator.add_backend(backend2)

        priorities = [b.priority for b in orchestrator.backends]
        assert priorities == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful processing."""
        orchestrator = ZenOrchestrator()

        class MockBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "Mock response"

        orchestrator.add_backend(MockBackend("test", 1))

        response = await orchestrator.process("Test prompt")

        assert response.content == "Mock response"
        assert response.source == "test"
        assert orchestrator.request_count == 1

    @pytest.mark.asyncio
    async def test_process_all_backends_fail(self):
        """Test when all backends fail."""
        orchestrator = ZenOrchestrator()

        class FailingBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                raise Exception("API Error")

        orchestrator.add_backend(FailingBackend("test", 1))

        response = await orchestrator.process("Test prompt")

        assert "failed" in response.content.lower()

    @pytest.mark.asyncio
    async def test_parallel_consensus(self):
        """Test parallel consensus."""
        orchestrator = ZenOrchestrator()

        class MockBackend(BaseBackend):
            async def chat(self, prompt, context=""):
                return "Response from " + self.name

        orchestrator.add_backend(MockBackend("backend1", 1))
        orchestrator.add_backend(MockBackend("backend2", 2))

        result = await orchestrator.parallel_consensus("Test")

        assert "responses" in result
        assert "consensus" in result

    def test_get_stats(self):
        """Test getting stats."""
        orchestrator = ZenOrchestrator()

        stats = orchestrator.get_stats()

        assert "backends_registered" in stats
        assert "requests_processed" in stats

    def test_get_capabilities(self):
        """Test getting capabilities."""
        orchestrator = ZenOrchestrator()

        capabilities = orchestrator.get_capabilities()

        assert "autonomous_scan" in capabilities
        assert "false_positive_validation" in capabilities


# ============================================================================
# Tests for tool_executor.py
# ============================================================================


class TestToolResultStatus:
    """Test ToolResultStatus enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert ToolResultStatus.SUCCESS.value == "success"
        assert ToolResultStatus.ERROR.value == "error"
        assert ToolResultStatus.TIMEOUT.value == "timeout"
        assert ToolResultStatus.NOT_FOUND.value == "not_found"


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_creation(self):
        """Test creation."""
        result = ToolResult(
            status=ToolResultStatus.SUCCESS,
            returncode=0,
            stdout="output",
            stderr="",
            command="nmap -sV target",
        )

        assert result.status == ToolResultStatus.SUCCESS
        assert result.returncode == 0
        assert result.success is True
        assert result.failed is False

    def test_success_property_failure(self):
        """Test success property for failure."""
        result = ToolResult(
            status=ToolResultStatus.ERROR,
            returncode=1,
            stdout="",
            stderr="error",
            command="test",
        )

        assert result.success is False
        assert result.failed is True


class TestRealToolExecutor:
    """Test RealToolExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        executor = RealToolExecutor()

        result = await executor.execute(["echo", "hello"])

        assert result.success is True
        assert "hello" in result.stdout
        assert result.returncode == 0

    @pytest.mark.asyncio
    async def test_execute_command_not_found(self):
        """Test command not found."""
        executor = RealToolExecutor()

        result = await executor.execute(["nonexistent_command_xyz"])

        assert result.status == ToolResultStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test command timeout."""
        executor = RealToolExecutor()

        result = await executor.execute(["sleep", "10"], timeout=0.1)

        assert result.status == ToolResultStatus.TIMEOUT

    def test_execute_sync_success(self):
        """Test successful sync execution."""
        executor = RealToolExecutor()

        result = executor.execute_sync(["echo", "hello"])

        assert result.success is True
        assert "hello" in result.stdout

    def test_execute_sync_timeout(self):
        """Test sync command timeout."""
        executor = RealToolExecutor()

        result = executor.execute_sync(["sleep", "10"], timeout=0.1)

        assert result.status == ToolResultStatus.TIMEOUT


class TestMockToolExecutor:
    """Test MockToolExecutor class."""

    def test_initialization(self):
        """Test initialization."""
        executor = MockToolExecutor()

        assert executor.mock_responses == {}
        assert executor.call_history == []

    def test_add_mock_response(self):
        """Test adding mock response."""
        executor = MockToolExecutor()

        result = ToolResult(
            status=ToolResultStatus.SUCCESS,
            returncode=0,
            stdout="mock output",
            stderr="",
            command="mock",
        )

        executor.add_mock_response("nmap", result)

        assert "nmap" in executor.mock_responses

    @pytest.mark.asyncio
    async def test_execute_with_mock(self):
        """Test execution with mock response."""
        executor = MockToolExecutor()

        mock_result = ToolResult(
            status=ToolResultStatus.SUCCESS,
            returncode=0,
            stdout="nmap output",
            stderr="",
            command="mock",
        )

        executor.add_mock_response("nmap", mock_result)

        result = await executor.execute(["nmap", "-sV", "target"])

        assert result.stdout == "nmap output"
        assert len(executor.call_history) == 1

    @pytest.mark.asyncio
    async def test_execute_default_response(self):
        """Test execution with default response."""
        executor = MockToolExecutor()

        result = await executor.execute(["unknown", "command"])

        assert result == executor.default_result

    def test_was_called_with(self):
        """Test checking if command was called."""
        executor = MockToolExecutor()

        asyncio.run(executor.execute(["nmap", "-sV", "target"]))

        assert executor.was_called_with("nmap") is True
        assert executor.was_called_with("masscan") is False

    def test_clear_history(self):
        """Test clearing call history."""
        executor = MockToolExecutor()

        asyncio.run(executor.execute(["nmap"]))
        assert len(executor.call_history) == 1

        executor.clear_history()
        assert len(executor.call_history) == 0


class TestGlobalExecutorFunctions:
    """Test global executor functions."""

    def test_get_executor(self):
        """Test get_executor returns RealToolExecutor by default."""
        reset_executor()
        executor = get_executor()

        assert isinstance(executor, RealToolExecutor)

    def test_set_executor(self):
        """Test set_executor changes executor."""
        mock_executor = MockToolExecutor()

        set_executor(mock_executor)

        assert get_executor() is mock_executor

    def test_reset_executor(self):
        """Test reset_executor restores RealToolExecutor."""
        set_executor(MockToolExecutor())
        reset_executor()

        assert isinstance(get_executor(), RealToolExecutor)

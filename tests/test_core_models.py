"""
Comprehensive tests for core/models.py - Pydantic Models for Zen AI Pentest

Tests all data models, validation methods, and serialization/deserialization.
Target: 80%+ coverage for core/models.py
"""

from datetime import datetime, timedelta

import pytest

from core.models import (  # Enums; Base Models
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

# ==================== Enum Tests ====================


class TestEnums:
    """Test enum definitions"""

    def test_severity_values(self):
        """Test Severity enum values"""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"

    def test_severity_comparison(self):
        """Test severity ordering"""
        severities = [Severity.LOW, Severity.HIGH, Severity.CRITICAL]
        assert sorted(severities, key=lambda x: ["info", "low", "medium", "high", "critical"].index(x.value)) == [
            Severity.LOW,
            Severity.HIGH,
            Severity.CRITICAL,
        ]

    def test_scan_status_values(self):
        """Test ScanStatus enum values"""
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"

    def test_backend_type_values(self):
        """Test BackendType enum values"""
        assert BackendType.DUCKDUCKGO == "duckduckgo"
        assert BackendType.OPENROUTER == "openrouter"
        assert BackendType.OPENAI == "openai"
        assert BackendType.ANTHROPIC == "anthropic"


# ==================== TimestampedModel Tests ====================


class TestTimestampedModel:
    """Test TimestampedModel base class"""

    def test_default_creation(self):
        """Test model with default timestamps"""
        model = TimestampedModel()
        assert isinstance(model.created_at, datetime)
        assert model.updated_at is None

    def test_custom_timestamps(self):
        """Test model with custom timestamps"""
        created = datetime(2024, 1, 1, 12, 0, 0)
        updated = datetime(2024, 1, 2, 12, 0, 0)
        model = TimestampedModel(created_at=created, updated_at=updated)
        assert model.created_at == created
        assert model.updated_at == updated

    def test_serialization(self):
        """Test serialization to dict"""
        model = TimestampedModel()
        data = model.model_dump()
        assert "created_at" in data
        assert "updated_at" in data


# ==================== APIKeyConfig Tests ====================


class TestAPIKeyConfig:
    """Test APIKeyConfig model"""

    def test_empty_config(self):
        """Test empty API key config"""
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None
        assert config.anthropic_key is None
        assert config.github_token is None
        assert config.shodan_key is None

    def test_valid_openrouter_key(self):
        """Test valid OpenRouter API key"""
        config = APIKeyConfig(openrouter_key="sk-or-abcdefghijklmnopqrstuvwxyz")
        assert config.openrouter_key == "sk-or-abcdefghijklmnopqrstuvwxyz"

    def test_invalid_openrouter_key(self):
        """Test invalid OpenRouter API key format"""
        with pytest.raises(ValueError):
            APIKeyConfig(openrouter_key="invalid-key")

    def test_valid_openai_key(self):
        """Test valid OpenAI API key"""
        config = APIKeyConfig(openai_key="sk-abcdefghijklmnopqrstuvwxyz")
        assert config.openai_key == "sk-abcdefghijklmnopqrstuvwxyz"

    def test_invalid_openai_key(self):
        """Test invalid OpenAI API key format"""
        with pytest.raises(ValueError):
            APIKeyConfig(openai_key="invalid")

    def test_valid_anthropic_key(self):
        """Test valid Anthropic API key"""
        config = APIKeyConfig(anthropic_key="sk-ant-abcdefghijklmnopqrstuvwxyz")
        assert config.anthropic_key == "sk-ant-abcdefghijklmnopqrstuvwxyz"

    def test_invalid_anthropic_key(self):
        """Test invalid Anthropic API key format"""
        with pytest.raises(ValueError):
            APIKeyConfig(anthropic_key="invalid-key")

    def test_github_token_min_length(self):
        """Test GitHub token minimum length validation"""
        with pytest.raises(ValueError):
            APIKeyConfig(github_token="short")

    def test_get_key_openrouter(self):
        """Test getting OpenRouter key"""
        config = APIKeyConfig(openrouter_key="sk-or-abcdefghijklmnopqrstuvwxyz")
        assert config.get_key(BackendType.OPENROUTER) == "sk-or-abcdefghijklmnopqrstuvwxyz"

    def test_get_key_openai(self):
        """Test getting OpenAI key"""
        config = APIKeyConfig(openai_key="sk-abcdefghijklmnopqrstuvwxyz")
        assert config.get_key(BackendType.OPENAI) == "sk-abcdefghijklmnopqrstuvwxyz"

    def test_get_key_anthropic(self):
        """Test getting Anthropic key"""
        config = APIKeyConfig(anthropic_key="sk-ant-abcdefghijklmnopqrstuvwxyz")
        assert config.get_key(BackendType.ANTHROPIC) == "sk-ant-abcdefghijklmnopqrstuvwxyz"

    def test_get_key_duckduckgo(self):
        """Test getting DuckDuckGo key (should be None)"""
        config = APIKeyConfig()
        assert config.get_key(BackendType.DUCKDUCKGO) is None

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            APIKeyConfig(invalid_field="value")


# ==================== ScanConfig Tests ====================


class TestScanConfig:
    """Test ScanConfig model"""

    def test_default_values(self):
        """Test default scan configuration"""
        config = ScanConfig(target="example.com")
        assert config.target == "example.com"
        assert config.scan_type == "quick"
        assert config.ports == [80, 443]
        assert config.templates == []
        assert config.timeout == 300
        assert config.concurrent == 5
        assert config.follow_redirects is True

    def test_custom_values(self):
        """Test custom scan configuration"""
        config = ScanConfig(
            target="192.168.1.1", scan_type="full", ports=[22, 80, 443], timeout=600, concurrent=10, follow_redirects=False
        )
        assert config.target == "192.168.1.1"
        assert config.scan_type == "full"
        assert config.ports == [22, 80, 443]
        assert config.timeout == 600
        assert config.concurrent == 10
        assert config.follow_redirects is False

    def test_target_validation_domain(self):
        """Test target validation with valid domain"""
        config = ScanConfig(target="example.com")
        assert config.target == "example.com"

    def test_target_validation_subdomain(self):
        """Test target validation with subdomain"""
        config = ScanConfig(target="sub.example.com")
        assert config.target == "sub.example.com"

    def test_target_validation_ip(self):
        """Test target validation with IP address"""
        config = ScanConfig(target="192.168.1.1")
        assert config.target == "192.168.1.1"

    def test_target_validation_dangerous_chars(self):
        """Test target validation rejects dangerous characters"""
        with pytest.raises(ValueError, match="dangerous characters"):
            ScanConfig(target="example.com; rm -rf /")

    def test_target_validation_invalid_format(self):
        """Test target validation rejects invalid format"""
        with pytest.raises(ValueError, match="Invalid target format"):
            ScanConfig(target="!!!invalid!!!")

    def test_target_validation_empty(self):
        """Test target validation rejects empty string"""
        with pytest.raises(ValueError):
            ScanConfig(target="")

    def test_target_validation_too_long(self):
        """Test target validation rejects too long domain"""
        with pytest.raises(ValueError):
            ScanConfig(target="a" * 254)

    def test_ports_validation_valid(self):
        """Test port validation with valid ports"""
        config = ScanConfig(target="example.com", ports=[80, 443, 8080])
        assert config.ports == [80, 443, 8080]

    def test_ports_validation_invalid_low(self):
        """Test port validation rejects port < 1"""
        with pytest.raises(ValueError, match="Invalid port"):
            ScanConfig(target="example.com", ports=[0])

    def test_ports_validation_invalid_high(self):
        """Test port validation rejects port > 65535"""
        with pytest.raises(ValueError, match="Invalid port"):
            ScanConfig(target="example.com", ports=[65536])

    def test_timeout_validation_min(self):
        """Test timeout minimum validation"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", timeout=5)

    def test_timeout_validation_max(self):
        """Test timeout maximum validation"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", timeout=4000)

    def test_concurrent_validation_min(self):
        """Test concurrent minimum validation"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", concurrent=0)

    def test_concurrent_validation_max(self):
        """Test concurrent maximum validation"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", concurrent=100)

    def test_scan_type_validation(self):
        """Test scan type validation"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", scan_type="invalid")

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", invalid_field="value")


# ==================== Finding Tests ====================


class TestFinding:
    """Test Finding model"""

    def test_minimal_creation(self):
        """Test creating a finding with minimal fields"""
        finding = Finding(title="Test Finding", description="Test description", severity=Severity.HIGH, host="example.com")
        assert finding.title == "Test Finding"
        assert finding.description == "Test description"
        assert finding.severity == Severity.HIGH
        assert finding.host == "example.com"
        assert finding.id is None
        assert finding.cvss_score is None

    def test_full_creation(self):
        """Test creating a finding with all fields"""
        finding = Finding(
            id="FIND-001",
            title="SQL Injection",
            description="SQL injection vulnerability found",
            severity=Severity.CRITICAL,
            cvss_score=9.8,
            host="example.com",
            port=443,
            service="web",
            evidence="error: syntax error at or near",
            remediation="Use parameterized queries",
            references=["https://owasp.org/sql-injection"],
            cve_ids=["CVE-2023-1234"],
            tags=["sql", "injection", "critical"],
            confidence="confirmed",
        )
        assert finding.id == "FIND-001"
        assert finding.cvss_score == 9.8
        assert finding.port == 443
        assert finding.confidence == "confirmed"

    def test_default_values(self):
        """Test finding default values"""
        finding = Finding(title="Test", description="Test desc", severity=Severity.LOW, host="test.com")
        assert finding.cve_ids == []
        assert finding.tags == []
        assert finding.references == []
        assert finding.confidence == "possible"

    def test_cve_validation_valid(self):
        """Test CVE ID validation with valid CVE"""
        finding = Finding(
            title="Test",
            description="Test desc",
            severity=Severity.HIGH,
            host="test.com",
            cve_ids=["CVE-2023-1234", "CVE-2024-5678"],
        )
        assert finding.cve_ids == ["CVE-2023-1234", "CVE-2024-5678"]

    def test_cve_validation_invalid(self):
        """Test CVE ID validation with invalid CVE format"""
        with pytest.raises(ValueError, match="Invalid CVE format"):
            Finding(title="Test", description="Test desc", severity=Severity.HIGH, host="test.com", cve_ids=["INVALID-CVE"])

    def test_cve_validation_case_insensitive(self):
        """Test CVE ID validation is case insensitive"""
        finding = Finding(
            title="Test", description="Test desc", severity=Severity.HIGH, host="test.com", cve_ids=["cve-2023-1234"]
        )
        assert finding.cve_ids == ["CVE-2023-1234"]

    def test_cvss_score_validation(self):
        """Test CVSS score validation"""
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test desc", severity=Severity.HIGH, host="test.com", cvss_score=11.0)

    def test_port_validation(self):
        """Test port validation"""
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test desc", severity=Severity.HIGH, host="test.com", port=70000)

    def test_title_validation(self):
        """Test title length validation"""
        with pytest.raises(ValueError):
            Finding(title="", description="Test desc", severity=Severity.HIGH, host="test.com")

    def test_confidence_validation(self):
        """Test confidence level validation"""
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test desc", severity=Severity.HIGH, host="test.com", confidence="invalid")


# ==================== ScanResult Tests ====================


class TestScanResult:
    """Test ScanResult model"""

    def test_minimal_creation(self):
        """Test creating scan result with minimal fields"""
        started = datetime.utcnow()
        result = ScanResult(scan_id="SCAN-001", target="example.com", status=ScanStatus.RUNNING, started_at=started)
        assert result.scan_id == "SCAN-001"
        assert result.target == "example.com"
        assert result.status == ScanStatus.RUNNING
        assert result.started_at == started
        assert result.findings == []
        assert result.stats == {}

    def test_with_findings(self):
        """Test scan result with findings"""
        finding = Finding(title="Test Finding", description="Test", severity=Severity.HIGH, host="example.com")
        started = datetime.utcnow()
        completed = started + timedelta(minutes=5)
        result = ScanResult(
            scan_id="SCAN-001",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            findings=[finding],
            stats={"ports_scanned": 100},
        )
        assert len(result.findings) == 1
        assert result.completed_at == completed

    def test_duration_seconds_property(self):
        """Test duration_seconds property"""
        started = datetime.utcnow()
        completed = started + timedelta(minutes=5, seconds=30)
        result = ScanResult(
            scan_id="SCAN-001", target="example.com", status=ScanStatus.COMPLETED, started_at=started, completed_at=completed
        )
        assert result.duration_seconds == 330.0

    def test_duration_seconds_running(self):
        """Test duration_seconds returns None for running scan"""
        started = datetime.utcnow()
        result = ScanResult(scan_id="SCAN-001", target="example.com", status=ScanStatus.RUNNING, started_at=started)
        assert result.duration_seconds is None

    def test_severity_counts_property(self):
        """Test severity_counts property"""
        findings = [
            Finding(title="Critical", description="Test", severity=Severity.CRITICAL, host="test.com"),
            Finding(title="High1", description="Test", severity=Severity.HIGH, host="test.com"),
            Finding(title="High2", description="Test", severity=Severity.HIGH, host="test.com"),
            Finding(title="Medium", description="Test", severity=Severity.MEDIUM, host="test.com"),
        ]
        started = datetime.utcnow()
        result = ScanResult(
            scan_id="SCAN-001", target="example.com", status=ScanStatus.COMPLETED, started_at=started, findings=findings
        )
        counts = result.severity_counts
        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["low"] == 0
        assert counts["info"] == 0

    def test_serialization(self):
        """Test serialization to dict"""
        started = datetime.utcnow()
        result = ScanResult(scan_id="SCAN-001", target="example.com", status=ScanStatus.COMPLETED, started_at=started)
        data = result.model_dump()
        assert data["scan_id"] == "SCAN-001"
        assert data["target"] == "example.com"
        assert data["status"] == "completed"


# ==================== LLMRequest Tests ====================


class TestLLMRequest:
    """Test LLMRequest model"""

    def test_minimal_creation(self):
        """Test creating LLM request with minimal fields"""
        request = LLMRequest(prompt="Hello, world!")
        assert request.prompt == "Hello, world!"
        assert request.temperature == 0.7
        assert request.system_prompt is None
        assert request.max_tokens is None
        assert request.backend is None

    def test_full_creation(self):
        """Test creating LLM request with all fields"""
        request = LLMRequest(
            prompt="Analyze this code",
            system_prompt="You are a security expert",
            temperature=0.5,
            max_tokens=1000,
            backend=BackendType.OPENAI,
        )
        assert request.prompt == "Analyze this code"
        assert request.system_prompt == "You are a security expert"
        assert request.temperature == 0.5
        assert request.max_tokens == 1000
        assert request.backend == BackendType.OPENAI

    def test_prompt_validation_empty(self):
        """Test prompt validation rejects empty string"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="")

    def test_prompt_validation_too_long(self):
        """Test prompt validation rejects too long prompt"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="a" * 10001)

    def test_system_prompt_validation(self):
        """Test system prompt max length validation"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="Hello", system_prompt="a" * 5001)

    def test_temperature_validation_min(self):
        """Test temperature minimum validation"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="Hello", temperature=-0.1)

    def test_temperature_validation_max(self):
        """Test temperature maximum validation"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="Hello", temperature=2.1)

    def test_max_tokens_validation(self):
        """Test max tokens validation"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="Hello", max_tokens=0)

    def test_prompt_sanitization_null_bytes(self):
        """Test prompt sanitization removes null bytes"""
        request = LLMRequest(prompt="Hello\x00World")
        assert "\x00" not in request.prompt

    def test_prompt_sanitization_control_chars(self):
        """Test prompt sanitization removes control characters"""
        request = LLMRequest(prompt="Hello\x01\x02World")
        assert "\x01" not in request.prompt
        assert "\x02" not in request.prompt

    def test_prompt_sanitization_keeps_newlines(self):
        """Test prompt sanitization keeps newlines and tabs"""
        request = LLMRequest(prompt="Line1\nLine2\tTabbed")
        assert "\n" in request.prompt
        assert "\t" in request.prompt

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            LLMRequest(prompt="Hello", invalid_field="value")


# ==================== LLMResponse Tests ====================


class TestLLMResponse:
    """Test LLMResponse model"""

    def test_minimal_creation(self):
        """Test creating LLM response with minimal fields"""
        response = LLMResponse(content="Hello!", backend=BackendType.OPENAI)
        assert response.content == "Hello!"
        assert response.backend == BackendType.OPENAI
        assert response.model is None
        assert response.tokens_used is None
        assert response.cached is False
        assert response.error is None

    def test_full_creation(self):
        """Test creating LLM response with all fields"""
        response = LLMResponse(
            content="Analysis complete",
            backend=BackendType.ANTHROPIC,
            model="claude-3",
            tokens_used=150,
            latency_ms=500.0,
            cached=True,
            error=None,
        )
        assert response.content == "Analysis complete"
        assert response.model == "claude-3"
        assert response.tokens_used == 150
        assert response.latency_ms == 500.0
        assert response.cached is True

    def test_success_property_true(self):
        """Test success property when no error"""
        response = LLMResponse(content="Hello!", backend=BackendType.OPENAI)
        assert response.success is True

    def test_success_property_false(self):
        """Test success property when error present"""
        response = LLMResponse(content="", backend=BackendType.OPENAI, error="API rate limit exceeded")
        assert response.success is False


# ==================== SubdomainInfo Tests ====================


class TestSubdomainInfo:
    """Test SubdomainInfo model"""

    def test_minimal_creation(self):
        """Test creating subdomain info with minimal fields"""
        info = SubdomainInfo(name="sub.example.com")
        assert info.name == "sub.example.com"
        assert info.ip_addresses == []
        assert info.technologies == []
        assert info.ports == []
        assert info.is_alive is False

    def test_full_creation(self):
        """Test creating subdomain info with all fields"""
        info = SubdomainInfo(
            name="sub.example.com",
            ip_addresses=["192.168.1.1", "192.168.1.2"],
            technologies=["nginx", "PHP", "MySQL"],
            ports=[80, 443, 22],
            is_alive=True,
        )
        assert info.name == "sub.example.com"
        assert info.ip_addresses == ["192.168.1.1", "192.168.1.2"]
        assert info.technologies == ["nginx", "PHP", "MySQL"]
        assert info.ports == [80, 443, 22]
        assert info.is_alive is True


# ==================== DomainRecon Tests ====================


class TestDomainRecon:
    """Test DomainRecon model"""

    def test_minimal_creation(self):
        """Test creating domain recon with minimal fields"""
        recon = DomainRecon(domain="example.com")
        assert recon.domain == "example.com"
        assert recon.subdomains == []
        assert recon.emails == []
        assert recon.technologies == []

    def test_full_creation(self):
        """Test creating domain recon with all fields"""
        subdomain = SubdomainInfo(name="www.example.com", ip_addresses=["192.168.1.1"], is_alive=True)
        recon = DomainRecon(
            domain="example.com",
            registrar="GoDaddy",
            creation_date=datetime(2020, 1, 1),
            expiration_date=datetime(2025, 1, 1),
            name_servers=["ns1.example.com", "ns2.example.com"],
            subdomains=[subdomain],
            emails=["admin@example.com"],
            technologies=["Cloudflare", "WordPress"],
        )
        assert recon.domain == "example.com"
        assert recon.registrar == "GoDaddy"
        assert len(recon.subdomains) == 1
        assert len(recon.emails) == 1


# ==================== HealthStatus Tests ====================


class TestHealthStatus:
    """Test HealthStatus model"""

    def test_creation(self):
        """Test creating health status"""
        status = HealthStatus(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.0,
            checks={"database": True, "redis": False},
            backends={"openai": "available", "anthropic": "unavailable"},
        )
        assert status.status == "healthy"
        assert status.version == "1.0.0"
        assert status.uptime_seconds == 3600.0
        assert status.checks["database"] is True
        assert status.backends["openai"] == "available"

    def test_default_checks(self):
        """Test default empty checks dict"""
        status = HealthStatus(status="healthy", version="1.0.0", uptime_seconds=0.0)
        assert status.checks == {}
        assert status.backends == {}


# ==================== PaginatedResponse Tests ====================


class TestPaginatedResponse:
    """Test PaginatedResponse model"""

    def test_creation(self):
        """Test creating paginated response"""
        response = PaginatedResponse(items=["item1", "item2", "item3"], total=100, page=1, per_page=10, pages=10)
        assert len(response.items) == 3
        assert response.total == 100
        assert response.page == 1
        assert response.per_page == 10
        assert response.pages == 10

    def test_has_next_true(self):
        """Test has_next when there are more pages"""
        response = PaginatedResponse(items=[], total=100, page=1, per_page=10, pages=10)
        assert response.has_next is True

    def test_has_next_false(self):
        """Test has_next when on last page"""
        response = PaginatedResponse(items=[], total=100, page=10, per_page=10, pages=10)
        assert response.has_next is False

    def test_has_prev_true(self):
        """Test has_prev when not on first page"""
        response = PaginatedResponse(items=[], total=100, page=2, per_page=10, pages=10)
        assert response.has_prev is True

    def test_has_prev_false(self):
        """Test has_prev when on first page"""
        response = PaginatedResponse(items=[], total=100, page=1, per_page=10, pages=10)
        assert response.has_prev is False


# ==================== ReportConfig Tests ====================


class TestReportConfig:
    """Test ReportConfig model"""

    def test_default_values(self):
        """Test default report configuration"""
        config = ReportConfig(title="Security Assessment Report", client_name="Example Corp")
        assert config.title == "Security Assessment Report"
        assert config.client_name == "Example Corp"
        assert config.format == "markdown"
        assert config.template == "technical"
        assert config.include_evidence is True
        assert config.include_remediation is True
        assert config.severity_filter is None

    def test_custom_values(self):
        """Test custom report configuration"""
        config = ReportConfig(
            title="Penetration Test Report",
            client_name="Acme Inc",
            format="pdf",
            template="executive",
            include_evidence=False,
            include_remediation=True,
            severity_filter=[Severity.HIGH, Severity.CRITICAL],
        )
        assert config.format == "pdf"
        assert config.template == "executive"
        assert config.include_evidence is False
        assert len(config.severity_filter) == 2

    def test_format_validation(self):
        """Test format validation"""
        with pytest.raises(ValueError):
            ReportConfig(title="Test", client_name="Test", format="invalid")

    def test_template_validation_valid(self):
        """Test template validation with valid templates"""
        for template in ["executive", "technical", "detailed"]:
            config = ReportConfig(title="Test", client_name="Test", template=template)
            assert config.template == template

    def test_template_validation_invalid(self):
        """Test template validation with invalid template"""
        with pytest.raises(ValueError, match="Template must be one of"):
            ReportConfig(title="Test", client_name="Test", template="invalid")

    def test_title_validation_empty(self):
        """Test title validation rejects empty string"""
        with pytest.raises(ValueError):
            ReportConfig(title="", client_name="Test")

    def test_title_validation_too_long(self):
        """Test title validation rejects too long title"""
        with pytest.raises(ValueError):
            ReportConfig(title="a" * 201, client_name="Test")

    def test_client_name_validation_empty(self):
        """Test client name validation rejects empty string"""
        with pytest.raises(ValueError):
            ReportConfig(title="Test", client_name="")

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            ReportConfig(title="Test", client_name="Test", invalid_field="value")


# ==================== Serialization Tests ====================


class TestSerialization:
    """Test model serialization and deserialization"""

    def test_finding_serialization(self):
        """Test finding serialization to JSON"""
        finding = Finding(
            title="Test Finding",
            description="Test description",
            severity=Severity.HIGH,
            host="example.com",
            cve_ids=["CVE-2023-1234"],
        )
        json_str = finding.model_dump_json()
        assert "Test Finding" in json_str
        assert "high" in json_str

    def test_finding_deserialization(self):
        """Test finding deserialization from dict"""
        data = {"title": "Test Finding", "description": "Test description", "severity": "high", "host": "example.com"}
        finding = Finding.model_validate(data)
        assert finding.title == "Test Finding"
        assert finding.severity == Severity.HIGH

    def test_scan_result_serialization(self):
        """Test scan result serialization"""
        started = datetime.utcnow()
        result = ScanResult(scan_id="SCAN-001", target="example.com", status=ScanStatus.COMPLETED, started_at=started)
        data = result.model_dump()
        assert data["scan_id"] == "SCAN-001"
        assert data["status"] == "completed"

    def test_complex_nested_serialization(self):
        """Test serialization of nested models"""
        finding = Finding(title="Test", description="Test", severity=Severity.CRITICAL, host="example.com")
        started = datetime.utcnow()
        result = ScanResult(
            scan_id="SCAN-001", target="example.com", status=ScanStatus.COMPLETED, started_at=started, findings=[finding]
        )
        data = result.model_dump()
        assert len(data["findings"]) == 1
        assert data["findings"][0]["title"] == "Test"


# ==================== Edge Case Tests ====================


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_unicode_in_fields(self):
        """Test handling of unicode characters"""
        finding = Finding(
            title="Unicode Test: 日本語", description="Description with emoji: 🚀", severity=Severity.INFO, host="例子.com"
        )
        assert finding.title == "Unicode Test: 日本語"
        assert "🚀" in finding.description

    def test_special_chars_in_description(self):
        """Test handling of special characters"""
        finding = Finding(title="Special Chars", description="Special: <>&\"'", severity=Severity.LOW, host="test.com")
        assert "<>&\"'" in finding.description

    def test_very_long_description(self):
        """Test handling of very long description"""
        long_desc = "A" * 10000
        finding = Finding(title="Long Description Test", description=long_desc, severity=Severity.MEDIUM, host="test.com")
        assert len(finding.description) == 10000

    def test_multiple_cve_ids(self):
        """Test handling of multiple CVE IDs"""
        cves = [f"CVE-2023-{i:04d}" for i in range(1, 11)]
        finding = Finding(title="Multiple CVEs", description="Test", severity=Severity.HIGH, host="test.com", cve_ids=cves)
        assert len(finding.cve_ids) == 10

    def test_empty_lists(self):
        """Test handling of explicitly empty lists"""
        finding = Finding(
            title="Empty Lists", description="Test", severity=Severity.LOW, host="test.com", cve_ids=[], tags=[], references=[]
        )
        assert finding.cve_ids == []
        assert finding.tags == []
        assert finding.references == []

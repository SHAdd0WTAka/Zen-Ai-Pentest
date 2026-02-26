"""
Tests for core/models.py
Target: 90%+ Coverage
"""
import pytest
from datetime import datetime, timedelta


class TestEnums:
    """Test Enum classes"""
    
    def test_severity_enum(self):
        """Test Severity enum values"""
        from core.models import Severity
        
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"
    
    def test_scan_status_enum(self):
        """Test ScanStatus enum values"""
        from core.models import ScanStatus
        
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"
    
    def test_backend_type_enum(self):
        """Test BackendType enum values"""
        from core.models import BackendType
        
        assert BackendType.DUCKDUCKGO == "duckduckgo"
        assert BackendType.OPENROUTER == "openrouter"
        assert BackendType.OPENAI == "openai"
        assert BackendType.ANTHROPIC == "anthropic"


class TestTimestampedModel:
    """Test TimestampedModel"""
    
    def test_default_timestamps(self):
        """Test default timestamp creation"""
        from core.models import TimestampedModel
        
        model = TimestampedModel()
        assert model.created_at is not None
        assert model.updated_at is None


class TestAPIKeyConfig:
    """Test APIKeyConfig model"""
    
    def test_valid_openrouter_key(self):
        """Test valid OpenRouter key"""
        from core.models import APIKeyConfig
        
        config = APIKeyConfig(openrouter_key="sk-or-123456789012345678901234567890")
        assert config.openrouter_key is not None
    
    def test_valid_openai_key(self):
        """Test valid OpenAI key"""
        from core.models import APIKeyConfig
        
        config = APIKeyConfig(openai_key="sk-1234567890123456789012345678")
        assert config.openai_key is not None
    
    def test_valid_anthropic_key(self):
        """Test valid Anthropic key"""
        from core.models import APIKeyConfig
        
        config = APIKeyConfig(anthropic_key="sk-ant-12345678901234567890")
        assert config.anthropic_key is not None
    
    def test_get_key_mapping(self):
        """Test get_key returns correct key"""
        from core.models import APIKeyConfig, BackendType
        
        config = APIKeyConfig(
            openrouter_key="sk-or-123456789012345678901234567890",
            openai_key="sk-12345678901234567890123456789012",
            anthropic_key="sk-ant-1234567890123456789012345"
        )
        
        assert config.get_key(BackendType.OPENROUTER) == "sk-or-123456789012345678901234567890"
        assert config.get_key(BackendType.OPENAI) == "sk-12345678901234567890123456789012"
        assert config.get_key(BackendType.ANTHROPIC) == "sk-ant-1234567890123456789012345"
        assert config.get_key(BackendType.DUCKDUCKGO) is None
    
    def test_empty_config(self):
        """Test empty config is valid"""
        from core.models import APIKeyConfig
        
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None


class TestScanConfig:
    """Test ScanConfig model"""
    
    def test_default_config(self):
        """Test default configuration"""
        from core.models import ScanConfig
        
        config = ScanConfig(target="example.com")
        assert config.target == "example.com"
        assert config.scan_type == "quick"
        assert config.ports == [80, 443]
        assert config.templates == []
        assert config.timeout == 300
        assert config.concurrent == 5
        assert config.follow_redirects is True
    
    def test_valid_target_domain(self):
        """Test valid domain target"""
        from core.models import ScanConfig
        
        config = ScanConfig(target="example.com")
        assert config.target == "example.com"
    
    def test_valid_target_ip(self):
        """Test valid IP target"""
        from core.models import ScanConfig
        
        config = ScanConfig(target="192.168.1.1")
        assert config.target == "192.168.1.1"
    
    def test_invalid_target_dangerous_chars(self):
        """Test target with dangerous chars is rejected"""
        from core.models import ScanConfig
        
        with pytest.raises(ValueError):
            ScanConfig(target="example.com; rm -rf")
    
    def test_invalid_target_format(self):
        """Test invalid target format is rejected"""
        from core.models import ScanConfig
        
        with pytest.raises(ValueError):
            ScanConfig(target="not_a_valid_target!")
    
    def test_valid_ports(self):
        """Test valid port numbers"""
        from core.models import ScanConfig
        
        config = ScanConfig(target="example.com", ports=[80, 443, 8080, 22])
        assert config.ports == [80, 443, 8080, 22]
    
    def test_invalid_port_too_low(self):
        """Test port below 1 is rejected"""
        from core.models import ScanConfig
        
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", ports=[0])
    
    def test_invalid_port_too_high(self):
        """Test port above 65535 is rejected"""
        from core.models import ScanConfig
        
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", ports=[70000])
    
    def test_timeout_constraints(self):
        """Test timeout constraints"""
        from core.models import ScanConfig
        
        # Valid timeouts
        ScanConfig(target="example.com", timeout=10)
        ScanConfig(target="example.com", timeout=3600)
        
        # Invalid timeouts
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", timeout=5)
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", timeout=4000)
    
    def test_concurrent_constraints(self):
        """Test concurrent constraints"""
        from core.models import ScanConfig
        
        # Valid
        ScanConfig(target="example.com", concurrent=1)
        ScanConfig(target="example.com", concurrent=50)
        
        # Invalid
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", concurrent=0)
        with pytest.raises(ValueError):
            ScanConfig(target="example.com", concurrent=100)


class TestFinding:
    """Test Finding model"""
    
    def test_create_finding(self):
        """Test creating a finding"""
        from core.models import Finding, Severity
        
        finding = Finding(
            title="SQL Injection",
            description="SQL injection vulnerability found",
            severity=Severity.HIGH,
            host="example.com"
        )
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH
    
    def test_valid_cve_format(self):
        """Test valid CVE ID format"""
        from core.models import Finding, Severity
        
        finding = Finding(
            title="Test",
            description="Test finding",
            severity=Severity.MEDIUM,
            host="example.com",
            cve_ids=["CVE-2021-44228", "CVE-2023-1234"]
        )
        assert "CVE-2021-44228" in finding.cve_ids
    
    def test_cve_converted_to_uppercase(self):
        """Test CVE IDs are converted to uppercase"""
        from core.models import Finding, Severity
        
        finding = Finding(
            title="Test",
            description="Test finding",
            severity=Severity.MEDIUM,
            host="example.com",
            cve_ids=["cve-2021-44228"]
        )
        assert "CVE-2021-44228" in finding.cve_ids
    
    def test_invalid_cve_format(self):
        """Test invalid CVE format is rejected"""
        from core.models import Finding, Severity
        
        with pytest.raises(ValueError):
            Finding(
                title="Test",
                description="Test finding",
                severity=Severity.MEDIUM,
                host="example.com",
                cve_ids=["invalid-cve"]
            )
    
    def test_cvss_score_range(self):
        """Test CVSS score range validation"""
        from core.models import Finding, Severity
        
        # Valid scores
        Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", cvss_score=0)
        Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", cvss_score=10)
        
        # Invalid scores
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", cvss_score=-1)
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", cvss_score=11)
    
    def test_port_range(self):
        """Test port range validation"""
        from core.models import Finding, Severity
        
        # Valid
        Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", port=80)
        Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", port=65535)
        
        # Invalid
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", port=0)
        with pytest.raises(ValueError):
            Finding(title="Test", description="Test", severity=Severity.LOW, host="example.com", port=70000)


class TestScanResult:
    """Test ScanResult model"""
    
    def test_create_scan_result(self):
        """Test creating scan result"""
        from core.models import ScanResult, ScanStatus
        
        result = ScanResult(
            scan_id="scan-123",
            target="example.com",
            status=ScanStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        assert result.scan_id == "scan-123"
        assert result.duration_seconds is None  # Not completed yet
    
    def test_duration_seconds(self):
        """Test duration calculation"""
        from core.models import ScanResult, ScanStatus
        
        started = datetime.utcnow()
        completed = started + timedelta(minutes=5)
        
        result = ScanResult(
            scan_id="scan-123",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=started,
            completed_at=completed
        )
        
        assert result.duration_seconds is not None
        assert result.duration_seconds == pytest.approx(300, abs=1)
    
    def test_severity_counts(self):
        """Test severity counting"""
        from core.models import ScanResult, ScanStatus, Finding, Severity
        
        result = ScanResult(
            scan_id="scan-123",
            target="example.com",
            status=ScanStatus.COMPLETED,
            started_at=datetime.utcnow(),
            findings=[
                Finding(title="Crit", description="Critical", severity=Severity.CRITICAL, host="h1"),
                Finding(title="High1", description="High", severity=Severity.HIGH, host="h1"),
                Finding(title="High2", description="High", severity=Severity.HIGH, host="h1"),
                Finding(title="Med", description="Medium", severity=Severity.MEDIUM, host="h1"),
            ]
        )
        
        counts = result.severity_counts
        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["low"] == 0


class TestLLMRequest:
    """Test LLMRequest model"""
    
    def test_default_values(self):
        """Test default values"""
        from core.models import LLMRequest
        
        request = LLMRequest(prompt="Hello")
        assert request.prompt == "Hello"
        assert request.temperature == 0.7
        assert request.system_prompt is None
    
    def test_prompt_sanitization(self):
        """Test prompt sanitization"""
        from core.models import LLMRequest
        
        request = LLMRequest(prompt="Hello\x00World\x01\x02")
        assert "\x00" not in request.prompt
        assert "\x01" not in request.prompt
    
    def test_temperature_range(self):
        """Test temperature range validation"""
        from core.models import LLMRequest
        
        # Valid
        LLMRequest(prompt="Test", temperature=0)
        LLMRequest(prompt="Test", temperature=2)
        
        # Invalid
        with pytest.raises(ValueError):
            LLMRequest(prompt="Test", temperature=-0.1)
        with pytest.raises(ValueError):
            LLMRequest(prompt="Test", temperature=2.1)
    
    def test_max_tokens_range(self):
        """Test max_tokens range validation"""
        from core.models import LLMRequest
        
        # Valid
        LLMRequest(prompt="Test", max_tokens=1)
        LLMRequest(prompt="Test", max_tokens=32000)
        
        # Invalid
        with pytest.raises(ValueError):
            LLMRequest(prompt="Test", max_tokens=0)
        with pytest.raises(ValueError):
            LLMRequest(prompt="Test", max_tokens=40000)


class TestLLMResponse:
    """Test LLMResponse model"""
    
    def test_success_property(self):
        """Test success property"""
        from core.models import LLMResponse, BackendType
        
        success_response = LLMResponse(
            content="Hello",
            backend=BackendType.OPENAI
        )
        assert success_response.success is True
        
        error_response = LLMResponse(
            content="",
            backend=BackendType.OPENAI,
            error="API Error"
        )
        assert error_response.success is False


class TestSubdomainInfo:
    """Test SubdomainInfo model"""
    
    def test_create_subdomain(self):
        """Test creating subdomain info"""
        from core.models import SubdomainInfo
        
        subdomain = SubdomainInfo(
            name="sub.example.com",
            ip_addresses=["192.168.1.1"],
            technologies=["nginx", "php"],
            ports=[80, 443],
            is_alive=True
        )
        assert subdomain.name == "sub.example.com"
        assert subdomain.is_alive is True
    
    def test_default_values(self):
        """Test default values"""
        from core.models import SubdomainInfo
        
        subdomain = SubdomainInfo(name="sub.example.com")
        assert subdomain.ip_addresses == []
        assert subdomain.technologies == []
        assert subdomain.ports == []
        assert subdomain.is_alive is False


class TestDomainRecon:
    """Test DomainRecon model"""
    
    def test_create_recon(self):
        """Test creating domain recon"""
        from core.models import DomainRecon, SubdomainInfo
        
        recon = DomainRecon(
            domain="example.com",
            registrar="GoDaddy",
            name_servers=["ns1.example.com", "ns2.example.com"],
            subdomains=[SubdomainInfo(name="www.example.com")],
            emails=["admin@example.com"]
        )
        assert recon.domain == "example.com"
        assert len(recon.subdomains) == 1


class TestHealthStatus:
    """Test HealthStatus model"""
    
    def test_create_health_status(self):
        """Test creating health status"""
        from core.models import HealthStatus
        
        status = HealthStatus(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600,
            checks={"database": True, "api": True}
        )
        assert status.status == "healthy"
        assert status.checks["database"] is True


class TestPaginatedResponse:
    """Test PaginatedResponse model"""
    
    def test_pagination_properties(self):
        """Test pagination properties"""
        from core.models import PaginatedResponse
        
        response = PaginatedResponse(
            items=[1, 2, 3],
            total=100,
            page=1,
            per_page=10,
            pages=10
        )
        assert response.has_next is True
        assert response.has_prev is False
    
    def test_middle_page(self):
        """Test middle page pagination"""
        from core.models import PaginatedResponse
        
        response = PaginatedResponse(
            items=[],
            total=100,
            page=5,
            per_page=10,
            pages=10
        )
        assert response.has_next is True
        assert response.has_prev is True
    
    def test_last_page(self):
        """Test last page pagination"""
        from core.models import PaginatedResponse
        
        response = PaginatedResponse(
            items=[],
            total=100,
            page=10,
            per_page=10,
            pages=10
        )
        assert response.has_next is False
        assert response.has_prev is True


class TestReportConfig:
    """Test ReportConfig model"""
    
    def test_default_config(self):
        """Test default configuration"""
        from core.models import ReportConfig
        
        config = ReportConfig(
            title="Test Report",
            client_name="Test Client"
        )
        assert config.format == "markdown"
        assert config.template == "technical"
        assert config.include_evidence is True
    
    def test_valid_template(self):
        """Test valid template values"""
        from core.models import ReportConfig
        
        ReportConfig(title="Test", client_name="Client", template="executive")
        ReportConfig(title="Test", client_name="Client", template="technical")
        ReportConfig(title="Test", client_name="Client", template="detailed")
    
    def test_invalid_template(self):
        """Test invalid template is rejected"""
        from core.models import ReportConfig
        
        with pytest.raises(ValueError):
            ReportConfig(title="Test", client_name="Client", template="invalid")
    
    def test_title_constraints(self):
        """Test title length constraints"""
        from core.models import ReportConfig
        
        # Valid
        ReportConfig(title="A" * 200, client_name="Client")
        
        # Invalid
        with pytest.raises(ValueError):
            ReportConfig(title="", client_name="Client")
        with pytest.raises(ValueError):
            ReportConfig(title="A" * 201, client_name="Client")

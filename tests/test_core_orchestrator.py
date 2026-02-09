"""
Tests for core/orchestrator.py - ZenOrchestrator

This module tests the ZenOrchestrator class which manages multi-LLM routing
and penetration testing capabilities.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Mock modules that may not be available
import sys
from unittest.mock import MagicMock

# Create mock modules
mock_autonomous = MagicMock()
mock_autonomous.AutonomousAgentLoop = MagicMock
mock_autonomous.AgentState = MagicMock
mock_autonomous.AgentMemory = MagicMock
mock_autonomous.ExploitValidator = MagicMock
mock_autonomous.ExploitValidatorPool = MagicMock
mock_autonomous.ExploitType = MagicMock()
mock_autonomous.ExploitType.WEB_SQLI = "sqli"
mock_autonomous.ExploitType.WEB_XSS = "xss"
mock_autonomous.ExploitType.WEB_RCE = "rce"
mock_autonomous.ExploitType.WEB_LFI = "lfi"
mock_autonomous.ExploitType.WEB_CMD_INJECTION = "cmd_injection"
mock_autonomous.ScopeConfig = MagicMock
mock_autonomous.SandboxConfig = MagicMock
mock_autonomous.ExploitResult = MagicMock

mock_risk_engine = MagicMock()
mock_risk_engine.FalsePositiveEngine = MagicMock
mock_risk_engine.BusinessImpactCalculator = MagicMock
mock_risk_engine.Finding = MagicMock
mock_risk_engine.FindingStatus = MagicMock
mock_risk_engine.ValidationResult = MagicMock
mock_risk_engine.ConfidenceLevel = MagicMock
mock_risk_engine.ComplianceType = MagicMock
mock_risk_engine.DataClassification = MagicMock
mock_risk_engine.AssetContext = MagicMock
mock_risk_engine.AssetCriticality = MagicMock

sys.modules['autonomous'] = mock_autonomous
sys.modules['risk_engine'] = mock_risk_engine
sys.modules['integrations'] = MagicMock()

from core.orchestrator import (
    ZenOrchestrator,
    BaseBackend,
    QualityLevel,
    LLMResponse,
)


class MockBackend(BaseBackend):
    """Mock backend for testing"""
    
    def __init__(self, name: str, priority: int, response: str = "test response"):
        super().__init__(name, priority)
        self.response = response
        self.call_count = 0
        self.should_fail = False
    
    async def chat(self, prompt: str, context: str = "") -> str:
        self.call_count += 1
        if self.should_fail:
            raise Exception("Backend failed")
        return self.response
    
    async def health_check(self) -> bool:
        return not self.should_fail


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator instance"""
    return ZenOrchestrator()


@pytest.fixture
def mock_backend_low():
    """Create a low priority (free) backend"""
    return MockBackend("ddg", 1, "DDG response")


@pytest.fixture
def mock_backend_medium():
    """Create a medium priority backend"""
    return MockBackend("openrouter", 2, "OpenRouter response")


@pytest.fixture
def mock_backend_high():
    """Create a high priority (premium) backend"""
    return MockBackend("openai", 3, "OpenAI premium response")


class TestZenOrchestratorInitialization:
    """Test ZenOrchestrator initialization"""
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly"""
        orch = ZenOrchestrator()
        assert orch is not None
        assert orch.backends == []
        assert orch.results_cache == {}
        assert orch.request_count == 0
    
    def test_orchestrator_initializes_components(self):
        """Test that orchestrator initializes optional components"""
        orch = ZenOrchestrator()
        # Components may or may not be available depending on imports
        assert hasattr(orch, '_autonomous_loop')
        assert hasattr(orch, '_fp_engine')
        assert hasattr(orch, '_exploit_validator')
        assert hasattr(orch, '_business_impact')
        assert hasattr(orch, '_integrations')


class TestBackendRegistration:
    """Test backend registration"""
    
    @pytest.mark.asyncio
    async def test_add_single_backend(self, orchestrator, mock_backend_low):
        """Test adding a single backend"""
        orchestrator.add_backend(mock_backend_low)
        assert len(orchestrator.backends) == 1
        assert orchestrator.backends[0].name == "ddg"
    
    @pytest.mark.asyncio
    async def test_add_multiple_backends_sorted(self, orchestrator, mock_backend_low, mock_backend_medium, mock_backend_high):
        """Test that backends are sorted by priority"""
        orchestrator.add_backend(mock_backend_high)
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        
        assert len(orchestrator.backends) == 3
        # Should be sorted by priority (lowest first)
        assert orchestrator.backends[0].priority == 1
        assert orchestrator.backends[1].priority == 2
        assert orchestrator.backends[2].priority == 3
    
    @pytest.mark.asyncio
    async def test_add_backend_logs_registration(self, orchestrator, mock_backend_low, caplog):
        """Test that backend registration is logged"""
        import logging
        with caplog.at_level(logging.INFO):
            orchestrator.add_backend(mock_backend_low)
        assert "ddg" in caplog.text
        assert "registered" in caplog.text


class TestPromptProcessing:
    """Test prompt processing through backends"""
    
    @pytest.mark.asyncio
    async def test_process_with_single_backend(self, orchestrator, mock_backend_low):
        """Test processing with a single backend"""
        orchestrator.add_backend(mock_backend_low)
        
        response = await orchestrator.process("test prompt", QualityLevel.LOW)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "DDG response"
        assert response.source == "ddg"
        assert response.quality == QualityLevel.LOW
        assert response.latency >= 0
    
    @pytest.mark.asyncio
    async def test_process_with_multiple_backends_fallback(self, orchestrator, mock_backend_low, mock_backend_medium):
        """Test fallback to second backend when first fails"""
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        
        response = await orchestrator.process("test prompt", QualityLevel.MEDIUM)
        
        assert response.content == "OpenRouter response"
        assert response.source == "openrouter"
        assert mock_backend_low.call_count == 1
        assert mock_backend_medium.call_count == 1
    
    @pytest.mark.asyncio
    async def test_process_all_backends_fail(self, orchestrator, mock_backend_low):
        """Test when all backends fail"""
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        
        response = await orchestrator.process("test prompt")
        
        assert "failed" in response.content.lower()
        assert response.source == "None"
    
    @pytest.mark.asyncio
    async def test_process_quality_filtering_low(self, orchestrator, mock_backend_low, mock_backend_medium, mock_backend_high):
        """Test that LOW quality only uses priority 1 backends"""
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        orchestrator.add_backend(mock_backend_high)
        
        response = await orchestrator.process("test", QualityLevel.LOW)
        
        assert mock_backend_low.call_count == 1
        assert mock_backend_medium.call_count == 0
        assert mock_backend_high.call_count == 0
    
    @pytest.mark.asyncio
    async def test_process_quality_filtering_medium(self, orchestrator, mock_backend_low, mock_backend_medium, mock_backend_high):
        """Test that MEDIUM quality uses priority 1-2 backends"""
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        orchestrator.add_backend(mock_backend_high)
        
        response = await orchestrator.process("test", QualityLevel.MEDIUM)
        
        assert mock_backend_medium.call_count == 1
        assert mock_backend_high.call_count == 0
    
    @pytest.mark.asyncio
    async def test_process_quality_filtering_high(self, orchestrator, mock_backend_low, mock_backend_medium, mock_backend_high):
        """Test that HIGH quality uses all backends"""
        mock_backend_low.should_fail = True
        mock_backend_medium.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        orchestrator.add_backend(mock_backend_high)
        
        response = await orchestrator.process("test", QualityLevel.HIGH)
        
        assert response.source == "openai"
    
    @pytest.mark.asyncio
    async def test_process_tracks_request_count(self, orchestrator, mock_backend_low):
        """Test that request count is tracked"""
        orchestrator.add_backend(mock_backend_low)
        
        await orchestrator.process("test1")
        await orchestrator.process("test2")
        await orchestrator.process("test3")
        
        assert orchestrator.request_count == 3
    
    @pytest.mark.asyncio
    async def test_process_short_response_considered_failure(self, orchestrator):
        """Test that very short responses are treated as failures"""
        backend = MockBackend("test", 1, "ab")  # Too short
        orchestrator.add_backend(backend)
        
        response = await orchestrator.process("test")
        
        assert "failed" in response.content.lower()


class TestParallelConsensus:
    """Test parallel consensus mode"""
    
    @pytest.mark.asyncio
    async def test_parallel_consensus_returns_responses(self, orchestrator, mock_backend_low, mock_backend_medium):
        """Test parallel consensus returns responses from multiple backends"""
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        
        result = await orchestrator.parallel_consensus("test prompt")
        
        assert "responses" in result
        assert "consensus" in result
        assert len(result["responses"]) == 2
    
    @pytest.mark.asyncio
    async def test_parallel_consensus_handles_failures(self, orchestrator, mock_backend_low, mock_backend_medium):
        """Test parallel consensus handles backend failures"""
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        
        result = await orchestrator.parallel_consensus("test prompt")
        
        assert len(result["responses"]) == 1
        assert result["consensus"] is not None
    
    @pytest.mark.asyncio
    async def test_parallel_consensus_all_fail(self, orchestrator, mock_backend_low):
        """Test parallel consensus when all backends fail"""
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        
        result = await orchestrator.parallel_consensus("test prompt")
        
        assert result["responses"] == []
        assert result["consensus"] is None


class TestAutonomousScan:
    """Test autonomous scan functionality"""
    
    @pytest.mark.asyncio
    async def test_autonomous_scan_not_available(self, orchestrator):
        """Test autonomous scan when component not available"""
        orchestrator._autonomous_loop = None
        
        result = await orchestrator.run_autonomous_scan("target.com", "find vulns")
        
        assert result["success"] is False
        assert "not available" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_autonomous_scan_success(self, orchestrator):
        """Test successful autonomous scan"""
        mock_loop = AsyncMock()
        mock_loop.run.return_value = {
            "success": True,
            "state": "completed",
            "findings": {"items": [{"id": "1", "title": "Test Finding"}]}
        }
        orchestrator._autonomous_loop = mock_loop
        orchestrator._fp_engine = None  # Skip validation
        
        result = await orchestrator.run_autonomous_scan("target.com", "find vulns")
        
        assert result["success"] is True
        assert mock_loop.run.called
    
    @pytest.mark.asyncio
    async def test_autonomous_scan_exception(self, orchestrator):
        """Test autonomous scan when exception occurs"""
        mock_loop = AsyncMock()
        mock_loop.run.side_effect = Exception("Scan failed")
        orchestrator._autonomous_loop = mock_loop
        
        result = await orchestrator.run_autonomous_scan("target.com", "find vulns")
        
        assert result["success"] is False
        assert "scan failed" in result["error"].lower()


class TestFindingsValidation:
    """Test findings validation functionality"""
    
    @pytest.mark.asyncio
    async def test_validate_findings_not_available(self, orchestrator):
        """Test validation when risk engine not available"""
        orchestrator._fp_engine = None
        
        findings = [{"id": "1", "title": "Test"}]
        result = await orchestrator.validate_findings(findings)
        
        assert result == findings  # Should return unvalidated
    
    @pytest.mark.asyncio
    async def test_validate_findings_with_engine(self, orchestrator):
        """Test validation with risk engine"""
        mock_engine = AsyncMock()
        mock_result = Mock()
        mock_result.is_false_positive = False
        mock_result.confidence = 0.9
        mock_result.priority = 1
        mock_result.to_dict.return_value = {"score": 0.9}
        mock_engine.validate_finding.return_value = mock_result
        orchestrator._fp_engine = mock_engine
        
        findings = [{"id": "1", "title": "Test", "severity": "high"}]
        result = await orchestrator.validate_findings(findings)
        
        assert len(result) == 1
        assert "validation" in result[0]
        assert result[0]["is_false_positive"] is False


class TestExploitExecution:
    """Test exploit execution functionality"""
    
    @pytest.mark.asyncio
    async def test_execute_exploit_not_available(self, orchestrator):
        """Test exploit execution when validator not available"""
        with patch('core.orchestrator.AUTONOMOUS_AVAILABLE', False):
            result = await orchestrator.execute_exploit({}, "target.com")
            
            assert result["success"] is False
            assert "not available" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_execute_exploit_success(self, orchestrator):
        """Test successful exploit execution"""
        with patch('core.orchestrator.AUTONOMOUS_AVAILABLE', True):
            with patch('core.orchestrator.ExploitValidator') as mock_validator_class:
                mock_validator = AsyncMock()
                mock_result = Mock()
                mock_result.success = True
                mock_result.evidence = Mock()
                mock_result.evidence.to_dict.return_value = {"screenshot": "test.png"}
                mock_result.output = "Exploit output"
                mock_result.error = None
                mock_result.severity = "high"
                mock_result.remediation = "Patch it"
                mock_result.execution_time = 1.5
                mock_validator.validate.return_value = mock_result
                mock_validator_class.return_value = mock_validator
                
                exploit = {"code": "exploit_code", "type": "rce"}
                result = await orchestrator.execute_exploit(exploit, "target.com")
                
                assert result["success"] is True
                assert result["exploitable"] is True
                assert result["severity"] == "high"


class TestBusinessImpact:
    """Test business impact calculation"""
    
    @pytest.mark.asyncio
    async def test_calculate_business_impact_not_available(self, orchestrator):
        """Test business impact when calculator not available"""
        orchestrator._business_impact = None
        
        result = await orchestrator.calculate_business_impact({"type": "sql_injection"})
        
        assert "error" in result
        assert result["overall_score"] == 0.5
    
    @pytest.mark.asyncio
    async def test_calculate_business_impact_success(self, orchestrator):
        """Test successful business impact calculation"""
        mock_calc = Mock()
        mock_result = Mock()
        mock_result.overall_score = 8.5
        mock_result.get_risk_category.return_value = "HIGH"
        mock_result.financial_impact = Mock()
        mock_result.financial_impact.total_costs = 100000
        mock_result.financial_impact.direct_costs = 50000
        mock_result.financial_impact.indirect_costs = 50000
        mock_result.compliance_impact = Mock()
        mock_result.compliance_impact.frameworks = []
        mock_result.compliance_impact.violated_controls = []
        mock_result.compliance_impact.get_max_fine.return_value = 0
        mock_result.get_prioritized_remediation.return_value = ["Fix immediately"]
        mock_calc.calculate_overall_impact.return_value = mock_result
        orchestrator._business_impact = mock_calc
        
        with patch('core.orchestrator.RISK_ENGINE_AVAILABLE', True):
            with patch('core.orchestrator.AssetContext') as mock_ctx:
                mock_ctx.return_value = Mock()
                result = await orchestrator.calculate_business_impact(
                    {"type": "sql_injection", "severity": "critical"},
                    {"criticality": "HIGH"}
                )
                
                assert result["overall_score"] == 8.5
                assert result["risk_category"] == "HIGH"


class TestNotifications:
    """Test integration notifications"""
    
    @pytest.mark.asyncio
    async def test_notify_scan_started(self, orchestrator):
        """Test scan started notification"""
        mock_integration = AsyncMock()
        orchestrator._integrations = {"slack": mock_integration}
        
        result = await orchestrator.notify_integrations("scan_started", {"target": "test.com"})
        
        assert result["slack"] is True
        mock_integration.notify_scan_started.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_scan_completed(self, orchestrator):
        """Test scan completed notification"""
        mock_integration = AsyncMock()
        orchestrator._integrations = {"slack": mock_integration}
        
        result = await orchestrator.notify_integrations("scan_completed", {"target": "test.com"})
        
        assert result["slack"] is True
        mock_integration.notify_scan_completed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_finding(self, orchestrator):
        """Test finding notification"""
        mock_integration = AsyncMock()
        orchestrator._integrations = {"slack": mock_integration}
        
        result = await orchestrator.notify_integrations("finding", {"title": "SQL Injection"})
        
        assert result["slack"] is True
        mock_integration.notify_finding.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_integration_failure(self, orchestrator):
        """Test handling integration failure"""
        mock_integration = AsyncMock()
        mock_integration.notify_scan_started.side_effect = Exception("Slack down")
        orchestrator._integrations = {"slack": mock_integration}
        
        result = await orchestrator.notify_integrations("scan_started", {"target": "test.com"})
        
        assert result["slack"] is False


class TestStatsAndCapabilities:
    """Test statistics and capabilities reporting"""
    
    def test_get_stats_empty(self, orchestrator):
        """Test stats with no backends"""
        stats = orchestrator.get_stats()
        
        assert stats["backends_registered"] == 0
        assert stats["requests_processed"] == 0
        assert stats["backends"] == []
    
    def test_get_stats_with_backends(self, orchestrator, mock_backend_low, mock_backend_medium):
        """Test stats with registered backends"""
        orchestrator.add_backend(mock_backend_low)
        orchestrator.add_backend(mock_backend_medium)
        orchestrator.request_count = 10
        
        stats = orchestrator.get_stats()
        
        assert stats["backends_registered"] == 2
        assert stats["requests_processed"] == 10
        assert "ddg" in stats["backends"]
        assert "openrouter" in stats["backends"]
    
    def test_get_capabilities(self, orchestrator):
        """Test capabilities report"""
        caps = orchestrator.get_capabilities()
        
        assert "autonomous_scan" in caps
        assert "false_positive_validation" in caps
        assert "exploit_validation" in caps
        assert "business_impact" in caps
        assert "slack_notifications" in caps
        assert "github_integration" in caps
        assert "jira_integration" in caps
    
    def test_get_capabilities_with_integrations(self, orchestrator):
        """Test capabilities with integrations loaded"""
        orchestrator._integrations = {"slack": Mock(), "github": Mock()}
        orchestrator._autonomous_loop = Mock()
        orchestrator._fp_engine = Mock()
        
        caps = orchestrator.get_capabilities()
        
        assert caps["slack_notifications"] is True
        assert caps["github_integration"] is True
        assert caps["autonomous_scan"] is True


class TestQualityLevel:
    """Test QualityLevel enum"""
    
    def test_quality_levels(self):
        """Test quality level values"""
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"
    
    def test_quality_level_comparison(self):
        """Test quality level ordering"""
        # These are enum values, not numeric
        assert QualityLevel.LOW != QualityLevel.MEDIUM
        assert QualityLevel.MEDIUM != QualityLevel.HIGH


class TestLLMResponse:
    """Test LLMResponse dataclass"""
    
    def test_llm_response_creation(self):
        """Test creating LLMResponse"""
        response = LLMResponse(
            content="Test content",
            source="test_backend",
            latency=0.5,
            quality=QualityLevel.HIGH,
            metadata={"model": "gpt-4"}
        )
        
        assert response.content == "Test content"
        assert response.source == "test_backend"
        assert response.latency == 0.5
        assert response.quality == QualityLevel.HIGH
        assert response.metadata == {"model": "gpt-4"}
    
    def test_llm_response_defaults(self):
        """Test LLMResponse with default metadata"""
        response = LLMResponse(
            content="Test",
            source="test",
            latency=0.1,
            quality=QualityLevel.LOW
        )
        
        assert response.metadata is None


class TestBaseBackend:
    """Test BaseBackend abstract class"""
    
    @pytest.mark.asyncio
    async def test_backend_context_manager(self):
        """Test backend as context manager"""
        backend = MockBackend("test", 1)
        
        async with backend as b:
            assert b.session is not None
        
        # Session should be closed
        # Note: actual closing happens in __aexit__
    
    @pytest.mark.asyncio
    async def test_health_check_default(self):
        """Test default health check implementation"""
        backend = MockBackend("test", 1)
        assert await backend.health_check() is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with failing backend"""
        backend = MockBackend("test", 1)
        backend.should_fail = True
        # Default implementation always returns True
        assert await backend.health_check() is True


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_process_logs_backend_errors(self, orchestrator, mock_backend_low, caplog):
        """Test that backend errors are logged"""
        import logging
        mock_backend_low.should_fail = True
        orchestrator.add_backend(mock_backend_low)
        
        with caplog.at_level(logging.ERROR):
            await orchestrator.process("test")
        
        assert "failed" in caplog.text.lower()
    
    @pytest.mark.asyncio
    async def test_backend_chat_not_implemented(self):
        """Test that BaseBackend chat is abstract"""
        # MockBackend implements chat, so test abstract behavior
        class IncompleteBackend(BaseBackend):
            pass
        
        with pytest.raises(TypeError):
            IncompleteBackend("test", 1)

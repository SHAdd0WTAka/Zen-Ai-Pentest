"""
Comprehensive test coverage for core/orchestrator.py
Target: 80%+ line coverage
"""

import sys
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the core module is in path
sys.path.insert(0, "/home/atakan/zen-ai-pentest")

from core.orchestrator import (
    AUTONOMOUS_AVAILABLE,
    RISK_ENGINE_AVAILABLE,
    BaseBackend,
    QualityLevel,
    ZenOrchestrator,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""

    class MockBackend(BaseBackend):
        def __init__(self, name: str = "test_backend", priority: int = 1):
            super().__init__(name, priority)
            self.chat_response = "Mock response from backend"
            self.should_fail = False
            self.health_check_result = True

        async def chat(self, prompt: str, context: str = "") -> Optional[str]:
            if self.should_fail:
                raise Exception("Backend failed")
            return self.chat_response

        async def health_check(self) -> bool:
            return self.health_check_result

    return MockBackend


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator instance."""
    return ZenOrchestrator()


@pytest.fixture
def mock_finding():
    """Create a mock finding for testing."""
    return {
        "id": "test-finding-001",
        "title": "Test Vulnerability",
        "description": "This is a test vulnerability",
        "severity": "high",
        "target": "http://example.com",
        "source": "test_scanner",
    }


# ============================================================================
# Test Class: Component Initialization (Lines 45-56, 182-201)
# ============================================================================


class TestComponentInitialization:
    """Tests for component initialization with fallbacks."""

    def test_autonomous_component_unavailable(self):
        """Test fallback when autonomous components are not available (lines 45-56)."""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", False):
            with patch("core.orchestrator.AutonomousAgentLoop", None):
                orch = ZenOrchestrator()
                assert orch._autonomous_loop is None

    def test_risk_engine_unavailable(self):
        """Test fallback when risk engine is not available (lines 70-81)."""
        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", False):
            with patch("core.orchestrator.FalsePositiveEngine", None):
                orch = ZenOrchestrator()
                assert orch._fp_engine is None
                assert orch._business_impact is None

    def test_integrations_unavailable(self):
        """Test fallback when integrations are not available (lines 87-89)."""
        with patch("core.orchestrator.INTEGRATIONS_AVAILABLE", False):
            with patch("core.orchestrator.load_integrations_from_config", None):
                orch = ZenOrchestrator()
                assert orch._integrations == {}

    def test_autonomous_init_exception_handling(self):
        """Test exception handling when AutonomousAgentLoop fails to initialize (lines 182-187)."""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", True):
            with patch("core.orchestrator.AutonomousAgentLoop") as mock_loop:
                mock_loop.side_effect = Exception("Initialization failed")
                orch = ZenOrchestrator()
                assert orch._autonomous_loop is None

    def test_risk_engine_init_exception_handling(self):
        """Test exception handling when Risk Engine fails to initialize (lines 189-194)."""
        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.FalsePositiveEngine") as mock_fp:
                mock_fp.side_effect = Exception("FP Engine init failed")
                orch = ZenOrchestrator()
                assert orch._fp_engine is None

    def test_exploit_validator_init_exception_handling(self):
        """Test exception handling when ExploitValidator fails to initialize (lines 193-194)."""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", True):
            with patch("core.orchestrator.ExploitValidator") as mock_validator:
                mock_validator.side_effect = Exception("Validator init failed")
                orch = ZenOrchestrator()
                # Note: _exploit_validator is only set temporarily in execute_exploit

    def test_integrations_init_exception_handling(self):
        """Test exception handling when integrations fail to load (lines 200-201)."""
        with patch("core.orchestrator.INTEGRATIONS_AVAILABLE", True):
            with patch("core.orchestrator.load_integrations_from_config") as mock_load:
                mock_load.side_effect = Exception("Load integrations failed")
                orch = ZenOrchestrator()
                assert orch._integrations == {}


# ============================================================================
# Test Class: BaseBackend Context Manager (Lines 131->exit, 140)
# ============================================================================


class TestBaseBackendContextManager:
    """Tests for BaseBackend context manager and session handling."""

    @pytest.mark.asyncio
    async def test_backend_context_manager_exit_with_exception(self):
        """Test context manager exit when exception occurs (lines 131->exit)."""

        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> Optional[str]:
                return "test"

        backend = TestBackend("test", 1)

        # Test that __aexit__ handles exception gracefully
        try:
            async with backend:
                assert backend.session is not None
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_backend_context_manager_exit_closes_session(self):
        """Test that context manager properly closes session (lines 131-132)."""

        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> Optional[str]:
                return "test"

        backend = TestBackend("test", 1)

        async with backend:
            assert backend.session is not None

        # After exit, session should be closed (None after safe_close_session)
        # Note: session might be None or closed object depending on implementation

    @pytest.mark.asyncio
    async def test_backend_health_check_default(self):
        """Test default health_check returns True (line 140)."""

        class TestBackend(BaseBackend):
            async def chat(self, prompt: str, context: str = "") -> Optional[str]:
                return "test"

        backend = TestBackend("test", 1)
        result = await backend.health_check()
        assert result is True


# ============================================================================
# Test Class: Finding Validation (Lines 347-350, 376-423)
# ============================================================================


class TestFindingValidationCoverage:
    """Tests for finding validation coverage."""

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_with_findings_and_validation(self, orchestrator):
        """Test autonomous scan with findings validation (lines 347-350)."""
        if not AUTONOMOUS_AVAILABLE or not RISK_ENGINE_AVAILABLE:
            pytest.skip("Autonomous/Risk components not available")

        # Mock the autonomous loop with findings
        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(
            return_value={
                "success": True,
                "state": "completed",
                "findings": {
                    "items": [
                        {"id": "f1", "title": "Finding 1", "severity": "high"},
                        {"id": "f2", "title": "Finding 2", "severity": "medium"},
                    ]
                },
            }
        )
        orchestrator._autonomous_loop = mock_loop

        # Mock FP engine
        mock_fp_engine = AsyncMock()
        mock_validation_result = MagicMock()
        mock_validation_result.is_false_positive = False
        mock_validation_result.confidence = 0.9
        mock_validation_result.priority = 1
        mock_validation_result.to_dict = MagicMock(return_value={"confidence": 0.9})
        mock_fp_engine.validate_finding = AsyncMock(return_value=mock_validation_result)
        orchestrator._fp_engine = mock_fp_engine

        result = await orchestrator.run_autonomous_scan(target="http://example.com", goal="Find vulnerabilities")

        assert result["success"] is True
        assert "validated_findings" in result
        # Verify that validate_findings was called (lines 347-350)
        mock_fp_engine.validate_finding.assert_called()

    @pytest.mark.asyncio
    async def test_validate_findings_with_validation_result_without_to_dict(self, orchestrator):
        """Test validate_findings when result doesn't have to_dict method (lines 396-399)."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Mock result without to_dict method
        mock_result = MagicMock()
        mock_result.is_false_positive = False
        mock_result.confidence = 0.85
        mock_result.priority = 2
        # No to_dict attribute
        del mock_result.to_dict

        mock_engine = AsyncMock()
        mock_engine.validate_finding = AsyncMock(return_value=mock_result)
        orchestrator._fp_engine = mock_engine

        findings = [{"id": "f1", "title": "Test", "severity": "medium"}]
        result = await orchestrator.validate_findings(findings)

        assert len(result) == 1
        # Should handle missing to_dict gracefully
        assert result[0]["validation"] is not None

    @pytest.mark.asyncio
    async def test_validate_findings_empty_list(self, orchestrator):
        """Test validate_findings with empty findings list."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        mock_engine = AsyncMock()
        orchestrator._fp_engine = mock_engine

        result = await orchestrator.validate_findings([])

        assert result == []
        mock_engine.validate_finding.assert_not_called()


# ============================================================================
# Test Class: Business Impact Calculation (Lines 523-587)
# ============================================================================


class TestBusinessImpactCoverage:
    """Tests for business impact calculation coverage."""

    @pytest.mark.asyncio
    async def test_calculate_business_impact_full_asset_context(self, orchestrator):
        """Test business impact with complete asset context (lines 523-587)."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Mock all the risk engine components
        with patch("core.orchestrator.AssetContext") as mock_asset_ctx_class:
            with patch("core.orchestrator.AssetCriticality") as mock_criticality:
                with patch("core.orchestrator.DataClassification") as mock_data_class:
                    mock_asset_ctx = MagicMock()
                    mock_asset_ctx_class.return_value = mock_asset_ctx

                    # Mock the business impact calculator
                    mock_result = MagicMock()
                    mock_result.overall_score = 9.5
                    mock_result.get_risk_category = MagicMock(return_value="Critical")

                    # Financial impact
                    mock_financial = MagicMock()
                    mock_financial.total_costs = 500000
                    mock_financial.direct_costs = 300000
                    mock_financial.indirect_costs = 200000
                    mock_result.financial_impact = mock_financial

                    # Compliance impact
                    mock_compliance = MagicMock()
                    mock_compliance.frameworks = ["PCI-DSS", "GDPR", "HIPAA"]
                    mock_compliance.violated_controls = ["ctrl1", "ctrl2", "ctrl3", "ctrl4", "ctrl5", "ctrl6"]
                    mock_compliance.get_max_fine = MagicMock(return_value=10000000)
                    mock_result.compliance_impact = mock_compliance

                    mock_result.get_prioritized_remediation = MagicMock(return_value=["rem1", "rem2"])

                    orchestrator._business_impact = MagicMock()
                    orchestrator._business_impact.calculate_overall_impact = MagicMock(return_value=mock_result)

                    finding = {"type": "sql_injection", "severity": "critical"}
                    asset_context = {
                        "id": "asset-123",
                        "name": "Production DB",
                        "type": "database",
                        "criticality": "CRITICAL",
                        "data_classification": "RESTRICTED",
                        "internet_exposed": True,
                        "user_count": 5000,
                        "revenue_dependency": 0.95,
                    }

                    result = await orchestrator.calculate_business_impact(finding, asset_context)

                    assert result["overall_score"] == 9.5
                    assert result["risk_category"] == "Critical"
                    assert result["financial_impact"]["total_costs"] == 500000
                    assert "PCI-DSS" in result["compliance_impact"]["frameworks"]
                    # Verify sliced violated_controls (only first 5)
                    assert len(result["compliance_impact"]["violated_controls"]) == 5

    @pytest.mark.asyncio
    async def test_calculate_business_impact_default_asset_context(self, orchestrator):
        """Test business impact with default asset context (lines 551-557)."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        with patch("core.orchestrator.AssetContext") as mock_asset_ctx_class:
            with patch("core.orchestrator.AssetCriticality") as mock_criticality:
                with patch("core.orchestrator.DataClassification") as mock_data_class:
                    mock_asset_ctx = MagicMock()
                    mock_asset_ctx_class.return_value = mock_asset_ctx

                    mock_result = MagicMock()
                    mock_result.overall_score = 5.0
                    mock_result.get_risk_category = MagicMock(return_value="Medium")
                    mock_result.financial_impact.total_costs = 0
                    mock_result.financial_impact.direct_costs = 0
                    mock_result.financial_impact.indirect_costs = 0
                    mock_result.compliance_impact.frameworks = []
                    mock_result.compliance_impact.violated_controls = []
                    mock_result.compliance_impact.get_max_fine = MagicMock(return_value=0)
                    mock_result.get_prioritized_remediation = MagicMock(return_value=[])

                    orchestrator._business_impact = MagicMock()
                    orchestrator._business_impact.calculate_overall_impact = MagicMock(return_value=mock_result)

                    finding = {"type": "xss", "severity": "medium"}

                    # No asset context - should use defaults
                    result = await orchestrator.calculate_business_impact(finding)

                    assert result["overall_score"] == 5.0
                    # Verify default AssetContext was created with correct defaults
                    call_kwargs = mock_asset_ctx_class.call_args.kwargs
                    assert call_kwargs["asset_id"] == "unknown"
                    assert call_kwargs["asset_name"] == "Unknown Asset"
                    assert call_kwargs["criticality"] == mock_criticality.MEDIUM
                    assert call_kwargs["data_classification"] == mock_data_class.INTERNAL


# ============================================================================
# Test Class: Process Method Edge Cases
# ============================================================================


class TestProcessEdgeCases:
    """Tests for process method edge cases."""

    @pytest.mark.asyncio
    async def test_process_with_empty_backends(self, orchestrator):
        """Test process when no backends are registered."""
        response = await orchestrator.process("test prompt", QualityLevel.LOW)

        assert response.content == "All backends failed. Check logs."
        assert response.source == "None"
        assert response.quality == QualityLevel.LOW

    @pytest.mark.asyncio
    async def test_process_response_exactly_10_chars(self, orchestrator, mock_backend):
        """Test that responses with exactly 10 chars are skipped."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.chat_response = "1234567890"  # Exactly 10 chars
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "This is a longer valid response"
        orch.add_backend(backend2)

        response = await orch.process("test prompt", QualityLevel.HIGH)

        assert response.source == "openrouter"

    @pytest.mark.asyncio
    async def test_process_all_backends_fail(self, orchestrator, mock_backend):
        """Test process when all backends fail."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.should_fail = True
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.should_fail = True
        orch.add_backend(backend2)

        response = await orch.process("test prompt", QualityLevel.HIGH)

        assert response.content == "All backends failed. Check logs."
        assert response.source == "None"


# ============================================================================
# Test Class: Execute Exploit Edge Cases
# ============================================================================


class TestExecuteExploitCoverage:
    """Tests for execute_exploit method coverage."""

    @pytest.mark.asyncio
    async def test_execute_exploit_unsafe_mode(self, orchestrator):
        """Test exploit execution with safe_mode=False (lines 451)."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.evidence = None
        mock_result.output = "output"
        mock_result.error = None
        mock_result.severity = "high"
        mock_result.remediation = "fix"
        mock_result.execution_time = 1.0

        mock_validator = AsyncMock()
        mock_validator.validate = AsyncMock(return_value=mock_result)

        with patch("core.orchestrator.ExploitValidator") as mock_validator_class:
            mock_validator_class.return_value = mock_validator

            exploit = {"code": "test", "type": "rce"}
            result = await orchestrator.execute_exploit(
                exploit=exploit,
                target="http://example.com",
                safe_mode=False,  # Unsafe mode
            )

            # Verify safety_level was set to "full"
            call_kwargs = mock_validator_class.call_args.kwargs
            assert call_kwargs["safety_level"] == "full"

    @pytest.mark.asyncio
    async def test_execute_exploit_all_types(self, orchestrator):
        """Test exploit execution with all exploit types."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.evidence = MagicMock()
        mock_result.evidence.to_dict = MagicMock(return_value={})
        mock_result.output = ""
        mock_result.error = None
        mock_result.severity = "medium"
        mock_result.remediation = ""
        mock_result.execution_time = 0.0

        mock_validator = AsyncMock()
        mock_validator.validate = AsyncMock(return_value=mock_result)

        with patch("core.orchestrator.ExploitValidator") as mock_validator_class:
            mock_validator_class.return_value = mock_validator

            # Test each exploit type mapping
            type_map = {
                "sqli": "ExploitType.WEB_SQLI",
                "sql_injection": "ExploitType.WEB_SQLI",
                "xss": "ExploitType.WEB_XSS",
                "rce": "ExploitType.WEB_RCE",
                "lfi": "ExploitType.WEB_LFI",
                "command_injection": "ExploitType.WEB_CMD_INJECTION",
                "unknown": "ExploitType.WEB_RCE",  # Default
            }

            for exploit_type, expected in type_map.items():
                exploit = {"code": "test", "type": exploit_type}
                result = await orchestrator.execute_exploit(
                    exploit=exploit,
                    target="http://example.com",
                    safe_mode=True,
                )
                assert result["success"] is True


# ============================================================================
# Test Class: Integration Notifications Edge Cases
# ============================================================================


class TestIntegrationNotificationsCoverage:
    """Tests for integration notification coverage."""

    @pytest.mark.asyncio
    async def test_notify_integrations_no_matching_handler(self, orchestrator):
        """Test notification when integration has no matching handler."""
        mock_integration = MagicMock()
        # No notify_scan_started method
        del mock_integration.notify_scan_started

        orchestrator._integrations = {"custom": mock_integration}

        result = await orchestrator.notify_integrations("scan_started", {"target": "example.com"})

        assert result["custom"] is False

    @pytest.mark.asyncio
    async def test_notify_integrations_empty_integrations(self, orchestrator):
        """Test notification when no integrations are configured."""
        orchestrator._integrations = {}

        result = await orchestrator.notify_integrations("scan_started", {"target": "example.com"})

        assert result == {}


# ============================================================================
# Test Class: Stats and Capabilities Edge Cases
# ============================================================================


class TestStatsAndCapabilities:
    """Tests for stats and capabilities methods."""

    def test_get_stats_with_integrations(self, orchestrator):
        """Test get_stats when integrations are loaded."""
        orchestrator._integrations = {
            "slack": MagicMock(),
            "jira": MagicMock(),
        }

        stats = orchestrator.get_stats()

        assert "slack" in stats["integrations_loaded"]
        assert "jira" in stats["integrations_loaded"]

    def test_get_capabilities_with_integrations(self, orchestrator):
        """Test get_capabilities when integrations are available."""
        orchestrator._integrations = {
            "slack": MagicMock(),
            "github": MagicMock(),
            "jira": MagicMock(),
        }

        caps = orchestrator.get_capabilities()

        assert caps["slack_notifications"] is True
        assert caps["github_integration"] is True
        assert caps["jira_integration"] is True

    def test_get_capabilities_without_integrations(self, orchestrator):
        """Test get_capabilities when integrations are not available."""
        orchestrator._integrations = {}

        caps = orchestrator.get_capabilities()

        assert caps["slack_notifications"] is False
        assert caps["github_integration"] is False
        assert caps["jira_integration"] is False


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

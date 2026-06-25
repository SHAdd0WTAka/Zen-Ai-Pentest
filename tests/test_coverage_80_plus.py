"""
Additional tests to reach 80% coverage
Targeting specific uncovered lines in core/orchestrator.py and database/models.py
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestOrchestratorImportErrorHandling:
    """Test import error handling paths (lines 45-56, 70, 87-89)"""

    def test_autonomous_not_available(self):
        """Test when AUTONOMOUS_AVAILABLE is False (lines 45-56)"""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", False):
            with patch("core.orchestrator.AutonomousAgentLoop", None):
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._autonomous_loop is None

    def test_risk_engine_not_available(self):
        """Test when RISK_ENGINE_AVAILABLE is False (line 70)"""
        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", False):
            with patch("core.orchestrator.FalsePositiveEngine", None):
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._fp_engine is None
                assert o._business_impact is None

    def test_integrations_not_available(self):
        """Test when INTEGRATIONS_AVAILABLE is False (lines 87-89)"""
        with patch("core.orchestrator.INTEGRATIONS_AVAILABLE", False):
            with patch("core.orchestrator.load_integrations_from_config", None):
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._integrations == {}


class TestOrchestratorInitializationErrors:
    """Test exception handling in _initialize_components (lines 172-201)"""

    def test_autonomous_loop_init_exception(self):
        """Test exception handling when AutonomousAgentLoop fails to initialize"""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", True):
            with patch("core.orchestrator.AutonomousAgentLoop") as MockLoop:
                MockLoop.side_effect = Exception("Init failed")
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                # Should not raise, should log warning
                assert o._autonomous_loop is None

    def test_fp_engine_init_exception(self):
        """Test exception handling when FalsePositiveEngine fails to initialize"""
        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.FalsePositiveEngine") as MockFP:
                MockFP.side_effect = Exception("FP Init failed")
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._fp_engine is None

    def test_business_impact_init_exception(self):
        """Test exception handling when BusinessImpactCalculator fails"""
        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.FalsePositiveEngine"):
                with patch("core.orchestrator.BusinessImpactCalculator") as MockBI:
                    MockBI.side_effect = Exception("BI Init failed")
                    from core.orchestrator import ZenOrchestrator

                    o = ZenOrchestrator()
                    assert o._business_impact is None

    def test_exploit_validator_init_exception(self):
        """Test exception handling when ExploitValidator fails to initialize"""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", True):
            with patch("core.orchestrator.ExploitValidator") as MockEV:
                MockEV.side_effect = Exception("EV Init failed")
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._exploit_validator is None

    def test_integrations_load_exception(self):
        """Test exception handling when load_integrations_from_config fails"""
        with patch("core.orchestrator.INTEGRATIONS_AVAILABLE", True):
            with patch("core.orchestrator.load_integrations_from_config") as MockLoad:
                MockLoad.side_effect = Exception("Load failed")
                from core.orchestrator import ZenOrchestrator

                o = ZenOrchestrator()
                assert o._integrations == {}


class TestOrchestratorAutonomousScanWithFindings:
    """Test run_autonomous_scan with findings validation (lines 330-356)"""

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_with_findings_validation(self):
        """Test run_autonomous_scan with findings and risk engine validation"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        # Mock the autonomous loop
        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(
            return_value={
                "state": "completed",
                "findings": {"items": [{"id": "1", "title": "XSS", "severity": "high"}]},
                "success": True,
            }
        )
        o._autonomous_loop = mock_loop

        # Mock fp_engine to enable validation
        mock_fp_engine = AsyncMock()
        mock_result = Mock()
        mock_result.to_dict = Mock(return_value={"confidence": 0.9})
        mock_result.is_false_positive = False
        mock_result.confidence = 0.9
        mock_result.priority = 1
        mock_fp_engine.validate_finding = AsyncMock(return_value=mock_result)
        o._fp_engine = mock_fp_engine

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.logger"):
                with patch("core.orchestrator.Finding"):
                    result = await o.run_autonomous_scan("target.com", "find vulnerabilities")

        assert result["success"] is True
        assert "validated_findings" in result

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_with_findings_no_risk_engine(self):
        """Test run_autonomous_scan with findings but no risk engine"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(
            return_value={
                "state": "completed",
                "findings": {"items": [{"id": "1", "title": "XSS"}]},
            }
        )
        o._autonomous_loop = mock_loop
        o._fp_engine = None  # No risk engine

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", False):
            result = await o.run_autonomous_scan("target.com", "goal")

        assert "validated_findings" not in result

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_empty_findings(self):
        """Test run_autonomous_scan with empty findings"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(
            return_value={
                "state": "completed",
                "findings": None,  # No findings
            }
        )
        o._autonomous_loop = mock_loop

        result = await o.run_autonomous_scan("target.com", "goal")
        assert "validated_findings" not in result


class TestOrchestratorValidateFindings:
    """Test validate_findings method (lines 376-423)"""

    @pytest.mark.asyncio
    async def test_validate_findings_with_valid_result(self):
        """Test validate_findings with valid validation result"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        # Mock fp_engine with proper return value
        mock_result = Mock()
        mock_result.to_dict = Mock(return_value={"confidence": 0.9, "is_valid": True})
        mock_result.is_false_positive = False
        mock_result.confidence = 0.9
        mock_result.priority = 1

        mock_fp_engine = AsyncMock()
        mock_fp_engine.validate_finding = AsyncMock(return_value=mock_result)
        o._fp_engine = mock_fp_engine

        findings = [
            {
                "id": "1",
                "title": "Test Finding",
                "description": "Test description",
                "severity": "high",
                "target": "test.com",
                "source": "scanner",
            }
        ]

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.Finding"):  # Mock Finding class
                result = await o.validate_findings(findings)

        assert len(result) == 1
        assert result[0]["validation"] is not None
        assert result[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_validate_findings_result_without_to_dict(self):
        """Test validate_findings when result has no to_dict method (line 399)"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        # Mock result without to_dict
        mock_result = Mock()
        del mock_result.to_dict  # Remove to_dict attribute
        mock_result.is_false_positive = True
        mock_result.confidence = 0.5
        mock_result.priority = 2

        mock_fp_engine = AsyncMock()
        mock_fp_engine.validate_finding = AsyncMock(return_value=mock_result)
        o._fp_engine = mock_fp_engine

        findings = [
            {
                "id": "1",
                "title": "Test",
                "severity": "medium",
                "target": "t.com",
                "source": "s",
            }
        ]

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.Finding"):
                result = await o.validate_findings(findings)

        assert len(result) == 1
        assert result[0]["is_false_positive"]

    @pytest.mark.asyncio
    async def test_validate_findings_exception_in_validation(self):
        """Test validate_findings when exception occurs during validation (lines 409-418)"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        mock_fp_engine = AsyncMock()
        mock_fp_engine.validate_finding = AsyncMock(side_effect=Exception("Validation failed"))
        o._fp_engine = mock_fp_engine

        findings = [
            {
                "id": "1",
                "title": "Test",
                "severity": "medium",
                "target": "t.com",
                "source": "s",
            }
        ]

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.Finding"):
                with patch("core.orchestrator.logger") as mock_logger:
                    result = await o.validate_findings(findings)

        assert len(result) == 1
        assert "error" in result[0]
        assert not result[0]["is_false_positive"]

    @pytest.mark.asyncio
    async def test_validate_findings_sorting_by_priority(self):
        """Test that validate_findings sorts results by priority (line 421)"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        # Create results with different priorities
        results = [
            Mock(
                to_dict=Mock(return_value={}),
                is_false_positive=False,
                confidence=0.8,
                priority=3,
            ),
            Mock(
                to_dict=Mock(return_value={}),
                is_false_positive=False,
                confidence=0.9,
                priority=1,
            ),
            Mock(
                to_dict=Mock(return_value={}),
                is_false_positive=False,
                confidence=0.7,
                priority=2,
            ),
        ]

        mock_fp_engine = AsyncMock()
        mock_fp_engine.validate_finding = AsyncMock(side_effect=results)
        o._fp_engine = mock_fp_engine

        findings = [
            {
                "id": "1",
                "title": "Test1",
                "severity": "medium",
                "target": "t.com",
                "source": "s",
            },
            {
                "id": "2",
                "title": "Test2",
                "severity": "medium",
                "target": "t.com",
                "source": "s",
            },
            {
                "id": "3",
                "title": "Test3",
                "severity": "medium",
                "target": "t.com",
                "source": "s",
            },
        ]

        with patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True):
            with patch("core.orchestrator.Finding"):
                result = await o.validate_findings(findings)

        # Check sorted by priority (1, 2, 3)
        priorities = [r["priority"] for r in result]
        assert priorities == [1, 2, 3]


class TestDatabaseModelsExtended:
    """Extended tests for database models"""

    def test_user_with_hashed_password(self):
        """Test User with hashed_password attribute"""
        from database.models import User

        user = User(
            username="testuser",
            email="test@test.com",
            hashed_password="hash123",
        )
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.hashed_password == "hash123"

    def test_scan_with_status_transitions(self):
        """Test Scan status transitions"""
        from database.models import Scan

        scan = Scan(target="example.com", scan_type="web", status="pending")
        scan.status = "running"
        scan.status = "completed"
        assert scan.status == "completed"

    def test_finding_with_evidence(self):
        """Test Finding with evidence"""
        from database.models import Finding

        finding = Finding(
            title="SQL Injection",
            severity="critical",
            description="SQLi found",
            evidence="/path/to/evidence",
        )
        assert finding.evidence == "/path/to/evidence"

    def test_report_model_creation(self):
        """Test Report model creation"""
        from database.models import Report

        report = Report(format="pdf", status="pending", template="default")
        assert report.format == "pdf"
        assert report.status == "pending"
        assert report.template == "default"


class TestOrchestratorExecuteExploit:
    """Test execute_exploit method if it exists"""

    @pytest.mark.asyncio
    async def test_execute_exploit_safe_mode(self):
        """Test execute_exploit with safe_mode=True"""
        from core.orchestrator import ZenOrchestrator

        o = ZenOrchestrator()

        # Check if method exists
        if hasattr(o, "execute_exploit"):
            exploit = {"name": "test_exploit", "type": "rce"}
            result = await o.execute_exploit(exploit, "target.com", safe_mode=True)
            assert isinstance(result, dict)

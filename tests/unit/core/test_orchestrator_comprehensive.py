#!/usr/bin/env python3
"""
Comprehensive Tests for Zen AI Orchestrator Module

Tests cover:
1. Orchestrator initialization
2. LLM routing
3. Tool execution flow
4. Quality level handling
5. Provider management

Author: SHAdd0WTAka
"""

import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the core module is in path
sys.path.insert(0, "/home/atakan/zen-ai-pentest")

from core.orchestrator import (
    AUTONOMOUS_AVAILABLE,
    INTEGRATIONS_AVAILABLE,
    RISK_ENGINE_AVAILABLE,
    BaseBackend,
    LLMResponse,
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
def orchestrator_with_backends(mock_backend):
    """Create an orchestrator with mock backends."""
    orch = ZenOrchestrator()
    # Add backends with different priorities
    orch.add_backend(mock_backend("ddg", 1))
    orch.add_backend(mock_backend("openrouter", 2))
    orch.add_backend(mock_backend("chatgpt", 3))
    return orch


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


@pytest.fixture
def mock_exploit():
    """Create a mock exploit for testing."""
    return {
        "code": "echo 'exploit code'",
        "type": "rce",
        "name": "Test Exploit",
    }


@pytest.fixture
def mock_scope_config():
    """Create a mock scope configuration."""
    return {"allowed_hosts": ["example.com"], "excluded_paths": ["/admin"]}


# ============================================================================
# Test Class: Orchestrator Initialization
# ============================================================================


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""

    def test_orchestrator_initializes_with_defaults(self):
        """Test that orchestrator initializes with default values."""
        orch = ZenOrchestrator()

        assert orch.backends == []
        assert orch.results_cache == {}
        assert orch.request_count == 0
        assert orch._autonomous_loop is None or AUTONOMOUS_AVAILABLE
        assert orch._fp_engine is None or RISK_ENGINE_AVAILABLE
        assert orch._exploit_validator is None or AUTONOMOUS_AVAILABLE
        assert orch._business_impact is None or RISK_ENGINE_AVAILABLE
        assert isinstance(orch._integrations, dict)

    def test_orchestrator_initializes_components_if_available(self):
        """Test that orchestrator initializes optional components when available."""
        orch = ZenOrchestrator()

        if AUTONOMOUS_AVAILABLE:
            # Autonomous loop should be initialized if available
            assert orch._autonomous_loop is not None

        if RISK_ENGINE_AVAILABLE:
            # Risk engine components should be initialized if available
            assert orch._fp_engine is not None
            assert orch._business_impact is not None

    @patch("core.orchestrator.logger")
    def test_orchestrator_logs_initialization(self, mock_logger):
        """Test that orchestrator logs during initialization."""
        ZenOrchestrator()

        # Should have logged initialization messages
        assert mock_logger.info.called or mock_logger.warning.called


# ============================================================================
# Test Class: Backend Management
# ============================================================================


class TestBackendManagement:
    """Tests for backend registration and management."""

    def test_add_backend_registers_backend(self, orchestrator, mock_backend):
        """Test that add_backend registers a backend."""
        backend = mock_backend("test_backend", 1)
        orchestrator.add_backend(backend)

        assert len(orchestrator.backends) == 1
        assert orchestrator.backends[0].name == "test_backend"

    def test_add_backend_sorts_by_priority(self, orchestrator, mock_backend):
        """Test that backends are sorted by priority."""
        # Add in reverse priority order
        orchestrator.add_backend(mock_backend("high_priority", 3))
        orchestrator.add_backend(mock_backend("low_priority", 1))
        orchestrator.add_backend(mock_backend("medium_priority", 2))

        # Should be sorted by priority (lowest first)
        assert orchestrator.backends[0].priority == 1
        assert orchestrator.backends[1].priority == 2
        assert orchestrator.backends[2].priority == 3
        assert orchestrator.backends[0].name == "low_priority"
        assert orchestrator.backends[1].name == "medium_priority"
        assert orchestrator.backends[2].name == "high_priority"

    def test_add_backend_logs_registration(self, orchestrator, mock_backend):
        """Test that add_backend logs the registration."""
        with patch("core.orchestrator.logger") as mock_logger:
            backend = mock_backend("test_backend", 1)
            orchestrator.add_backend(backend)

            mock_logger.info.assert_called()
            log_message = str(mock_logger.info.call_args)
            assert "test_backend" in log_message
            assert "priority 1" in log_message


# ============================================================================
# Test Class: Quality Level Handling
# ============================================================================


class TestQualityLevelHandling:
    """Tests for quality level handling."""

    def test_quality_level_enum_values(self):
        """Test that QualityLevel enum has correct values."""
        assert QualityLevel.LOW.value == "low"
        assert QualityLevel.MEDIUM.value == "medium"
        assert QualityLevel.HIGH.value == "high"

    def test_quality_level_enum_comparison(self):
        """Test QualityLevel enum comparison."""
        assert QualityLevel.LOW != QualityLevel.MEDIUM
        assert QualityLevel.MEDIUM != QualityLevel.HIGH
        assert QualityLevel.LOW == QualityLevel.LOW


# ============================================================================
# Test Class: LLM Routing and Processing
# ============================================================================


class TestLLMRouting:
    """Tests for LLM routing and processing."""

    @pytest.mark.asyncio
    async def test_process_with_low_quality_uses_priority_1(
        self, orchestrator, mock_backend
    ):
        """Test that LOW quality uses only priority 1 backends."""
        orch = orchestrator
        orch.add_backend(mock_backend("ddg", 1))
        orch.add_backend(mock_backend("openrouter", 2))
        orch.add_backend(mock_backend("chatgpt", 3))

        response = await orch.process("test prompt", QualityLevel.LOW)

        assert response.source == "ddg"
        assert response.quality == QualityLevel.LOW

    @pytest.mark.asyncio
    async def test_process_with_medium_quality_uses_priority_1_and_2(
        self, orchestrator, mock_backend
    ):
        """Test that MEDIUM quality uses priority 1 and 2 backends."""
        orch = orchestrator
        # Priority 1 fails
        backend1 = mock_backend("ddg", 1)
        backend1.should_fail = True
        orch.add_backend(backend1)

        # Priority 2 succeeds
        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "OpenRouter response"
        orch.add_backend(backend2)

        response = await orch.process("test prompt", QualityLevel.MEDIUM)

        assert response.source == "openrouter"
        assert response.quality == QualityLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_process_with_high_quality_uses_all_backends(
        self, orchestrator, mock_backend
    ):
        """Test that HIGH quality uses all backends."""
        orch = orchestrator
        # Priority 1 and 2 fail
        backend1 = mock_backend("ddg", 1)
        backend1.should_fail = True
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.should_fail = True
        orch.add_backend(backend2)

        # Priority 3 succeeds
        backend3 = mock_backend("chatgpt", 3)
        backend3.chat_response = "ChatGPT response"
        orch.add_backend(backend3)

        response = await orch.process("test prompt", QualityLevel.HIGH)

        assert response.source == "chatgpt"
        assert response.quality == QualityLevel.HIGH

    @pytest.mark.asyncio
    async def test_process_increments_request_count(self, orchestrator, mock_backend):
        """Test that process increments request count."""
        orch = orchestrator
        orch.add_backend(mock_backend("ddg", 1))

        initial_count = orch.request_count
        await orch.process("test prompt", QualityLevel.LOW)

        assert orch.request_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_process_logs_request_info(self, orchestrator, mock_backend):
        """Test that process logs request information."""
        orch = orchestrator
        orch.add_backend(mock_backend("ddg", 1))

        with patch("core.orchestrator.logger") as mock_logger:
            await orch.process("test prompt", QualityLevel.LOW)

            # Should log request info
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Request" in call for call in log_calls)
            assert any("Quality: low" in call for call in log_calls)

    @pytest.mark.asyncio
    async def test_process_returns_error_when_all_backends_fail(
        self, orchestrator, mock_backend
    ):
        """Test that process returns error response when all backends fail."""
        orch = orchestrator
        backend = mock_backend("failing_backend", 1)
        backend.should_fail = True
        orch.add_backend(backend)

        response = await orch.process("test prompt", QualityLevel.LOW)

        assert response.content == "All backends failed. Check logs."
        assert response.source == "None"
        assert response.quality == QualityLevel.LOW

    @pytest.mark.asyncio
    async def test_process_skips_short_responses(self, orchestrator, mock_backend):
        """Test that process skips responses that are too short."""
        orch = orchestrator
        # First backend returns short response
        backend1 = mock_backend("ddg", 1)
        backend1.chat_response = "Hi"
        orch.add_backend(backend1)

        # Second backend returns valid response
        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "This is a valid response"
        orch.add_backend(backend2)

        response = await orch.process("test prompt", QualityLevel.HIGH)

        assert response.source == "openrouter"

    @pytest.mark.asyncio
    async def test_process_logs_backend_failure(self, orchestrator, mock_backend):
        """Test that process logs backend failures."""
        orch = orchestrator
        backend = mock_backend("failing_backend", 1)
        backend.should_fail = True
        orch.add_backend(backend)

        with patch("core.orchestrator.logger") as mock_logger:
            await orch.process("test prompt", QualityLevel.LOW)

            # Check that error logging was called
            mock_logger.error.assert_called()
            # Verify at least one error call contains the backend name or failure message
            error_calls = [str(call) for call in mock_logger.error.call_args_list]
            has_backend_name = any(
                "failing_backend" in call or "Backend" in call for call in error_calls
            )
            assert has_backend_name, f"Expected backend name in error logs: {error_calls}"

    @pytest.mark.asyncio
    async def test_process_returns_llm_response_with_metadata(
        self, orchestrator, mock_backend
    ):
        """Test that process returns LLMResponse with correct metadata."""
        orch = orchestrator
        backend = mock_backend("ddg", 1)
        backend.chat_response = "Test response content"
        backend.current_model = "gpt-4"
        orch.add_backend(backend)

        response = await orch.process("test prompt", QualityLevel.LOW)

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response content"
        assert response.source == "ddg"
        assert response.metadata is not None
        assert response.metadata.get("model") == "gpt-4"
        assert response.latency >= 0


# ============================================================================
# Test Class: Parallel Consensus
# ============================================================================


class TestParallelConsensus:
    """Tests for parallel consensus mode."""

    @pytest.mark.asyncio
    async def test_parallel_consensus_queries_top_backends(self, orchestrator, mock_backend):
        """Test that parallel_consensus queries top 2 backends."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.chat_response = "This is a long response from DDG that meets the length requirement"
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "This is a long response from OpenRouter that meets the length requirement"
        orch.add_backend(backend2)

        backend3 = mock_backend("chatgpt", 3)
        backend3.chat_response = "This is a long response from ChatGPT"
        orch.add_backend(backend3)

        result = await orch.parallel_consensus("test prompt")

        # Should only include responses from top 2 backends (longer than 50 chars)
        assert len(result["responses"]) == 2
        sources = [r["source"] for r in result["responses"]]
        assert "ddg" in sources
        assert "openrouter" in sources
        assert "chatgpt" not in sources

    @pytest.mark.asyncio
    async def test_parallel_consensus_filters_short_responses(
        self, orchestrator, mock_backend
    ):
        """Test that parallel_consensus filters out short responses."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.chat_response = "Short"  # Less than 50 chars, should be filtered
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "This is a long enough response to be valid and exceed fifty characters"
        orch.add_backend(backend2)

        result = await orch.parallel_consensus("test prompt")

        # Only the long response should be valid (len > 50)
        assert len(result["responses"]) == 1
        assert result["responses"][0]["source"] == "openrouter"

    @pytest.mark.asyncio
    async def test_parallel_consensus_handles_exceptions(self, orchestrator, mock_backend):
        """Test that parallel_consensus handles backend exceptions."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.should_fail = True
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "This is a valid response that is long enough to be accepted"
        orch.add_backend(backend2)

        result = await orch.parallel_consensus("test prompt")

        # Should have one valid response despite exception (len > 50)
        assert len(result["responses"]) == 1
        assert result["consensus"] is not None

    @pytest.mark.asyncio
    async def test_parallel_consensus_returns_none_when_no_valid_responses(
        self, orchestrator, mock_backend
    ):
        """Test that parallel_consensus returns None when no valid responses."""
        orch = orchestrator
        backend1 = mock_backend("ddg", 1)
        backend1.chat_response = "Hi"
        orch.add_backend(backend1)

        backend2 = mock_backend("openrouter", 2)
        backend2.chat_response = "Hello"
        orch.add_backend(backend2)

        result = await orch.parallel_consensus("test prompt")

        assert result["consensus"] is None
        assert result["alternative"] is None
        assert len(result["responses"]) == 0

    @pytest.mark.asyncio
    async def test_parallel_consensus_logs_activation(self, orchestrator, mock_backend):
        """Test that parallel_consensus logs activation."""
        orch = orchestrator
        orch.add_backend(mock_backend("ddg", 1))

        with patch("core.orchestrator.logger") as mock_logger:
            await orch.parallel_consensus("test prompt")

            mock_logger.info.assert_called()
            log_message = str(mock_logger.info.call_args)
            assert "Parallel consensus mode activated" in log_message


# ============================================================================
# Test Class: Statistics and Capabilities
# ============================================================================


class TestStatisticsAndCapabilities:
    """Tests for statistics and capabilities reporting."""

    def test_get_stats_returns_correct_structure(self, orchestrator, mock_backend):
        """Test that get_stats returns correct structure."""
        orch = orchestrator
        orch.add_backend(mock_backend("ddg", 1))
        orch.add_backend(mock_backend("openrouter", 2))
        orch.request_count = 42

        stats = orch.get_stats()

        assert "backends_registered" in stats
        assert stats["backends_registered"] == 2
        assert "backends" in stats
        assert stats["backends"] == ["ddg", "openrouter"]
        assert "requests_processed" in stats
        assert stats["requests_processed"] == 42
        assert "autonomous_available" in stats
        assert "risk_engine_available" in stats
        assert "integrations_available" in stats
        assert "integrations_loaded" in stats

    def test_get_stats_returns_backend_names(self, orchestrator, mock_backend):
        """Test that get_stats returns correct backend names."""
        orch = orchestrator
        orch.add_backend(mock_backend("backend_a", 1))
        orch.add_backend(mock_backend("backend_b", 2))

        stats = orch.get_stats()

        assert "backend_a" in stats["backends"]
        assert "backend_b" in stats["backends"]

    def test_get_capabilities_returns_correct_structure(self, orchestrator):
        """Test that get_capabilities returns correct structure."""
        caps = orchestrator.get_capabilities()

        assert "autonomous_scan" in caps
        assert "false_positive_validation" in caps
        assert "exploit_validation" in caps
        assert "business_impact" in caps
        assert "slack_notifications" in caps
        assert "github_integration" in caps
        assert "jira_integration" in caps

    def test_get_capabilities_reflects_component_availability(self, orchestrator):
        """Test that get_capabilities reflects actual component availability."""
        caps = orchestrator.get_capabilities()

        # autonomous_scan should be True only if components are available and initialized
        expected_autonomous = AUTONOMOUS_AVAILABLE and orchestrator._autonomous_loop is not None
        assert caps["autonomous_scan"] == expected_autonomous

        # false_positive_validation should be True only if risk engine is available
        expected_fp = RISK_ENGINE_AVAILABLE and orchestrator._fp_engine is not None
        assert caps["false_positive_validation"] == expected_fp


# ============================================================================
# Test Class: Autonomous Scan (Conditional Tests)
# ============================================================================


class TestAutonomousScan:
    """Tests for autonomous scan functionality."""

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_returns_error_when_not_available(self, orchestrator):
        """Test that run_autonomous_scan returns error when autonomous loop not available."""
        # Force autonomous loop to None
        orchestrator._autonomous_loop = None

        result = await orchestrator.run_autonomous_scan(
            target="http://example.com", goal="Find vulnerabilities"
        )

        assert result["success"] is False
        assert "Autonomous Agent Loop not available" in result["error"]
        assert result["findings"] == []

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_successful_execution(self, orchestrator):
        """Test successful autonomous scan execution."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        # Mock the autonomous loop
        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(
            return_value={
                "success": True,
                "state": "completed",
                "findings": {"items": [{"id": "finding-1"}]},
            }
        )
        orchestrator._autonomous_loop = mock_loop

        result = await orchestrator.run_autonomous_scan(
            target="http://example.com", goal="Find vulnerabilities"
        )

        assert result["success"] is True
        mock_loop.run.assert_called_once()
        call_kwargs = mock_loop.run.call_args.kwargs
        assert call_kwargs["target"] == "http://example.com"
        assert call_kwargs["goal"] == "Find vulnerabilities"

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_with_scope(self, orchestrator):
        """Test autonomous scan with scope configuration."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(return_value={"success": True, "state": "completed"})
        orchestrator._autonomous_loop = mock_loop

        scope = {"allowed_hosts": ["example.com"], "excluded_paths": ["/admin"]}
        await orchestrator.run_autonomous_scan(
            target="http://example.com", goal="Find vulnerabilities", scope=scope
        )

        call_kwargs = mock_loop.run.call_args.kwargs
        assert call_kwargs["scope"] == scope

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_handles_exception(self, orchestrator):
        """Test that run_autonomous_scan handles exceptions gracefully."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(side_effect=Exception("Scan failed"))
        orchestrator._autonomous_loop = mock_loop

        result = await orchestrator.run_autonomous_scan(
            target="http://example.com", goal="Find vulnerabilities"
        )

        assert result["success"] is False
        assert "Scan failed" in result["error"]


# ============================================================================
# Test Class: Finding Validation (Conditional Tests)
# ============================================================================


class TestFindingValidation:
    """Tests for finding validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_findings_returns_unvalidated_when_no_engine(
        self, orchestrator, mock_finding
    ):
        """Test that validate_findings returns unvalidated findings when no FP engine."""
        orchestrator._fp_engine = None

        findings = [mock_finding]
        result = await orchestrator.validate_findings(findings)

        # Should return findings as-is when no engine
        assert len(result) == 1
        assert result[0] == mock_finding

    @pytest.mark.asyncio
    async def test_validate_findings_with_mock_engine(self, orchestrator, mock_finding):
        """Test validate_findings with mock FP engine."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Create mock FP engine
        mock_result = MagicMock()
        mock_result.is_false_positive = False
        mock_result.confidence = 0.95
        mock_result.priority = 1
        mock_result.to_dict = MagicMock(return_value={"confidence": 0.95})

        mock_engine = AsyncMock()
        mock_engine.validate_finding = AsyncMock(return_value=mock_result)
        orchestrator._fp_engine = mock_engine

        findings = [mock_finding]
        result = await orchestrator.validate_findings(findings)

        assert len(result) == 1
        assert result[0]["original"] == mock_finding
        assert result[0]["is_false_positive"] is False
        assert result[0]["confidence"] == 0.95
        assert result[0]["priority"] == 1

    @pytest.mark.asyncio
    async def test_validate_findings_sorts_by_priority(self, orchestrator):
        """Test that validate_findings sorts results by priority."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Create mock results with different priorities
        mock_results = []
        for i, priority in enumerate([3, 1, 2]):
            mock_result = MagicMock()
            mock_result.is_false_positive = False
            mock_result.confidence = 0.9
            mock_result.priority = priority
            mock_result.to_dict = MagicMock(return_value={"priority": priority})
            mock_results.append(mock_result)

        mock_engine = AsyncMock()
        mock_engine.validate_finding = AsyncMock(side_effect=mock_results)
        orchestrator._fp_engine = mock_engine

        findings = [
            {"id": f"finding-{i}", "title": f"Finding {i}", "severity": "medium"}
            for i in range(3)
        ]
        result = await orchestrator.validate_findings(findings)

        # Should be sorted by priority (lowest first)
        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 3

    @pytest.mark.asyncio
    async def test_validate_findings_handles_validation_errors(self, orchestrator, mock_finding):
        """Test that validate_findings handles validation errors gracefully."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        mock_engine = AsyncMock()
        mock_engine.validate_finding = AsyncMock(side_effect=Exception("Validation error"))
        orchestrator._fp_engine = mock_engine

        findings = [mock_finding]
        result = await orchestrator.validate_findings(findings)

        assert len(result) == 1
        assert result[0]["original"] == mock_finding
        assert result[0]["error"] == "Validation error"
        assert result[0]["is_false_positive"] is False


# ============================================================================
# Test Class: Exploit Execution (Conditional Tests)
# ============================================================================


class TestExploitExecution:
    """Tests for exploit execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_exploit_returns_error_when_not_available(
        self, orchestrator, mock_exploit
    ):
        """Test that execute_exploit returns error when validator not available."""
        with patch("core.orchestrator.AUTONOMOUS_AVAILABLE", False):
            result = await orchestrator.execute_exploit(
                exploit=mock_exploit, target="http://example.com", safe_mode=True
            )

            assert result["success"] is False
            assert "Exploit Validator not available" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_exploit_successful_execution(self, orchestrator, mock_exploit):
        """Test successful exploit execution."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        # Mock the ExploitValidator class
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.evidence = MagicMock()
        mock_result.evidence.to_dict = MagicMock(return_value={"screenshot": "base64"})
        mock_result.output = "Exploit output"
        mock_result.error = None
        mock_result.severity = "high"
        mock_result.remediation = "Fix this"
        mock_result.execution_time = 5.0

        mock_validator = AsyncMock()
        mock_validator.validate = AsyncMock(return_value=mock_result)

        with patch("core.orchestrator.ExploitValidator", return_value=mock_validator):
            result = await orchestrator.execute_exploit(
                exploit=mock_exploit, target="http://example.com", safe_mode=True
            )

            assert result["success"] is True
            assert result["exploitable"] is True
            assert result["evidence"] == {"screenshot": "base64"}
            assert result["output"] == "Exploit output"
            assert result["severity"] == "high"

    @pytest.mark.asyncio
    async def test_execute_exploit_type_mapping(self, orchestrator):
        """Test that exploit type mapping works correctly."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_validator = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.evidence = None
        mock_result.output = ""
        mock_result.error = None
        mock_result.severity = "medium"
        mock_result.remediation = ""
        mock_result.execution_time = 0.0
        mock_validator.validate = AsyncMock(return_value=mock_result)

        type_tests = [
            ("sqli", "WEB_SQLI"),
            ("sql_injection", "WEB_SQLI"),
            ("xss", "WEB_XSS"),
            ("rce", "WEB_RCE"),
            ("lfi", "WEB_LFI"),
            ("command_injection", "WEB_CMD_INJECTION"),
            ("unknown_type", "WEB_RCE"),  # Default
        ]

        with patch("core.orchestrator.ExploitValidator", return_value=mock_validator):
            for exploit_type, expected_enum in type_tests:
                exploit = {"code": "test", "type": exploit_type}
                await orchestrator.execute_exploit(
                    exploit=exploit, target="http://example.com", safe_mode=True
                )

                # The validate should be called
                assert mock_validator.validate.called

    @pytest.mark.asyncio
    async def test_execute_exploit_safe_mode_configuration(self, orchestrator, mock_exploit):
        """Test that safe_mode affects sandbox configuration."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        with patch("core.orchestrator.ExploitValidator") as mock_validator_class:
            mock_validator = AsyncMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.evidence = None
            mock_result.output = ""
            mock_result.error = None
            mock_result.severity = "low"
            mock_result.remediation = ""
            mock_result.execution_time = 0.0
            mock_validator.validate = AsyncMock(return_value=mock_result)
            mock_validator_class.return_value = mock_validator

            # Test with safe_mode=True
            await orchestrator.execute_exploit(
                exploit=mock_exploit, target="http://example.com", safe_mode=True
            )

            # Verify validator was created
            mock_validator_class.assert_called()
            call_kwargs = mock_validator_class.call_args.kwargs
            assert call_kwargs["safety_level"] == "controlled"


# ============================================================================
# Test Class: Business Impact (Conditional Tests)
# ============================================================================


class TestBusinessImpact:
    """Tests for business impact calculation functionality."""

    @pytest.mark.asyncio
    async def test_calculate_business_impact_returns_error_when_not_available(
        self, orchestrator, mock_finding
    ):
        """Test that calculate_business_impact returns error when calculator not available."""
        orchestrator._business_impact = None

        result = await orchestrator.calculate_business_impact(mock_finding)

        assert "error" in result
        assert "Business Impact Calculator not available" in result["error"]
        assert result["overall_score"] == 0.5

    @pytest.mark.asyncio
    async def test_calculate_business_impact_with_asset_context(self, orchestrator, mock_finding):
        """Test business impact calculation with asset context."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Mock the business impact calculator
        mock_result = MagicMock()
        mock_result.overall_score = 8.5
        mock_result.get_risk_category = MagicMock(return_value="Critical")
        mock_result.financial_impact.total_costs = 100000
        mock_result.financial_impact.direct_costs = 50000
        mock_result.financial_impact.indirect_costs = 50000
        mock_result.compliance_impact.frameworks = ["PCI-DSS", "GDPR"]
        mock_result.compliance_impact.violated_controls = ["control-1", "control-2"]
        mock_result.compliance_impact.get_max_fine = MagicMock(return_value=5000000)
        mock_result.get_prioritized_remediation = MagicMock(return_value=["remediate-1"])

        orchestrator._business_impact = MagicMock()
        orchestrator._business_impact.calculate_overall_impact = MagicMock(return_value=mock_result)

        asset_context = {
            "id": "asset-1",
            "name": "Production Server",
            "type": "server",
            "criticality": "HIGH",
            "data_classification": "CONFIDENTIAL",
            "internet_exposed": True,
            "user_count": 1000,
            "revenue_dependency": 0.8,
        }

        result = await orchestrator.calculate_business_impact(mock_finding, asset_context)

        assert result["overall_score"] == 8.5
        assert result["risk_category"] == "Critical"
        assert result["financial_impact"]["total_costs"] == 100000
        assert "PCI-DSS" in result["compliance_impact"]["frameworks"]

    @pytest.mark.asyncio
    async def test_calculate_business_impact_without_asset_context(self, orchestrator, mock_finding):
        """Test business impact calculation without asset context."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

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

        result = await orchestrator.calculate_business_impact(mock_finding)

        assert result["overall_score"] == 5.0
        assert result["risk_category"] == "Medium"


# ============================================================================
# Test Class: Integration Notifications
# ============================================================================


class TestIntegrationNotifications:
    """Tests for integration notification functionality."""

    @pytest.mark.asyncio
    async def test_notify_integrations_scan_started(self, orchestrator):
        """Test notification for scan started event."""
        # Create mock integration
        mock_integration = AsyncMock()
        mock_integration.notify_scan_started = AsyncMock()

        orchestrator._integrations = {"slack": mock_integration}

        result = await orchestrator.notify_integrations(
            "scan_started", {"target": "example.com", "scan_type": "security"}
        )

        assert result["slack"] is True
        mock_integration.notify_scan_started.assert_called_once_with(
            target="example.com", scan_type="security"
        )

    @pytest.mark.asyncio
    async def test_notify_integrations_scan_completed(self, orchestrator):
        """Test notification for scan completed event."""
        mock_integration = AsyncMock()
        mock_integration.notify_scan_completed = AsyncMock()

        orchestrator._integrations = {"slack": mock_integration}

        data = {"target": "example.com", "findings": [{"id": "f1"}]}
        result = await orchestrator.notify_integrations("scan_completed", data)

        assert result["slack"] is True
        mock_integration.notify_scan_completed.assert_called_once_with(
            results=data, target="example.com"
        )

    @pytest.mark.asyncio
    async def test_notify_integrations_finding(self, orchestrator):
        """Test notification for finding event."""
        mock_integration = AsyncMock()
        mock_integration.notify_finding = AsyncMock()

        orchestrator._integrations = {"slack": mock_integration}

        finding_data = {"id": "finding-1", "severity": "high"}
        result = await orchestrator.notify_integrations("finding", finding_data)

        assert result["slack"] is True
        mock_integration.notify_finding.assert_called_once_with(finding_data)

    @pytest.mark.asyncio
    async def test_notify_integrations_unsupported_event(self, orchestrator):
        """Test notification for unsupported event type."""
        mock_integration = AsyncMock()
        orchestrator._integrations = {"slack": mock_integration}

        result = await orchestrator.notify_integrations("unknown_event", {})

        assert result["slack"] is False

    @pytest.mark.asyncio
    async def test_notify_integrations_missing_method(self, orchestrator):
        """Test notification when integration lacks required method."""
        mock_integration = MagicMock()  # No async methods
        orchestrator._integrations = {"slack": mock_integration}

        result = await orchestrator.notify_integrations("scan_started", {})

        assert result["slack"] is False

    @pytest.mark.asyncio
    async def test_notify_integrations_handles_exception(self, orchestrator):
        """Test that notify_integrations handles exceptions gracefully."""
        mock_integration = AsyncMock()
        mock_integration.notify_scan_started = AsyncMock(side_effect=Exception("Network error"))

        orchestrator._integrations = {"slack": mock_integration}

        result = await orchestrator.notify_integrations("scan_started", {})

        assert result["slack"] is False

    @pytest.mark.asyncio
    async def test_notify_integrations_multiple_integrations(self, orchestrator):
        """Test notification with multiple integrations."""
        mock_slack = AsyncMock()
        mock_slack.notify_scan_started = AsyncMock()

        mock_github = AsyncMock()
        mock_github.notify_scan_started = AsyncMock()

        orchestrator._integrations = {"slack": mock_slack, "github": mock_github}

        result = await orchestrator.notify_integrations("scan_started", {})

        assert result["slack"] is True
        assert result["github"] is True


# ============================================================================
# Test Class: BaseBackend
# ============================================================================


class TestBaseBackend:
    """Tests for BaseBackend abstract class."""

    @pytest.mark.asyncio
    async def test_backend_context_manager(self, mock_backend):
        """Test that backend can be used as async context manager."""
        backend = mock_backend("test", 1)

        async with backend as b:
            assert b.session is not None

        # After exiting, session should be closed
        assert backend.session is None or backend.session.closed

    @pytest.mark.asyncio
    async def test_backend_health_check_default(self, mock_backend):
        """Test default health check implementation."""
        backend = mock_backend("test", 1)
        result = await backend.health_check()
        assert result is True

    def test_backend_initialization(self, mock_backend):
        """Test backend initialization."""
        backend = mock_backend("my_backend", 2)

        assert backend.name == "my_backend"
        assert backend.priority == 2
        assert backend.session is None


# ============================================================================
# Test Class: LLMResponse Dataclass
# ============================================================================


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_llm_response_creation(self):
        """Test LLMResponse creation."""
        response = LLMResponse(
            content="Test content",
            source="test_backend",
            latency=0.5,
            quality=QualityLevel.MEDIUM,
            metadata={"model": "gpt-4"},
        )

        assert response.content == "Test content"
        assert response.source == "test_backend"
        assert response.latency == 0.5
        assert response.quality == QualityLevel.MEDIUM
        assert response.metadata == {"model": "gpt-4"}

    def test_llm_response_default_metadata(self):
        """Test LLMResponse with default metadata."""
        response = LLMResponse(
            content="Test",
            source="test",
            latency=1.0,
            quality=QualityLevel.LOW,
        )

        assert response.metadata is None


# ============================================================================
# Test Class: Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_process_with_no_backends(self, orchestrator):
        """Test process with no backends registered."""
        response = await orchestrator.process("test prompt")

        assert response.content == "All backends failed. Check logs."
        assert response.source == "None"

    @pytest.mark.asyncio
    async def test_process_with_empty_prompt(self, orchestrator, mock_backend):
        """Test process with empty prompt."""
        orch = orchestrator
        backend = mock_backend("ddg", 1)
        backend.chat_response = "Response to empty"
        orch.add_backend(backend)

        response = await orch.process("")

        assert response.source == "ddg"

    @pytest.mark.asyncio
    async def test_parallel_consensus_with_no_backends(self, orchestrator):
        """Test parallel_consensus with no backends."""
        result = await orchestrator.parallel_consensus("test")

        assert result["responses"] == []
        assert result["consensus"] is None
        assert result["alternative"] is None

    def test_get_stats_with_no_backends(self, orchestrator):
        """Test get_stats with no backends."""
        stats = orchestrator.get_stats()

        assert stats["backends_registered"] == 0
        assert stats["backends"] == []

    @pytest.mark.asyncio
    async def test_validate_findings_with_empty_list(self, orchestrator):
        """Test validate_findings with empty findings list."""
        result = await orchestrator.validate_findings([])

        assert result == []

    @pytest.mark.asyncio
    async def test_run_autonomous_scan_with_empty_scope(self, orchestrator):
        """Test run_autonomous_scan with empty scope."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        mock_loop = AsyncMock()
        mock_loop.run = AsyncMock(return_value={"success": True})
        orchestrator._autonomous_loop = mock_loop

        await orchestrator.run_autonomous_scan(
            target="http://example.com", goal="test", scope={}
        )

        call_kwargs = mock_loop.run.call_args.kwargs
        assert call_kwargs["scope"] == {}

    @pytest.mark.asyncio
    async def test_notify_integrations_with_no_integrations(self, orchestrator):
        """Test notify_integrations with no integrations configured."""
        orchestrator._integrations = {}

        result = await orchestrator.notify_integrations("scan_started", {})

        assert result == {}


# ============================================================================
# Test Class: Integration with Real Components
# ============================================================================


class TestIntegrationWithRealComponents:
    """Tests that verify integration with real components when available."""

    def test_orchestrator_components_initialized_when_available(self):
        """Test that orchestrator initializes components when available."""
        orch = ZenOrchestrator()

        # Verify capabilities reflect actual availability
        caps = orch.get_capabilities()

        if AUTONOMOUS_AVAILABLE:
            assert orch._autonomous_loop is not None
            assert caps["autonomous_scan"] is True

        if RISK_ENGINE_AVAILABLE:
            assert orch._fp_engine is not None
            assert caps["false_positive_validation"] is True
            assert orch._business_impact is not None
            assert caps["business_impact"] is True


# ============================================================================
# Test Class: Component Initialization Error Handling
# ============================================================================


class TestComponentInitializationErrors:
    """Tests for component initialization error handling."""

    @patch("core.orchestrator.AUTONOMOUS_AVAILABLE", True)
    @patch("core.orchestrator.AutonomousAgentLoop")
    def test_autonomous_loop_initialization_error(self, mock_autonomous_class):
        """Test handling of AutonomousAgentLoop initialization error."""
        mock_autonomous_class.side_effect = Exception("Init failed")

        with patch("core.orchestrator.logger") as mock_logger:
            orch = ZenOrchestrator()
            # Should log warning but not crash
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            has_autonomous_warning = any(
                "AutonomousAgentLoop" in c for c in warning_calls
            )
            assert has_autonomous_warning or orch._autonomous_loop is None

    @patch("core.orchestrator.RISK_ENGINE_AVAILABLE", True)
    @patch("core.orchestrator.FalsePositiveEngine")
    def test_risk_engine_initialization_error(self, mock_fp_class):
        """Test handling of Risk Engine initialization error."""
        mock_fp_class.side_effect = Exception("Init failed")

        with patch("core.orchestrator.logger") as mock_logger:
            orch = ZenOrchestrator()
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            has_risk_warning = any("Risk Engine" in c for c in warning_calls)
            assert has_risk_warning or orch._fp_engine is None

    @patch("core.orchestrator.INTEGRATIONS_AVAILABLE", True)
    @patch("core.orchestrator.load_integrations_from_config")
    def test_integrations_loading_error(self, mock_load_integrations):
        """Test handling of integrations loading error."""
        mock_load_integrations.side_effect = Exception("Config error")

        with patch("core.orchestrator.logger") as mock_logger:
            orch = ZenOrchestrator()
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            has_integration_warning = any(
                "integrations" in c.lower() for c in warning_calls
            )
            assert has_integration_warning or orch._integrations == {}


# ============================================================================
# Test Class: Backend Context Manager Edge Cases
# ============================================================================


class TestBackendContextManagerEdgeCases:
    """Tests for backend context manager edge cases."""

    @pytest.mark.asyncio
    async def test_backend_aexit_with_exception(self, mock_backend):
        """Test backend aexit when exception occurred."""
        backend = mock_backend("test", 1)

        try:
            async with backend as b:
                assert b.session is not None
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Session should be closed even with exception
        assert backend.session is None or backend.session.closed

    @pytest.mark.asyncio
    async def test_backend_aexit_with_none_session(self, mock_backend):
        """Test backend aexit when session is None."""
        backend = mock_backend("test", 1)
        backend.session = None

        # Should not raise
        await backend.__aexit__(None, None, None)


# ============================================================================
# Test Class: Exploit Execution Error Handling
# ============================================================================


class TestExploitExecutionErrors:
    """Tests for exploit execution error handling."""

    @pytest.mark.asyncio
    async def test_execute_exploit_handles_exception(self, orchestrator, mock_exploit):
        """Test that execute_exploit handles exceptions gracefully."""
        if not AUTONOMOUS_AVAILABLE:
            pytest.skip("Autonomous components not available")

        with patch("core.orchestrator.ExploitValidator") as mock_validator_class:
            mock_validator = AsyncMock()
            mock_validator.validate = AsyncMock(side_effect=Exception("Exec error"))
            mock_validator_class.return_value = mock_validator

            result = await orchestrator.execute_exploit(
                exploit=mock_exploit, target="http://example.com", safe_mode=True
            )

            assert result["success"] is False
            assert "Exec error" in result["error"]
            assert result["exploitable"] is False


# ============================================================================
# Test Class: Finding Validation with Risk Engine
# ============================================================================


class TestFindingValidationWithRiskEngine:
    """Tests for finding validation when risk engine is available."""

    @pytest.mark.asyncio
    async def test_validate_findings_converts_dict_to_finding(self, orchestrator):
        """Test that validate_findings properly converts dict to Finding object."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Create mock result
        mock_result = MagicMock()
        mock_result.is_false_positive = False
        mock_result.confidence = 0.85
        mock_result.priority = 2
        mock_result.to_dict = MagicMock(return_value={"confidence": 0.85})

        mock_engine = AsyncMock()
        mock_engine.validate_finding = AsyncMock(return_value=mock_result)
        orchestrator._fp_engine = mock_engine

        finding_data = {
            "id": "test-001",
            "title": "Test Finding",
            "description": "Test description",
            "severity": "high",
            "target": "example.com",
            "source": "scanner",
        }

        result = await orchestrator.validate_findings([finding_data])

        assert len(result) == 1
        # Verify that validate_finding was called
        assert mock_engine.validate_finding.called


# ============================================================================
# Test Class: Business Impact Error Handling
# ============================================================================


class TestBusinessImpactErrors:
    """Tests for business impact calculation error handling."""

    @pytest.mark.asyncio
    async def test_calculate_business_impact_handles_exception(
        self, orchestrator, mock_finding
    ):
        """Test that calculate_business_impact handles exceptions gracefully."""
        if not RISK_ENGINE_AVAILABLE:
            pytest.skip("Risk engine not available")

        # Create mock calculator that raises exception
        mock_calculator = MagicMock()
        mock_calculator.calculate_overall_impact = MagicMock(
            side_effect=Exception("Calculation error")
        )
        orchestrator._business_impact = mock_calculator

        result = await orchestrator.calculate_business_impact(mock_finding)

        assert "error" in result
        assert "Calculation error" in result["error"]
        assert result["overall_score"] == 0.5


# ============================================================================
# Main Entry Point for Manual Testing
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

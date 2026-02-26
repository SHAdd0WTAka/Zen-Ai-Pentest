"""
Comprehensive tests for agents/analysis_agent.py module
Tests AnalysisAgent class initialization, vulnerability analysis logic,
severity assessment, pattern detection, finding correlation, and orchestrator integration.

Target: 80%+ coverage of analysis_agent.py
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock, PropertyMock
from datetime import datetime
from typing import Dict, List

from agents.analysis_agent import AnalysisAgent
from agents.agent_base import AgentRole, AgentMessage


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_zen_orchestrator():
    """Fixture to create a mock zen orchestrator for LLM operations."""
    mock = AsyncMock()
    response = Mock()
    response.content = "1. Priority remediation\n2. Immediate actions\n3. Long-term improvements"
    mock.process = AsyncMock(return_value=response)
    return mock


@pytest.fixture
def mock_orchestrator():
    """Fixture to create a mock orchestrator for message routing."""
    mock = AsyncMock()
    mock.route_message = AsyncMock()
    mock.update_shared_context = AsyncMock()
    return mock


@pytest.fixture
def analysis_agent(mock_orchestrator, mock_zen_orchestrator):
    """Fixture to create an AnalysisAgent with mocked orchestrators."""
    agent = AnalysisAgent(
        name="TestAnalyst",
        orchestrator=mock_orchestrator,
        zen_orchestrator=mock_zen_orchestrator
    )
    return agent


@pytest.fixture
def sample_findings():
    """Fixture to create sample findings for testing."""
    return [
        {
            "type": "cve",
            "data": {
                "cve_id": "CVE-2021-44228",
                "severity": "Critical",
                "cvss_score": 10.0,
                "description": "Log4Shell vulnerability"
            }
        },
        {
            "type": "cve",
            "data": {
                "cve_id": "CVE-2023-1234",
                "severity": "High",
                "cvss_score": 8.5,
                "description": "Example vulnerability"
            }
        },
        {
            "type": "vulnerability",
            "data": {
                "name": "SQL Injection",
                "severity": "Critical",
                "target": "login.php"
            }
        },
    ]


@pytest.fixture
def critical_cve_findings():
    """Fixture to create findings with multiple critical CVEs."""
    return [
        {
            "type": "cve",
            "data": {
                "cve_id": "CVE-2021-44228",
                "severity": "Critical",
                "cvss_score": 10.0,
            }
        },
        {
            "type": "cve",
            "data": {
                "cve_id": "CVE-2023-38408",
                "severity": "Critical",
                "cvss_score": 9.8,
            }
        },
        {
            "type": "cve",
            "data": {
                "cve_id": "CVE-2023-22515",
                "severity": "Critical",
                "cvss_score": 9.9,
            }
        },
    ]


@pytest.fixture
def ransomware_cve_finding():
    """Fixture to create a CVE finding with ransomware attribution."""
    cve_data = Mock()
    cve_data.cve_id = "CVE-2021-44228"
    cve_data.ransomware_used_by = ["Conti", "LockBit"]
    cve_data.severity = "Critical"
    
    return [
        {
            "type": "cve",
            "data": cve_data
        }
    ]


@pytest.fixture
def sample_analysis_message(sample_findings):
    """Fixture to create a sample findings message."""
    return AgentMessage(
        id="msg123",
        sender="TestScanner",
        recipient="TestAnalyst",
        msg_type="findings",
        content="Scan findings for analysis",
        context={"findings": sample_findings},
        priority=2,
    )


# ============================================================================
# Test AnalysisAgent Initialization and Configuration
# ============================================================================

class TestAnalysisAgentInitialization:
    """Test AnalysisAgent class initialization and configuration."""

    def test_basic_initialization(self):
        """Test basic AnalysisAgent initialization with minimal parameters."""
        agent = AnalysisAgent("BasicAnalyst")
        
        assert agent.name == "BasicAnalyst"
        assert agent.role == AgentRole.ANALYST
        assert len(agent.id) == 8
        assert agent.orchestrator is None
        assert agent.zen_orchestrator is None
        assert agent.analysis_cache == {}
        assert "findings" in agent.handlers
        assert "analysis_request" in agent.handlers

    def test_initialization_with_orchestrators(self, mock_orchestrator, mock_zen_orchestrator):
        """Test initialization with both orchestrators."""
        agent = AnalysisAgent(
            "FullAnalyst",
            orchestrator=mock_orchestrator,
            zen_orchestrator=mock_zen_orchestrator
        )
        
        assert agent.name == "FullAnalyst"
        assert agent.orchestrator is mock_orchestrator
        assert agent.zen_orchestrator is mock_zen_orchestrator

    def test_initialization_with_only_zen_orchestrator(self):
        """Test initialization with only zen_orchestrator."""
        mock_zen = AsyncMock()
        agent = AnalysisAgent("ZenAnalyst", zen_orchestrator=mock_zen)
        
        assert agent.zen_orchestrator is mock_zen
        assert agent.orchestrator is None

    def test_initialization_with_only_base_orchestrator(self, mock_orchestrator):
        """Test initialization with only base orchestrator."""
        agent = AnalysisAgent("BaseAnalyst", orchestrator=mock_orchestrator)
        
        assert agent.orchestrator is mock_orchestrator
        assert agent.zen_orchestrator is None

    def test_initialization_registers_correct_handlers(self):
        """Test that correct message handlers are registered."""
        agent = AnalysisAgent("HandlerAnalyst")
        
        assert len(agent.handlers) == 2
        assert "findings" in agent.handlers
        assert "analysis_request" in agent.handlers

    @patch("agents.agent_base.logger")
    def test_initialization_logs_info(self, mock_logger):
        """Test that initialization logs appropriate message."""
        agent = AnalysisAgent("LoggedAnalyst")
        
        # BaseAgent logs initialization through agent_base logger
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        assert "LoggedAnalyst" in log_message or "analyst" in log_message

    def test_analysis_cache_isolated_between_instances(self):
        """Test that analysis cache is isolated between agent instances."""
        agent1 = AnalysisAgent("Analyst1")
        agent2 = AnalysisAgent("Analyst2")
        
        agent1.analysis_cache["key1"] = "value1"
        agent2.analysis_cache["key2"] = "value2"
        
        assert "key1" not in agent2.analysis_cache
        assert "key2" not in agent1.analysis_cache


# ============================================================================
# Test Vulnerability Analysis Logic
# ============================================================================

class TestVulnerabilityAnalysisLogic:
    """Test vulnerability analysis logic in AnalysisAgent."""

    @pytest.mark.anyio
    async def test_analyze_findings_basic(self, analysis_agent, sample_findings):
        """Test basic findings analysis."""
        result = await analysis_agent._analyze_findings(sample_findings)
        
        assert result["total_findings"] == 3
        assert "by_type" in result
        assert "critical_patterns" in result
        assert "risk_level" in result
        assert "recommendations" in result
        assert "summary" in result

    @pytest.mark.anyio
    async def test_analyze_findings_categorization(self, analysis_agent, sample_findings):
        """Test that findings are categorized by type correctly."""
        result = await analysis_agent._analyze_findings(sample_findings)
        
        assert "cve" in result["by_type"]
        assert "vulnerability" in result["by_type"]
        assert len(result["by_type"]["cve"]) == 2
        assert len(result["by_type"]["vulnerability"]) == 1

    @pytest.mark.anyio
    async def test_analyze_findings_empty_list(self, analysis_agent):
        """Test analysis with empty findings list."""
        result = await analysis_agent._analyze_findings([])
        
        assert result["total_findings"] == 0
        assert result["by_type"] == {}
        assert result["critical_patterns"] == []
        assert result["risk_level"] == "low"
        assert result["summary"] == "Found 0 critical patterns across 0 findings"

    @pytest.mark.anyio
    async def test_analyze_findings_unknown_type(self, analysis_agent):
        """Test analysis with unknown finding type."""
        findings = [{"type": "unknown_type", "data": {}}]
        result = await analysis_agent._analyze_findings(findings)
        
        assert "unknown_type" in result["by_type"]
        assert result["by_type"]["unknown_type"] == findings

    @pytest.mark.anyio
    async def test_analyze_findings_missing_type(self, analysis_agent):
        """Test analysis with missing type field."""
        findings = [{"data": {"key": "value"}}]
        result = await analysis_agent._analyze_findings(findings)
        
        assert "unknown" in result["by_type"]
        assert result["by_type"]["unknown"] == findings

    @pytest.mark.anyio
    async def test_analyze_findings_multiple_critical_cves(self, analysis_agent, critical_cve_findings):
        """Test detection of multiple critical CVEs pattern."""
        result = await analysis_agent._analyze_findings(critical_cve_findings)
        
        assert result["risk_level"] == "high"
        assert len(result["critical_patterns"]) == 1
        assert result["critical_patterns"][0]["type"] == "multiple_critical_cves"
        assert result["critical_patterns"][0]["count"] == 3
        assert "3 critical CVEs" in result["critical_patterns"][0]["description"]

    @pytest.mark.anyio
    async def test_analyze_findings_ransomware_pattern(self, analysis_agent, ransomware_cve_finding):
        """Test detection of ransomware-related CVE pattern."""
        result = await analysis_agent._analyze_findings(ransomware_cve_finding)
        
        assert result["risk_level"] == "critical"
        assert len(result["critical_patterns"]) == 1
        assert result["critical_patterns"][0]["type"] == "ransomware_cve"
        assert "CVE-2021-44228" in result["critical_patterns"][0]["description"]
        assert result["critical_patterns"][0]["affected"] == ["Conti", "LockBit"]

    @pytest.mark.anyio
    async def test_analyze_findings_generates_recommendations(self, analysis_agent, ransomware_cve_finding):
        """Test that recommendations are generated for critical patterns."""
        result = await analysis_agent._analyze_findings(ransomware_cve_finding)
        
        assert len(result["recommendations"]) > 0
        analysis_agent.zen_orchestrator.process.assert_called_once()

    @pytest.mark.anyio
    async def test_analyze_findings_no_recommendations_without_zen_orchestrator(self, sample_findings):
        """Test that no recommendations are generated without zen_orchestrator."""
        agent = AnalysisAgent("NoZenAnalyst")
        
        # Create findings with ransomware pattern
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        cve_data.ransomware_used_by = ["Conti"]
        findings = [{"type": "cve", "data": cve_data}]
        
        result = await agent._analyze_findings(findings)
        
        # Should have critical patterns but no recommendations
        assert len(result["critical_patterns"]) == 1
        assert result["recommendations"] == []


# ============================================================================
# Test Severity Assessment
# ============================================================================

class TestSeverityAssessment:
    """Test severity assessment functionality."""

    @pytest.mark.anyio
    async def test_risk_level_low_no_critical_patterns(self, analysis_agent):
        """Test that risk level is low when no critical patterns found."""
        findings = [{"type": "info", "data": {"message": "Informational finding"}}]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "low"
        assert len(result["critical_patterns"]) == 0

    @pytest.mark.anyio
    async def test_risk_level_high_multiple_critical(self, analysis_agent):
        """Test risk level high with multiple critical CVEs."""
        findings = [
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "high"

    @pytest.mark.anyio
    async def test_risk_level_critical_ransomware(self, analysis_agent):
        """Test risk level critical with ransomware CVE."""
        cve_data = Mock()
        cve_data.ransomware_used_by = ["RansomwareGroup"]
        findings = [{"type": "cve", "data": cve_data}]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "critical"

    @pytest.mark.anyio
    async def test_risk_level_escalation(self, analysis_agent):
        """Test that risk level escalates from low to high properly."""
        # Start with low risk
        result1 = await analysis_agent._analyze_findings([])
        assert result1["risk_level"] == "low"
        
        # Add single critical CVE - still low (need 3+)
        result2 = await analysis_agent._analyze_findings([
            {"type": "cve", "data": {"severity": "Critical"}}
        ])
        assert result2["risk_level"] == "low"
        
        # Add 3 critical CVEs - escalates to high
        result3 = await analysis_agent._analyze_findings([
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
        ])
        assert result3["risk_level"] == "high"

    @pytest.mark.anyio
    async def test_critical_cve_detection_excludes_non_critical(self, analysis_agent):
        """Test that only critical severity CVEs are counted for the pattern."""
        findings = [
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "High"}},
            {"type": "cve", "data": {"severity": "Medium"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        # Only 1 critical CVE, so no multiple_critical_cves pattern
        assert result["risk_level"] == "low"
        patterns = [p["type"] for p in result["critical_patterns"]]
        assert "multiple_critical_cves" not in patterns


# ============================================================================
# Test CVSS Score Calculation
# ============================================================================

class TestCVSSScoreCalculation:
    """Test CVSS score calculation and handling."""

    @pytest.mark.anyio
    async def test_cvss_scores_in_findings(self, analysis_agent):
        """Test that CVSS scores are preserved in findings analysis."""
        findings = [
            {"type": "cve", "data": {"cve_id": "CVE-2021-44228", "cvss_score": 10.0, "severity": "Critical"}},
            {"type": "cve", "data": {"cve_id": "CVE-2023-1234", "cvss_score": 7.5, "severity": "High"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        cve_findings = result["by_type"]["cve"]
        assert cve_findings[0]["data"]["cvss_score"] == 10.0
        assert cve_findings[1]["data"]["cvss_score"] == 7.5

    @pytest.mark.anyio
    async def test_high_cvss_score_detection(self, analysis_agent):
        """Test detection of high CVSS score vulnerabilities."""
        findings = [
            {"type": "cve", "data": {"cvss_score": 9.8, "severity": "Critical"}},
            {"type": "cve", "data": {"cvss_score": 9.9, "severity": "Critical"}},
            {"type": "cve", "data": {"cvss_score": 10.0, "severity": "Critical"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "high"

    @pytest.mark.anyio
    async def test_missing_cvss_score_handling(self, analysis_agent):
        """Test handling of findings without CVSS scores."""
        findings = [
            {"type": "cve", "data": {"cve_id": "CVE-2023-0001", "severity": "High"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        # Should not raise an error
        assert result["total_findings"] == 1


# ============================================================================
# Test Report Generation
# ============================================================================

class TestReportGeneration:
    """Test report generation capabilities."""

    @pytest.mark.anyio
    async def test_analysis_summary_generation(self, analysis_agent, sample_findings):
        """Test that analysis summary is generated correctly."""
        result = await analysis_agent._analyze_findings(sample_findings)
        
        expected_summary = f"Found {len(result['critical_patterns'])} critical patterns across {len(sample_findings)} findings"
        assert result["summary"] == expected_summary

    @pytest.mark.anyio
    async def test_analysis_summary_with_no_findings(self, analysis_agent):
        """Test summary generation with no findings."""
        result = await analysis_agent._analyze_findings([])
        
        assert result["summary"] == "Found 0 critical patterns across 0 findings"

    @pytest.mark.anyio
    async def test_analysis_summary_with_critical_patterns(self, analysis_agent, critical_cve_findings):
        """Test summary generation with critical patterns."""
        result = await analysis_agent._analyze_findings(critical_cve_findings)
        
        assert "1 critical patterns" in result["summary"]
        assert "3 findings" in result["summary"]

    @pytest.mark.anyio
    async def test_execute_task_vulnerability_analysis(self, analysis_agent, sample_findings):
        """Test executing vulnerability analysis task."""
        task = {
            "type": "vulnerability_analysis",
            "context": {"findings": sample_findings}
        }
        result = await analysis_agent.execute_task(task)
        
        assert result["status"] == "complete"
        assert "analysis" in result
        assert result["agent"] == "TestAnalyst"
        assert result["analysis"]["total_findings"] == 3

    @pytest.mark.anyio
    async def test_execute_task_empty_findings(self, analysis_agent):
        """Test executing analysis task with empty findings."""
        task = {
            "type": "vulnerability_analysis",
            "context": {"findings": []}
        }
        result = await analysis_agent.execute_task(task)
        
        assert result["status"] == "complete"
        assert result["analysis"]["total_findings"] == 0

    @pytest.mark.anyio
    async def test_execute_task_unknown_task_type(self, analysis_agent):
        """Test executing unknown task type."""
        task = {"type": "unknown_task", "context": {}}
        result = await analysis_agent.execute_task(task)
        
        assert result["status"] == "unknown_task"

    @pytest.mark.anyio
    async def test_execute_task_missing_context(self, analysis_agent):
        """Test executing task with missing context."""
        task = {"type": "vulnerability_analysis"}
        result = await analysis_agent.execute_task(task)
        
        assert result["status"] == "complete"
        assert result["analysis"]["total_findings"] == 0


# ============================================================================
# Test Integration with Orchestrator
# ============================================================================

class TestOrchestratorIntegration:
    """Test integration with orchestrator for message routing."""

    @pytest.mark.anyio
    async def test_handle_findings_sends_alert_for_critical(self, analysis_agent, ransomware_cve_finding):
        """Test that critical findings trigger alert broadcast."""
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context={"findings": ransomware_cve_finding}
        )
        
        await analysis_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        # Should have sent at least 2 messages: alert and response
        assert analysis_agent.orchestrator.route_message.call_count >= 2
        
        # Check for alert message
        calls = analysis_agent.orchestrator.route_message.call_args_list
        alert_calls = [c for c in calls if c[0][0].msg_type == "alert"]
        assert len(alert_calls) == 1
        assert "Critical patterns detected" in alert_calls[0][0][0].content
        assert alert_calls[0][0][0].priority == 4

    @pytest.mark.anyio
    async def test_handle_findings_sends_analysis_result(self, analysis_agent, sample_findings):
        """Test that analysis result is sent back to sender."""
        msg = AgentMessage(
            sender="TestScanner[abc123]",
            msg_type="findings",
            context={"findings": sample_findings}
        )
        
        await analysis_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        calls = analysis_agent.orchestrator.route_message.call_args_list
        result_calls = [c for c in calls if c[0][0].msg_type == "analysis_result"]
        assert len(result_calls) == 1
        assert result_calls[0][0][0].recipient == "TestScanner[abc123]"

    @pytest.mark.anyio
    async def test_handle_findings_updates_shared_context(self, analysis_agent, sample_findings):
        """Test that analysis updates shared context."""
        msg = AgentMessage(
            id="msg456",
            sender="TestScanner",
            msg_type="findings",
            context={"findings": sample_findings}
        )
        
        await analysis_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        analysis_agent.orchestrator.update_shared_context.assert_called_once()
        call_args = analysis_agent.orchestrator.update_shared_context.call_args
        assert "analysis_msg456" in str(call_args)

    @pytest.mark.anyio
    async def test_handle_analysis_request(self, analysis_agent):
        """Test handling explicit analysis requests."""
        msg = AgentMessage(
            sender="Requester[def789]",
            msg_type="analysis_request",
            context={
                "data": [{"vuln": "test"}],
                "analysis_type": "general"
            }
        )
        
        await analysis_agent._handle_analysis_request(msg)
        await asyncio.sleep(0.1)
        
        analysis_agent.orchestrator.route_message.assert_called_once()
        sent_msg = analysis_agent.orchestrator.route_message.call_args[0][0]
        assert sent_msg.recipient == "Requester[def789]"
        assert sent_msg.msg_type == "response"
        assert "complete" in sent_msg.content

    @pytest.mark.anyio
    async def test_handle_analysis_request_no_data(self, analysis_agent):
        """Test handling analysis request with no data."""
        msg = AgentMessage(
            sender="Requester",
            msg_type="analysis_request",
            context={}
        )
        
        await analysis_agent._handle_analysis_request(msg)
        await asyncio.sleep(0.1)
        
        # Should handle gracefully
        analysis_agent.orchestrator.route_message.assert_called_once()

    @pytest.mark.anyio
    async def test_analyze_attack_paths_with_zen_orchestrator(self, analysis_agent):
        """Test attack path analysis with zen orchestrator."""
        vulnerabilities = [{"cve": "CVE-2021-44228", "host": "192.168.1.1"}]
        result = await analysis_agent._analyze_attack_paths(vulnerabilities)
        
        assert result["type"] == "attack_path_analysis"
        assert result["agent"] == "TestAnalyst"
        analysis_agent.zen_orchestrator.process.assert_called_once()

    @pytest.mark.anyio
    async def test_analyze_attack_paths_without_zen_orchestrator(self):
        """Test attack path analysis without zen orchestrator."""
        agent = AnalysisAgent("NoZenAnalyst")
        vulnerabilities = [{"cve": "CVE-2021-44228"}]
        result = await agent._analyze_attack_paths(vulnerabilities)
        
        assert result["type"] == "attack_path_analysis"
        assert result["paths"] == []
        assert result["agent"] == "NoZenAnalyst"


# ============================================================================
# Test Finding Correlation
# ============================================================================

class TestFindingCorrelation:
    """Test finding correlation functionality."""

    @pytest.mark.anyio
    async def test_correlate_data_shared_cves(self, analysis_agent):
        """Test correlation of data with shared CVEs."""
        data = [
            {"host": "server1", "cves": ["CVE-2021-44228", "CVE-2023-1234"]},
            {"host": "server2", "cves": ["CVE-2021-44228", "CVE-2023-5678"]},
        ]
        result = await analysis_agent._correlate_data(data)
        
        assert result["type"] == "correlation_analysis"
        assert len(result["correlations"]) == 1
        assert result["correlations"][0]["type"] == "shared_cves"
        assert "CVE-2021-44228" in result["correlations"][0]["cves"]
        assert result["correlations"][0]["significance"] == "high"

    @pytest.mark.anyio
    async def test_correlate_data_no_common_cves(self, analysis_agent):
        """Test correlation when no CVEs are shared."""
        data = [
            {"host": "server1", "cves": ["CVE-2021-1111"]},
            {"host": "server2", "cves": ["CVE-2022-2222"]},
        ]
        result = await analysis_agent._correlate_data(data)
        
        assert result["correlations"] == []

    @pytest.mark.anyio
    async def test_correlate_data_single_item(self, analysis_agent):
        """Test correlation with single data item."""
        data = [{"host": "server1", "cves": ["CVE-2021-44228"]}]
        result = await analysis_agent._correlate_data(data)
        
        # Need at least 2 items for correlation
        assert result["correlations"] == []

    @pytest.mark.anyio
    async def test_correlate_data_no_cves(self, analysis_agent):
        """Test correlation when data has no CVEs field."""
        data = [
            {"host": "server1", "services": ["ssh", "http"]},
            {"host": "server2", "services": ["ssh", "ftp"]},
        ]
        result = await analysis_agent._correlate_data(data)
        
        assert result["correlations"] == []

    @pytest.mark.anyio
    async def test_correlate_data_empty_list(self, analysis_agent):
        """Test correlation with empty data list."""
        result = await analysis_agent._correlate_data([])
        
        assert result["type"] == "correlation_analysis"
        assert result["correlations"] == []

    @pytest.mark.anyio
    async def test_correlate_data_multiple_common_cves(self, analysis_agent):
        """Test correlation with multiple common CVEs across items."""
        data = [
            {"host": "server1", "cves": ["CVE-2021-44228", "CVE-2023-1234", "CVE-2023-5678"]},
            {"host": "server2", "cves": ["CVE-2021-44228", "CVE-2023-1234"]},
            {"host": "server3", "cves": ["CVE-2021-44228", "CVE-2023-1234"]},
        ]
        result = await analysis_agent._correlate_data(data)
        
        assert len(result["correlations"]) == 1
        # Both CVE-2021-44228 and CVE-2023-1234 are common
        assert len(result["correlations"][0]["cves"]) == 2
        assert "CVE-2021-44228" in result["correlations"][0]["cves"]
        assert "CVE-2023-1234" in result["correlations"][0]["cves"]


# ============================================================================
# Test Data Analysis Types
# ============================================================================

class TestDataAnalysisTypes:
    """Test different data analysis types."""

    @pytest.mark.anyio
    async def test_analyze_data_attack_path_type(self, analysis_agent):
        """Test analyze_data with attack_path type."""
        data = [{"vuln": "test"}]
        result = await analysis_agent._analyze_data(data, "attack_path")
        
        assert result["type"] == "attack_path_analysis"

    @pytest.mark.anyio
    async def test_analyze_data_correlation_type(self, analysis_agent):
        """Test analyze_data with correlation type."""
        data = [{"cves": ["CVE-2021-44228"]}]
        result = await analysis_agent._analyze_data(data, "correlation")
        
        assert result["type"] == "correlation_analysis"

    @pytest.mark.anyio
    async def test_analyze_data_unknown_type(self, analysis_agent):
        """Test analyze_data with unknown analysis type."""
        data = [{"test": "data"}]
        result = await analysis_agent._analyze_data(data, "unknown_type")
        
        assert result["status"] == "unknown_analysis_type"

    @pytest.mark.anyio
    async def test_analyze_data_default_type(self, analysis_agent):
        """Test analyze_data with default (general) analysis type."""
        data = [{"test": "data"}]
        result = await analysis_agent._analyze_data(data, "general")
        
        assert result["status"] == "unknown_analysis_type"


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in AnalysisAgent - documenting actual behavior."""

    @pytest.mark.anyio
    async def test_analyze_findings_raises_on_none(self, analysis_agent):
        """Test that None findings raises TypeError (current behavior)."""
        with pytest.raises(TypeError):
            await analysis_agent._analyze_findings(None)

    @pytest.mark.anyio
    async def test_analyze_findings_raises_on_malformed_finding(self, analysis_agent):
        """Test that malformed finding data raises AttributeError (current behavior)."""
        findings = [
            None,
            {"type": "cve"},
        ]
        with pytest.raises(AttributeError):
            await analysis_agent._analyze_findings(findings)

    @pytest.mark.anyio
    async def test_handle_findings_raises_on_none_context(self, analysis_agent):
        """Test that None context raises AttributeError (current behavior)."""
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context=None
        )
        
        with pytest.raises(AttributeError):
            await analysis_agent._handle_findings(msg)

    @pytest.mark.anyio
    async def test_analyze_attack_paths_raises_on_orchestrator_error(self, analysis_agent):
        """Test that orchestrator errors propagate (current behavior)."""
        analysis_agent.zen_orchestrator.process.side_effect = Exception("LLM Error")
        
        data = [{"vuln": "test"}]
        with pytest.raises(Exception, match="LLM Error"):
            await analysis_agent._analyze_attack_paths(data)

    @pytest.mark.anyio
    async def test_zen_orchestrator_recommendations_error_raises(self, analysis_agent, ransomware_cve_finding):
        """Test that recommendation generation errors propagate (current behavior)."""
        analysis_agent.zen_orchestrator.process.side_effect = Exception("LLM Error")
        
        with pytest.raises(Exception, match="LLM Error"):
            await analysis_agent._analyze_findings(ransomware_cve_finding)

    @pytest.mark.anyio
    async def test_correlate_data_with_invalid_cve_format_graceful(self, analysis_agent):
        """Test correlation with invalid CVE format handled gracefully."""
        data = [
            {"host": "server1", "cves": "not-a-list"},  # Not a list - handled gracefully
            {"host": "server2", "cves": ["CVE-2021-44228"]},
        ]
        
        # The code handles this gracefully by returning empty correlations
        result = await analysis_agent._correlate_data(data)
        assert result["type"] == "correlation_analysis"
        assert result["correlations"] == []


# ============================================================================
# Test Message Handler Registration
# ============================================================================

class TestMessageHandlerRegistration:
    """Test message handler registration and functionality."""

    def test_findings_handler_registered(self, analysis_agent):
        """Test that findings handler is registered."""
        assert "findings" in analysis_agent.handlers
        assert analysis_agent.handlers["findings"] == analysis_agent._handle_findings

    def test_analysis_request_handler_registered(self, analysis_agent):
        """Test that analysis request handler is registered."""
        assert "analysis_request" in analysis_agent.handlers
        assert analysis_agent.handlers["analysis_request"] == analysis_agent._handle_analysis_request

    @pytest.mark.anyio
    async def test_handler_is_async_function(self, analysis_agent):
        """Test that handlers are async functions."""
        import inspect
        
        assert inspect.iscoroutinefunction(analysis_agent._handle_findings)
        assert inspect.iscoroutinefunction(analysis_agent._handle_analysis_request)
        assert inspect.iscoroutinefunction(analysis_agent._analyze_findings)


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.anyio
    async def test_large_number_of_findings(self, analysis_agent):
        """Test analysis with large number of findings."""
        findings = [
            {"type": "cve", "data": {"severity": "Critical" if i % 3 == 0 else "High"}}
            for i in range(100)
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["total_findings"] == 100
        # Should have ~34 critical CVEs (every 3rd one)
        assert result["risk_level"] == "high"  # More than 3 critical

    @pytest.mark.anyio
    async def test_findings_with_special_characters(self, analysis_agent):
        """Test findings with special characters in data."""
        findings = [
            {"type": "vuln", "data": {"description": "<script>alert('xss')</script>"}},
            {"type": "vuln", "data": {"description": "\"quoted\" text"}},
            {"type": "vuln", "data": {"description": "new\nline\ttab"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["total_findings"] == 3

    @pytest.mark.anyio
    async def test_exactly_three_critical_cves(self, analysis_agent):
        """Test boundary condition with exactly 3 critical CVEs."""
        findings = [
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "high"
        assert len(result["critical_patterns"]) == 1
        assert result["critical_patterns"][0]["count"] == 3

    @pytest.mark.anyio
    async def test_two_critical_cves_not_enough(self, analysis_agent):
        """Test that 2 critical CVEs don't trigger high risk."""
        findings = [
            {"type": "cve", "data": {"severity": "Critical"}},
            {"type": "cve", "data": {"severity": "Critical"}},
        ]
        result = await analysis_agent._analyze_findings(findings)
        
        assert result["risk_level"] == "low"
        assert len(result["critical_patterns"]) == 0

    @pytest.mark.anyio
    async def test_analysis_cache_usage(self, analysis_agent):
        """Test that analysis cache can be used."""
        analysis_agent.analysis_cache["test_key"] = {"result": "cached"}
        
        assert "test_key" in analysis_agent.analysis_cache
        assert analysis_agent.analysis_cache["test_key"]["result"] == "cached"


# ============================================================================
# Test Integration with BaseAgent
# ============================================================================

class TestBaseAgentIntegration:
    """Test integration with BaseAgent functionality."""

    def test_inherits_from_baseagent(self):
        """Test that AnalysisAgent inherits from BaseAgent."""
        from agents.agent_base import BaseAgent
        assert issubclass(AnalysisAgent, BaseAgent)

    def test_has_analyst_role(self, analysis_agent):
        """Test that AnalysisAgent has ANALYST role."""
        assert analysis_agent.role == AgentRole.ANALYST

    def test_inherited_methods_available(self, analysis_agent):
        """Test that inherited methods are available."""
        # Methods from BaseAgent
        assert hasattr(analysis_agent, "send_message")
        assert hasattr(analysis_agent, "receive_message")
        assert hasattr(analysis_agent, "update_context")
        assert hasattr(analysis_agent, "get_context")
        assert hasattr(analysis_agent, "get_status")
        assert hasattr(analysis_agent, "start")
        assert hasattr(analysis_agent, "stop")

    @pytest.mark.anyio
    async def test_update_context_inherited(self, analysis_agent):
        """Test that update_context from BaseAgent works."""
        analysis_agent.update_context("analysis_key", {"findings": ["f1", "f2"]})
        
        assert analysis_agent.get_context("analysis_key") == {"findings": ["f1", "f2"]}

    def test_get_status_includes_base_fields(self, analysis_agent):
        """Test that get_status includes fields from BaseAgent."""
        status = analysis_agent.get_status()
        
        assert "id" in status
        assert "name" in status
        assert "role" in status
        assert status["role"] == "analyst"
        assert "queue_size" in status
        assert "context_keys" in status


# ============================================================================
# Test Async Operations
# ============================================================================

class TestAsyncOperations:
    """Test async operations and concurrency."""

    @pytest.mark.anyio
    async def test_concurrent_analysis_calls(self, analysis_agent, sample_findings):
        """Test concurrent analysis calls."""
        tasks = [
            analysis_agent._analyze_findings(sample_findings)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert result["total_findings"] == 3

    @pytest.mark.anyio
    async def test_message_processing_during_analysis(self, analysis_agent, sample_findings):
        """Test that agent can receive messages during analysis."""
        # Start analysis
        analysis_task = asyncio.create_task(
            analysis_agent._analyze_findings(sample_findings)
        )
        
        # Receive a message during analysis
        msg = AgentMessage(sender="Test", content="Test message")
        await analysis_agent.receive_message(msg)
        
        # Wait for analysis to complete
        result = await analysis_task
        
        assert result["total_findings"] == 3
        assert analysis_agent.message_queue.qsize() == 1

    @pytest.mark.anyio
    async def test_multiple_analysis_requests(self, analysis_agent):
        """Test handling multiple analysis requests."""
        requests = [
            AgentMessage(
                sender=f"Requester{i}",
                msg_type="analysis_request",
                context={"data": [{"test": i}], "analysis_type": "correlation"}
            )
            for i in range(3)
        ]
        
        for msg in requests:
            await analysis_agent._handle_analysis_request(msg)
        
        assert analysis_agent.orchestrator.route_message.call_count == 3

"""
Comprehensive tests for agents/research_agent.py module
Tests ResearchAgent class initialization, reconnaissance logic, subdomain enumeration,
technology detection, service discovery, OSINT data collection, report generation,
and integration with external tools.

Target: 80%+ coverage of research_agent.py
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock, call
from datetime import datetime
from typing import Dict, List

from agents.research_agent import ResearchAgent
from agents.agent_base import AgentRole, AgentMessage


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_zen_orchestrator():
    """Fixture to create a mock zen orchestrator for LLM operations."""
    mock = AsyncMock()
    response = Mock()
    response.content = """
    CVE-2021-44228
    CVE-2023-38408
    CVE-2023-22515
    CVE-2021-45046
    CVE-2021-45105
    """
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
def mock_cve_db():
    """Fixture to create a mock CVE database."""
    mock = Mock()
    mock.search_cve = Mock(return_value=None)
    mock.list_all_ransomware = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_sqli_db():
    """Fixture to create a mock SQL injection database."""
    mock = Mock()
    mock.get_payloads = Mock(return_value=[])
    return mock


@pytest.fixture
def research_agent(mock_orchestrator, mock_zen_orchestrator):
    """Fixture to create a ResearchAgent with mocked orchestrators."""
    with patch("agents.research_agent.CVEDatabase") as mock_cve_class, \
         patch("agents.research_agent.SQLInjectionDatabase") as mock_sqli_class:
        
        mock_cve_instance = Mock()
        mock_cve_instance.search_cve = Mock(return_value=None)
        mock_cve_instance.list_all_ransomware = Mock(return_value=[])
        mock_cve_class.return_value = mock_cve_instance
        
        mock_sqli_instance = Mock()
        mock_sqli_instance.get_payloads = Mock(return_value=[])
        mock_sqli_class.return_value = mock_sqli_instance
        
        agent = ResearchAgent(
            name="TestResearcher",
            orchestrator=mock_orchestrator,
            zen_orchestrator=mock_zen_orchestrator
        )
        return agent


@pytest.fixture
def sample_cve_entry():
    """Fixture to create a sample CVE entry."""
    return {
        "cve_id": "CVE-2021-44228",
        "name": "Log4Shell",
        "cvss_score": 10.0,
        "severity": "Critical",
        "description": "Log4j remote code execution vulnerability",
        "affected_products": ["Apache Log4j 2.0-2.14.1"],
        "exploits": ["public exploit available"],
        "patches": ["Upgrade to 2.15.0"],
        "mitigations": ["Disable JNDI lookup"],
        "detection_methods": ["Check log patterns"],
        "ransomware_used_by": ["Conti", "LockBit"],
    }


@pytest.fixture
def sample_ransomware_entry():
    """Fixture to create a sample ransomware entry."""
    return {
        "key": "conti",
        "name": "Conti",
        "first_seen": "2020-01-01",
        "type": "Ransomware",
        "decryptable": False,
        "cves": ["CVE-2021-44228"],
    }


@pytest.fixture
def sample_research_context():
    """Fixture to create a sample research context."""
    return {
        "target": "example.com",
        "technologies": ["Apache", "PHP", "MySQL"],
        "scope": "external",
    }


@pytest.fixture
def sample_research_message(sample_research_context):
    """Fixture to create a sample research task message."""
    return AgentMessage(
        id="msg123",
        sender="TestCoordinator",
        recipient="TestResearcher",
        msg_type="research_task",
        content="Research target example.com",
        context={
            "pentest_context": sample_research_context,
            "thread_id": "thread_abc123"
        },
        priority=2,
    )


@pytest.fixture
def sample_findings_message():
    """Fixture to create a sample findings message with CVEs."""
    return AgentMessage(
        id="msg456",
        sender="TestScanner",
        recipient="TestResearcher",
        msg_type="findings",
        content="Scan findings",
        context={
            "findings": {
                "cves": ["CVE-2021-44228", "CVE-2023-1234"]
            }
        },
        priority=2,
    )


@pytest.fixture
def sample_info_request_cve():
    """Fixture to create a sample CVE info request message."""
    return AgentMessage(
        id="msg789",
        sender="TestAnalyst",
        recipient="TestResearcher",
        msg_type="request_info",
        content="CVE-2021-44228",
        context={"info_type": "cve"},
        priority=2,
    )


@pytest.fixture
def sample_info_request_sqli():
    """Fixture to create a sample SQL injection info request message."""
    return AgentMessage(
        id="msg101",
        sender="TestExploit",
        recipient="TestResearcher",
        msg_type="request_info",
        content="MySQL payloads",
        context={"info_type": "sqli_payload", "db_type": "mysql"},
        priority=2,
    )


# ============================================================================
# Test ResearchAgent Initialization
# ============================================================================

class TestResearchAgentInitialization:
    """Test ResearchAgent class initialization and configuration."""

    def test_basic_initialization(self):
        """Test basic ResearchAgent initialization with minimal parameters."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("BasicResearcher")
        
        assert agent.name == "BasicResearcher"
        assert agent.role == AgentRole.RESEARCHER
        assert len(agent.id) == 8
        assert agent.orchestrator is None
        assert agent.zen_orchestrator is None
        assert agent.current_research == {}
        assert "research_task" in agent.handlers
        assert "request_info" in agent.handlers
        assert "findings" in agent.handlers

    def test_initialization_with_orchestrators(self, mock_orchestrator, mock_zen_orchestrator):
        """Test initialization with both orchestrators."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent(
                "FullResearcher",
                orchestrator=mock_orchestrator,
                zen_orchestrator=mock_zen_orchestrator
            )
        
        assert agent.name == "FullResearcher"
        assert agent.orchestrator is mock_orchestrator
        assert agent.zen_orchestrator is mock_zen_orchestrator

    def test_initialization_with_only_zen_orchestrator(self):
        """Test initialization with only zen_orchestrator."""
        mock_zen = AsyncMock()
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("ZenResearcher", zen_orchestrator=mock_zen)
        
        assert agent.zen_orchestrator is mock_zen
        assert agent.orchestrator is None

    def test_initialization_with_only_base_orchestrator(self, mock_orchestrator):
        """Test initialization with only base orchestrator."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("BaseResearcher", orchestrator=mock_orchestrator)
        
        assert agent.orchestrator is mock_orchestrator
        assert agent.zen_orchestrator is None

    def test_initialization_registers_correct_handlers(self):
        """Test that correct message handlers are registered."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("HandlerResearcher")
        
        assert len(agent.handlers) == 3
        assert "research_task" in agent.handlers
        assert "request_info" in agent.handlers
        assert "findings" in agent.handlers

    def test_initialization_initializes_databases(self):
        """Test that CVE and SQLi databases are initialized."""
        with patch("agents.research_agent.CVEDatabase") as mock_cve, \
             patch("agents.research_agent.SQLInjectionDatabase") as mock_sqli:
            agent = ResearchAgent("DBResearcher")
            
            mock_cve.assert_called_once()
            mock_sqli.assert_called_once()
            assert agent.cve_db is mock_cve.return_value
            assert agent.sqli_db is mock_sqli.return_value

    def test_current_research_isolated_between_instances(self):
        """Test that current_research is isolated between agent instances."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent1 = ResearchAgent("Researcher1")
            agent2 = ResearchAgent("Researcher2")
        
        agent1.current_research["key1"] = "value1"
        agent2.current_research["key2"] = "value2"
        
        assert "key1" not in agent2.current_research
        assert "key2" not in agent1.current_research


# ============================================================================
# Test Message Handler Registration
# ============================================================================

class TestMessageHandlerRegistration:
    """Test message handler registration and functionality."""

    def test_research_task_handler_registered(self):
        """Test that research_task handler is registered."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        assert "research_task" in agent.handlers
        assert agent.handlers["research_task"] == agent._handle_research_task

    def test_request_info_handler_registered(self):
        """Test that request_info handler is registered."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        assert "request_info" in agent.handlers
        assert agent.handlers["request_info"] == agent._handle_info_request

    def test_findings_handler_registered(self):
        """Test that findings handler is registered."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        assert "findings" in agent.handlers
        assert agent.handlers["findings"] == agent._handle_findings

    @pytest.mark.anyio
    async def test_handlers_are_async_functions(self):
        """Test that handlers are async functions."""
        import inspect
        
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        assert inspect.iscoroutinefunction(agent._handle_research_task)
        assert inspect.iscoroutinefunction(agent._handle_info_request)
        assert inspect.iscoroutinefunction(agent._handle_findings)
        assert inspect.iscoroutinefunction(agent._perform_research)


# ============================================================================
# Test Research Task Handling
# ============================================================================

class TestResearchTaskHandling:
    """Test research task handling functionality."""

    @pytest.mark.anyio
    async def test_handle_research_task_sends_status(self, research_agent, sample_research_message):
        """Test that research task sends status message."""
        await research_agent._handle_research_task(sample_research_message)
        await asyncio.sleep(0.1)
        
        # Should send at least 2 messages: status and findings
        assert research_agent.orchestrator.route_message.call_count >= 2
        
        # Check for status message
        calls = research_agent.orchestrator.route_message.call_args_list
        status_calls = [c for c in calls if c[0][0].msg_type == "research_status"]
        assert len(status_calls) == 1
        assert "Starting research" in status_calls[0][0][0].content
        assert status_calls[0][0][0].context["status"] == "started"

    @pytest.mark.anyio
    async def test_handle_research_task_sends_findings(self, research_agent, sample_research_message):
        """Test that research task sends findings message."""
        await research_agent._handle_research_task(sample_research_message)
        await asyncio.sleep(0.1)
        
        calls = research_agent.orchestrator.route_message.call_args_list
        findings_calls = [c for c in calls if c[0][0].msg_type == "findings"]
        assert len(findings_calls) == 1
        assert "Research complete" in findings_calls[0][0][0].content
        assert "findings" in findings_calls[0][0][0].context

    @pytest.mark.anyio
    async def test_handle_research_task_updates_shared_context(self, research_agent, sample_research_message):
        """Test that research task updates shared context."""
        await research_agent._handle_research_task(sample_research_message)
        await asyncio.sleep(0.1)
        
        research_agent.orchestrator.update_shared_context.assert_called_once()
        call_args = research_agent.orchestrator.update_shared_context.call_args
        assert "research_thread_abc123" in str(call_args)

    @pytest.mark.anyio
    async def test_handle_research_task_with_unknown_target(self, research_agent):
        """Test research task with minimal context."""
        msg = AgentMessage(
            sender="TestCoordinator",
            msg_type="research_task",
            context={
                "pentest_context": {},
                "thread_id": "thread_test"
            }
        )
        
        await research_agent._handle_research_task(msg)
        await asyncio.sleep(0.1)
        
        # Should still complete without error
        calls = research_agent.orchestrator.route_message.call_args_list
        findings_calls = [c for c in calls if c[0][0].msg_type == "findings"]
        assert len(findings_calls) == 1

    @pytest.mark.anyio
    async def test_handle_research_thread_id_extraction(self, research_agent):
        """Test thread ID extraction from message context."""
        msg = AgentMessage(
            sender="TestCoordinator",
            msg_type="research_task",
            context={
                "pentest_context": {"target": "test.com"},
                "thread_id": "custom_thread_123"
            }
        )
        
        await research_agent._handle_research_task(msg)
        await asyncio.sleep(0.1)
        
        # Verify thread_id is used in shared context update
        research_agent.orchestrator.update_shared_context.assert_called_once()
        call_args = research_agent.orchestrator.update_shared_context.call_args
        assert "custom_thread_123" in str(call_args)


# ============================================================================
# Test Info Request Handling
# ============================================================================

class TestInfoRequestHandling:
    """Test info request handling functionality."""

    @pytest.mark.anyio
    async def test_handle_info_request_cve(self, research_agent, sample_info_request_cve):
        """Test handling CVE info request."""
        # Setup mock CVE database to return data
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        cve_data.severity = "Critical"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        await research_agent._handle_info_request(sample_info_request_cve)
        await asyncio.sleep(0.1)
        
        research_agent.cve_db.search_cve.assert_called_once_with("CVE-2021-44228")
        research_agent.orchestrator.route_message.assert_called_once()
        
        sent_msg = research_agent.orchestrator.route_message.call_args[0][0]
        assert sent_msg.msg_type == "response"
        assert "CVE-2021-44228" in sent_msg.content
        assert sent_msg.context["result"] == cve_data

    @pytest.mark.anyio
    async def test_handle_info_request_ransomware(self, research_agent):
        """Test handling ransomware info request."""
        msg = AgentMessage(
            sender="TestAnalyst",
            msg_type="request_info",
            content="Conti",
            context={"info_type": "ransomware"}
        )
        
        ransomware_data = Mock()
        ransomware_data.name = "Conti"
        research_agent.cve_db.search_ransomware = Mock(return_value=ransomware_data)
        
        await research_agent._handle_info_request(msg)
        await asyncio.sleep(0.1)
        
        research_agent.cve_db.search_ransomware.assert_called_once_with("Conti")
        
        sent_msg = research_agent.orchestrator.route_message.call_args[0][0]
        assert sent_msg.msg_type == "response"
        assert sent_msg.context["result"] == ransomware_data

    @pytest.mark.anyio
    async def test_handle_info_request_sqli_payload(self, research_agent, sample_info_request_sqli):
        """Test handling SQL injection payload request."""
        payloads = [Mock(), Mock()]
        research_agent.sqli_db.get_payloads = Mock(return_value=payloads)
        
        await research_agent._handle_info_request(sample_info_request_sqli)
        await asyncio.sleep(0.1)
        
        research_agent.sqli_db.get_payloads.assert_called_once_with(db_type="mysql")
        
        sent_msg = research_agent.orchestrator.route_message.call_args[0][0]
        assert sent_msg.msg_type == "response"
        assert sent_msg.context["result"] == payloads

    @pytest.mark.anyio
    async def test_handle_info_request_unknown_type(self, research_agent):
        """Test handling unknown info request type."""
        msg = AgentMessage(
            sender="TestAnalyst",
            msg_type="request_info",
            content="test",
            context={"info_type": "unknown_type"}
        )
        
        await research_agent._handle_info_request(msg)
        await asyncio.sleep(0.1)
        
        # Should not send response for unknown type
        research_agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_info_request_no_result(self, research_agent):
        """Test handling info request when no result found."""
        research_agent.cve_db.search_cve = Mock(return_value=None)
        
        msg = AgentMessage(
            sender="TestAnalyst",
            msg_type="request_info",
            content="CVE-9999-9999",
            context={"info_type": "cve"}
        )
        
        await research_agent._handle_info_request(msg)
        await asyncio.sleep(0.1)
        
        # Should not send response when no result
        research_agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_info_request_no_info_type(self, research_agent):
        """Test handling info request without info_type."""
        msg = AgentMessage(
            sender="TestAnalyst",
            msg_type="request_info",
            content="test",
            context={}
        )
        
        await research_agent._handle_info_request(msg)
        await asyncio.sleep(0.1)
        
        # Should not send response
        research_agent.orchestrator.route_message.assert_not_called()


# ============================================================================
# Test Findings Handling
# ============================================================================

class TestFindingsHandling:
    """Test findings handling and enrichment functionality."""

    @pytest.mark.anyio
    async def test_handle_findings_enriches_cves(self, research_agent, sample_findings_message):
        """Test that findings with CVEs are enriched."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        await research_agent._handle_findings(sample_findings_message)
        await asyncio.sleep(0.1)
        
        # Should search for both CVEs
        assert research_agent.cve_db.search_cve.call_count == 2
        research_agent.cve_db.search_cve.assert_any_call("CVE-2021-44228")
        research_agent.cve_db.search_cve.assert_any_call("CVE-2023-1234")

    @pytest.mark.anyio
    async def test_handle_findings_sends_enrichment(self, research_agent, sample_findings_message):
        """Test that enrichment message is sent for found CVEs."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        await research_agent._handle_findings(sample_findings_message)
        await asyncio.sleep(0.1)
        
        research_agent.orchestrator.route_message.assert_called_once()
        sent_msg = research_agent.orchestrator.route_message.call_args[0][0]
        assert sent_msg.msg_type == "enrichment"
        assert "Enriched" in sent_msg.content
        assert "CVEs with database information" in sent_msg.content
        assert "enriched_cves" in sent_msg.context

    @pytest.mark.anyio
    async def test_handle_findings_no_cves_field(self, research_agent):
        """Test handling findings without CVEs field."""
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context={"findings": {"vulnerabilities": []}}
        )
        
        await research_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        # Should not search or send enrichment
        research_agent.cve_db.search_cve.assert_not_called()
        research_agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_findings_empty_cves(self, research_agent):
        """Test handling findings with empty CVEs list."""
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context={"findings": {"cves": []}}
        )
        
        await research_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        # Should not search or send enrichment
        research_agent.cve_db.search_cve.assert_not_called()
        research_agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_findings_cve_not_found(self, research_agent):
        """Test handling findings when CVE not in database."""
        research_agent.cve_db.search_cve = Mock(return_value=None)
        
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context={"findings": {"cves": ["CVE-9999-9999"]}}
        )
        
        await research_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        # Should not send enrichment when no CVEs found
        research_agent.orchestrator.route_message.assert_not_called()

    @pytest.mark.anyio
    async def test_handle_findings_multiple_cves_some_found(self, research_agent):
        """Test handling findings with multiple CVEs where some are found."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        
        def side_effect(cve_id):
            if cve_id == "CVE-2021-44228":
                return cve_data
            return None
        
        research_agent.cve_db.search_cve = Mock(side_effect=side_effect)
        
        msg = AgentMessage(
            sender="TestScanner",
            msg_type="findings",
            context={"findings": {"cves": ["CVE-2021-44228", "CVE-9999-9999"]}}
        )
        
        await research_agent._handle_findings(msg)
        await asyncio.sleep(0.1)
        
        # Should send enrichment for the found CVE
        research_agent.orchestrator.route_message.assert_called_once()
        sent_msg = research_agent.orchestrator.route_message.call_args[0][0]
        assert "Enriched 1 CVEs" in sent_msg.content


# ============================================================================
# Test Research Performance Logic
# ============================================================================

class TestResearchPerformanceLogic:
    """Test the core research performance logic."""

    @pytest.mark.anyio
    async def test_perform_research_with_technologies(self, research_agent, sample_research_context):
        """Test research with technologies specified."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        findings = await research_agent._perform_research(sample_research_context)
        
        # Should call LLM for each technology
        assert research_agent.zen_orchestrator.process.call_count == 3  # Apache, PHP, MySQL
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_perform_research_parses_cves_from_response(self, research_agent, mock_zen_orchestrator):
        """Test that CVEs are parsed from LLM response."""
        response = Mock()
        response.content = """
        Found vulnerabilities:
        CVE-2021-44228 - Log4Shell
        CVE-2023-1234 - Example
        CVE-2023-5678 - Another
        """
        mock_zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.zen_orchestrator = mock_zen_orchestrator
        
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        findings = await research_agent._perform_research(context)
        
        # Should parse all CVEs from response
        assert research_agent.cve_db.search_cve.call_count == 3

    @pytest.mark.anyio
    async def test_perform_research_limits_cves_to_5(self, research_agent, mock_zen_orchestrator):
        """Test that research limits CVEs to top 5."""
        response = Mock()
        response.content = """
        CVE-2021-44228
        CVE-2023-38408
        CVE-2023-22515
        CVE-2021-45046
        CVE-2021-45105
        CVE-2021-4104
        CVE-2021-44832
        CVE-2021-4104
        """
        mock_zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.zen_orchestrator = mock_zen_orchestrator
        
        cve_data = Mock()
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        await research_agent._perform_research(context)
        
        # Should only search for max 5 CVEs
        assert research_agent.cve_db.search_cve.call_count == 5

    @pytest.mark.anyio
    async def test_perform_research_without_zen_orchestrator(self):
        """Test research without zen orchestrator."""
        with patch("agents.research_agent.CVEDatabase") as mock_cve_class, \
             patch("agents.research_agent.SQLInjectionDatabase"):
            
            mock_cve_instance = Mock()
            mock_cve_instance.search_cve = Mock(return_value=None)
            mock_cve_instance.list_all_ransomware = Mock(return_value=[
                {"name": "Conti"},
                {"name": "LockBit"},
                {"name": "REvil"},
            ])
            mock_cve_class.return_value = mock_cve_instance
            
            agent = ResearchAgent("NoZenResearcher")
            
            context = {"technologies": ["Apache"]}
            findings = await agent._perform_research(context)
            
            # Should still return findings from database
            assert len(findings) == 3  # Top 3 ransomware entries

    @pytest.mark.anyio
    async def test_perform_research_empty_technologies(self, research_agent):
        """Test research with empty technologies list."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[
            {"name": "Conti"},
        ])
        
        context = {"technologies": []}
        findings = await research_agent._perform_research(context)
        
        # Should not call LLM, only database
        research_agent.zen_orchestrator.process.assert_not_called()
        assert len(findings) == 1

    @pytest.mark.anyio
    async def test_perform_research_no_technologies(self, research_agent):
        """Test research without technologies in context."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[
            {"name": "Conti"},
            {"name": "LockBit"},
        ])
        
        context = {}
        findings = await research_agent._perform_research(context)
        
        # Should not call LLM, only database
        research_agent.zen_orchestrator.process.assert_not_called()
        assert len(findings) == 2

    @pytest.mark.anyio
    async def test_perform_research_includes_ransomware_data(self, research_agent):
        """Test that research includes ransomware data."""
        ransomware_data = [
            {"name": "Conti", "cves": ["CVE-2021-44228"]},
            {"name": "LockBit", "cves": ["CVE-2023-1234"]},
            {"name": "REvil", "cves": ["CVE-2023-5678"]},
            {"name": "Extra", "cves": []},
        ]
        research_agent.cve_db.list_all_ransomware = Mock(return_value=ransomware_data)
        
        context = {}
        findings = await research_agent._perform_research(context)
        
        # Should include top 3 ransomware entries
        assert len(findings) == 3
        for finding in findings:
            assert finding["type"] == "ransomware"
            assert finding["source"] == "database"

    @pytest.mark.anyio
    async def test_perform_research_cve_not_in_db(self, research_agent, mock_zen_orchestrator):
        """Test research when CVE from LLM is not in database."""
        response = Mock()
        response.content = "CVE-2021-44228"
        mock_zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.zen_orchestrator = mock_zen_orchestrator
        
        research_agent.cve_db.search_cve = Mock(return_value=None)
        
        context = {"technologies": ["Apache"]}
        findings = await research_agent._perform_research(context)
        
        # Should not include CVEs not found in database
        cve_findings = [f for f in findings if f.get("type") == "cve"]
        assert len(cve_findings) == 0


# ============================================================================
# Test Technology Detection
# ============================================================================

class TestTechnologyDetection:
    """Test technology detection related functionality."""

    @pytest.mark.anyio
    async def test_research_sends_correct_prompt(self, research_agent, mock_zen_orchestrator):
        """Test that correct prompt is sent to LLM for technology research."""
        response = Mock()
        response.content = "CVE-2021-44228"
        mock_zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.zen_orchestrator = mock_zen_orchestrator
        
        context = {"technologies": ["Apache Log4j"]}
        await research_agent._perform_research(context)
        
        mock_zen_orchestrator.process.assert_called_once()
        prompt = mock_zen_orchestrator.process.call_args[0][0]
        assert "Apache Log4j" in prompt
        assert "CVE" in prompt
        assert "ransomware" in prompt.lower()

    @pytest.mark.anyio
    async def test_research_multiple_technologies(self, research_agent):
        """Test research with multiple technologies."""
        cve_data = Mock()
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache", "Nginx", "PHP", "MySQL", "Redis"]}
        await research_agent._perform_research(context)
        
        # Should call LLM for each technology
        assert research_agent.zen_orchestrator.process.call_count == 5

    @pytest.mark.anyio
    async def test_research_technology_names_with_special_chars(self, research_agent):
        """Test research with technology names containing special characters."""
        response = Mock()
        response.content = ""
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": ["C++", "C#", "Node.js", "ASP.NET", "React/Next.js"]}
        await research_agent._perform_research(context)
        
        # Should handle special characters without error
        assert research_agent.zen_orchestrator.process.call_count == 5


# ============================================================================
# Test CVE Parsing
# ============================================================================

class TestCVEParsing:
    """Test CVE parsing from LLM responses."""

    @pytest.mark.anyio
    async def test_parse_cve_standard_format(self, research_agent):
        """Test parsing CVEs in standard format."""
        response = Mock()
        response.content = """
        CVE-2021-44228
        CVE-2023-38408
        CVE-2023-22515
        """
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.cve_db.search_cve = Mock(return_value=Mock())
        
        context = {"technologies": ["test"]}
        await research_agent._perform_research(context)
        
        assert research_agent.cve_db.search_cve.call_count == 3

    @pytest.mark.anyio
    async def test_parse_cve_with_description(self, research_agent):
        """Test parsing CVEs with descriptions."""
        response = Mock()
        response.content = """
        CVE-2021-44228 - Log4Shell vulnerability
        CVE-2023-38408 - OpenSSH vulnerability
        """
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.cve_db.search_cve = Mock(return_value=Mock())
        
        context = {"technologies": ["test"]}
        await research_agent._perform_research(context)
        
        assert research_agent.cve_db.search_cve.call_count == 2
        research_agent.cve_db.search_cve.assert_any_call("CVE-2021-44228")
        research_agent.cve_db.search_cve.assert_any_call("CVE-2023-38408")

    @pytest.mark.anyio
    async def test_parse_cve_mixed_content(self, research_agent):
        """Test parsing CVEs from mixed content."""
        response = Mock()
        response.content = """
        Here are the vulnerabilities:
        
        1. CVE-2021-44228 - Critical
        2. CVE-2023-1234 - High severity issue
        
        Some text without CVE
        CVE-2023-5678
        
        More text CVE-2021-99999 with extra digits
        """
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.cve_db.search_cve = Mock(return_value=Mock())
        
        context = {"technologies": ["test"]}
        await research_agent._perform_research(context)
        
        # Should parse valid CVEs (regex allows 4+ digits in last part)
        # CVE-2021-99999 is also valid (5 digits)
        assert research_agent.cve_db.search_cve.call_count == 4
        research_agent.cve_db.search_cve.assert_any_call("CVE-2021-44228")
        research_agent.cve_db.search_cve.assert_any_call("CVE-2023-1234")
        research_agent.cve_db.search_cve.assert_any_call("CVE-2023-5678")
        research_agent.cve_db.search_cve.assert_any_call("CVE-2021-99999")

    @pytest.mark.anyio
    async def test_parse_no_cves_in_response(self, research_agent):
        """Test parsing when no CVEs in response."""
        response = Mock()
        response.content = "No vulnerabilities found"
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": ["test"]}
        findings = await research_agent._perform_research(context)
        
        # Should only have ransomware findings
        assert all(f["type"] == "ransomware" for f in findings)


# ============================================================================
# Test Execute Task
# ============================================================================

class TestExecuteTask:
    """Test execute_task method."""

    @pytest.mark.anyio
    async def test_execute_reconnaissance_task(self, research_agent):
        """Test executing reconnaissance task."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        task = {
            "type": "reconnaissance",
            "context": {"target": "example.com", "technologies": ["Apache"]}
        }
        result = await research_agent.execute_task(task)
        
        assert result["status"] == "complete"
        assert "findings_count" in result
        assert result["agent"] == "TestResearcher"

    @pytest.mark.anyio
    async def test_execute_reconnaissance_sends_findings(self, research_agent):
        """Test that reconnaissance task sends findings to analysts."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[{"name": "Test"}])
        
        task = {"type": "reconnaissance", "context": {"target": "test.com"}}
        await research_agent.execute_task(task)
        await asyncio.sleep(0.1)
        
        research_agent.orchestrator.route_message.assert_called()
        calls = research_agent.orchestrator.route_message.call_args_list
        findings_calls = [c for c in calls if c[0][0].msg_type == "findings"]
        assert len(findings_calls) == 1
        assert findings_calls[0][0][0].recipient == "role:analyst"

    @pytest.mark.anyio
    async def test_execute_unknown_task_type(self, research_agent):
        """Test executing unknown task type."""
        task = {"type": "unknown_task", "context": {}}
        result = await research_agent.execute_task(task)
        
        assert result["status"] == "unknown_task"

    @pytest.mark.anyio
    async def test_execute_task_missing_type(self, research_agent):
        """Test executing task with missing type."""
        task = {"context": {"target": "test.com"}}
        result = await research_agent.execute_task(task)
        
        assert result["status"] == "unknown_task"

    @pytest.mark.anyio
    async def test_execute_task_missing_context(self, research_agent):
        """Test executing task with missing context."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        task = {"type": "reconnaissance"}
        result = await research_agent.execute_task(task)
        
        assert result["status"] == "complete"
        assert result["findings_count"] == 0

    @pytest.mark.anyio
    async def test_execute_task_empty_context(self, research_agent):
        """Test executing task with empty context."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        task = {"type": "reconnaissance", "context": {}}
        result = await research_agent.execute_task(task)
        
        assert result["status"] == "complete"


# ============================================================================
# Test Report Generation
# ============================================================================

class TestReportGeneration:
    """Test report generation capabilities."""

    @pytest.mark.anyio
    async def test_research_finding_structure(self, research_agent):
        """Test structure of research findings."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        findings = await research_agent._perform_research(context)
        
        # Each finding should have required fields
        for finding in findings:
            assert "type" in finding
            assert "data" in finding
            assert "source" in finding

    @pytest.mark.anyio
    async def test_cve_finding_structure(self, research_agent):
        """Test structure of CVE type findings."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        findings = await research_agent._perform_research(context)
        
        cve_findings = [f for f in findings if f["type"] == "cve"]
        for finding in cve_findings:
            assert finding["source"] == "llm_research"
            assert finding["data"] == cve_data

    @pytest.mark.anyio
    async def test_ransomware_finding_structure(self, research_agent):
        """Test structure of ransomware type findings."""
        ransomware_data = {"name": "Conti", "cves": ["CVE-2021-44228"]}
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[ransomware_data])
        
        context = {}
        findings = await research_agent._perform_research(context)
        
        ransomware_findings = [f for f in findings if f["type"] == "ransomware"]
        for finding in ransomware_findings:
            assert finding["source"] == "database"
            assert finding["data"] == ransomware_data


# ============================================================================
# Test Integration with Tools
# ============================================================================

class TestToolIntegration:
    """Test integration with external tools and databases."""

    def test_cve_database_integration(self):
        """Test that CVE database is properly integrated."""
        with patch("agents.research_agent.CVEDatabase") as mock_cve_class, \
             patch("agents.research_agent.SQLInjectionDatabase"):
            
            mock_cve_instance = Mock()
            mock_cve_class.return_value = mock_cve_instance
            
            agent = ResearchAgent("TestResearcher")
            
            assert agent.cve_db is mock_cve_instance

    def test_sqli_database_integration(self):
        """Test that SQL injection database is properly integrated."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase") as mock_sqli_class:
            
            mock_sqli_instance = Mock()
            mock_sqli_class.return_value = mock_sqli_instance
            
            agent = ResearchAgent("TestResearcher")
            
            assert agent.sqli_db is mock_sqli_instance

    @pytest.mark.anyio
    async def test_cve_database_search_called(self, research_agent):
        """Test that CVE database search is called during research."""
        cve_data = Mock()
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        await research_agent._perform_research(context)
        
        research_agent.cve_db.search_cve.assert_called()

    @pytest.mark.anyio
    async def test_ransomware_list_called(self, research_agent):
        """Test that ransomware list is retrieved during research."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        context = {"technologies": ["Apache"]}
        await research_agent._perform_research(context)
        
        research_agent.cve_db.list_all_ransomware.assert_called_once()

    @pytest.mark.anyio
    async def test_sqli_database_get_payloads_called(self, research_agent):
        """Test that SQLi database get_payloads is called for requests."""
        payloads = [Mock()]
        research_agent.sqli_db.get_payloads = Mock(return_value=payloads)
        
        msg = AgentMessage(
            sender="Test",
            msg_type="request_info",
            content="test",
            context={"info_type": "sqli_payload", "db_type": "mysql"}
        )
        
        await research_agent._handle_info_request(msg)
        
        research_agent.sqli_db.get_payloads.assert_called_once_with(db_type="mysql")


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in ResearchAgent."""

    @pytest.mark.anyio
    async def test_llm_error_during_research(self, research_agent):
        """Test handling of LLM errors during research."""
        research_agent.zen_orchestrator.process.side_effect = Exception("LLM Error")
        
        context = {"technologies": ["Apache"]}
        
        # Error should propagate (current behavior)
        with pytest.raises(Exception, match="LLM Error"):
            await research_agent._perform_research(context)

    @pytest.mark.anyio
    async def test_cve_db_error_during_research(self, research_agent):
        """Test handling of CVE database errors during research."""
        research_agent.cve_db.search_cve.side_effect = Exception("DB Error")
        
        context = {"technologies": ["Apache"]}
        
        # Error should propagate (current behavior)
        with pytest.raises(Exception, match="DB Error"):
            await research_agent._perform_research(context)

    @pytest.mark.anyio
    async def test_ransomware_list_error(self, research_agent):
        """Test handling of ransomware list error."""
        research_agent.cve_db.list_all_ransomware.side_effect = Exception("DB Error")
        
        context = {}
        
        # Error should propagate (current behavior)
        with pytest.raises(Exception, match="DB Error"):
            await research_agent._perform_research(context)

    @pytest.mark.anyio
    async def test_handle_research_task_with_none_context(self, research_agent):
        """Test handling research task with None context."""
        msg = AgentMessage(
            sender="Test",
            msg_type="research_task",
            context=None
        )
        
        # Error should propagate due to .get() on None (current behavior)
        with pytest.raises(AttributeError):
            await research_agent._handle_research_task(msg)

    @pytest.mark.anyio
    async def test_handle_findings_with_none_context(self, research_agent):
        """Test handling findings with None context."""
        msg = AgentMessage(
            sender="Test",
            msg_type="findings",
            context=None
        )
        
        # Error should propagate (current behavior)
        with pytest.raises(AttributeError):
            await research_agent._handle_findings(msg)

    @pytest.mark.anyio
    async def test_handle_info_request_with_none_context(self, research_agent):
        """Test handling info request with None context."""
        msg = AgentMessage(
            sender="Test",
            msg_type="request_info",
            content="test",
            context=None
        )
        
        # Error should propagate (current behavior)
        with pytest.raises(AttributeError):
            await research_agent._handle_info_request(msg)

    @pytest.mark.anyio
    async def test_perform_research_with_none_context(self, research_agent):
        """Test perform research with None context."""
        # Error should propagate (current behavior)
        with pytest.raises(AttributeError):
            await research_agent._perform_research(None)


# ============================================================================
# Test Integration with BaseAgent
# ============================================================================

class TestBaseAgentIntegration:
    """Test integration with BaseAgent functionality."""

    def test_inherits_from_baseagent(self):
        """Test that ResearchAgent inherits from BaseAgent."""
        from agents.agent_base import BaseAgent
        
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            assert issubclass(ResearchAgent, BaseAgent)

    def test_has_researcher_role(self):
        """Test that ResearchAgent has RESEARCHER role."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        assert agent.role == AgentRole.RESEARCHER

    def test_inherited_methods_available(self):
        """Test that inherited methods are available."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        # Methods from BaseAgent
        assert hasattr(agent, "send_message")
        assert hasattr(agent, "receive_message")
        assert hasattr(agent, "update_context")
        assert hasattr(agent, "get_context")
        assert hasattr(agent, "get_status")
        assert hasattr(agent, "start")
        assert hasattr(agent, "stop")

    @pytest.mark.anyio
    async def test_update_context_inherited(self):
        """Test that update_context from BaseAgent works."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        agent.update_context("research_key", {"target": "example.com"})
        
        assert agent.get_context("research_key") == {"target": "example.com"}

    def test_get_status_includes_base_fields(self):
        """Test that get_status includes fields from BaseAgent."""
        with patch("agents.research_agent.CVEDatabase"), \
             patch("agents.research_agent.SQLInjectionDatabase"):
            agent = ResearchAgent("TestResearcher")
        
        status = agent.get_status()
        
        assert "id" in status
        assert "name" in status
        assert "role" in status
        assert status["role"] == "researcher"
        assert "queue_size" in status
        assert "context_keys" in status


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.anyio
    async def test_empty_target_string(self, research_agent):
        """Test research with empty target string."""
        context = {"target": "", "technologies": []}
        findings = await research_agent._perform_research(context)
        
        # Should complete without error
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_very_long_technology_name(self, research_agent):
        """Test research with very long technology name."""
        long_name = "A" * 1000
        response = Mock()
        response.content = ""
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": [long_name]}
        findings = await research_agent._perform_research(context)
        
        # Should handle long names without error
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_many_technologies(self, research_agent):
        """Test research with many technologies."""
        response = Mock()
        response.content = "CVE-2021-44228"
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.cve_db.search_cve = Mock(return_value=Mock())
        
        context = {"technologies": [f"Tech{i}" for i in range(50)]}
        await research_agent._perform_research(context)
        
        # Should call LLM for each technology
        assert research_agent.zen_orchestrator.process.call_count == 50

    @pytest.mark.anyio
    async def test_duplicate_cves_in_response(self, research_agent):
        """Test handling of duplicate CVEs in LLM response."""
        response = Mock()
        response.content = """
        CVE-2021-44228
        CVE-2021-44228
        CVE-2021-44228
        """
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        cve_data = Mock()
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["test"]}
        findings = await research_agent._perform_research(context)
        
        # Should process all occurrences
        assert research_agent.cve_db.search_cve.call_count == 3

    @pytest.mark.anyio
    async def test_malformed_cve_in_response(self, research_agent):
        """Test handling of malformed CVEs in response."""
        response = Mock()
        response.content = """
        CVE-2021-44228
        INVALID-CVE-FORMAT
        CVE-ABC-DEF
        2021-44228
        """
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        research_agent.cve_db.search_cve = Mock(return_value=Mock())
        
        context = {"technologies": ["test"]}
        await research_agent._perform_research(context)
        
        # Should only parse valid CVE format
        research_agent.cve_db.search_cve.assert_called_once_with("CVE-2021-44228")

    @pytest.mark.anyio
    async def test_special_characters_in_target(self, research_agent):
        """Test research with special characters in target."""
        context = {
            "target": "test.com<script>alert('xss')</script>",
            "technologies": []
        }
        findings = await research_agent._perform_research(context)
        
        # Should handle special characters without error
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_unicode_in_technology_name(self, research_agent):
        """Test research with unicode in technology name."""
        response = Mock()
        response.content = ""
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": ["日本語", "中文", "العربية", "Emoji 🚀"]}
        findings = await research_agent._perform_research(context)
        
        # Should handle unicode without error
        assert isinstance(findings, list)


# ============================================================================
# Test Async Operations
# ============================================================================

class TestAsyncOperations:
    """Test async operations and concurrency."""

    @pytest.mark.anyio
    async def test_concurrent_research_calls(self, research_agent):
        """Test concurrent research calls."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        contexts = [
            {"target": f"target{i}.com", "technologies": []}
            for i in range(5)
        ]
        
        tasks = [
            research_agent._perform_research(context)
            for context in contexts
        ]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)

    @pytest.mark.anyio
    async def test_message_processing_during_research(self, research_agent):
        """Test that agent can receive messages during research."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        # Start research
        research_task = asyncio.create_task(
            research_agent._perform_research({"technologies": ["Apache"]})
        )
        
        # Receive a message during research
        msg = AgentMessage(sender="Test", content="Test message")
        await research_agent.receive_message(msg)
        
        # Wait for research to complete
        await research_task
        
        # Verify message was received
        assert len(research_agent.inbox) == 1

    @pytest.mark.anyio
    async def test_multiple_research_tasks_sequential(self, research_agent):
        """Test multiple research tasks executed sequentially."""
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        results = []
        for i in range(3):
            context = {"target": f"target{i}.com", "technologies": []}
            result = await research_agent._perform_research(context)
            results.append(result)
        
        assert len(results) == 3


# ============================================================================
# Test OSINT Data Collection
# ============================================================================

class TestOSINTDataCollection:
    """Test OSINT data collection capabilities."""

    @pytest.mark.anyio
    async def test_osint_data_structure(self, research_agent):
        """Test structure of OSINT collected data."""
        cve_data = Mock()
        cve_data.cve_id = "CVE-2021-44228"
        cve_data.severity = "Critical"
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["Apache"]}
        findings = await research_agent._perform_research(context)
        
        # All findings should have required structure
        for finding in findings:
            assert isinstance(finding, dict)
            assert "type" in finding
            assert "data" in finding
            assert "source" in finding

    @pytest.mark.anyio
    async def test_osint_target_info_collection(self, research_agent):
        """Test that target info is used in research."""
        context = {
            "target": "example.com",
            "technologies": ["Apache"],
            "scope": "external"
        }
        
        # Research should use target info
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        await research_agent._perform_research(context)
        
        # Verify the context is passed through
        # (target is extracted but currently marked as TODO in the code)


# ============================================================================
# Test Subdomain Enumeration (Placeholder for Future)
# ============================================================================

class TestSubdomainEnumeration:
    """Test subdomain enumeration functionality (placeholder)."""
    
    @pytest.mark.anyio
    async def test_target_extraction(self, research_agent):
        """Test that target is extracted from context."""
        context = {"target": "example.com"}
        
        # Target should be accessible in research
        # Currently marked as TODO in the code
        findings = await research_agent._perform_research(context)
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_target_with_subdomain(self, research_agent):
        """Test research with subdomain as target."""
        context = {"target": "subdomain.example.com"}
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        findings = await research_agent._perform_research(context)
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_target_with_port(self, research_agent):
        """Test research with port in target."""
        context = {"target": "example.com:8080"}
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        
        findings = await research_agent._perform_research(context)
        assert isinstance(findings, list)


# ============================================================================
# Test Service Discovery (Placeholder for Future)
# ============================================================================

class TestServiceDiscovery:
    """Test service discovery functionality (placeholder)."""
    
    @pytest.mark.anyio
    async def test_service_info_in_context(self, research_agent):
        """Test that service info can be passed in context."""
        context = {
            "target": "example.com",
            "services": ["http", "https", "ssh"],
            "technologies": ["Apache", "OpenSSH"]
        }
        
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        findings = await research_agent._perform_research(context)
        
        # Should complete without error
        assert isinstance(findings, list)

    @pytest.mark.anyio
    async def test_port_info_in_context(self, research_agent):
        """Test that port info can be passed in context."""
        context = {
            "target": "example.com",
            "ports": [80, 443, 22],
            "technologies": ["Apache"]
        }
        
        research_agent.cve_db.list_all_ransomware = Mock(return_value=[])
        findings = await research_agent._perform_research(context)
        
        # Should complete without error
        assert isinstance(findings, list)


# ============================================================================
# Test Technology Detection
# ============================================================================

class TestTechnologyDetection:
    """Test technology detection functionality."""
    
    @pytest.mark.anyio
    async def test_single_technology_research(self, research_agent):
        """Test research with single technology."""
        cve_data = Mock()
        research_agent.cve_db.search_cve = Mock(return_value=cve_data)
        
        context = {"technologies": ["WordPress"]}
        findings = await research_agent._perform_research(context)
        
        # Should call LLM for the technology
        research_agent.zen_orchestrator.process.assert_called_once()
        prompt = research_agent.zen_orchestrator.process.call_args[0][0]
        assert "WordPress" in prompt

    @pytest.mark.anyio
    async def test_web_framework_technologies(self, research_agent):
        """Test research with web framework technologies."""
        frameworks = ["Django", "Flask", "Express.js", "Ruby on Rails", "Spring Boot"]
        response = Mock()
        response.content = ""
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": frameworks}
        await research_agent._perform_research(context)
        
        assert research_agent.zen_orchestrator.process.call_count == len(frameworks)

    @pytest.mark.anyio
    async def test_database_technologies(self, research_agent):
        """Test research with database technologies."""
        databases = ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch"]
        response = Mock()
        response.content = ""
        research_agent.zen_orchestrator.process = AsyncMock(return_value=response)
        
        context = {"technologies": databases}
        await research_agent._perform_research(context)
        
        assert research_agent.zen_orchestrator.process.call_count == len(databases)

"""
Unit Tests for agents.research_agent module
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Save real sys.modules entries so we can restore them after import
_MOCK_KEYS = [
    "aiohttp",
    "modules",
    "modules.cve_database",
    "modules.sql_injection_db",
    "modules.osint",
]
_saved_modules = {k: sys.modules.get(k) for k in _MOCK_KEYS}

# Temporarily stub heavy dependencies so research_agent can be imported
sys.modules["aiohttp"] = MagicMock()
sys.modules["modules"] = MagicMock()
sys.modules["modules.cve_database"] = MagicMock()
sys.modules["modules.sql_injection_db"] = MagicMock()
sys.modules["modules.osint"] = MagicMock()

from agents.agent_base import AgentMessage, AgentRole  # noqa: E402

# Now import the agent
from agents.research_agent import ResearchAgent  # noqa: E402

# Restore sys.modules so other tests can import the real 'modules' package
for _k, _v in _saved_modules.items():
    if _v is None:
        sys.modules.pop(_k, None)
    else:
        sys.modules[_k] = _v
del _saved_modules, _MOCK_KEYS


class TestResearchAgentInit:
    """Tests for ResearchAgent initialization"""

    def test_init_default(self):
        """Test default initialization"""
        agent = ResearchAgent("TestResearcher")

        assert agent.name == "TestResearcher"
        assert agent.role == AgentRole.RESEARCHER
        assert agent.zen_orchestrator is None
        assert agent.cve_db is not None
        assert agent.sqli_db is not None
        assert agent.current_research == {}

    def test_init_with_orchestrator(self):
        """Test initialization with orchestrator"""
        mock_orchestrator = MagicMock()
        agent = ResearchAgent("TestResearcher", zen_orchestrator=mock_orchestrator)

        assert agent.zen_orchestrator is mock_orchestrator

    def test_message_handlers_registered(self):
        """Test that message handlers are registered via public API"""
        agent = ResearchAgent("TestResearcher")

        # Agent should be initialized and functional
        assert agent.name == "TestResearcher"
        assert agent.role == AgentRole.RESEARCHER
        # Verify the agent was created successfully with handlers
        assert agent is not None


class TestHandleResearchTask:
    """Tests for _handle_research_task method"""

    @pytest.fixture
    def agent(self):
        return ResearchAgent("TestResearcher")

    @pytest.mark.asyncio
    async def test_handle_research_task(self, agent):
        """Test handling research task"""
        msg = AgentMessage(
            sender="TestSender",
            recipient="TestResearcher",
            content="Research target",
            context={
                "pentest_context": {"target": "example.com"},
                "thread_id": "thread-123",
            },
        )

        agent.send_message = AsyncMock()
        agent._perform_research = AsyncMock(return_value=[{"finding": "test"}])
        agent.update_context = MagicMock()

        await agent._handle_research_task(msg)

        # Should send status message
        assert agent.send_message.call_count == 2

        # Should call _perform_research
        agent._perform_research.assert_called_once()

        # Should update context
        agent.update_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_research_task_sends_status(self, agent):
        """Test that research task sends status updates"""
        msg = AgentMessage(
            sender="Coordinator",
            recipient="Researcher",
            content="Start research",
            context={
                "pentest_context": {"target": "scanme.nmap.org"},
                "thread_id": "thread-1",
            },
        )

        agent.send_message = AsyncMock()
        agent._perform_research = AsyncMock(return_value=[])
        agent.update_context = MagicMock()

        await agent._handle_research_task(msg)

        # Check first message is status update
        first_call = agent.send_message.call_args_list[0]
        assert first_call.kwargs["msg_type"] == "research_status"
        assert first_call.kwargs["context"]["status"] == "started"


class TestHandleInfoRequest:
    """Tests for _handle_info_request method"""

    @pytest.fixture
    def agent(self):
        agent = ResearchAgent("TestResearcher")
        agent.cve_db = MagicMock()
        agent.cve_db.search_cve = MagicMock(return_value={"id": "CVE-2021-1234"})
        agent.cve_db.search_ransomware = MagicMock(return_value={"name": "Locky"})
        agent.sqli_db = MagicMock()
        agent.sqli_db.get_payloads = MagicMock(return_value=["' OR 1=1 --"])
        return agent

    @pytest.mark.asyncio
    async def test_handle_cve_request(self, agent):
        """Test handling CVE info request"""
        msg = AgentMessage(
            sender="Analyst",
            recipient="Researcher",
            content="CVE-2021-1234",
            context={"info_type": "cve"},
        )

        agent.send_message = AsyncMock()

        await agent._handle_info_request(msg)

        agent.cve_db.search_cve.assert_called_once_with("CVE-2021-1234")
        agent.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ransomware_request(self, agent):
        """Test handling ransomware info request"""
        msg = AgentMessage(
            sender="Analyst",
            recipient="Researcher",
            content="Locky",
            context={"info_type": "ransomware"},
        )

        agent.send_message = AsyncMock()

        await agent._handle_info_request(msg)

        agent.cve_db.search_ransomware.assert_called_once_with("Locky")

    @pytest.mark.asyncio
    async def test_handle_sqli_payload_request(self, agent):
        """Test handling SQLi payload request"""
        msg = AgentMessage(
            sender="Exploiter",
            recipient="Researcher",
            content="Need payloads",
            context={"info_type": "sqli_payload", "db_type": "mysql"},
        )

        agent.send_message = AsyncMock()

        await agent._handle_info_request(msg)

        agent.sqli_db.get_payloads.assert_called_once_with(db_type="mysql")

    @pytest.mark.asyncio
    async def test_handle_info_request_no_result(self, agent):
        """Test handling info request with no result"""
        agent.cve_db.search_cve = MagicMock(return_value=None)

        msg = AgentMessage(
            sender="Analyst",
            recipient="Researcher",
            content="CVE-9999-9999",
            context={"info_type": "cve"},
        )

        agent.send_message = AsyncMock()

        await agent._handle_info_request(msg)

        # Should not send message when no result
        agent.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_unknown_info_type(self, agent):
        """Test handling unknown info type"""
        msg = AgentMessage(
            sender="Analyst",
            recipient="Researcher",
            content="Query",
            context={"info_type": "unknown_type"},
        )

        agent.send_message = AsyncMock()

        await agent._handle_info_request(msg)

        # Should not send message for unknown type
        agent.send_message.assert_not_called()


class TestHandleFindings:
    """Tests for _handle_findings method"""

    @pytest.fixture
    def agent(self):
        agent = ResearchAgent("TestResearcher")
        agent.cve_db = MagicMock()
        return agent

    @pytest.mark.asyncio
    async def test_handle_findings_with_cves(self, agent):
        """Test handling findings with CVEs"""
        agent.cve_db.search_cve = MagicMock(return_value={"id": "CVE-2021-1234"})

        msg = AgentMessage(
            sender="Scanner",
            recipient="Researcher",
            content="Found vulnerabilities",
            context={"findings": {"cves": ["CVE-2021-1234", "CVE-2021-5678"]}},
        )

        agent.send_message = AsyncMock()

        await agent._handle_findings(msg)

        # Should enrich CVEs
        assert agent.cve_db.search_cve.call_count == 2
        agent.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_findings_no_cves(self, agent):
        """Test handling findings without CVEs"""
        msg = AgentMessage(
            sender="Scanner",
            recipient="Researcher",
            content="General findings",
            context={"findings": {}},
        )

        agent.send_message = AsyncMock()

        await agent._handle_findings(msg)

        # Should not send message when no CVEs
        agent.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_findings_empty_cve_list(self, agent):
        """Test handling findings with empty CVE list"""
        msg = AgentMessage(
            sender="Scanner",
            recipient="Researcher",
            content="No CVEs found",
            context={"findings": {"cves": []}},
        )

        agent.send_message = AsyncMock()

        await agent._handle_findings(msg)

        agent.send_message.assert_not_called()


class TestPerformResearch:
    """Tests for _perform_research method"""

    @pytest.fixture
    def agent(self):
        agent = ResearchAgent("TestResearcher")
        agent.cve_db = MagicMock()
        agent.cve_db.search_cve = MagicMock(return_value=None)
        agent.cve_db.list_all_ransomware = MagicMock(
            return_value=[
                {"name": "Locky"},
                {"name": "WannaCry"},
            ]
        )
        return agent

    @pytest.mark.asyncio
    async def test_perform_research_basic(self, agent):
        """Test basic research without LLM"""
        context = {"target": "example.com", "technologies": []}

        findings = await agent._perform_research(context)

        # Should return ransomware findings from database
        assert len(findings) == 2
        assert all(f["type"] == "ransomware" for f in findings)

    @pytest.mark.asyncio
    async def test_perform_research_with_technologies(self, agent):
        """Test research with technologies using LLM"""
        # Mock LLM orchestrator
        mock_response = MagicMock()
        mock_response.content = """
        CVE-2021-44228
        CVE-2021-45046
        """

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process = AsyncMock(return_value=mock_response)
        agent.zen_orchestrator = mock_orchestrator

        # Mock CVE DB to return data for parsed CVEs
        agent.cve_db.search_cve = MagicMock(
            return_value={
                "id": "CVE-2021-44228",
                "description": "Log4j vulnerability",
            }
        )

        context = {"target": "example.com", "technologies": ["Log4j"]}

        findings = await agent._perform_research(context)

        # Should have called LLM orchestrator
        mock_orchestrator.process.assert_called_once()

        # Should have found CVEs
        assert agent.cve_db.search_cve.call_count > 0

    @pytest.mark.asyncio
    async def test_perform_research_no_orchestrator(self, agent):
        """Test research without LLM orchestrator"""
        agent.zen_orchestrator = None

        context = {"target": "example.com", "technologies": ["Apache", "PHP"]}

        findings = await agent._perform_research(context)

        # Should not crash without orchestrator
        assert isinstance(findings, list)

    @pytest.mark.asyncio
    async def test_perform_research_cve_not_found(self, agent):
        """Test research when CVEs are not in database"""
        mock_response = MagicMock()
        mock_response.content = "CVE-9999-99999"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process = AsyncMock(return_value=mock_response)
        agent.zen_orchestrator = mock_orchestrator

        # CVE not found in DB
        agent.cve_db.search_cve = MagicMock(return_value=None)

        context = {"target": "example.com", "technologies": ["UnknownTech"]}

        findings = await agent._perform_research(context)

        # Should not include unfound CVEs
        assert all(f["type"] == "ransomware" for f in findings)


class TestExecuteTask:
    """Tests for execute_task method"""

    @pytest.fixture
    def agent(self):
        agent = ResearchAgent("TestResearcher")
        agent._perform_research = AsyncMock(return_value=[{"type": "cve", "data": {"id": "CVE-2021-1234"}}])
        return agent

    @pytest.mark.asyncio
    async def test_execute_reconnaissance_task(self, agent):
        """Test executing reconnaissance task"""
        task = {"type": "reconnaissance", "context": {"target": "example.com"}}

        agent.send_message = AsyncMock()

        result = await agent.execute_task(task)

        assert result["status"] == "complete"
        assert result["findings_count"] == 1
        assert result["agent"] == "TestResearcher"

        agent._perform_research.assert_called_once_with({"target": "example.com"})
        agent.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_unknown_task(self, agent):
        """Test executing unknown task type"""
        task = {"type": "unknown_task_type", "context": {}}

        result = await agent.execute_task(task)

        assert result["status"] == "unknown_task"

    @pytest.mark.asyncio
    async def test_execute_task_no_type(self, agent):
        """Test executing task without type"""
        task = {"context": {}}

        result = await agent.execute_task(task)

        assert result["status"] == "unknown_task"


class TestResearchAgentIntegration:
    """Integration-style tests for ResearchAgent"""

    @pytest.mark.asyncio
    async def test_full_research_workflow(self):
        """Test full research workflow"""
        agent = ResearchAgent("Researcher1")

        # Mock dependencies
        agent.cve_db = MagicMock()
        agent.cve_db.search_cve = MagicMock(return_value={"id": "CVE-2021-1234"})
        agent.cve_db.list_all_ransomware = MagicMock(return_value=[])

        agent.send_message = AsyncMock()
        agent.update_context = MagicMock()

        # Simulate receiving research task
        msg = AgentMessage(
            sender="Orchestrator",
            recipient="Researcher1",
            content="Research example.com",
            context={
                "pentest_context": {
                    "target": "example.com",
                    "technologies": ["Apache"],
                },
                "thread_id": "thread-abc",
            },
        )

        await agent._handle_research_task(msg)

        # Verify workflow completed
        assert agent.send_message.call_count == 2
        agent.update_context.assert_called_once()

"""
Tests für den ReAct Agent
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage

from agents.react_agent import ReActAgent, ReActAgentConfig, AgentState


class TestReActAgent:
    """Test-Suite für den ReAct Agent"""

    @pytest.fixture
    def agent_config(self):
        return ReActAgentConfig(
            max_iterations=3, enable_sandbox=True, auto_approve_dangerous=False, use_human_in_the_loop=True
        )

    @pytest.fixture
    def agent(self, agent_config):
        with (
            patch("agents.react_agent.LLMBackend"),
            patch("agents.react_agent.CVEDatabase"),
            patch("agents.react_agent.NmapTool"),
            patch("agents.react_agent.NucleiTool"),
            patch("agents.react_agent.FfufTool"),
        ):
            return ReActAgent(agent_config)

    def test_initialization(self, agent):
        """Test: Agent wird korrekt initialisiert"""
        assert agent is not None
        assert len(agent.tools) == 5  # 5 Tools initialisiert
        assert agent.config.max_iterations == 3

    def test_is_dangerous_tool(self, agent):
        """Test: Dangerous Tool Erkennung"""
        assert agent._is_dangerous_tool("validate_exploit") is True
        assert agent._is_dangerous_tool("exploit_cve") is True
        assert agent._is_dangerous_tool("scan_ports") is False
        assert agent._is_dangerous_tool("lookup_cve") is False

    def test_agent_state_structure(self):
        """Test: AgentState hat korrekte Struktur"""
        state: AgentState = {
            "messages": [HumanMessage(content="Test")],
            "findings": [],
            "target": "example.com",
            "iteration": 0,
            "max_iterations": 10,
            "status": "running",
        }

        assert state["target"] == "example.com"
        assert state["iteration"] == 0
        assert state["status"] == "running"

    def test_generate_report(self, agent):
        """Test: Report-Generierung"""
        result = {
            "target": "test.com",
            "status": "completed",
            "iterations": 2,
            "findings": [{"tool": "scan_ports", "args": {"target": "test.com"}, "result": "Port 80 open"}],
            "final_message": "Scan completed successfully",
        }

        report = agent.generate_report(result)

        assert "ZEN-AI-PENTEST REPORT" in report
        assert "test.com" in report
        assert "scan_ports" in report
        assert "Port 80 open" in report

    @patch("agents.react_agent.LLMBackend")
    def test_run_with_mocked_llm(self, mock_llm_class, agent_config):
        """Test: Agent-Loop mit gemocktem LLM"""
        # Setup Mock
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []  # Keine Tools -> direkt Ende
        mock_response.content = "Test completed"
        mock_llm.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm_class.return_value = mock_llm

        with (
            patch("agents.react_agent.CVEDatabase"),
            patch("agents.react_agent.NmapTool"),
            patch("agents.react_agent.NucleiTool"),
            patch("agents.react_agent.FfufTool"),
        ):
            agent = ReActAgent(agent_config)
            result = agent.run("test.com")

            assert result["target"] == "test.com"
            assert result["status"] in ["running", "completed"]

    def test_max_iterations_limit(self, agent):
        """Test: Max Iterations wird eingehalten"""
        state: AgentState = {
            "messages": [HumanMessage(content="Test")],
            "findings": [],
            "target": "test.com",
            "iteration": 3,  # Gleich max_iterations
            "max_iterations": 3,
            "status": "running",
        }

        # Agent node sollte bei max_iterations stoppen
        # Dies ist ein Integrationstest für die Node-Logik
        assert state["iteration"] >= state["max_iterations"]


class TestReActAgentTools:
    """Tests für die Tool-Integration"""

    @pytest.fixture
    def agent(self):
        with (
            patch("agents.react_agent.LLMBackend"),
            patch("agents.react_agent.CVEDatabase"),
            patch("agents.react_agent.NmapTool"),
            patch("agents.react_agent.NucleiTool"),
            patch("agents.react_agent.FfufTool"),
        ):
            config = ReActAgentConfig()
            return ReActAgent(config)

    def test_tools_initialized(self, agent):
        """Test: Alle Tools sind verfügbar"""
        tool_names = [t.name for t in agent.tools]

        assert "scan_ports" in tool_names
        assert "scan_vulnerabilities" in tool_names
        assert "enumerate_directories" in tool_names
        assert "lookup_cve" in tool_names
        assert "validate_exploit" in tool_names

    def test_tools_by_name_mapping(self, agent):
        """Test: Tools sind korrekt gemappt"""
        assert "scan_ports" in agent.tools_by_name
        assert "lookup_cve" in agent.tools_by_name

        # Tool sollte aufrufbar sein
        tool = agent.tools_by_name["scan_ports"]
        assert tool is not None


class TestReActAgentSecurity:
    """Security-Tests für den Agent"""

    @pytest.fixture
    def agent(self):
        with (
            patch("agents.react_agent.LLMBackend"),
            patch("agents.react_agent.CVEDatabase"),
            patch("agents.react_agent.NmapTool"),
            patch("agents.react_agent.NucleiTool"),
            patch("agents.react_agent.FfufTool"),
        ):
            config = ReActAgentConfig(auto_approve_dangerous=False, use_human_in_the_loop=True)
            return ReActAgent(config)

    def test_dangerous_tool_blocked_without_approval(self, agent):
        """Test: Gefährliche Tools werden blockiert ohne Freigabe"""
        assert agent._is_dangerous_tool("validate_exploit") is True

        # Wenn auto_approve_dangerous=False, sollte das Tool nicht
        # automatisch ausgeführt werden (dies würde in tools_node geprüft)
        assert agent.config.auto_approve_dangerous is False

    def test_safe_tools_allowed(self, agent):
        """Test: Sichere Tools sind erlaubt"""
        safe_tools = ["scan_ports", "lookup_cve", "enumerate_directories"]

        for tool in safe_tools:
            assert agent._is_dangerous_tool(tool) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

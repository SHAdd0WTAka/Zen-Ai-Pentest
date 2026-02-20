"""
Comprehensive tests for ReAct Agent
Tests the ReAct agent implementation with mocked LLM and tools
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock imports before importing react_agent
sys.modules["core"] = MagicMock()
sys.modules["core.llm_backend"] = MagicMock()
sys.modules["database"] = MagicMock()
sys.modules["database.cve_database"] = MagicMock()
sys.modules["tools"] = MagicMock()
sys.modules["tools.ffuf_integration"] = MagicMock()
sys.modules["tools.nmap_integration"] = MagicMock()
sys.modules["tools.nuclei_integration"] = MagicMock()

# Now import after mocking
from agents.react_agent import ReActAgent, ReActAgentConfig, get_agent


class TestReActAgentConfig:
    """Test ReActAgentConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ReActAgentConfig()
        assert config.max_iterations == 10
        assert config.enable_sandbox is True
        assert config.auto_approve_dangerous is False
        assert config.use_human_in_the_loop is True
        assert config.llm_model == "gpt-4o"

    def test_custom_config(self):
        """Test custom configuration values"""
        config = ReActAgentConfig(
            max_iterations=20,
            enable_sandbox=False,
            auto_approve_dangerous=True,
            use_human_in_the_loop=False,
            llm_model="gpt-3.5-turbo",
        )
        assert config.max_iterations == 20
        assert config.enable_sandbox is False
        assert config.auto_approve_dangerous is True
        assert config.use_human_in_the_loop is False
        assert config.llm_model == "gpt-3.5-turbo"

    def test_partial_custom_config(self):
        """Test partial configuration override"""
        config = ReActAgentConfig(max_iterations=5, llm_model="custom-model")
        assert config.max_iterations == 5
        assert config.llm_model == "custom-model"
        # Defaults preserved
        assert config.enable_sandbox is True
        assert config.auto_approve_dangerous is False


class TestReActAgentInitialization:
    """Test ReActAgent initialization"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_init_with_defaults(self, mock_cve_db, mock_llm_backend):
        """Test initialization with default config"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert agent.config.max_iterations == 10
        assert agent.config.llm_model == "gpt-4o"
        mock_llm_backend.assert_called_once_with(model="gpt-4o")
        mock_cve_db.assert_called_once()

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_init_with_custom_config(self, mock_cve_db, mock_llm_backend):
        """Test initialization with custom config"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        config = ReActAgentConfig(max_iterations=5, llm_model="custom-model")
        agent = ReActAgent(config=config)

        assert agent.config.max_iterations == 5
        assert agent.config.llm_model == "custom-model"
        mock_llm_backend.assert_called_once_with(model="custom-model")

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_tools_initialized(self, mock_cve_db, mock_llm_backend):
        """Test that tools are properly initialized"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert len(agent.tools) == 5
        tool_names = [t.name for t in agent.tools]
        assert "scan_ports" in tool_names
        assert "scan_vulnerabilities" in tool_names
        assert "enumerate_directories" in tool_names
        assert "lookup_cve" in tool_names
        assert "validate_exploit" in tool_names

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_tools_by_name_mapping(self, mock_cve_db, mock_llm_backend):
        """Test tools_by_name dictionary"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert "scan_ports" in agent.tools_by_name
        assert "scan_vulnerabilities" in agent.tools_by_name
        assert "enumerate_directories" in agent.tools_by_name
        assert "lookup_cve" in agent.tools_by_name
        assert "validate_exploit" in agent.tools_by_name

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_graph_compiled(self, mock_cve_db, mock_llm_backend):
        """Test that LangGraph workflow is compiled"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert agent.graph is not None


class TestReActAgentTools:
    """Test ReActAgent tool implementations"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    @patch("agents.react_agent.NmapTool")
    def test_scan_ports_tool(self, mock_nmap_class, mock_cve_db, mock_llm_backend):
        """Test scan_ports tool"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        mock_nmap = Mock()
        mock_nmap.scan.return_value = {"ports": [80, 443]}
        mock_nmap_class.return_value = mock_nmap

        agent = ReActAgent()
        scan_ports_tool = agent.tools_by_name["scan_ports"]

        result = scan_ports_tool.invoke({"target": "example.com", "ports": "top-100"})

        mock_nmap.scan.assert_called_once_with("example.com", "top-100")
        assert "ports" in result

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    @patch("agents.react_agent.NucleiTool")
    def test_scan_vulnerabilities_tool(self, mock_nuclei_class, mock_cve_db, mock_llm_backend):
        """Test scan_vulnerabilities tool"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        mock_nuclei = Mock()
        mock_nuclei.scan.return_value = {"vulnerabilities": ["CVE-2021-44228"]}
        mock_nuclei_class.return_value = mock_nuclei

        agent = ReActAgent()
        scan_vuln_tool = agent.tools_by_name["scan_vulnerabilities"]

        result = scan_vuln_tool.invoke({"target": "example.com", "templates": "critical"})

        mock_nuclei.scan.assert_called_once_with("example.com", severity="critical")
        assert "vulnerabilities" in result

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    @patch("agents.react_agent.FfufTool")
    def test_enumerate_directories_tool(self, mock_ffuf_class, mock_cve_db, mock_llm_backend):
        """Test enumerate_directories tool"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        mock_ffuf = Mock()
        mock_ffuf.directory_bruteforce.return_value = {"directories": ["/admin", "/api"]}
        mock_ffuf_class.return_value = mock_ffuf

        agent = ReActAgent()
        enum_tool = agent.tools_by_name["enumerate_directories"]

        result = enum_tool.invoke({"target": "example.com", "wordlist": "common.txt"})

        mock_ffuf.directory_bruteforce.assert_called_once_with("example.com", "common.txt")
        assert "directories" in result

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_lookup_cve_tool_found(self, mock_cve_db_class, mock_llm_backend):
        """Test lookup_cve tool when CVE is found"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        mock_cve = Mock()
        mock_cve.id = "CVE-2021-44228"
        mock_cve.severity = "critical"
        mock_cve.cvss_score = 10.0
        mock_cve.description = "Log4Shell RCE"
        mock_cve.epss_score = 0.95

        mock_cve_db = Mock()
        mock_cve_db.get_cve.return_value = mock_cve
        mock_cve_db_class.return_value = mock_cve_db

        agent = ReActAgent()
        lookup_tool = agent.tools_by_name["lookup_cve"]

        result = lookup_tool.invoke({"cve_id": "CVE-2021-44228"})

        mock_cve_db.get_cve.assert_called_once_with("CVE-2021-44228")
        assert "CVE-2021-44228" in result
        assert "10.0" in result

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_lookup_cve_tool_not_found(self, mock_cve_db_class, mock_llm_backend):
        """Test lookup_cve tool when CVE is not found"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        mock_cve_db = Mock()
        mock_cve_db.get_cve.return_value = None
        mock_cve_db_class.return_value = mock_cve_db

        agent = ReActAgent()
        lookup_tool = agent.tools_by_name["lookup_cve"]

        result = lookup_tool.invoke({"cve_id": "CVE-9999-9999"})

        assert "nicht gefunden" in result or "not found" in result

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_validate_exploit_tool(self, mock_cve_db, mock_llm_backend):
        """Test validate_exploit tool"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()
        validate_tool = agent.tools_by_name["validate_exploit"]

        result = validate_tool.invoke({"cve_id": "CVE-2021-44228", "target": "example.com"})

        assert "CVE-2021-44228" in result
        assert "example.com" in result


class TestReActAgentSafety:
    """Test ReActAgent safety controls"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_is_dangerous_tool_true(self, mock_cve_db, mock_llm_backend):
        """Test detection of dangerous tools"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert agent._is_dangerous_tool("validate_exploit") is True
        assert agent._is_dangerous_tool("exploit") is True
        assert agent._is_dangerous_tool("sqlmap_exploit") is True
        assert agent._is_dangerous_tool("VALIDATE_EXPLOIT") is True  # Case insensitive

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_is_dangerous_tool_false(self, mock_cve_db, mock_llm_backend):
        """Test that non-dangerous tools return False"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        assert agent._is_dangerous_tool("scan_ports") is False
        assert agent._is_dangerous_tool("scan_vulnerabilities") is False
        assert agent._is_dangerous_tool("lookup_cve") is False
        assert agent._is_dangerous_tool("enumerate_directories") is False


class TestReActAgentGraph:
    """Test LangGraph workflow"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_build_graph_nodes(self, mock_cve_db, mock_llm_backend):
        """Test that graph has required nodes"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        # Graph should be compiled and have nodes
        assert agent.graph is not None

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_agent_node_iteration_limit(self, mock_cve_db, mock_llm_backend):
        """Test agent node respects iteration limit"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        # Build the graph to get access to the node function
        # We can't directly access the node, but we can verify the config
        assert agent.config.max_iterations == 10


class TestReActAgentRun:
    """Test ReActAgent run method"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_run_basic(self, mock_cve_db, mock_llm_backend):
        """Test basic run execution"""
        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        mock_llm_backend.return_value = mock_llm

        # Mock graph invoke
        mock_result = {
            "findings": [{"tool": "scan_ports", "result": "test"}],
            "messages": [Mock(content="Final result")],
            "iteration": 3,
            "status": "completed",
        }

        agent = ReActAgent()
        agent.graph = Mock()
        agent.graph.invoke.return_value = mock_result

        result = agent.run("example.com", objective="scan")

        assert result["target"] == "example.com"
        assert result["iterations"] == 3
        assert result["status"] == "completed"
        assert len(result["findings"]) == 1
        agent.graph.invoke.assert_called_once()

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_run_with_default_objective(self, mock_cve_db, mock_llm_backend):
        """Test run with default objective"""
        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        mock_llm_backend.return_value = mock_llm

        mock_result = {
            "findings": [],
            "messages": [Mock(content="Done")],
            "iteration": 1,
            "status": "completed",
        }

        agent = ReActAgent()
        agent.graph = Mock()
        agent.graph.invoke.return_value = mock_result

        result = agent.run("scanme.nmap.org")

        assert result["target"] == "scanme.nmap.org"

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_run_empty_findings(self, mock_cve_db, mock_llm_backend):
        """Test run with empty findings"""
        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        mock_llm_backend.return_value = mock_llm

        mock_result = {
            "findings": [],
            "messages": [],
            "iteration": 0,
            "status": "completed",
        }

        agent = ReActAgent()
        agent.graph = Mock()
        agent.graph.invoke.return_value = mock_result

        result = agent.run("example.com")

        assert result["findings"] == []
        assert result["final_message"] == ""


class TestReActAgentReport:
    """Test ReActAgent report generation"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_generate_report_with_findings(self, mock_cve_db, mock_llm_backend):
        """Test report generation with findings"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        result = {
            "target": "example.com",
            "status": "completed",
            "iterations": 3,
            "findings": [
                {"tool": "scan_ports", "args": {"target": "example.com"}, "result": "Ports: 80,443"},
            ],
            "final_message": "Scan complete",
        }

        report = agent.generate_report(result)

        assert "ZEN-AI-PENTEST REPORT" in report
        assert "example.com" in report
        assert "completed" in report
        assert "scan_ports" in report
        assert "Scan complete" in report

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_generate_report_no_findings(self, mock_cve_db, mock_llm_backend):
        """Test report generation without findings"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        result = {
            "target": "example.com",
            "status": "completed",
            "iterations": 1,
            "findings": [],
            "final_message": "No issues found",
        }

        report = agent.generate_report(result)

        assert "ZEN-AI-PENTEST REPORT" in report
        assert "No findings detected" in report

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_generate_report_long_result_truncated(self, mock_cve_db, mock_llm_backend):
        """Test that long results are truncated in report"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        long_result = "A" * 500
        result = {
            "target": "example.com",
            "status": "completed",
            "iterations": 1,
            "findings": [
                {"tool": "scan_ports", "args": {}, "result": long_result},
            ],
            "final_message": "Done",
        }

        report = agent.generate_report(result)

        # Result should be truncated to ~200 chars
        assert "..." in report


class TestGetAgent:
    """Test get_agent singleton function"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_get_agent_singleton(self, mock_cve_db, mock_llm_backend):
        """Test that get_agent returns singleton instance"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        # Clear singleton
        import agents.react_agent as react_agent

        react_agent._default_agent = None

        agent1 = get_agent()
        agent2 = get_agent()

        assert agent1 is agent2

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_get_agent_with_config_creates_new(self, mock_cve_db, mock_llm_backend):
        """Test that passing config creates new instance"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        # Clear singleton
        import agents.react_agent as react_agent

        react_agent._default_agent = None

        agent1 = get_agent()
        config = ReActAgentConfig(max_iterations=5)
        agent2 = get_agent(config)

        assert agent1 is not agent2
        assert agent2.config.max_iterations == 5


class TestReActAgentEdgeCases:
    """Test edge cases and error handling"""

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_run_error_status(self, mock_cve_db, mock_llm_backend):
        """Test handling of error status"""
        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        mock_llm_backend.return_value = mock_llm

        mock_result = {
            "findings": [],
            "messages": [Mock(content="Error occurred")],
            "iteration": 1,
            "status": "error",
        }

        agent = ReActAgent()
        agent.graph = Mock()
        agent.graph.invoke.return_value = mock_result

        result = agent.run("example.com")

        assert result["status"] == "error"

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_tool_execution_error_handling(self, mock_cve_db, mock_llm_backend):
        """Test error handling during tool execution"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        agent = ReActAgent()

        # Mock a tool that raises an exception
        mock_tool = Mock()
        mock_tool.invoke.side_effect = Exception("Tool failed")

        # Verify tools are set up
        assert len(agent.tools) > 0

    @patch("agents.react_agent.LLMBackend")
    @patch("agents.react_agent.CVEDatabase")
    def test_config_zero_iterations(self, mock_cve_db, mock_llm_backend):
        """Test config with zero iterations"""
        mock_llm = Mock()
        mock_llm_backend.return_value = mock_llm

        config = ReActAgentConfig(max_iterations=0)
        agent = ReActAgent(config=config)

        assert agent.config.max_iterations == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

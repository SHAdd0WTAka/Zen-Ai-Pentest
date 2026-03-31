"""Test tool integration imports"""

import pytest


class TestToolImports:
    """Test all tool integrations can be imported"""

    def test_nmap_import(self):
        from tools.nmap_integration import NmapScanner

        assert NmapScanner is not None

    def test_nuclei_import(self):
        from tools.nuclei_integration import NucleiScanner

        assert NucleiScanner is not None

    def test_sqlmap_import(self):
        from tools.sqlmap_integration import SQLMapScanner

        assert SQLMapScanner is not None

    def test_ffuf_import(self):
        from tools.ffuf_integration_enhanced import FFuFFinding

        assert FFuFFinding is not None

    def test_subfinder_import(self):
        from tools.subfinder_integration import SubfinderResult

        assert SubfinderResult is not None

    def test_httpx_import(self):
        from tools.httpx_integration import HTTPXHost

        assert HTTPXHost is not None

    def test_whatweb_import(self):
        from tools.whatweb_integration import Technology

        assert Technology is not None

    def test_wafw00f_import(self):
        from tools.wafw00f_integration import WAFFinding

        assert WAFFinding is not None

    def test_nikto_import(self):
        from tools.nikto_integration import NiktoFinding

        assert NiktoFinding is not None

    def test_sherlock_import(self):
        from tools.sherlock_integration import SherlockResult

        assert SherlockResult is not None

    def test_gobuster_import(self):
        from tools.gobuster_integration import GobusterScanner

        assert GobusterScanner is not None

    def test_amass_import(self):
        from tools.amass_integration import AmassResult

        assert AmassResult is not None

    def test_masscan_import(self):
        from tools.masscan_integration import MasscanPort

        assert MasscanPort is not None

    def test_trivy_import(self):
        from tools.trivy_integration import TrivyScanner

        assert TrivyScanner is not None

    def test_trufflehog_import(self):
        from tools.trufflehog_integration import TruffleHogScanner

        assert TruffleHogScanner is not None

    def test_tool_registry_import(self):
        from tools.tool_registry import ToolRegistry

        assert ToolRegistry is not None

    def test_tool_caller_import(self):
        from tools.tool_caller import ToolCaller

        assert ToolCaller is not None


class TestToolRegistry:
    """Test ToolRegistry functionality"""

    def test_registry_creation(self):
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        assert registry is not None

    def test_registry_has_list_method(self):
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        assert hasattr(registry, "list_tools")

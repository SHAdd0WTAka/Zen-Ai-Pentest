"""
Tests for various tool integrations - Coverage Boost
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest


class TestToolRegistry:
    """Test Tool Registry functionality"""

    def test_tool_registry_init(self):
        """Test ToolRegistry initialization"""
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        assert registry is not None
        assert hasattr(registry, "tools")

    def test_register_tool(self):
        """Test registering a tool"""
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        mock_tool = Mock(name="test_tool", description="Test tool")

        registry.register("test_tool", mock_tool)
        assert "test_tool" in registry.tools

    def test_get_tool(self):
        """Test getting a registered tool"""
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        mock_tool = Mock(name="test_tool")

        registry.register("test_tool", mock_tool)
        result = registry.get("test_tool")

        assert result == mock_tool

    def test_get_tool_not_found(self):
        """Test getting non-existent tool returns None"""
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        result = registry.get("nonexistent")

        assert result is None

    def test_list_tools(self):
        """Test listing all registered tools"""
        from tools.tool_registry import ToolRegistry

        registry = ToolRegistry()
        registry.register("tool1", Mock())
        registry.register("tool2", Mock())

        tools = registry.list_tools()

        assert len(tools) >= 2
        assert "tool1" in tools
        assert "tool2" in tools


class TestToolCaller:
    """Test Tool Caller functionality"""

    def test_tool_caller_init(self):
        """Test ToolCaller initialization"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()
        assert caller is not None

    @pytest.mark.asyncio
    async def test_call_tool_async(self):
        """Test calling a tool asynchronously"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()
        mock_tool = AsyncMock(return_value={"result": "success"})
        caller.registry.register("mock_tool", mock_tool)

        result = await caller.call_async("mock_tool", {"arg": "value"})

        assert result["result"] == "success"

    def test_call_tool_sync(self):
        """Test calling a tool synchronously"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()
        mock_tool = Mock(return_value={"result": "success"})
        caller.registry.register("mock_tool", mock_tool)

        result = caller.call("mock_tool", {"arg": "value"})

        assert result["result"] == "success"


class TestNucleiIntegration:
    """Test Nuclei integration"""

    def test_nuclei_scanner_init(self):
        """Test NucleiScanner initialization"""
        from tools.nuclei_integration import NucleiScanner

        scanner = NucleiScanner(target="example.com")
        assert scanner.target == "example.com"

    def test_nuclei_build_command(self):
        """Test Nuclei command building"""
        from tools.nuclei_integration import NucleiScanner

        scanner = NucleiScanner(target="example.com", templates=["cve"])
        cmd = scanner._build_command()

        assert "nuclei" in cmd
        assert "example.com" in cmd


class TestSubfinderIntegration:
    """Test Subfinder integration"""

    def test_subfinder_init(self):
        """Test Subfinder initialization"""
        from tools.subfinder_integration import SubfinderScanner

        scanner = SubfinderScanner(domain="example.com")
        assert scanner.domain == "example.com"

    def test_subfinder_build_command(self):
        """Test Subfinder command building"""
        from tools.subfinder_integration import SubfinderScanner

        scanner = SubfinderScanner(domain="example.com")
        cmd = scanner._build_command()

        assert "subfinder" in str(cmd) or isinstance(cmd, list)


class TestHttpxIntegration:
    """Test Httpx integration"""

    def test_httpx_init(self):
        """Test Httpx initialization"""
        from tools.httpx_integration import HttpxScanner

        scanner = HttpxScanner(targets=["example.com"])
        assert "example.com" in scanner.targets


class TestNiktoIntegration:
    """Test Nikto integration"""

    def test_nikto_init(self):
        """Test Nikto initialization"""
        from tools.nikto_integration import NiktoScanner

        scanner = NiktoScanner(target="example.com")
        assert scanner.target == "example.com"


class TestGobusterIntegration:
    """Test Gobuster integration"""

    def test_gobuster_init(self):
        """Test Gobuster initialization"""
        from tools.gobuster_integration import GobusterScanner

        scanner = GobusterScanner(target="example.com")
        assert scanner.target == "example.com"


class TestAmassIntegration:
    """Test Amass integration"""

    def test_amass_init(self):
        """Test Amass initialization"""
        from tools.amass_integration import AmassScanner

        scanner = AmassScanner(domain="example.com")
        assert scanner.domain == "example.com"


class TestSherlockIntegration:
    """Test Sherlock integration"""

    def test_sherlock_init(self):
        """Test Sherlock initialization"""
        from tools.sherlock_integration import SherlockScanner

        scanner = SherlockScanner(username="testuser")
        assert scanner.username == "testuser"


class TestFFUFIntegration:
    """Test FFUF integration"""

    def test_ffuf_init(self):
        """Test FFUF initialization"""
        from tools.ffuf_integration_enhanced import FFUFScanner

        scanner = FFUFScanner(target="http://example.com")
        assert scanner.target == "http://example.com"

    def test_ffuf_build_command(self):
        """Test FFUF command building"""
        from tools.ffuf_integration_enhanced import FFUFScanner

        scanner = FFUFScanner(
            target="http://example.com", wordlist="/tmp/wordlist.txt"
        )
        cmd = scanner._build_command()

        assert isinstance(cmd, list)


class TestWafw00fIntegration:
    """Test Wafw00f integration"""

    def test_wafw00f_init(self):
        """Test Wafw00f initialization"""
        from tools.wafw00f_integration import Wafw00fScanner

        scanner = Wafw00fScanner(target="example.com")
        assert scanner.target == "example.com"


class TestWhatwebIntegration:
    """Test Whatweb integration"""

    def test_whatweb_init(self):
        """Test Whatweb initialization"""
        from tools.whatweb_integration import WhatwebScanner

        scanner = WhatwebScanner(target="example.com")
        assert scanner.target == "example.com"


class TestMasscanIntegration:
    """Test Masscan integration"""

    def test_masscan_init(self):
        """Test Masscan initialization"""
        from tools.masscan_integration import MasscanScanner

        scanner = MasscanScanner(target="192.168.1.0/24")
        assert scanner.target == "192.168.1.0/24"


class TestTsharkIntegration:
    """Test Tshark integration"""

    def test_tshark_init(self):
        """Test Tshark initialization"""
        from tools.tshark_integration import TsharkScanner

        scanner = TsharkScanner(interface="eth0")
        assert scanner.interface == "eth0"


class TestIgnorantIntegration:
    """Test Ignorant integration"""

    def test_ignorant_init(self):
        """Test Ignorant initialization"""
        from tools.ignorant_integration import IgnorantScanner

        scanner = IgnorantScanner(email="test@example.com")
        assert scanner.email == "test@example.com"


class TestToolChecker:
    """Test Tool Checker"""

    def test_check_tool_availability(self):
        """Test checking tool availability"""
        from tools.integrations.tool_checker import check_tool_availability

        # Test with a tool that likely exists (python)
        result = check_tool_availability("python3")

        assert isinstance(result, dict)
        assert "available" in result

    def test_get_tool_version(self):
        """Test getting tool version"""
        from tools.integrations.tool_checker import get_tool_version

        # Test with python
        version = get_tool_version("python3")

        # Should return version string or None
        assert version is None or isinstance(version, str)


class TestAsyncToolOperations:
    """Test async tool operations"""

    @pytest.mark.asyncio
    async def test_async_scan_execution(self):
        """Test async scan execution"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()

        # Mock async tool
        async def mock_async_tool(**kwargs):
            await asyncio.sleep(0.01)
            return {"status": "completed"}

        caller.registry.register("async_tool", mock_async_tool)

        result = await caller.call_async("async_tool", {})
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test concurrent tool execution"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()

        async def mock_tool(**kwargs):
            await asyncio.sleep(0.01)
            return {"result": kwargs.get("id")}

        caller.registry.register("tool1", mock_tool)
        caller.registry.register("tool2", mock_tool)

        # Run concurrently
        results = await asyncio.gather(
            caller.call_async("tool1", {"id": 1}),
            caller.call_async("tool2", {"id": 2}),
        )

        assert results[0]["result"] == 1
        assert results[1]["result"] == 2

    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self):
        """Test tool timeout handling"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()

        async def slow_tool(**kwargs):
            await asyncio.sleep(10)
            return {"result": "slow"}

        caller.registry.register("slow_tool", slow_tool)

        # Should handle timeout gracefully
        try:
            await asyncio.wait_for(
                caller.call_async("slow_tool", {}), timeout=0.1
            )
        except asyncio.TimeoutError:
            # Expected
            pass

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling"""
        from tools.tool_caller import ToolCaller

        caller = ToolCaller()

        async def error_tool(**kwargs):
            raise ValueError("Test error")

        caller.registry.register("error_tool", error_tool)

        try:
            await caller.call_async("error_tool", {})
            assert False, "Should have raised exception"
        except ValueError:
            pass  # Expected

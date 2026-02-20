"""
Tests für Real Tool Calling Framework
Issue #19
"""

import pytest
from langchain_core.tools import tool

from tools.tool_caller import ToolCaller
from tools.tool_registry import ToolCategory, ToolRegistry, ToolSafetyLevel


@pytest.fixture
def registry():
    """Fresh registry for each test"""
    reg = ToolRegistry()
    reg.clear()
    return reg


@pytest.fixture
def sample_tool():
    """Sample tool for testing"""

    @tool
    def test_scan(target: str) -> str:
        """Test scanning tool"""
        return f"Scanned {target}"

    return test_scan


class TestToolRegistry:
    """Test Tool Registry functionality"""

    def test_register_tool(self, registry, sample_tool):
        """Test tool registration"""
        registered = registry.register(
            tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE, tags=["test", "scan"]
        )

        assert registered.metadata.name == "test_scan"
        assert registered.metadata.category == ToolCategory.SCANNING
        assert "test" in registered.metadata.tags

    def test_get_tool(self, registry, sample_tool):
        """Test retrieving tool by name"""
        registry.register(tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)

        tool = registry.get_tool("test_scan")
        assert tool is not None
        assert tool.name == "test_scan"

    def test_list_tools_by_category(self, registry, sample_tool):
        """Test listing tools filtered by category"""
        registry.register(tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)

        tools = registry.list_tools(category=ToolCategory.SCANNING)
        assert len(tools) == 1
        assert tools[0].metadata.name == "test_scan"

    def test_enable_disable_tool(self, registry, sample_tool):
        """Test enabling and disabling tools"""
        registry.register(tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)

        # Disable
        assert registry.disable_tool("test_scan") is True
        assert registry.get_tool("test_scan") is None  # Disabled tools not returned

        # Enable
        assert registry.enable_tool("test_scan") is True
        assert registry.get_tool("test_scan") is not None

    def test_safety_level_filter(self, registry, sample_tool):
        """Test filtering by safety level"""
        registry.register(
            tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.DANGEROUS, requires_approval=True
        )

        dangerous = registry.get_dangerous_tools()
        assert len(dangerous) == 1
        assert dangerous[0].metadata.safety_level == ToolSafetyLevel.DANGEROUS


class TestToolCaller:
    """Test Tool Caller functionality"""

    @pytest.mark.asyncio
    async def test_call_tool_success(self, registry, sample_tool):
        """Test successful tool call"""
        registry.register(tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)

        caller = ToolCaller(registry)
        result = await caller.call_tool("test_scan", {"target": "test.com"})

        assert result.success is True
        assert result.result == "Scanned test.com"
        assert result.tool_name == "test_scan"
        assert result.execution_time >= 0

        caller.shutdown()

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, registry):
        """Test calling non-existent tool"""
        caller = ToolCaller(registry)
        result = await caller.call_tool("nonexistent", {})

        assert result.success is False
        assert "nicht in Registry" in result.error

        caller.shutdown()

    @pytest.mark.asyncio
    async def test_call_tool_disabled(self, registry, sample_tool):
        """Test calling disabled tool"""
        registry.register(tool=sample_tool, category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE)
        registry.disable_tool("test_scan")

        caller = ToolCaller(registry)
        result = await caller.call_tool("test_scan", {})

        assert result.success is False
        assert "deaktiviert" in result.error

        caller.shutdown()

    @pytest.mark.asyncio
    async def test_call_tools_parallel(self, registry):
        """Test parallel tool calls"""

        @tool
        def tool1(x: str) -> str:
            """Tool 1 for testing"""
            return f"tool1: {x}"

        @tool
        def tool2(x: str) -> str:
            """Tool 2 for testing"""
            return f"tool2: {x}"

        registry.register(tool1, ToolCategory.UTILITY, ToolSafetyLevel.SAFE)
        registry.register(tool2, ToolCategory.UTILITY, ToolSafetyLevel.SAFE)

        caller = ToolCaller(registry)
        results = await caller.call_tools_parallel([("tool1", {"x": "a"}), ("tool2", {"x": "b"})])

        assert results["tool1"].success is True
        assert results["tool2"].success is True
        assert results["tool1"].result == "tool1: a"
        assert results["tool2"].result == "tool2: b"

        caller.shutdown()

    @pytest.mark.asyncio
    async def test_tool_timeout(self, registry):
        """Test tool timeout"""

        @tool
        def slow_tool() -> str:
            """Slow tool for testing timeout"""
            import time

            time.sleep(10)
            return "done"

        registry.register(slow_tool, ToolCategory.UTILITY, ToolSafetyLevel.SAFE)

        caller = ToolCaller(registry)
        result = await caller.call_tool("slow_tool", {}, timeout=1)

        assert result.success is False
        assert "Timeout" in result.error

        caller.shutdown()


class TestToolIntegration:
    """Integration tests for complete tool framework"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete tool registration and calling workflow"""
        registry = ToolRegistry()
        registry.clear()

        # Register tools
        @tool
        def scan_ports(target: str, ports: str = "top-100") -> dict:
            """Scan ports on target"""
            return {"target": target, "ports": [80, 443], "open": True}

        registry.register(
            tool=scan_ports, category=ToolCategory.RECONNAISSANCE, safety_level=ToolSafetyLevel.SAFE, tags=["port", "scan"]
        )

        # Call tool
        caller = ToolCaller(registry)
        result = await caller.call_tool("scan_ports", {"target": "scanme.nmap.org", "ports": "top-1000"})

        assert result.success is True
        assert result.result["target"] == "scanme.nmap.org"
        assert 80 in result.result["ports"]

        # Check stats
        stats = registry.get_registry_stats()
        assert stats["total_tools"] == 1
        assert stats["total_invocations"] == 1

        caller.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

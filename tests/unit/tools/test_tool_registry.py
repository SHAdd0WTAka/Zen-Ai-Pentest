"""
Tool Registry Tests
Target: 80%+ Coverage for tools module components
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestToolRegistry:
    """Test tool registry functionality"""

    def test_tool_registry_import(self):
        """Test that tool registry can be imported"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()
        assert registry is not None

    def test_tool_registry_singleton(self):
        """Test that tool registry is a singleton"""
        from core.tool_registry import ToolRegistry

        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2

    def test_register_tool(self):
        """Test registering a tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        tool_def = {
            "name": "test_tool",
            "category": "test",
            "description": "Test tool",
            "handler": lambda: "test",
        }

        registry.register("test_tool", tool_def)
        assert "test_tool" in registry.tools

    def test_get_tool(self):
        """Test getting a tool from registry"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        tool_def = {
            "name": "test_tool",
            "category": "test",
            "description": "Test tool",
            "handler": lambda: "test",
        }

        registry.register("test_tool", tool_def)
        retrieved = registry.get("test_tool")

        assert retrieved is not None
        assert retrieved["name"] == tool_def["name"]
        assert retrieved["category"] == tool_def["category"]

    def test_get_nonexistent_tool(self):
        """Test getting a non-existent tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        result = registry.get("nonexistent")
        assert result is None

    def test_list_tools(self):
        """Test listing all tools"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Register some tools
        registry.register("tool1", {"category": "cat1"})
        registry.register("tool2", {"category": "cat2"})
        registry.register("tool3", {"category": "cat1"})

        tools = registry.list_tools()
        assert len(tools) >= 3

    def test_list_tools_by_category(self):
        """Test listing tools filtered by category"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        registry.register("tool1", {"category": "network"})
        registry.register("tool2", {"category": "web"})
        registry.register("tool3", {"category": "network"})

        network_tools = registry.list_tools(category="network")
        for tool in network_tools:
            assert tool.get("category") == "network"

    def test_unregister_tool(self):
        """Test unregistering a tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        registry.register("temp_tool", {"category": "test"})
        assert "temp_tool" in registry.tools

        registry.unregister("temp_tool")
        assert "temp_tool" not in registry.tools


class TestToolMetadata:
    """Test tool metadata handling"""

    def test_tool_metadata_validation(self):
        """Test tool metadata validation"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Valid metadata
        valid_tool = {
            "name": "valid_tool",
            "category": "network",
            "description": "A valid tool",
            "version": "1.0.0",
            "author": "Test Author",
            "safe": True,
        }

        assert registry.validate_tool_def(valid_tool) is True

    def test_tool_metadata_missing_fields(self):
        """Test validation with missing required fields"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Missing required fields
        invalid_tool = {
            "name": "invalid_tool"
            # Missing category and description
        }

        assert registry.validate_tool_def(invalid_tool) is False

    def test_tool_safety_level(self):
        """Test tool safety level classification"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        safe_tool = {"name": "safe", "safe": True}
        unsafe_tool = {"name": "unsafe", "safe": False}

        registry.register("safe", safe_tool)
        registry.register("unsafe", unsafe_tool)

        assert registry.is_tool_safe("safe") is True
        assert registry.is_tool_safe("unsafe") is False


class TestToolExecution:
    """Test tool execution through registry"""

    @pytest.mark.asyncio
    async def test_execute_registered_tool(self):
        """Test executing a registered tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        async def mock_handler(params):
            return {"result": "success", "params": params}

        registry.register(
            "mock_tool",
            {
                "name": "mock_tool",
                "category": "test",
                "handler": mock_handler,
                "async": True,
            },
        )

        result = await registry.execute("mock_tool", {"target": "example.com"})
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a non-existent tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        with pytest.raises(Exception):
            await registry.execute("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self):
        """Test executing a tool that raises an error"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        async def failing_handler(params):
            raise ValueError("Tool failed")

        registry.register(
            "failing_tool",
            {
                "name": "failing_tool",
                "category": "test",
                "handler": failing_handler,
                "async": True,
            },
        )

        with pytest.raises(ValueError):
            await registry.execute("failing_tool", {})

    def test_sync_tool_execution(self):
        """Test executing a synchronous tool"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        def sync_handler(params):
            return {"result": "sync_success"}

        registry.register(
            "sync_tool",
            {
                "name": "sync_tool",
                "category": "test",
                "handler": sync_handler,
                "async": False,
            },
        )

        result = registry.execute_sync("sync_tool", {})
        assert result["result"] == "sync_success"


class TestToolCategories:
    """Test tool categorization"""

    def test_get_categories(self):
        """Test getting all tool categories"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        registry.register("tool1", {"category": "network"})
        registry.register("tool2", {"category": "web"})
        registry.register("tool3", {"category": "recon"})

        categories = registry.get_categories()
        assert "network" in categories
        assert "web" in categories
        assert "recon" in categories

    def test_tools_in_category(self):
        """Test getting tools in a specific category"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        registry.register("nmap", {"category": "network"})
        registry.register("masscan", {"category": "network"})
        registry.register("sqlmap", {"category": "web"})

        network_tools = registry.get_tools_in_category("network")
        assert len(network_tools) >= 2
        assert all(t["category"] == "network" for t in network_tools)


class TestToolDependencies:
    """Test tool dependency handling"""

    def test_tool_with_dependencies(self):
        """Test registering a tool with dependencies"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        tool_def = {
            "name": "dependent_tool",
            "category": "test",
            "dependencies": ["nmap", "python-nmap"],
            "handler": lambda: "test",
        }

        registry.register("dependent_tool", tool_def)

        deps = registry.get_dependencies("dependent_tool")
        assert "nmap" in deps
        assert "python-nmap" in deps

    def test_check_dependencies(self):
        """Test dependency checking"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        # Mock dependency check
        registry.register(
            "tool_with_deps",
            {"category": "test", "dependencies": ["existing_dep"]},
        )

        # Check should return True for satisfied dependencies
        # or list of missing dependencies
        result = registry.check_dependencies("tool_with_deps")
        assert isinstance(result, (bool, list))


class TestToolVersioning:
    """Test tool versioning"""

    def test_tool_version(self):
        """Test tool version tracking"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        registry.register("versioned_tool", {"category": "test", "version": "2.1.0"})

        version = registry.get_tool_version("versioned_tool")
        assert version == "2.1.0"

    def test_tool_version_comparison(self):
        """Test comparing tool versions"""
        from core.tool_registry import ToolRegistry

        registry = ToolRegistry()

        assert registry.compare_versions("1.0.0", "2.0.0") < 0
        assert registry.compare_versions("2.0.0", "1.0.0") > 0
        assert registry.compare_versions("1.0.0", "1.0.0") == 0

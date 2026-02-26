"""
Comprehensive Tests for Tool Registry Module
Target: 80%+ Coverage
"""

import sys
from unittest.mock import MagicMock, patch

# Mock langchain_core before importing the module
mock_base_tool = MagicMock()
mock_base_tool.name = "mock_tool"
mock_base_tool.description = "Mock tool description"

mock_langchain = MagicMock()
mock_langchain.BaseTool = mock_base_tool
mock_langchain.Tool = MagicMock(return_value=MagicMock(name="mock_tool", description="Mock tool"))

sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.tools'] = mock_langchain

import pytest

sys.path.insert(0, "/home/atakan/zen-ai-pentest")

from tools.tool_registry import (
    ToolCategory,
    ToolMetadata,
    ToolRegistry,
    RegisteredTool,
    ToolSafetyLevel,
    BaseTool,
)


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name="mock_tool"):
        self._name = name
        
    @property
    def name(self):
        return self._name
        
    @property
    def description(self):
        return f"Description for {self._name}"
        
    def _run(self, query: str) -> str:
        return f"Result for {query}"
        
    async def _arun(self, query: str) -> str:
        return self._run(query)


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_all_categories_exist(self):
        """Test all tool categories are defined."""
        categories = list(ToolCategory)
        assert len(categories) > 0
        for cat in categories:
            assert isinstance(cat, ToolCategory)

    def test_category_values(self):
        """Test category has string values."""
        assert ToolCategory.RECONNAISSANCE.value == "reconnaissance"
        assert ToolCategory.SCANNING.value == "scanning"
        assert ToolCategory.EXPLOITATION.value == "exploitation"


class TestToolSafetyLevel:
    """Tests for ToolSafetyLevel enum."""

    def test_all_safety_levels_exist(self):
        """Test all safety levels are defined."""
        levels = list(ToolSafetyLevel)
        assert len(levels) > 0
        for level in levels:
            assert isinstance(level, ToolSafetyLevel)


class TestToolMetadata:
    """Tests for ToolMetadata dataclass."""

    def test_basic_creation(self):
        """Test basic ToolMetadata creation."""
        tool = ToolMetadata(
            name="nmap",
            description="Network scanner",
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
        )
        assert tool.name == "nmap"
        assert tool.description == "Network scanner"
        assert tool.category == ToolCategory.RECONNAISSANCE
        assert tool.safety_level == ToolSafetyLevel.SAFE

    def test_full_creation(self):
        """Test ToolMetadata with all fields."""
        tool = ToolMetadata(
            name="sqlmap",
            description="SQL injection tool",
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
        )
        assert tool.category == ToolCategory.EXPLOITATION
        assert tool.safety_level == ToolSafetyLevel.DANGEROUS


class TestRegisteredTool:
    """Tests for RegisteredTool dataclass."""

    def test_creation(self):
        """Test RegisteredTool creation."""
        mock_tool = MockTool()
        metadata = ToolMetadata(
            name="test",
            description="Test tool",
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        reg = RegisteredTool(
            tool=mock_tool,
            metadata=metadata,
            enabled=True,
        )
        assert reg.metadata.name == "test"
        assert reg.enabled is True


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_singleton_pattern(self):
        """Test registry is singleton."""
        reg1 = ToolRegistry()
        reg2 = ToolRegistry()
        assert reg1 is reg2

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        mock_tool = MockTool("test_tool")
        
        result = registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        assert result is not None
        assert result.metadata.name == "test_tool"

    def test_get_nonexistent(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        result = registry.get("nonexistent_tool_xyz")
        assert result is None

    def test_get_tool_alias(self):
        """Test get_tool is alias for get."""
        registry = ToolRegistry()
        mock_tool = MockTool("alias_test")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        result1 = registry.get("alias_test")
        result2 = registry.get_tool("alias_test")
        assert result1 == result2

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert isinstance(tools, list)

    def test_get_all_tools(self):
        """Test getting all tools."""
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        assert isinstance(tools, list)

    def test_get_tools_by_category(self):
        """Test getting tools by category."""
        registry = ToolRegistry()
        mock_tool = MockTool("cat_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        tools = registry.get_tools_by_category(ToolCategory.RECONNAISSANCE)
        assert isinstance(tools, list)

    def test_enable_disable_tool(self):
        """Test enabling and disabling tools."""
        registry = ToolRegistry()
        mock_tool = MockTool("toggle_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        registry.disable_tool("toggle_tool")
        tool = registry.get("toggle_tool")
        assert tool.enabled is False
        
        registry.enable_tool("toggle_tool")
        tool = registry.get("toggle_tool")
        assert tool.enabled is True

    def test_unregister(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        mock_tool = MockTool("remove_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        assert registry.get("remove_tool") is not None
        registry.unregister("remove_tool")
        assert registry.get("remove_tool") is None

    def test_clear(self):
        """Test clearing all tools."""
        registry = ToolRegistry()
        mock_tool = MockTool("temp_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        registry.clear()
        assert registry.get("temp_tool") is None

    def test_get_safe_tools(self):
        """Test getting safe tools."""
        registry = ToolRegistry()
        mock_tool = MockTool("safe_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        safe_tools = registry.get_safe_tools()
        assert isinstance(safe_tools, list)

    def test_get_dangerous_tools(self):
        """Test getting dangerous tools."""
        registry = ToolRegistry()
        mock_tool = MockTool("dangerous_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
        )
        
        dangerous_tools = registry.get_dangerous_tools()
        assert isinstance(dangerous_tools, list)

    def test_record_invocation(self):
        """Test recording tool invocation."""
        registry = ToolRegistry()
        mock_tool = MockTool("record_tool")
        registry.register(
            tool=mock_tool,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )
        
        registry.record_invocation("record_tool", 1.5)
        tool = registry.get("record_tool")
        assert tool.metadata.invocation_count >= 1

    def test_get_registry_stats(self):
        """Test getting registry statistics."""
        registry = ToolRegistry()
        stats = registry.get_registry_stats()
        assert isinstance(stats, dict)
        assert "total_tools" in stats


class TestToolRegistryIntegration:
    """Integration tests for ToolRegistry."""

    def test_full_workflow(self):
        """Test full tool registration workflow."""
        registry = ToolRegistry()
        
        # Register multiple tools
        tools = [
            ("nmap", ToolCategory.RECONNAISSANCE, ToolSafetyLevel.SAFE),
            ("sqlmap", ToolCategory.EXPLOITATION, ToolSafetyLevel.DANGEROUS),
            ("nikto", ToolCategory.SCANNING, ToolSafetyLevel.NORMAL),
        ]
        
        for name, cat, safety in tools:
            mock_tool = MockTool(name)
            registry.register(
                tool=mock_tool,
                category=cat,
                safety_level=safety,
            )
        
        # Verify all registered
        assert registry.get("nmap") is not None
        assert registry.get("sqlmap") is not None
        
        # Get by category
        recon_tools = registry.get_tools_by_category(ToolCategory.RECONNAISSANCE)
        
        # Cleanup
        registry.unregister("nmap")
        assert registry.get("nmap") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=tools.tool_registry", "--cov-report=term"])

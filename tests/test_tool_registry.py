"""
Comprehensive Tests for Tool Registry Module

Tests for tools/tool_registry.py
Target: 80%+ coverage
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tool_registry import (
    RegisteredTool,
    ToolCategory,
    ToolMetadata,
    ToolRegistry,
    ToolSafetyLevel,
    register_tool,
    registry,
)

# Try to import LangChain tools
try:
    from langchain_core.tools import BaseTool, Tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = MagicMock
    Tool = MagicMock


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def fresh_registry():
    """Create a fresh ToolRegistry instance for testing."""
    # Clear the singleton instance
    ToolRegistry._instance = None
    reg = ToolRegistry()
    reg.clear()
    yield reg
    # Cleanup
    reg.clear()
    ToolRegistry._instance = None


@pytest.fixture
def mock_tool():
    """Create a mock LangChain tool."""
    if LANGCHAIN_AVAILABLE:
        return Tool(name="test_tool", description="A test tool", func=lambda x: x)
    else:
        tool = MagicMock(spec=BaseTool)
        tool.name = "test_tool"
        tool.description = "A test tool"
        return tool


@pytest.fixture
def mock_tool2():
    """Create a second mock LangChain tool."""
    if LANGCHAIN_AVAILABLE:
        return Tool(name="test_tool2", description="Another test tool", func=lambda x: x)
    else:
        tool = MagicMock(spec=BaseTool)
        tool.name = "test_tool2"
        tool.description = "Another test tool"
        return tool


# ============================================================================
# Test ToolMetadata
# ============================================================================


class TestToolMetadata:
    """Test ToolMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating ToolMetadata with basic values."""
        metadata = ToolMetadata(
            name="test_tool",
            description="Test description",
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.NORMAL,
        )

        assert metadata.name == "test_tool"
        assert metadata.description == "Test description"
        assert metadata.category == ToolCategory.SCANNING
        assert metadata.safety_level == ToolSafetyLevel.NORMAL

    def test_metadata_defaults(self):
        """Test ToolMetadata default values."""
        metadata = ToolMetadata(
            name="test_tool",
            description="Test description",
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.NORMAL,
        )

        assert metadata.requires_approval is False
        assert metadata.supported_platforms == ["linux", "windows", "macos"]
        assert metadata.author == ""
        assert metadata.version == "1.0.0"
        assert metadata.tags == []
        assert metadata.invocation_count == 0
        assert metadata.avg_execution_time == 0.0
        assert metadata.last_used is None

    def test_metadata_custom_values(self):
        """Test ToolMetadata with custom values."""
        metadata = ToolMetadata(
            name="custom_tool",
            description="Custom tool",
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            supported_platforms=["linux"],
            author="Test Author",
            version="2.0.0",
            tags=["network", "scan"],
            invocation_count=5,
            avg_execution_time=1.5,
        )

        assert metadata.requires_approval is True
        assert metadata.supported_platforms == ["linux"]
        assert metadata.author == "Test Author"
        assert metadata.version == "2.0.0"
        assert metadata.tags == ["network", "scan"]
        assert metadata.invocation_count == 5
        assert metadata.avg_execution_time == 1.5


# ============================================================================
# Test RegisteredTool
# ============================================================================


class TestRegisteredTool:
    """Test RegisteredTool dataclass."""

    def test_to_dict(self, mock_tool):
        """Test conversion to dictionary."""
        metadata = ToolMetadata(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.NORMAL,
            requires_approval=True,
            supported_platforms=["linux", "windows"],
            author="Test Author",
            version="1.5.0",
            tags=["test", "mock"],
        )
        metadata.invocation_count = 10

        registered = RegisteredTool(tool=mock_tool, metadata=metadata, enabled=True)
        result = registered.to_dict()

        assert result["name"] == "test_tool"
        assert result["description"] == "Test tool"
        assert result["category"] == "scanning"
        assert result["safety_level"] == "normal"
        assert result["requires_approval"] is True
        assert result["supported_platforms"] == ["linux", "windows"]
        assert result["enabled"] is True
        assert result["invocation_count"] == 10
        assert result["tags"] == ["test", "mock"]
        assert result["version"] == "1.5.0"

    def test_to_dict_disabled(self, mock_tool):
        """Test to_dict when tool is disabled."""
        metadata = ToolMetadata(
            name="disabled_tool",
            description="Disabled tool",
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
        )

        registered = RegisteredTool(tool=mock_tool, metadata=metadata, enabled=False)
        result = registered.to_dict()

        assert result["enabled"] is False
        assert result["name"] == "disabled_tool"


# ============================================================================
# Test ToolCategory and ToolSafetyLevel Enums
# ============================================================================


class TestToolCategory:
    """Test ToolCategory enum."""

    def test_category_values(self):
        """Test all category values."""
        assert ToolCategory.RECONNAISSANCE.value == "reconnaissance"
        assert ToolCategory.SCANNING.value == "scanning"
        assert ToolCategory.EXPLOITATION.value == "exploitation"
        assert ToolCategory.POST_EXPLOITATION.value == "post_exploitation"
        assert ToolCategory.REPORTING.value == "reporting"
        assert ToolCategory.UTILITY.value == "utility"

    def test_all_categories(self):
        """Test that we have exactly 6 categories."""
        categories = list(ToolCategory)
        assert len(categories) == 6


class TestToolSafetyLevel:
    """Test ToolSafetyLevel enum."""

    def test_safety_level_values(self):
        """Test all safety level values."""
        assert ToolSafetyLevel.SAFE.value == "safe"
        assert ToolSafetyLevel.NORMAL.value == "normal"
        assert ToolSafetyLevel.DANGEROUS.value == "dangerous"
        assert ToolSafetyLevel.CRITICAL.value == "critical"

    def test_all_safety_levels(self):
        """Test that we have exactly 4 safety levels."""
        levels = list(ToolSafetyLevel)
        assert len(levels) == 4


# ============================================================================
# Test ToolRegistry Singleton
# ============================================================================


class TestToolRegistrySingleton:
    """Test ToolRegistry singleton pattern."""

    def test_singleton_pattern(self):
        """Test that ToolRegistry is a singleton."""
        # Reset singleton
        ToolRegistry._instance = None

        reg1 = ToolRegistry()
        reg2 = ToolRegistry()

        assert reg1 is reg2

    def test_initialization_once(self):
        """Test that registry initializes only once."""
        ToolRegistry._instance = None

        reg = ToolRegistry()
        reg._initialized = True
        reg._tools["test"] = "value"

        # Get instance again
        reg2 = ToolRegistry()
        assert reg2._tools["test"] == "value"

        # Cleanup
        reg.clear()
        ToolRegistry._instance = None


# ============================================================================
# Test Tool Registration
# ============================================================================


class TestToolRegistration:
    """Test tool registration functionality."""

    def test_register_single_tool(self, fresh_registry, mock_tool):
        """Test registering a single tool."""
        result = fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        assert result.metadata.name == "test_tool"
        assert result.metadata.category == ToolCategory.SCANNING
        assert result.enabled is True
        assert "test_tool" in fresh_registry._tools

    def test_register_with_all_options(self, fresh_registry, mock_tool):
        """Test registering with all optional parameters."""
        result = fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            supported_platforms=["linux"],
            author="Security Team",
            version="2.1.0",
            tags=["exploit", "network"],
            enabled=False,
        )

        assert result.metadata.requires_approval is True
        assert result.metadata.supported_platforms == ["linux"]
        assert result.metadata.author == "Security Team"
        assert result.metadata.version == "2.1.0"
        assert result.metadata.tags == ["exploit", "network"]
        assert result.enabled is False

    def test_register_overwrite_existing(self, fresh_registry, mock_tool, mock_tool2):
        """Test that registering overwrites existing tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        # Register again with different category
        with patch("tools.tool_registry.logger") as mock_logger:
            fresh_registry.register(
                tool=mock_tool,
                category=ToolCategory.RECONNAISSANCE,
                safety_level=ToolSafetyLevel.SAFE,
            )
            mock_logger.warning.assert_called_once()

        assert fresh_registry._tools["test_tool"].metadata.category == ToolCategory.RECONNAISSANCE

    def test_categories_tracking(self, fresh_registry, mock_tool, mock_tool2):
        """Test that categories are properly tracked."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        assert "test_tool" in fresh_registry._categories[ToolCategory.SCANNING]
        assert "test_tool2" in fresh_registry._categories[ToolCategory.SCANNING]
        assert len(fresh_registry._categories[ToolCategory.SCANNING]) == 2


# ============================================================================
# Test Tool Unregistration
# ============================================================================


class TestToolUnregistration:
    """Test tool unregistration."""

    def test_unregister_existing_tool(self, fresh_registry, mock_tool):
        """Test unregistering an existing tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        result = fresh_registry.unregister("test_tool")

        assert result is True
        assert "test_tool" not in fresh_registry._tools
        assert "test_tool" not in fresh_registry._categories[ToolCategory.SCANNING]

    def test_unregister_nonexistent_tool(self, fresh_registry):
        """Test unregistering a non-existent tool."""
        result = fresh_registry.unregister("nonexistent")
        assert result is False


# ============================================================================
# Test Tool Retrieval
# ============================================================================


class TestToolRetrieval:
    """Test tool retrieval methods."""

    def test_get_registered_tool(self, fresh_registry, mock_tool):
        """Test getting a registered tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        result = fresh_registry.get("test_tool")

        assert result is not None
        assert result.metadata.name == "test_tool"

    def test_get_nonexistent_tool(self, fresh_registry):
        """Test getting a non-existent tool."""
        result = fresh_registry.get("nonexistent")
        assert result is None

    def test_get_tool_langchain(self, fresh_registry, mock_tool):
        """Test getting LangChain tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        result = fresh_registry.get_tool("test_tool")
        assert result is not None

    def test_get_tool_disabled(self, fresh_registry, mock_tool):
        """Test that disabled tools return None."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        result = fresh_registry.get_tool("test_tool")
        assert result is None

    def test_get_tool_nonexistent(self, fresh_registry):
        """Test getting non-existent LangChain tool."""
        result = fresh_registry.get_tool("nonexistent")
        assert result is None


# ============================================================================
# Test Tool Listing
# ============================================================================


class TestToolListing:
    """Test tool listing with filters."""

    def test_list_all_tools(self, fresh_registry, mock_tool, mock_tool2):
        """Test listing all tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.NORMAL,
        )

        results = fresh_registry.list_tools()

        assert len(results) == 2

    def test_list_by_category(self, fresh_registry, mock_tool, mock_tool2):
        """Test filtering by category."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
        )

        results = fresh_registry.list_tools(category=ToolCategory.SCANNING)

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool"

    def test_list_by_safety_level(self, fresh_registry, mock_tool, mock_tool2):
        """Test filtering by safety level."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
        )

        results = fresh_registry.list_tools(safety_level=ToolSafetyLevel.SAFE)

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool"

    def test_list_enabled_only(self, fresh_registry, mock_tool, mock_tool2):
        """Test filtering enabled tools only."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        enabled = fresh_registry.list_tools(enabled_only=True)
        all_tools = fresh_registry.list_tools(enabled_only=False)

        assert len(enabled) == 1
        assert len(all_tools) == 2

    def test_list_by_tags(self, fresh_registry, mock_tool, mock_tool2):
        """Test filtering by tags."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network", "port"],
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["web", "vuln"],
        )

        results = fresh_registry.list_tools(tags=["network"])

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool"

    def test_list_by_multiple_tags(self, fresh_registry, mock_tool, mock_tool2):
        """Test filtering by multiple tags (AND logic)."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network", "port"],
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network"],
        )

        results = fresh_registry.list_tools(tags=["network", "port"])

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool"

    def test_list_combined_filters(self, fresh_registry, mock_tool, mock_tool2):
        """Test combining multiple filters."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network"],
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.DANGEROUS,
            tags=["network"],
        )

        results = fresh_registry.list_tools(
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network"],
        )

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool"


# ============================================================================
# Test Category-Based Retrieval
# ============================================================================


class TestCategoryRetrieval:
    """Test getting tools by category."""

    def test_get_tools_by_category(self, fresh_registry, mock_tool, mock_tool2):
        """Test getting all tools in a category."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        results = fresh_registry.get_tools_by_category(ToolCategory.SCANNING)

        assert len(results) == 2

    def test_get_tools_by_empty_category(self, fresh_registry):
        """Test getting tools from empty category."""
        results = fresh_registry.get_tools_by_category(ToolCategory.EXPLOITATION)
        assert len(results) == 0

    def test_get_tools_by_category_disabled_filtered(self, fresh_registry, mock_tool, mock_tool2):
        """Test that disabled tools are filtered in category query."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        results = fresh_registry.get_tools_by_category(ToolCategory.SCANNING)

        assert len(results) == 1


# ============================================================================
# Test Safe and Dangerous Tools
# ============================================================================


class TestSafeAndDangerousTools:
    """Test safe/dangerous tool retrieval."""

    def test_get_safe_tools(self, fresh_registry, mock_tool, mock_tool2):
        """Test getting safe tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
        )

        results = fresh_registry.get_safe_tools()

        assert len(results) == 1

    def test_get_safe_tools_disabled_filtered(self, fresh_registry, mock_tool, mock_tool2):
        """Test that disabled tools are filtered from safe tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        results = fresh_registry.get_safe_tools()

        assert len(results) == 1

    def test_get_dangerous_tools(self, fresh_registry, mock_tool, mock_tool2):
        """Test getting dangerous tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
        )

        results = fresh_registry.get_dangerous_tools()

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool2"

    def test_get_dangerous_tools_by_approval(self, fresh_registry, mock_tool, mock_tool2):
        """Test getting tools requiring approval."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=True,
        )

        results = fresh_registry.get_dangerous_tools()

        assert len(results) == 1
        assert results[0].metadata.name == "test_tool2"

    def test_get_dangerous_tools_critical(self, fresh_registry, mock_tool):
        """Test getting critical level tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.CRITICAL,
        )

        results = fresh_registry.get_dangerous_tools()

        assert len(results) == 1


# ============================================================================
# Test Enable/Disable
# ============================================================================


class TestEnableDisable:
    """Test enabling and disabling tools."""

    def test_enable_tool(self, fresh_registry, mock_tool):
        """Test enabling a disabled tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        result = fresh_registry.enable_tool("test_tool")

        assert result is True
        assert fresh_registry._tools["test_tool"].enabled is True

    def test_enable_nonexistent_tool(self, fresh_registry):
        """Test enabling a non-existent tool."""
        result = fresh_registry.enable_tool("nonexistent")
        assert result is False

    def test_disable_tool(self, fresh_registry, mock_tool):
        """Test disabling an enabled tool."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )

        result = fresh_registry.disable_tool("test_tool")

        assert result is True
        assert fresh_registry._tools["test_tool"].enabled is False

    def test_disable_nonexistent_tool(self, fresh_registry):
        """Test disabling a non-existent tool."""
        result = fresh_registry.disable_tool("nonexistent")
        assert result is False


# ============================================================================
# Test Invocation Recording
# ============================================================================


class TestInvocationRecording:
    """Test recording tool invocations."""

    def test_record_invocation_first(self, fresh_registry, mock_tool):
        """Test recording first invocation."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        fresh_registry.record_invocation("test_tool", 1.5)

        meta = fresh_registry._tools["test_tool"].metadata
        assert meta.invocation_count == 1
        assert meta.avg_execution_time == 1.5
        assert meta.last_used is not None

    def test_record_invocation_subsequent(self, fresh_registry, mock_tool):
        """Test recording multiple invocations."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        fresh_registry.record_invocation("test_tool", 1.0)
        fresh_registry.record_invocation("test_tool", 2.0)
        fresh_registry.record_invocation("test_tool", 3.0)

        meta = fresh_registry._tools["test_tool"].metadata
        assert meta.invocation_count == 3
        # Running average: (1.0 + 2.0 + 3.0) / 3 = 2.0
        assert meta.avg_execution_time == 2.0

    def test_record_invocation_nonexistent(self, fresh_registry):
        """Test recording invocation for non-existent tool."""
        # Should not raise exception
        fresh_registry.record_invocation("nonexistent", 1.0)


# ============================================================================
# Test Get All Tools
# ============================================================================


class TestGetAllTools:
    """Test getting all tools as LangChain tools."""

    def test_get_all_tools(self, fresh_registry, mock_tool, mock_tool2):
        """Test getting all enabled tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )

        results = fresh_registry.get_all_tools()

        assert len(results) == 2

    def test_get_all_tools_filters_disabled(self, fresh_registry, mock_tool, mock_tool2):
        """Test that disabled tools are filtered."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        results = fresh_registry.get_all_tools()

        assert len(results) == 1


# ============================================================================
# Test Registry Stats
# ============================================================================


class TestRegistryStats:
    """Test registry statistics."""

    def test_empty_registry_stats(self, fresh_registry):
        """Test stats for empty registry."""
        stats = fresh_registry.get_registry_stats()

        assert stats["total_tools"] == 0
        assert stats["enabled_tools"] == 0
        assert stats["disabled_tools"] == 0
        assert stats["total_invocations"] == 0

    def test_registry_stats(self, fresh_registry, mock_tool, mock_tool2):
        """Test stats calculation."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=True,
        )
        fresh_registry.register(
            tool=mock_tool2,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.DANGEROUS,
            enabled=False,
        )
        fresh_registry.record_invocation("test_tool", 1.0)

        stats = fresh_registry.get_registry_stats()

        assert stats["total_tools"] == 2
        assert stats["enabled_tools"] == 1
        assert stats["disabled_tools"] == 1
        assert stats["total_invocations"] == 1
        assert stats["by_category"]["scanning"] == 1
        assert stats["by_category"]["reconnaissance"] == 1
        assert stats["by_safety_level"]["safe"] == 1
        assert stats["by_safety_level"]["dangerous"] == 1


# ============================================================================
# Test Tool Discovery
# ============================================================================


class TestToolDiscovery:
    """Test automatic tool discovery."""

    @patch("tools.tool_registry.importlib.import_module")
    @patch("tools.tool_registry.inspect.getmembers")
    def test_discover_tools(self, mock_getmembers, mock_import_module, fresh_registry):
        """Test discovering tools in a module."""
        # Create mock tool with description
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "discovered_tool"
        mock_tool.description = "A discovered tool"

        # Setup mocks
        mock_module = MagicMock()
        mock_import_module.return_value = mock_module
        mock_getmembers.return_value = [("discovered_tool", mock_tool)]

        with patch("tools.tool_registry.isinstance", return_value=True):
            results = fresh_registry.discover_tools("test.module")

        assert len(results) == 1
        assert results[0].metadata.name == "discovered_tool"

    def test_discover_tools_import_error(self, fresh_registry):
        """Test handling import errors during discovery."""
        with patch("tools.tool_registry.importlib.import_module") as mock_import_module:
            mock_import_module.side_effect = ImportError("Module not found")

            results = fresh_registry.discover_tools("nonexistent.module")

            assert len(results) == 0


# ============================================================================
# Test Clear
# ============================================================================


class TestClear:
    """Test clearing registry."""

    def test_clear_registry(self, fresh_registry, mock_tool):
        """Test clearing all tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
        )

        fresh_registry.clear()

        assert len(fresh_registry._tools) == 0
        assert all(len(tools) == 0 for tools in fresh_registry._categories.values())


# ============================================================================
# Test Register Tool Decorator
# ============================================================================


class TestRegisterToolDecorator:
    """Test the @register_tool decorator."""

    def test_register_tool_decorator(self, fresh_registry):
        """Test using decorator to register tool."""
        # Reset to use our fresh registry
        with patch("tools.tool_registry.registry", fresh_registry):

            @register_tool(category=ToolCategory.SCANNING, safety_level=ToolSafetyLevel.SAFE, tags=["test"])
            def my_test_tool(target: str) -> str:
                """Test tool description."""
                return f"Scanned {target}"

            # Check tool was registered
            assert "my_test_tool" in fresh_registry._tools
            tool_meta = fresh_registry._tools["my_test_tool"].metadata
            assert tool_meta.category == ToolCategory.SCANNING
            assert tool_meta.safety_level == ToolSafetyLevel.SAFE
            assert "test" in tool_meta.tags

    def test_register_tool_decorator_preserves_function(self, fresh_registry):
        """Test that decorator preserves function behavior."""
        with patch("tools.tool_registry.registry", fresh_registry):

            @register_tool(category=ToolCategory.UTILITY)
            def add_tool(a: int, b: int) -> int:
                """Add two numbers."""
                return a + b

            # Function should still work
            assert add_tool(2, 3) == 5


# ============================================================================
# Test Global Registry Instance
# ============================================================================


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_global_registry_exists(self):
        """Test that global registry is created."""
        assert registry is not None
        assert isinstance(registry, ToolRegistry)


# ============================================================================
# Test Error Cases
# ============================================================================


class TestErrorCases:
    """Test error handling scenarios."""

    def test_get_tool_returns_none_when_disabled(self, fresh_registry, mock_tool):
        """Test that get_tool returns None for disabled tools."""
        fresh_registry.register(
            tool=mock_tool,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            enabled=False,
        )

        result = fresh_registry.get_tool("test_tool")
        assert result is None

    def test_get_tool_returns_none_when_not_found(self, fresh_registry):
        """Test that get_tool returns None for non-existent tools."""
        result = fresh_registry.get_tool("nonexistent")
        assert result is None

    def test_get_returns_none_when_not_found(self, fresh_registry):
        """Test that get returns None for non-existent tools."""
        result = fresh_registry.get("nonexistent")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

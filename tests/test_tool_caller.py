"""
Comprehensive Tests for Tool Caller Module

Tests for tools/tool_caller.py
Target: 80%+ coverage
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tool_caller import (
    ToolCallResult,
    ToolCaller,
    call_tool,
    call_tools_batch,
    get_tool_caller,
)
from tools.tool_registry import ToolRegistry

# Try to import LangChain tools
try:
    from langchain_core.tools import Tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Tool = MagicMock


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_registry():
    """Create a mock registry."""
    registry = MagicMock(spec=ToolRegistry)
    registry._tools = {}
    return registry


@pytest.fixture
def tool_caller(mock_registry):
    """Create a ToolCaller instance with mock registry."""
    return ToolCaller(registry=mock_registry, max_workers=2)


@pytest.fixture
def mock_sync_tool():
    """Create a mock synchronous tool."""
    tool = MagicMock()
    tool.name = "sync_tool"
    tool.func = MagicMock(return_value="sync_result")
    tool.invoke = MagicMock(return_value="sync_result")
    return tool


@pytest.fixture
def mock_async_tool():
    """Create a mock async tool."""
    tool = MagicMock()
    tool.name = "async_tool"

    async def async_func(*args, **kwargs):
        return "async_result"

    tool.func = async_func
    tool.ainvoke = AsyncMock(return_value="async_result")
    return tool


# ============================================================================
# Test ToolCallResult
# ============================================================================


class TestToolCallResult:
    """Test ToolCallResult dataclass."""

    def test_result_defaults(self):
        """Test ToolCallResult default values."""
        result = ToolCallResult(success=True, result="test", execution_time=1.5)

        assert result.success is True
        assert result.result == "test"
        assert result.execution_time == 1.5
        assert result.error is None
        assert result.tool_name == ""
        assert result.safety_level == ""

    def test_result_to_dict_success(self):
        """Test to_dict for successful result."""
        result = ToolCallResult(
            success=True,
            result="test_data",
            execution_time=1.567,
            tool_name="test_tool",
            safety_level="safe",
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["result"] == "test_data"
        assert data["execution_time"] == 1.57  # Rounded
        assert data["error"] is None
        assert data["tool_name"] == "test_tool"
        assert data["safety_level"] == "safe"

    def test_result_to_dict_failure(self):
        """Test to_dict for failed result."""
        result = ToolCallResult(
            success=False,
            result=None,
            execution_time=2.0,
            error="Something went wrong",
            tool_name="failing_tool",
        )

        data = result.to_dict()

        assert data["success"] is False
        assert data["result"] is None
        assert data["error"] == "Something went wrong"


# ============================================================================
# Test ToolCaller Initialization
# ============================================================================


class TestToolCallerInit:
    """Test ToolCaller initialization."""

    def test_init_with_registry(self, mock_registry):
        """Test initialization with provided registry."""
        caller = ToolCaller(registry=mock_registry, max_workers=5)

        assert caller.registry is mock_registry
        assert caller.default_timeout == 300
        assert caller.executor._max_workers == 5

    def test_init_default_registry(self):
        """Test initialization with default registry."""
        with patch("tools.tool_caller.ToolRegistry") as MockRegistry:
            mock_reg = MagicMock()
            MockRegistry.return_value = mock_reg

            caller = ToolCaller()

            assert caller.registry is not None

    def test_init_custom_workers(self):
        """Test initialization with custom worker count."""
        caller = ToolCaller(max_workers=10)
        assert caller.executor._max_workers == 10


# ============================================================================
# Test Call Tool - Success Cases
# ============================================================================


class TestCallToolSuccess:
    """Test successful tool execution."""

    @pytest.mark.asyncio
    async def test_call_sync_tool_success(self, tool_caller, mock_sync_tool):
        """Test calling a synchronous tool successfully."""
        # Setup mock registered tool
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {"arg": "value"})

        assert result.success is True
        assert result.result == "sync_result"
        assert result.tool_name == "sync_tool"
        assert result.safety_level == "safe"
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_call_async_tool_success(self, tool_caller, mock_async_tool):
        """Test calling an async tool successfully."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_async_tool
        registered.metadata.safety_level.value = "normal"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("async_tool", {"arg": "value"})

        assert result.success is True
        assert result.result == "async_result"
        mock_async_tool.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_with_custom_timeout(self, tool_caller, mock_sync_tool):
        """Test calling with custom timeout."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {}, timeout=60)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_call_records_invocation(self, tool_caller, mock_sync_tool):
        """Test that invocation is recorded."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        await tool_caller.call_tool("sync_tool", {})

        tool_caller.registry.record_invocation.assert_called_once()
        args = tool_caller.registry.record_invocation.call_args
        assert args[0][0] == "sync_tool"
        assert isinstance(args[0][1], float)


# ============================================================================
# Test Call Tool - Error Cases
# ============================================================================


class TestCallToolErrors:
    """Test tool execution error handling."""

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, tool_caller):
        """Test calling non-existent tool."""
        tool_caller.registry.get.return_value = None

        result = await tool_caller.call_tool("nonexistent", {})

        assert result.success is False
        assert "nicht in Registry gefunden" in result.error or "not found" in result.error.lower()
        assert result.tool_name == "nonexistent"

    @pytest.mark.asyncio
    async def test_call_tool_disabled(self, tool_caller):
        """Test calling disabled tool."""
        registered = MagicMock()
        registered.enabled = False
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("disabled_tool", {})

        assert result.success is False
        assert "deaktiviert" in result.error or "disabled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self, tool_caller):
        """Test tool execution timeout."""

        async def slow_tool(*args, **kwargs):
            await asyncio.sleep(10)
            return "result"

        mock_tool = MagicMock()
        mock_tool.name = "slow_tool"
        mock_tool.func = slow_tool
        mock_tool.ainvoke = slow_tool

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("slow_tool", {}, timeout=0.01)

        assert result.success is False
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_call_tool_exception(self, tool_caller):
        """Test handling tool execution exception."""
        mock_tool = MagicMock()
        mock_tool.name = "failing_tool"
        mock_tool.func = MagicMock(side_effect=Exception("Tool failed"))
        mock_tool.invoke = MagicMock(side_effect=Exception("Tool failed"))

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_tool
        registered.metadata.safety_level.value = "normal"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("failing_tool", {})

        assert result.success is False
        assert "Tool failed" in result.error


# ============================================================================
# Test Result Validation
# ============================================================================


class TestResultValidation:
    """Test result validation."""

    @pytest.mark.asyncio
    async def test_validate_result_none(self, tool_caller, mock_sync_tool):
        """Test validation fails for None result."""
        mock_sync_tool.invoke = MagicMock(return_value=None)

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {})

        assert result.success is False
        assert "Validierung" in result.error or "validation" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_result_empty_string(self, tool_caller, mock_sync_tool):
        """Test validation fails for empty string."""
        mock_sync_tool.invoke = MagicMock(return_value="")

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {})

        assert result.success is False

    @pytest.mark.asyncio
    async def test_validate_result_empty_list(self, tool_caller, mock_sync_tool):
        """Test validation fails for empty list."""
        mock_sync_tool.invoke = MagicMock(return_value=[])

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {})

        assert result.success is False

    @pytest.mark.asyncio
    async def test_validate_result_empty_dict(self, tool_caller, mock_sync_tool):
        """Test validation fails for empty dict."""
        mock_sync_tool.invoke = MagicMock(return_value={})

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {})

        assert result.success is False

    @pytest.mark.asyncio
    async def test_skip_validation(self, tool_caller, mock_sync_tool):
        """Test skipping result validation."""
        mock_sync_tool.invoke = MagicMock(return_value="")

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {}, validate_result=False)

        assert result.success is True


# ============================================================================
# Test Parallel Tool Calls
# ============================================================================


class TestParallelToolCalls:
    """Test parallel tool execution."""

    @pytest.mark.asyncio
    async def test_call_tools_parallel(self, tool_caller, mock_sync_tool):
        """Test calling multiple tools in parallel."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        calls = [
            ("tool1", {"arg": 1}),
            ("tool2", {"arg": 2}),
            ("tool3", {"arg": 3}),
        ]

        results = await tool_caller.call_tools_parallel(calls)

        assert len(results) == 3
        assert all(r.success for r in results.values())

    @pytest.mark.asyncio
    async def test_call_tools_parallel_with_exception(self, tool_caller, mock_sync_tool):
        """Test parallel calls with one failing."""

        def side_effect(*args, **kwargs):
            if args[0].get("fail"):
                raise Exception("Failed")
            return "success"

        mock_sync_tool.invoke = MagicMock(side_effect=side_effect)

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        calls = [
            ("tool1", {"fail": False}),
            ("tool2", {"fail": True}),
        ]

        results = await tool_caller.call_tools_parallel(calls)

        assert results["tool1"].success is True
        assert results["tool2"].success is False


# ============================================================================
# Test Tool Status
# ============================================================================


class TestToolStatus:
    """Test getting tool status."""

    @pytest.mark.asyncio
    async def test_get_tool_status(self, tool_caller):
        """Test getting tool status."""
        registered = MagicMock()
        registered.enabled = True
        registered.metadata.safety_level.value = "dangerous"
        registered.metadata.category.value = "scanning"
        registered.metadata.invocation_count = 5
        registered.metadata.avg_execution_time = 1.5
        registered.metadata.last_used = "2024-01-01T00:00:00"
        registered.metadata.requires_approval = True

        tool_caller.registry.get.return_value = registered

        status = await tool_caller.get_tool_status("test_tool")

        assert status["name"] == "test_tool"
        assert status["enabled"] is True
        assert status["safety_level"] == "dangerous"
        assert status["category"] == "scanning"
        assert status["invocation_count"] == 5
        assert status["avg_execution_time"] == 1.5
        assert status["last_used"] == "2024-01-01T00:00:00"
        assert status["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_get_tool_status_not_found(self, tool_caller):
        """Test getting status for non-existent tool."""
        tool_caller.registry.get.return_value = None

        status = await tool_caller.get_tool_status("nonexistent")

        assert "error" in status

    @pytest.mark.asyncio
    async def test_get_all_tool_status(self, tool_caller):
        """Test getting status for all tools."""
        tool1 = MagicMock()
        tool1.to_dict.return_value = {"name": "tool1"}
        tool2 = MagicMock()
        tool2.to_dict.return_value = {"name": "tool2"}

        tool_caller.registry.list_tools.return_value = [tool1, tool2]

        status_list = await tool_caller.get_all_tool_status()

        assert len(status_list) == 2
        assert status_list[0]["name"] == "tool1"
        assert status_list[1]["name"] == "tool2"


# ============================================================================
# Test Shutdown
# ============================================================================


class TestShutdown:
    """Test ToolCaller shutdown."""

    def test_shutdown(self, tool_caller):
        """Test proper shutdown."""
        with patch("tools.tool_caller.logger") as mock_logger:
            tool_caller.shutdown()
            mock_logger.info.assert_called_once()


# ============================================================================
# Test Convenience Functions
# ============================================================================


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    @patch("tools.tool_caller.ToolCaller")
    async def test_call_tool_convenience(self, MockCaller):
        """Test call_tool convenience function."""
        mock_instance = MagicMock()
        mock_result = ToolCallResult(success=True, result="test", execution_time=1.0)
        mock_instance.call_tool = AsyncMock(return_value=mock_result)
        MockCaller.return_value = mock_instance

        result = await call_tool("test_tool", arg1="value1")

        assert result.success is True
        mock_instance.call_tool.assert_called_once()

    @pytest.mark.asyncio
    @patch("tools.tool_caller.ToolCaller")
    async def test_call_tools_batch_convenience(self, MockCaller):
        """Test call_tools_batch convenience function."""
        mock_instance = MagicMock()
        mock_result = {"tool1": ToolCallResult(success=True, result="test", execution_time=1.0)}
        mock_instance.call_tools_parallel = AsyncMock(return_value=mock_result)
        MockCaller.return_value = mock_instance

        calls = [("tool1", {"arg": "value"})]
        result = await call_tools_batch(calls)

        assert "tool1" in result

    def test_get_tool_caller_singleton(self):
        """Test get_tool_caller singleton."""
        with patch("tools.tool_caller._default_caller", None):
            with patch("tools.tool_caller.ToolCaller") as MockCaller:
                mock_instance = MagicMock()
                MockCaller.return_value = mock_instance

                caller1 = get_tool_caller()
                caller2 = get_tool_caller()

                assert caller1 is caller2
                MockCaller.assert_called_once()


# ============================================================================
# Test Internal Validation
# ============================================================================


class TestInternalValidation:
    """Test internal validation methods."""

    def test_validate_result_true(self, tool_caller):
        """Test validation with valid result."""
        assert tool_caller._validate_result("valid") is True
        assert tool_caller._validate_result([1, 2, 3]) is True
        assert tool_caller._validate_result({"key": "value"}) is True
        assert tool_caller._validate_result(123) is True

    def test_validate_result_false(self, tool_caller):
        """Test validation with invalid result."""
        assert tool_caller._validate_result(None) is False
        assert tool_caller._validate_result("") is False
        assert tool_caller._validate_result([]) is False
        assert tool_caller._validate_result({}) is False


# ============================================================================
# Test Parameter Validation
# ============================================================================


class TestParameterValidation:
    """Test parameter validation in tool calls."""

    @pytest.mark.asyncio
    async def test_call_tool_with_empty_args(self, tool_caller, mock_sync_tool):
        """Test calling tool with empty arguments."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        result = await tool_caller.call_tool("sync_tool", {})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_call_tool_with_complex_args(self, tool_caller, mock_sync_tool):
        """Test calling tool with complex arguments."""
        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_sync_tool
        registered.metadata.safety_level.value = "safe"

        tool_caller.registry.get.return_value = registered

        complex_args = {
            "target": "scanme.nmap.org",
            "ports": [80, 443],
            "options": {"timing": "aggressive"},
            "enabled": True,
        }

        result = await tool_caller.call_tool("sync_tool", complex_args)

        assert result.success is True
        # Verify the tool was called with the correct arguments
        mock_sync_tool.invoke.assert_called_once_with(complex_args)


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_call_tool_with_none_registry(self):
        """Test calling tool with None in registry get."""
        caller = ToolCaller()
        with patch.object(caller.registry, 'get', return_value=None):
            result = await caller.call_tool("nonexistent_tool", {})
            assert result.success is False
            assert "not found" in result.error.lower() or "nicht in Registry" in result.error

    @pytest.mark.asyncio
    async def test_parallel_call_with_exception_handling(self, tool_caller):
        """Test parallel call exception handling."""

        def failing_invoke(*args, **kwargs):
            raise RuntimeError("Simulated tool failure")

        mock_tool = MagicMock()
        mock_tool.invoke = failing_invoke

        registered = MagicMock()
        registered.enabled = True
        registered.tool = mock_tool
        registered.metadata.safety_level.value = "normal"

        tool_caller.registry.get.return_value = registered

        calls = [("failing_tool", {"arg": "value"})]
        results = await tool_caller.call_tools_parallel(calls)

        assert results["failing_tool"].success is False
        assert "Simulated tool failure" in results["failing_tool"].error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

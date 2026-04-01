"""Test tool executor"""

import pytest


class TestToolExecutor:
    """Test tool executor"""

    def test_import(self):
        from core.tool_executor import ToolExecutor

        assert ToolExecutor is not None

    def test_result_status_import(self):
        from core.tool_executor import ToolResultStatus

        assert ToolResultStatus is not None

    def test_result_import(self):
        from core.tool_executor import ToolResult

        assert ToolResult is not None

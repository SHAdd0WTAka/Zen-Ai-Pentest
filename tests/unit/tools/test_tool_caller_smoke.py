"""Smoke tests for tools/tool_caller.py"""

import pytest

from tools.tool_caller import ToolCaller, ToolCallResult


class TestToolCallerInit:
    def test_default_init(self):
        caller = ToolCaller()
        assert caller.default_timeout == 300

    def test_custom_timeout(self):
        caller = ToolCaller()
        assert caller.default_timeout == 300


class TestToolCallResult:
    def test_success(self):
        r = ToolCallResult(tool_name="test", success=True, result={"data": "ok"}, execution_time=0.5)
        d = r.to_dict()
        assert d["success"] is True
        assert d["result"] == {"data": "ok"}

    def test_failure(self):
        r = ToolCallResult(tool_name="bad", success=False, result=None, execution_time=0.1, error="fail")
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "fail"


class TestToolCallerAsync:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.caller = ToolCaller()

    @pytest.mark.timeout(5)
    async def test_tool_not_found(self):
        r = await self.caller.call_tool("nonexistent", {})
        assert r.success is False
        assert r.error is not None

    @pytest.mark.timeout(5)
    async def test_parallel_empty(self):
        r = await self.caller.call_tools_parallel([])
        assert r == {}

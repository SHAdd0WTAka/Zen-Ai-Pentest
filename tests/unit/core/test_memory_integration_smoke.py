"""Smoke tests for core/memory_integration.py"""

import pytest

from core.memory_integration import (
    MemoryAwareOrchestrator,
    MemoryInstrumentedTool,
    instrument_tool_class,
    memory_efficient_batch,
    profile_memory,
)


class TestMemoryInstrumentedTool:
    def test_init_default(self):
        tool = MemoryInstrumentedTool()
        assert tool.tool_name == "unknown"
        assert tool._scan_stats == []

    def test_check_memory_health(self):
        tool = MemoryInstrumentedTool()
        assert tool.check_memory_health() is True

    def test_init_with_memory_guard(self):
        from core.memory_guard import MemoryGuard

        guard = MemoryGuard()
        tool = MemoryInstrumentedTool(memory_guard=guard)
        assert tool.memory_guard is guard

    def test_record_scan_stats(self):
        tool = MemoryInstrumentedTool()
        tool.record_scan_stats("example.com", 1.5, 10.0)
        assert len(tool._scan_stats) == 1
        assert tool._scan_stats[0]["target"] == "example.com"
        assert tool._scan_stats[0]["duration"] == 1.5
        assert tool._scan_stats[0]["memory_delta_mb"] == 10.0


class TestMemoryAwareOrchestrator:
    def test_init_defaults(self):
        orch = MemoryAwareOrchestrator()
        assert orch.max_memory_mb == 2000
        assert orch.tools == {}

    def test_init_custom(self):
        orch = MemoryAwareOrchestrator(max_memory_mb=1000)
        assert orch.max_memory_mb == 1000

    def test_register_tool(self):
        orch = MemoryAwareOrchestrator()
        tool = MemoryInstrumentedTool()
        tool.tool_name = "nmap"
        orch.register_tool(tool)
        assert "nmap" in orch.tools
        assert orch.tools["nmap"] is tool

    def test_force_cleanup(self):
        orch = MemoryAwareOrchestrator()
        result = orch.force_cleanup()
        assert "gc_result" in result
        assert "memory_after_cleanup" in result


class TestProfileMemoryDecorator:
    def test_decorator(self):
        @profile_memory("test_tool")
        def dummy():
            return 42

        assert dummy() == 42


class TestMemoryEfficientBatch:
    async def test_basic_batch(self):
        async def processor(batch):
            return [x * 2 for x in batch]

        results = await memory_efficient_batch(
            items=[1, 2, 3, 4, 5],
            process_func=processor,
            batch_size=2,
        )
        assert results == [2, 4, 6, 8, 10]


class TestInstrumentToolClass:
    def test_instrumentation(self):
        class DummyTool:
            def __init__(self):
                self.initialized = True

            def run(self):
                return "ok"

        cls = instrument_tool_class(DummyTool, "dummy")
        instance = cls()
        assert instance.initialized is True
        assert instance.run() == "ok"

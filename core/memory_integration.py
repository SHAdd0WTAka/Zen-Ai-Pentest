"""
Memory Guard Integration for Zen-AI-Pentest Tools
===============================================

Integrates MemoryGuard with existing tool integrations for automatic
memory profiling and leak detection during pentest operations.

Usage:
    from core.memory_integration import MemoryInstrumentedTool

    class NmapTool(MemoryInstrumentedTool):
        tool_name = "nmap"

        def run(self, target):
            with self.memory_context(target):
                # ... actual nmap execution ...
                pass
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional

from core.memory_guard import MemoryGuard, memory_context, track_memory

logger = logging.getLogger(__name__)


class MemoryInstrumentedTool:
    """
    Base class for tools with automatic memory instrumentation.

    Example:
        class MyScanner(MemoryInstrumentedTool):
            tool_name = "myscanner"

            async def scan(self, target):
                with self.memory_context(target):
                    return await self._do_scan(target)
    """

    tool_name: str = "unknown"

    def __init__(self, memory_guard: Optional[MemoryGuard] = None):
        self.memory_guard = memory_guard or MemoryGuard()
        self.logger = logging.getLogger(f"{__name__}.{self.tool_name}")
        self._scan_stats: List[Dict[str, Any]] = []

    def memory_context(self, target: str):
        """Context manager for memory tracking"""
        return memory_context(f"{self.tool_name}_{target}", self.memory_guard)

    def track(self, func):
        """Decorator for memory tracking"""
        return track_memory(self.tool_name, self.memory_guard)(func)

    def record_scan_stats(self, target: str, duration: float, memory_delta: float):
        """Record scan statistics"""
        self._scan_stats.append(
            {
                "tool": self.tool_name,
                "target": target,
                "duration": duration,
                "memory_delta_mb": memory_delta,
                "timestamp": time.time(),
            }
        )

    def get_memory_profile(self) -> Dict[str, Any]:
        """Get memory profile for this tool"""
        return self.memory_guard.get_tool_memory_profile(self.tool_name)

    def check_memory_health(self) -> bool:
        """Check if tool is operating within memory constraints"""
        profile = self.get_memory_profile()

        if "peak_memory_mb" in profile:
            peak = profile["peak_memory_mb"]
            if peak > 1000:  # 1GB threshold
                self.logger.warning(f"{self.tool_name} peak memory {peak:.1f}MB exceeds recommended limit")
                return False
        return True


class MemoryAwareOrchestrator:
    """
    Orchestrator that manages memory across multiple tools.
    Prevents memory exhaustion during complex pentest workflows.
    """

    def __init__(self, max_memory_mb: int = 2000):
        self.memory_guard = MemoryGuard(
            threshold_mb=max_memory_mb * 0.6,
            critical_threshold_mb=max_memory_mb * 0.8,
        )
        self.max_memory_mb = max_memory_mb
        self.tools: Dict[str, MemoryInstrumentedTool] = {}
        self.logger = logging.getLogger(__name__)

        # Register memory alert callback
        self.memory_guard.register_callback(self._on_memory_alert)

    def register_tool(self, tool: MemoryInstrumentedTool):
        """Register a tool with the orchestrator"""
        self.tools[tool.tool_name] = tool
        tool.memory_guard = self.memory_guard

    def _on_memory_alert(self, alert):
        """Handle memory alerts"""
        if alert.level == "critical":
            self.logger.critical(f"CRITICAL MEMORY: {alert.message}. Consider stopping scans or reducing concurrency.")
            # Could trigger automatic scan throttling here
        elif alert.level == "warning":
            self.logger.warning(f"Memory warning: {alert.message}")

    async def execute_with_memory_control(self, tool_name: str, target: str, coro) -> Any:
        """
        Execute a coroutine with memory monitoring and control.

        Args:
            tool_name: Name of the tool
            target: Scan target
            coro: Coroutine to execute

        Returns:
            Result of coroutine execution
        """
        # Check memory before starting
        alert = self.memory_guard.check_memory(f"pre_execute_{tool_name}")
        if alert and alert.level == "critical":
            self.logger.error(f"Cannot start {tool_name} scan: Memory critical ({alert.current_mb:.1f}MB)")
            raise MemoryError(f"Insufficient memory to start scan: {alert.message}")

        start_mem = self.memory_guard.process.memory_info().rss / 1024 / 1024
        start_time = time.time()

        try:
            with memory_context(f"{tool_name}_{target}", self.memory_guard):
                result = await coro

            end_mem = self.memory_guard.process.memory_info().rss / 1024 / 1024

            # Record stats
            if tool_name in self.tools:
                self.tools[tool_name].record_scan_stats(target, time.time() - start_time, end_mem - start_mem)

            return result

        except Exception as e:
            self.logger.error(f"Error in {tool_name} scan: {e}")
            raise

    def get_global_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report across all tools"""
        tool_profiles = {name: tool.get_memory_profile() for name, tool in self.tools.items()}

        return {
            "global_memory": {
                "current_mb": self.memory_guard.process.memory_info().rss / 1024 / 1024,
                "threshold_mb": self.memory_guard.threshold_mb,
                "critical_threshold_mb": self.memory_guard.critical_threshold_mb,
            },
            "tool_profiles": tool_profiles,
            "leak_detection": self.memory_guard.detect_leaks("global_report"),
            "recent_alerts": [
                {
                    "timestamp": a.timestamp,
                    "level": a.level,
                    "message": a.message,
                    "context": a.context,
                }
                for a in self.memory_guard._alerts[-20:]
            ],
        }

    def force_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup across all tools"""
        gc_result = self.memory_guard.force_gc()

        # Reset baseline for leak detection
        self.memory_guard.reset_baseline()

        return {
            "gc_result": gc_result,
            "memory_after_cleanup": self.memory_guard.process.memory_info().rss / 1024 / 1024,
        }


# Integration helpers for existing tools


def instrument_tool_class(tool_class, tool_name: Optional[str] = None):
    """
    Dynamically instrument an existing tool class with memory tracking.

    Usage:
        from tools.nmap_integration import NmapTool

        MemoryNmapTool = instrument_tool_class(NmapTool, "nmap")
        scanner = MemoryNmapTool()
    """

    class InstrumentedTool(MemoryInstrumentedTool, tool_class):
        def __init__(self, *args, **kwargs):
            tool_class.__init__(self, *args, **kwargs)
            MemoryInstrumentedTool.__init__(self)
            if tool_name:
                self.tool_name = tool_name

    return InstrumentedTool


# Performance profiling decorator for sync functions


def profile_memory(tool_name: str):
    """
    Decorator to profile memory usage of tool functions.

    Usage:
        @profile_memory("nmap")
        def run_nmap_scan(target):
            # ... scan code ...
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            guard = MemoryGuard()

            start_mem = guard.process.memory_info().rss / 1024 / 1024
            start_time = time.time()

            result = func(*args, **kwargs)

            end_mem = guard.process.memory_info().rss / 1024 / 1024
            duration = time.time() - start_time

            logging.getLogger(__name__).info(
                f"[{tool_name}] Duration: {duration:.2f}s, Memory delta: {end_mem - start_mem:.2f}MB"
            )

            return result

        return wrapper

    return decorator


# Memory-efficient batch processing


async def memory_efficient_batch(
    items: List[Any],
    process_func,
    batch_size: int = 10,
    memory_guard: Optional[MemoryGuard] = None,
):
    """
    Process items in batches with memory monitoring.
    Automatically pauses if memory is critical.

    Args:
        items: Items to process
        process_func: Async function to process each batch
        batch_size: Number of items per batch
        memory_guard: MemoryGuard instance
    """
    guard = memory_guard or MemoryGuard()
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        # Check memory before batch
        alert = guard.check_memory(f"batch_{i}")
        if alert and alert.level == "critical":
            logging.getLogger(__name__).critical(f"Memory critical ({alert.current_mb:.1f}MB). Pausing batch processing...")
            # Force cleanup
            guard.force_gc()
            await asyncio.sleep(5)  # Wait for memory to settle

        # Process batch
        batch_results = await process_func(batch)
        results.extend(batch_results)

        # Brief pause between batches to allow GC
        await asyncio.sleep(0.1)

    return results


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)

    orchestrator = MemoryAwareOrchestrator(max_memory_mb=1000)

    # Simulate tool execution
    async def demo_scan():
        logger.debug("Starting demo scan with memory monitoring...")

        # Simulate memory usage
        data = []
        for i in range(100):
            data.append("x" * 10000)
            if i % 20 == 0:
                alert = orchestrator.memory_guard.check_memory(f"demo_batch_{i}")
                if alert:
                    logger.debug(f"Alert: {alert.message}")

        return {"status": "completed", "items": len(data)}

    result = asyncio.run(demo_scan())

    report = orchestrator.get_global_memory_report()
    logger.debug("\nMemory Report:")
    logger.debug(f"Current: {report['global_memory']['current_mb']:.1f}MB")
    logger.debug(f"Recent alerts: {len(report['recent_alerts'])}")

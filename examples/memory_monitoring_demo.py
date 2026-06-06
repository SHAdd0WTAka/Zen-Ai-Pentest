#!/usr/bin/env python3
"""
Memory Monitoring Demo for CLAWDBOT/Zen-AI-Pentest
=================================================

Demonstrates memory guard integration with various usage patterns.

Run with:
    python examples/memory_monitoring_demo.py
"""

import asyncio
import gc
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_dashboard import MemoryDashboard
from core.memory_guard import (
    MemoryGuard,
    ValgrindWrapper,
    memory_context,
    track_memory,
)
from core.memory_integration import (
    MemoryInstrumentedTool,
    memory_efficient_batch,
)


def demo_basic_usage():
    """Demo 1: Basic memory monitoring"""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Memory Monitoring")
    print("=" * 60)

    guard = MemoryGuard(threshold_mb=100, critical_threshold_mb=200)

    print("Starting memory check...")

    # Normal memory usage
    alert = guard.check_memory("initial_check")
    print(f"Initial check: {alert}")

    # Create some memory pressure
    print("Allocating memory...")
    data = ["x" * 10000 for _ in range(10000)]

    alert = guard.check_memory("after_allocation")
    if alert:
        print(f"⚠️  Alert: {alert.message}")
    else:
        print("✅ Memory usage normal")

    # Cleanup
    del data
    gc.collect()

    print(f"Snapshots recorded: {len(guard._snapshots)}")


def demo_decorator():
    """Demo 2: Using @track_memory decorator"""
    print("\n" + "=" * 60)
    print("DEMO 2: @track_memory Decorator")
    print("=" * 60)

    guard = MemoryGuard()

    @track_memory("heavy_computation", guard)
    def heavy_computation(n):
        """Simulate heavy memory usage"""
        result = []
        for i in range(n):
            result.append([i] * 1000)
        return sum(sum(row) for row in result)

    print("Running decorated function...")
    result = heavy_computation(100)
    print(f"Result: {result}")
    print(f"Snapshots: {len(guard._snapshots)}")


def demo_context_manager():
    """Demo 3: Using memory_context"""
    print("\n" + "=" * 60)
    print("DEMO 3: memory_context Context Manager")
    print("=" * 60)

    guard = MemoryGuard()

    print("Entering memory context...")
    with memory_context("database_query", guard):
        # Simulate database operation
        data = [{"id": i, "data": "x" * 1000} for i in range(5000)]
        print(f"Loaded {len(data)} records")
        del data

    print("Exited context")
    print(f"Context snapshots: {[s.context for s in guard._snapshots]}")


class DemoScanner(MemoryInstrumentedTool):
    """Demo 4: Tool with memory instrumentation"""

    tool_name = "demo_scanner"

    def scan_target(self, target):
        with self.memory_context(target):
            print(f"  Scanning {target}...")
            # Simulate scan
            results = []
            for i in range(1000):
                results.append(f"result_{i}_{target}")
            return len(results)


def demo_tool_integration():
    """Demo 4: MemoryInstrumentedTool"""
    print("\n" + "=" * 60)
    print("DEMO 4: MemoryInstrumentedTool")
    print("=" * 60)

    scanner = DemoScanner()

    targets = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

    for target in targets:
        count = scanner.scan_target(target)
        print(f"  Found {count} results")

    profile = scanner.get_memory_profile()
    print(f"\nTool Profile: {profile}")


async def demo_batch_processing():
    """Demo 5: Memory-efficient batch processing"""
    print("\n" + "=" * 60)
    print("DEMO 5: Memory-Efficient Batch Processing")
    print("=" * 60)

    items = list(range(50))

    async def process_batch(batch):
        """Process a batch of items"""
        await asyncio.sleep(0.1)  # Simulate async work
        return [x * x for x in batch]

    print(f"Processing {len(items)} items in batches of 10...")

    results = await memory_efficient_batch(items, process_batch, batch_size=10)

    print(f"Processed {len(results)} items")
    print(f"Sample results: {results[:5]}")


def demo_leak_detection():
    """Demo 6: Memory leak detection"""
    print("\n" + "=" * 60)
    print("DEMO 6: Memory Leak Detection")
    print("=" * 60)

    guard = MemoryGuard()
    guard.reset_baseline()

    print("Creating potential memory leak...")
    # Simulate a leak
    leaked_data = []
    for i in range(5):
        leaked_data.extend(["x" * 10000 for _ in range(1000)])
        guard.check_memory(f"iteration_{i}")
        time.sleep(0.1)

    # Check for leaks
    leak_report = guard.detect_leaks("demo_leak")

    if leak_report:
        print(f"⚠️  Leaks detected: {leak_report['total_leaked_mb']:.1f}MB")
        for leak in leak_report["leaks"][:3]:
            print(f"  - {leak['file']}: {leak['size_diff_mb']:.1f}MB")
    else:
        print("✅ No significant leaks detected")

    # Cleanup
    del leaked_data
    gc.collect()


def demo_reporting():
    """Demo 7: Report generation"""
    print("\n" + "=" * 60)
    print("DEMO 7: Report Generation")
    print("=" * 60)

    guard = MemoryGuard()

    # Simulate various operations
    for i in range(10):
        guard.check_memory(f"operation_{i}")
        time.sleep(0.05)

    # Generate report
    report_path = guard.generate_report()
    print(f"Report saved to: {report_path}")

    # Show summary
    import json

    with open(report_path) as f:
        report = json.load(f)

    print("\nReport Summary:")
    print(f"  Total snapshots: {report['summary']['total_snapshots']}")
    print(f"  Total alerts: {report['summary']['total_alerts']}")
    print(f"  Generated: {report['generated_at']}")


def demo_valgrind_check():
    """Demo 8: Valgrind integration"""
    print("\n" + "=" * 60)
    print("DEMO 8: Valgrind Integration")
    print("=" * 60)

    wrapper = ValgrindWrapper()

    print(f"Valgrind available: {wrapper.available}")

    if wrapper.available:
        print("Running quick Valgrind check...")
        # This would take a while, so we just show the API
        print("Usage:")
        print("  wrapper.check_python_module('my_module')")
        print("  wrapper.quick_check('script.py')")
    else:
        print("Valgrind not installed. Install with:")
        print("  sudo apt install valgrind")


def demo_dashboard():
    """Demo 9: Live dashboard (if Rich is available)"""
    print("\n" + "=" * 60)
    print("DEMO 9: Live Dashboard")
    print("=" * 60)

    try:
        from rich.console import Console  # noqa: F401
        from rich.panel import Panel  # noqa: F401

        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

    guard = MemoryGuard()
    dashboard = MemoryDashboard(guard)

    if RICH_AVAILABLE:
        print("Rich available! Showing dashboard for 3 seconds...")
        print("(In real usage, use with dashboard.live_display():)")

        # Simulate work while showing dashboard
        try:
            with dashboard.live_display():
                for i in range(3):
                    # Allocate some memory
                    data = ["x" * 10000 for _ in range(1000)]
                    guard.check_memory(f"dashboard_demo_{i}")
                    del data
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("Rich not available. Simple display:")
        print(dashboard.get_simple_display())


async def main():
    """Run all demos"""
    print("\n" + "🛡️ " * 20)
    print("CLAWDBOT Memory Guard - Interactive Demo")
    print("🛡️ " * 20)

    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Decorator", demo_decorator),
        ("Context Manager", demo_context_manager),
        ("Tool Integration", demo_tool_integration),
        ("Batch Processing", demo_batch_processing),
        ("Leak Detection", demo_leak_detection),
        ("Reporting", demo_reporting),
        ("Valgrind", demo_valgrind_check),
        ("Dashboard", demo_dashboard),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            if asyncio.iscoroutinefunction(demo_func):
                await demo_func()
            else:
                demo_func()
        except Exception as e:
            print(f"Error in demo {name}: {e}")

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("  - core/MEMORY_README.md")
    print("  - core/memory_guard.py")
    print("  - tests/test_memory.py")


if __name__ == "__main__":
    asyncio.run(main())

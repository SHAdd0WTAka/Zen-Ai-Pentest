#!/usr/bin/env python3
"""
Performance Profiling Tool for Zen-AI-Pentest

Usage:
    python scripts/profile_performance.py --target core.cache
    python scripts/profile_performance.py --target api.main --line_profiler
    python scripts/profile_performance.py --memory
    python scripts/profile_performance.py --importtime
"""

import argparse
import cProfile
import importlib
import io
import pstats
import sys
import time
import tracemalloc
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def profile_imports():
    """Profile import times for key modules"""
    print("=" * 70)
    print("IMPORT TIME PROFILING")
    print("=" * 70)

    modules = [
        "core.cache",
        "core.database",
        "core.orchestrator",
        "core.models",
        "api.main",
        "api.routes.scans",
        "agents.react_agent",
        "tools.nmap_integration",
        "database.models",
    ]

    results = []
    for module in modules:
        # Clear from cache if already imported
        if module in sys.modules:
            del sys.modules[module]

        start = time.perf_counter()
        try:
            importlib.import_module(module)
            elapsed = (time.perf_counter() - start) * 1000
            results.append((module, elapsed, True))
            print(f"  {module:40s} {elapsed:8.2f}ms ✓")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            results.append((module, elapsed, False))
            print(f"  {module:40s} {elapsed:8.2f}ms ✗ ({e})")

    # Summary
    print("\n" + "-" * 70)
    successful = [r for r in results if r[2]]
    if successful:
        total_time = sum(r[1] for r in successful)
        avg_time = total_time / len(successful)
        slowest = max(successful, key=lambda x: x[1])

        print(f"Total import time: {total_time:.2f}ms")
        print(f"Average import time: {avg_time:.2f}ms")
        print(f"Slowest module: {slowest[0]} ({slowest[1]:.2f}ms)")

    return results


def profile_function(
    target: str, sort_by: str = "cumulative", lines: int = 50
):
    """Profile a specific function or module"""
    print("=" * 70)
    print(f"FUNCTION PROFILING: {target}")
    print("=" * 70)

    # Parse target (module.function or module.class.method)
    parts = target.split(".")
    module_name = parts[0]
    obj_path = parts[1:] if len(parts) > 1 else []

    # Import module
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Error importing {module_name}: {e}")
        return

    # Get target object
    obj = module
    for attr in obj_path:
        obj = getattr(obj, attr)

    # Profile
    profiler = cProfile.Profile()
    profiler.enable()

    start = time.perf_counter()

    # Call the function if callable, otherwise just access it
    if callable(obj):
        try:
            if hasattr(obj, "__self__"):  # bound method
                result = obj()
            else:
                result = obj()
        except Exception as e:
            print(f"Error calling {target}: {e}")
            result = None
    else:
        result = obj

    elapsed = (time.perf_counter() - start) * 1000

    profiler.disable()

    # Print stats
    s = io.StringIO()
    sort_key = sort_by
    ps = pstats.Stats(profiler, stream=s).sort_stats(sort_key)
    ps.print_stats(lines)

    print(f"\nExecution time: {elapsed:.2f}ms")
    print("\n" + "-" * 70)
    print(s.getvalue())

    return profiler


def profile_memory(target: str = None):
    """Profile memory usage"""
    print("=" * 70)
    print("MEMORY PROFILING")
    print("=" * 70)

    tracemalloc.start()

    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    start_mem = tracemalloc.get_traced_memory()[0] / 1024 / 1024

    if target:
        # Execute target
        parts = target.split(".")
        module_name = parts[0]
        obj_path = parts[1:] if len(parts) > 1 else []

        module = importlib.import_module(module_name)
        obj = module
        for attr in obj_path:
            obj = getattr(obj, attr)

        if callable(obj):
            obj()
        else:
            print(f"Accessed: {target}")
    else:
        # Import common modules
        modules = [
            "core.cache",
            "core.database",
            "api.main",
            "database.models",
        ]
        for mod in modules:
            try:
                importlib.import_module(mod)
                print(f"Imported: {mod}")
            except Exception as e:
                print(f"Failed to import {mod}: {e}")

    # Take final snapshot
    snapshot2 = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    end_mem = current / 1024 / 1024

    tracemalloc.stop()

    # Calculate delta
    delta = end_mem - start_mem

    print(f"\n{'─' * 70}")
    print("Memory Usage:")
    print(f"  Start: {start_mem:.2f}MB")
    print(f"  End: {end_mem:.2f}MB")
    print(f"  Delta: {delta:+.2f}MB")
    print(f"  Peak: {peak / 1024 / 1024:.2f}MB")

    # Top memory consumers
    print(f"\n{'─' * 70}")
    print("Top Memory Consumers:")
    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    for stat in top_stats[:15]:
        print(f"  {stat}")

    return snapshot2


def analyze_hotspots(module_name: str, function_name: str = None):
    """Analyze performance hotspots in a module"""
    print("=" * 70)
    print(f"HOTSPOT ANALYSIS: {module_name}")
    print("=" * 70)

    # Import and profile
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Error importing {module_name}: {e}")
        return

    # Get all functions
    import inspect

    functions = [
        (name, obj)
        for name, obj in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_")
    ]

    if function_name:
        functions = [(n, f) for n, f in functions if n == function_name]

    if not functions:
        print(f"No functions found in {module_name}")
        return

    results = []
    for name, func in functions:
        # Quick timing
        iterations = 100
        start = time.perf_counter()
        try:
            for _ in range(iterations):
                # Try to call with no args or sample args
                sig = inspect.signature(func)
                if len(sig.parameters) == 0:
                    func()
                elif all(
                    p.default != inspect.Parameter.empty
                    for p in sig.parameters.values()
                ):
                    func()
        except Exception as e:
            results.append((name, 0, f"Error: {e}"))
            continue

        elapsed = (time.perf_counter() - start) * 1000
        per_call = elapsed / iterations
        results.append((name, per_call, None))

    # Sort by time
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'─' * 70}")
    print(f"{'Function':<40} {'Time/call (ms)':>15} {'Status':>10}")
    print("-" * 70)

    for name, per_call, error in results[:20]:
        if error:
            print(f"{name:<40} {'N/A':>15} {error:>10}")
        else:
            print(f"{name:<40} {per_call:>15.4f} {'✓':>10}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Performance Profiling Tool for Zen-AI-Pentest"
    )
    parser.add_argument(
        "--target",
        help="Target module/function to profile (e.g., core.cache.MemoryCache)",
    )
    parser.add_argument(
        "--importtime", action="store_true", help="Profile import times"
    )
    parser.add_argument(
        "--memory", action="store_true", help="Profile memory usage"
    )
    parser.add_argument(
        "--hotspots", help="Analyze hotspots in a module (e.g., core.cache)"
    )
    parser.add_argument(
        "--sort",
        default="cumulative",
        choices=[
            "calls",
            "cumulative",
            "file",
            "module",
            "pcalls",
            "time",
            "tottime",
        ],
        help="Sort key for profiler output",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=50,
        help="Number of lines to show in profiler output",
    )
    parser.add_argument("--save", help="Save profile to file")

    args = parser.parse_args()

    if args.importtime:
        profile_imports()
    elif args.memory:
        profile_memory(args.target)
    elif args.hotspots:
        analyze_hotspots(args.hotspots)
    elif args.target:
        profiler = profile_function(args.target, args.sort, args.lines)
        if args.save and profiler:
            profiler.dump_stats(args.save)
            print(f"\nProfile saved to: {args.save}")
    else:
        # Default: profile imports
        profile_imports()


if __name__ == "__main__":
    main()

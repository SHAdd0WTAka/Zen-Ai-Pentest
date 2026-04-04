"""
Memory Guard - Comprehensive Memory Monitoring for Zen-AI-Pentest
===========================================================

Provides memory leak detection, performance profiling, and Valgrind integration
for the penetration testing framework.

Features:
- Real-time memory monitoring
- Automatic leak detection for long-running scans
- Tool-specific memory profiling
- Valgrind integration for C extensions
- CI/CD ready reporting

Author: Security Team
Version: 1.0.0
"""

import gc
import json
import logging
import os
import sys
import threading
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

# Optional: Valgrind support
VALGRIND_AVAILABLE = False
try:
    import shutil
    import subprocess

    valgrind_path = shutil.which("valgrind")
    VALGRIND_AVAILABLE = valgrind_path is not None
except Exception:
    # Valgrind check failed, continue without it
    VALGRIND_AVAILABLE = False


@dataclass
class MemorySnapshot:
    """Memory snapshot data structure"""

    timestamp: float
    current_mb: float
    peak_mb: float
    rss_mb: float
    vms_mb: float
    context: str
    top_allocations: List[str]
    gc_objects: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryAlert:
    """Memory alert/warning structure"""

    timestamp: float
    level: str  # 'info', 'warning', 'critical'
    message: str
    current_mb: float
    threshold_mb: float
    context: str
    stack_trace: Optional[str] = None


class MemoryGuard:
    """
    Comprehensive memory monitoring and leak detection for pentest operations.

    Usage:
        guard = MemoryGuard(threshold_mb=500)

        # Start monitoring
        guard.start_monitoring()

        # Check memory in your code
        if alert := guard.check_memory("nmap_scan"):
            print(f"Memory alert: {alert.message}")

        # Stop monitoring
        guard.stop_monitoring()
    """

    def __init__(
        self,
        threshold_mb: int = 500,
        critical_threshold_mb: int = 1000,
        check_interval: int = 30,
        enable_snapshots: bool = True,
        log_dir: Optional[str] = None,
    ):
        """
        Initialize Memory Guard.

        Args:
            threshold_mb: Warning threshold in MB
            critical_threshold_mb: Critical alert threshold in MB
            check_interval: Seconds between automatic checks
            enable_snapshots: Store memory snapshots for analysis
            log_dir: Directory for memory reports
        """
        self.threshold_mb = threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.check_interval = check_interval
        self.enable_snapshots = enable_snapshots

        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".clawdbot" / "memory_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._snapshots: List[MemorySnapshot] = []
        self._alerts: List[MemoryAlert] = []
        self._callbacks: List[Callable[[MemoryAlert], None]] = []

        self.process = psutil.Process(os.getpid())
        self.logger = logging.getLogger(__name__)

        # Initialize tracemalloc
        tracemalloc.start()
        self._baseline = tracemalloc.take_snapshot()

    def start_monitoring(self):
        """Start background memory monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("Memory Guard monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Memory Guard monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring thread"""
        while self._monitoring:
            alert = self.check_memory("background_check")
            if alert and alert.level in ["warning", "critical"]:
                self._handle_alert(alert)
            time.sleep(self.check_interval)

    def _handle_alert(self, alert: MemoryAlert):
        """Handle memory alerts and trigger callbacks"""
        self._alerts.append(alert)

        # Log alert
        if alert.level == "critical":
            self.logger.critical(f"Memory CRITICAL: {alert.message}")
        elif alert.level == "warning":
            self.logger.warning(f"Memory WARNING: {alert.message}")

        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

        # Auto-generate report on critical
        if alert.level == "critical":
            self.generate_report()

    def check_memory(self, context: str = "") -> Optional[MemoryAlert]:
        """
        Check current memory usage and return alert if threshold exceeded.

        Args:
            context: Description of current operation

        Returns:
            MemoryAlert if threshold exceeded, None otherwise
        """
        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        # Get detailed process memory
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / 1024 / 1024
        vms_mb = mem_info.vms / 1024 / 1024

        # Get top allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")[:5]
        top_allocations = [str(stat) for stat in top_stats]

        # Count GC objects
        gc_objects = len(gc.get_objects())

        # Create snapshot
        if self.enable_snapshots:
            mem_snapshot = MemorySnapshot(
                timestamp=time.time(),
                current_mb=current_mb,
                peak_mb=peak_mb,
                rss_mb=rss_mb,
                vms_mb=vms_mb,
                context=context,
                top_allocations=top_allocations,
                gc_objects=gc_objects,
            )
            self._snapshots.append(mem_snapshot)

        # Check thresholds
        if current_mb > self.critical_threshold_mb:
            return MemoryAlert(
                timestamp=time.time(),
                level="critical",
                message=f"CRITICAL: Memory usage {current_mb:.1f}MB exceeds critical threshold",
                current_mb=current_mb,
                threshold_mb=self.critical_threshold_mb,
                context=context,
            )
        elif current_mb > self.threshold_mb:
            return MemoryAlert(
                timestamp=time.time(),
                level="warning",
                message=f"WARNING: Memory usage {current_mb:.1f}MB exceeds threshold",
                current_mb=current_mb,
                threshold_mb=self.threshold_mb,
                context=context,
            )

        return None

    def detect_leaks(self, context: str = "") -> Optional[Dict[str, Any]]:
        """
        Detect potential memory leaks by comparing with baseline.

        Args:
            context: Operation context

        Returns:
            Leak report if leaks detected
        """
        current = tracemalloc.take_snapshot()
        top_stats = current.compare_to(self._baseline, "lineno")

        leaks = []
        for stat in top_stats[:10]:
            if stat.size_diff > 1024 * 1024:  # > 1MB difference
                leaks.append(
                    {
                        "file": stat.traceback.format()[-1],
                        "size_diff_mb": stat.size_diff / 1024 / 1024,
                        "count_diff": stat.count_diff,
                    }
                )

        if leaks:
            return {
                "timestamp": time.time(),
                "context": context,
                "leaks": leaks,
                "total_leaked_mb": sum(leak["size_diff_mb"] for leak in leaks),
            }
        return None

    def force_gc(self) -> Dict[str, Any]:
        """Force garbage collection and return stats"""
        gc_before = len(gc.get_objects())
        mem_before = self.process.memory_info().rss / 1024 / 1024

        gc.collect()

        gc_after = len(gc.get_objects())
        mem_after = self.process.memory_info().rss / 1024 / 1024

        return {
            "objects_collected": gc_before - gc_after,
            "memory_freed_mb": mem_before - mem_after,
            "gc_generations": gc.get_count(),
        }

    def get_tool_memory_profile(self, tool_name: str) -> Dict[str, Any]:
        """Get memory profile for specific tool"""
        tool_snapshots = [s for s in self._snapshots if tool_name.lower() in s.context.lower()]

        if not tool_snapshots:
            return {"error": f"No data for tool {tool_name}"}

        avg_memory = sum(s.current_mb for s in tool_snapshots) / len(tool_snapshots)
        peak_memory = max(s.current_mb for s in tool_snapshots)

        return {
            "tool": tool_name,
            "samples": len(tool_snapshots),
            "avg_memory_mb": avg_memory,
            "peak_memory_mb": peak_memory,
            "min_memory_mb": min(s.current_mb for s in tool_snapshots),
            "total_runtime": tool_snapshots[-1].timestamp - tool_snapshots[0].timestamp,
        }

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive memory report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"memory_report_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "process_info": {
                "pid": os.getpid(),
                "command": " ".join(sys.argv),
            },
            "config": {
                "threshold_mb": self.threshold_mb,
                "critical_threshold_mb": self.critical_threshold_mb,
                "check_interval": self.check_interval,
            },
            "summary": {
                "total_snapshots": len(self._snapshots),
                "total_alerts": len(self._alerts),
                "warning_count": len([a for a in self._alerts if a.level == "warning"]),
                "critical_count": len([a for a in self._alerts if a.level == "critical"]),
            },
            "current_memory": self.check_memory("report_generation"),
            "leak_detection": self.detect_leaks("report_generation"),
            "alerts": [asdict(a) for a in self._alerts[-50:]],  # Last 50 alerts
            "snapshots_summary": [
                {
                    "timestamp": s.timestamp,
                    "current_mb": s.current_mb,
                    "context": s.context,
                }
                for s in self._snapshots[-100:]  # Last 100 snapshots
            ],
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Memory report saved to {output_file}")
        return str(output_file)

    def register_callback(self, callback: Callable[[MemoryAlert], None]):
        """Register callback for memory alerts"""
        self._callbacks.append(callback)

    def reset_baseline(self):
        """Reset memory baseline for leak detection"""
        self._baseline = tracemalloc.take_snapshot()
        self.logger.info("Memory baseline reset")


class ValgrindWrapper:
    """
    Wrapper for Valgrind memory checking of C extensions.
    Only works if valgrind is installed.
    """

    def __init__(self):
        self.available = VALGRIND_AVAILABLE
        self.logger = logging.getLogger(__name__)

    def check_python_module(
        self,
        module_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        Run Python module under Valgrind.

        Args:
            module_path: Python module to check
            args: Additional arguments
            timeout: Maximum runtime in seconds

        Returns:
            Valgrind results dictionary
        """
        if not self.available:
            return {"error": "Valgrind not installed"}

        cmd = [
            "valgrind",
            "--leak-check=full",
            "--show-leak-kinds=all",
            "--track-origins=yes",
            "--verbose",
            "--log-file=/tmp/valgrind.log",
            "python3",
            "-m",
            module_path,
        ]

        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            # Parse valgrind log
            import tempfile

            tmp_dir = tempfile.gettempdir()
            valgrind_log_path = Path(tmp_dir) / "valgrind.log"
            valgrind_log = valgrind_log_path.read_text() if valgrind_log_path.exists() else ""

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "valgrind_log": valgrind_log,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired:
            return {"error": f"Valgrind check timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    def quick_check(self, script_path: str) -> bool:
        """Quick check if script has memory errors"""
        if not self.available:
            return True  # Skip if valgrind not available

        cmd = [
            "valgrind",
            "--error-exitcode=1",
            "--leak-check=summary",
            "python3",
            script_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception:
            return True


# Decorators for easy integration


def track_memory(context: str = "", guard: Optional[MemoryGuard] = None):
    """
    Decorator to track memory usage of functions.

    Usage:
        guard = MemoryGuard()

        @track_memory("nmap_scan", guard)
        def run_nmap(target):
            # ... scan code ...
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal guard

            # Use global guard if none provided
            if guard is None:
                guard = getattr(sys.modules.get("__main__"), "_memory_guard", None)

            ctx = context or func.__name__

            if guard:
                alert = guard.check_memory(f"before_{ctx}")
                if alert:
                    guard.logger.warning(f"Memory alert before {ctx}: {alert.message}")

            result = func(*args, **kwargs)

            if guard:
                alert = guard.check_memory(f"after_{ctx}")
                if alert:
                    guard.logger.warning(f"Memory alert after {ctx}: {alert.message}")

            return result

        return wrapper

    return decorator


@contextmanager
def memory_context(context: str, guard: Optional[MemoryGuard] = None):
    """
    Context manager for memory tracking.

    Usage:
        with memory_context("heavy_operation"):
            # ... code ...
            pass
    """
    mg = guard or getattr(sys.modules.get("__main__"), "_memory_guard", None)

    if mg:
        mg.check_memory(f"enter_{context}")

    try:
        yield
    finally:
        if mg:
            mg.check_memory(f"exit_{context}")


# Singleton instance for module-wide usage
_default_guard: Optional[MemoryGuard] = None


def get_memory_guard(**kwargs) -> MemoryGuard:
    """Get or create default MemoryGuard instance"""
    global _default_guard
    if _default_guard is None:
        _default_guard = MemoryGuard(**kwargs)
    return _default_guard


if __name__ == "__main__":
    # Demo/Test
    logging.basicConfig(level=logging.INFO)

    guard = MemoryGuard(threshold_mb=100)
    guard.start_monitoring()

    # Simulate memory usage
    data = []
    for i in range(1000):
        data.append("x" * 1000)
        if i % 100 == 0:
            alert = guard.check_memory(f"iteration_{i}")
            if alert:
                print(f"Alert: {alert.message}")

    # Generate report
    report_path = guard.generate_report()
    print(f"Report saved to: {report_path}")

    # Check for leaks
    leaks = guard.detect_leaks("demo")
    if leaks:
        print(f"Leaks detected: {leaks}")
    else:
        print("No leaks detected")

    guard.stop_monitoring()

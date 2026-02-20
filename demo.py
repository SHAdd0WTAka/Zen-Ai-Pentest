#!/usr/bin/env python3
"""
Zen-AI-Pentest Demo Script

Performs a complete demonstration scan workflow on scanme.nmap.org
(Safe target provided by Nmap for testing)
"""

import asyncio
import json
from datetime import datetime

# Target: Nmap's official test server (safe to scan)
TARGET = "scanme.nmap.org"


async def demo_workflow():
    """Run complete demo workflow"""

    print("=" * 70)
    print(" ZEN-AI-PENTEST DEMO")
    print(f" Target: {TARGET}")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Step 1: Check system status
    print("[1/5] Checking system status...")
    try:
        from tools.integrations.tool_checker import ToolChecker

        checker = ToolChecker()
        report = checker.get_status_report()

        print(f"      Required Tools: {report['required']['available']}/{report['required']['total']}")
        print(f"      Optional Tools: {report['optional']['available']}/{report['optional']['total']}")
        print(f"      System Ready: {report['ready']}")
    except Exception as e:
        print(f"      Error: {e}")
    print()

    # Step 2: Initialize components
    print("[2/5] Initializing components...")
    try:
        from dashboard import DashboardConfig, DashboardManager
        from orchestrator import OrchestratorConfig, ZenOrchestrator
        from performance import CacheManager

        # Create instances
        config = OrchestratorConfig(max_workers=2)
        orchestrator = ZenOrchestrator(config)
        dashboard = DashboardManager(DashboardConfig(websocket_enabled=False))
        cache = CacheManager()

        # Start
        await orchestrator.start()
        await dashboard.start()
        await cache.start()

        print("      Orchestrator: Started")
        print("      Dashboard: Started")
        print("      Cache: Started")
    except Exception as e:
        print(f"      Error: {e}")
        return
    print()

    # Step 3: Submit scan task
    print("[3/5] Submitting scan task...")
    try:
        task_data = {"type": "vulnerability_scan", "target": TARGET, "options": {"ports": "22,80,443", "scan_type": "quick"}}

        task_id = await orchestrator.submit_task(task_data=task_data, priority="normal")

        print(f"      Task ID: {task_id}")
        print(f"      Target: {TARGET}")
        print("      Type: vulnerability_scan")
    except Exception as e:
        print(f"      Error: {e}")
        return
    print()

    # Step 4: Monitor task
    print("[4/5] Monitoring task progress...")
    max_wait = 30  # seconds
    waited = 0

    while waited < max_wait:
        try:
            status = await orchestrator.get_task_status(task_id)
            state = status.get("state", "unknown")
            progress = status.get("progress", 0)

            print(f"      Status: {state}, Progress: {progress:.1f}%")

            if state in ["completed", "failed"]:
                break

            await asyncio.sleep(2)
            waited += 2

        except Exception as e:
            print(f"      Error: {e}")
            break
    print()

    # Step 5: Show results
    print("[5/5] Retrieving results...")
    try:
        results = await orchestrator.get_task_results(task_id)

        if results:
            print("      Results:")
            print(json.dumps(results, indent=6, default=str))
        else:
            print("      No results yet (task may still be running)")
    except Exception as e:
        print(f"      Error: {e}")
    print()

    # Cleanup
    print("[*] Cleaning up...")
    try:
        await cache.stop()
        await dashboard.stop()
        await orchestrator.stop()
        print("      All components stopped")
    except Exception as e:
        print(f"      Error during cleanup: {e}")
    print()

    # Summary
    print("=" * 70)
    print(" DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Target scanned: {TARGET}")
    print(f"  - Task ID: {task_id}")
    print("  - Components tested: Orchestrator, Dashboard, Cache")
    print()
    print("For full scan results, check the API:")
    print(f"  GET /api/v1/orchestrator/tasks/{task_id}/results")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(demo_workflow())
    except KeyboardInterrupt:
        print("\n\n[!] Demo interrupted by user")
    except Exception as e:
        print(f"\n\n[!] Demo failed: {e}")
        import traceback

        traceback.print_exc()

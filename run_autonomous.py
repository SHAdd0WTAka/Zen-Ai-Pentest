#!/usr/bin/env python3
"""
Autonomer LLM Scan - Das LLM macht alles automatisch!
"""

import asyncio
import os
import sys

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.async_fixes import (
    apply_windows_async_fixes,
    silence_asyncio_warnings,
)
from zen_ai_pentest import ZenAIPentest

apply_windows_async_fixes()
silence_asyncio_warnings()


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    goal = sys.argv[2] if len(sys.argv) > 2 else "Find vulnerabilities"

    print("=" * 60)
    print("ZEN AI PENTEST - AUTONOMOUS MODE")
    print("=" * 60)
    print(f"Target: {target}")
    print(f"Goal: {goal}")
    print("=" * 60)

    # Initialize
    app = ZenAIPentest()
    await app.initialize_backends()

    # Run autonomous scan
    result = await app.run_autonomous_scan(target=target, goal=goal)

    print("\n" + "=" * 60)
    print("AUTONOMOUS SCAN COMPLETE")
    print("=" * 60)
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Success: {result.get('success', False)}")

    if result.get("success"):
        findings = result.get("findings", {})
        print(f"Findings: {findings.get('count', 0)}")

        # Generate report
        await app.generate_report(target, "markdown")
        print("\nReport generated!")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    try:
        if sys.platform == "win32" and sys.version_info >= (3, 13):
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback

        traceback.print_exc()

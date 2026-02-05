#!/usr/bin/env python3
"""
Basic Usage Example for Zen AI Pentest
Author: SHAdd0WTAka
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.duckduckgo import DuckDuckGoBackend
from core.orchestrator import QualityLevel, ZenOrchestrator
from modules.recon import ReconModule
from modules.vuln_scanner import VulnScannerModule


async def basic_example():
    """Basic usage example"""
    print("=" * 60)
    print("Zen AI Pentest - Basic Usage Example")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = ZenOrchestrator()

    # Add DuckDuckGo backend (free, no auth required)
    async with DuckDuckGoBackend() as ddg:
        orchestrator.add_backend(ddg)

        print("\n[1] Testing LLM Backend...")
        test_response = await orchestrator.process(
            "What is penetration testing? Answer in one sentence.", QualityLevel.LOW
        )
        print(f"Response from {test_response.source}: {test_response.content[:100]}...")
        print(f"Latency: {test_response.latency:.2f}s")

        # Initialize modules
        print("\n[2] Initializing Modules...")
        _ = ReconModule(orchestrator)
        vuln_scanner = VulnScannerModule(orchestrator)

        # Example: Reconnaissance
        print("\n[3] Running Reconnaissance...")
        target = "example.com"
        print(f"Target: {target}")

        # Basic target validation
        from utils.helpers import validate_target

        validation = validate_target(target)
        print(f"Validation: {validation}")

        # Example nmap output analysis
        print("\n[4] Analyzing Sample Nmap Output...")
        sample_nmap = """
Nmap scan report for example.com (93.184.216.34)
Host is up (0.012s latency).
Not shown: 996 filtered ports
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.5
80/tcp  open  http     Apache httpd 2.4.41
443/tcp open  ssl/http Apache httpd 2.4.41
3306/tcp open mysql   MySQL 5.7.38
"""

        vulns = await vuln_scanner.analyze_nmap_output(sample_nmap)
        print(f"Found {len(vulns)} vulnerabilities:")

        for vuln in vulns:
            print(f"  - [{vuln.severity}] {vuln.name}")

        # Get severity summary
        summary = vuln_scanner.get_severity_summary(vulns)
        print(f"\nSummary: {summary}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(basic_example())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    except Exception as e:
        print(f"[!] Error: {e}")

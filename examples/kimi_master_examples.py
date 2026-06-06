#!/usr/bin/env python3
"""
Kimi Master Agent Examples
==========================

Shows how to use the Kimi Master Agent for AI-powered pentesting.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.kimi_master_agent import (
    KimiMasterAgent,
    KimiSwarmController,
    SwarmConfig,
    analyze_with_kimi,
    quick_scan,
)


def example_basic_usage():
    """Basic usage of Kimi Master Agent"""
    print("=" * 60)
    print("Example 1: Basic Kimi Master Agent")
    print("=" * 60)

    async def run():
        # Create master agent
        master = KimiMasterAgent()

        # Initialize (authenticates with Kimi CLI)
        success = await master.initialize()

        if not success:
            print("\n⚠️  Failed to initialize")
            print("   Make sure you ran: kimi login")
            return

        # Show auth status
        status = master.get_auth_status()
        print(f"\n✅ Authenticated: {status['authenticated']}")
        print(f"   Token: {status['token_preview']}")

        # Run swarm scan
        print("\n🎯 Running swarm scan...")
        results = await master.run_swarm_scan("example.com", "quick")

        print("\n📊 Results:")
        print(f"   Target: {results.get('target')}")
        print(f"   Findings: {len(results.get('scan_results', {}).get('findings', []))}")
        print(f"   AI Enhanced: {results.get('kimi_enhanced')}")

    asyncio.run(run())


def example_swarm_controller():
    """Using the high-level Swarm Controller"""
    print("\n" + "=" * 60)
    print("Example 2: Kimi Swarm Controller")
    print("=" * 60)

    async def run():
        # Create controller
        controller = KimiSwarmController()

        # Initialize
        success = await controller.start()
        if not success:
            print("\n⚠️  Not authenticated")
            return

        # Run multiple scans
        targets = ["site1.com", "site2.com", "site3.com"]
        scan_ids = []

        for target in targets:
            print(f"\n🚀 Scanning {target}...")
            scan_id = await controller.scan_target(target, "quick")
            scan_ids.append(scan_id)
            print(f"   Scan ID: {scan_id}")

        # Check all results
        print("\n📊 All Scans Complete:")
        for scan_id in scan_ids:
            result = controller.get_scan_status(scan_id)
            print(f"   {scan_id}: {result['target']} - {result['status']}")

    asyncio.run(run())


def example_custom_config():
    """Custom configuration"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Configuration")
    print("=" * 60)

    # Custom config
    config = SwarmConfig(
        scanner_email="custom-scanner@company.local",
        analyzer_email="custom-analyzer@company.local",
        reporter_email="custom-reporter@company.local",
        kimi_model="kimi-for-coding",
        use_kimi_for_analysis=True,
        max_concurrent_agents=5,
    )

    KimiMasterAgent(config)

    print("\nCustom Config:")
    print(f"   Scanner: {config.scanner_email}")
    print(f"   Analyzer: {config.analyzer_email}")
    print(f"   Reporter: {config.reporter_email}")
    print(f"   Max Concurrent: {config.max_concurrent_agents}")
    print(f"   AI Analysis: {config.use_kimi_for_analysis}")


def example_ask_kimi():
    """Query Kimi for security advice"""
    print("\n" + "=" * 60)
    print("Example 4: Ask Kimi AI")
    print("=" * 60)

    async def run():
        controller = KimiSwarmController()
        await controller.start()

        questions = [
            "How should I prioritize SQL Injection vs XSS vulnerabilities?",
            "What are the most common misconfigurations in Apache web servers?",
            "Explain the difference between CSRF and SSRF",
        ]

        for question in questions:
            print(f"\n❓ Question: {question}")
            answer = await controller.ask_kimi(question)
            print(f"💡 Kimi: {answer[:100]}...")

    asyncio.run(run())


def example_quick_scan():
    """One-liner quick scan"""
    print("\n" + "=" * 60)
    print("Example 5: Quick One-Liner Scan")
    print("=" * 60)

    async def run():
        # Just one line!
        results = await quick_scan("target.example.com")

        print("\nQuick scan results:")
        print(f"   {results}")

    asyncio.run(run())


def example_analyze_findings():
    """Analyze findings with Kimi"""
    print("\n" + "=" * 60)
    print("Example 6: AI-Powered Analysis")
    print("=" * 60)

    async def run():
        # Sample findings
        findings = [
            {
                "id": "VULN-001",
                "severity": "critical",
                "title": "SQL Injection",
            },
            {"id": "VULN-002", "severity": "high", "title": "XSS"},
            {"id": "VULN-003", "severity": "medium", "title": "CSRF"},
        ]

        print(f"\nAnalyzing {len(findings)} findings with Kimi AI...")
        analysis = await analyze_with_kimi(findings)

        print("\n🧠 Kimi Analysis:")
        print(f"   {analysis}")

    asyncio.run(run())


def example_integration_with_email_chain():
    """Integration with agent email chain"""
    print("\n" + "=" * 60)
    print("Example 7: Integration with Email Chain")
    print("=" * 60)

    from agent_comm.email_chain import AgentEmailNode, AgentHandlers

    async def run():
        # Create master
        master = KimiMasterAgent()
        await master.initialize()

        # Create custom agents
        scanner = AgentEmailNode(
            email="scanner@pentest.local",
            role="scanner",
            handler=AgentHandlers.scan_handler,
        )

        analyzer = AgentEmailNode(
            email="analyzer@pentest.local",
            role="analyzer",
            handler=AgentHandlers.analyze_handler,
        )

        # Master coordinates them
        print("\n🎯 Coordinating agents via email chain...")
        results = await master.coordinate_agents(
            agents=[scanner, analyzer],
            task={
                "target": "example.com",
                "scan_type": "full",
                "kimi_token": master.auth_token,
            },
        )

        print("\n✅ Coordination complete:")
        for result in results:
            print(f"   {result['agent']}: {result['status']}")

    asyncio.run(run())


def show_architecture():
    """Show system architecture"""
    print("\n" + "=" * 60)
    print("Kimi Master Agent Architecture")
    print("=" * 60)

    print("""
                    ┌─────────────────────────────────────┐
                    │      🌙 KIMI MASTER AGENT           │
                    │         (Central Brain)             │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │  Kimi CLI Auth  │  │  Agent Chain    │  │  AI Analysis    │
    │  (OAuth Token)  │  │  (Email/Base64) │  │  (Kimi API)     │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Secure Storage  │  │ Scanner Agent   │  │ Vuln Analysis   │
    │ ~/.kimi/creds   │  │ Analyzer Agent  │  │ Risk Scoring    │
    │                 │  │ Reporter Agent  │  │ Recommendations │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
    """)

    print("\nFlow:")
    print("  1. Kimi Master reads OAuth token from Kimi CLI")
    print("  2. Coordinates agents via Base64-encoded email messages")
    print("  3. Each agent processes and passes to next via email")
    print("  4. Kimi AI analyzes results and provides recommendations")
    print("  5. Final report generated and sent to user")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" 🌙 Kimi Master Agent - Examples")
    print("=" * 70)

    examples = [
        ("Architecture Overview", show_architecture),
        ("Basic Usage", example_basic_usage),
        ("Swarm Controller", example_swarm_controller),
        ("Custom Config", example_custom_config),
        ("Ask Kimi AI", example_ask_kimi),
        ("Quick Scan", example_quick_scan),
        ("AI Analysis", example_analyze_findings),
        ("Email Chain Integration", example_integration_with_email_chain),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n" + "=" * 70)
    print("Running all examples...")
    print("=" * 70 + "\n")

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n⚠️  {name} failed: {e}")

    print("\n" + "=" * 70)
    print(" Examples completed!")
    print("=" * 70)

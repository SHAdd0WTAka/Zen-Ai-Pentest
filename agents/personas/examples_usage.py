#!/usr/bin/env python3
"""
Zen-AI-Pentest Personas - Usage Examples

This file demonstrates how to use the new specialized AI personas.

Usage:
    python -m agents.personas.examples_usage
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZenAI.Personas.Examples")


async def example_1_basic_usage():
    """Example 1: Basic persona instantiation and usage"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Persona Usage")
    print("=" * 60)

    from agents.personas import (
        APISecurityExpertPersona,
        CloudSecurityExpertPersona,
        WebAppExpertPersona,
    )

    # Create persona instances
    webapp_expert = WebAppExpertPersona("WebApp-Scanner-01")
    api_expert = APISecurityExpertPersona("API-Tester-01")
    cloud_expert = CloudSecurityExpertPersona("Cloud-Auditor-01")

    print(f"Created WebApp Expert: {webapp_expert.name}")
    print(f"Created API Security Expert: {api_expert.name}")
    print(f"Created Cloud Security Expert: {cloud_expert.name}")

    # Display expertise
    print("\nWebApp Expert Expertise:")
    for skill in webapp_expert.expertise[:5]:
        print(f"  - {skill}")

    print("\nAPI Expert Tools:")
    for tool in api_expert.tools[:5]:
        print(f"  - {tool}")


async def example_2_using_registry():
    """Example 2: Using the persona registry"""
    print("\n" + "=" * 60)
    print("Example 2: Using the Persona Registry")
    print("=" * 60)

    from agents.personas import (
        create_persona,
        get_persona_info,
        get_personas_by_tag,
        list_personas,
    )

    # List all available personas
    print("\nAvailable Personas:")
    personas = list_personas()
    for pid, info in personas.items():
        print(f"  {info['icon']} {pid}: {info['name']}")
        print(f"     Description: {info['description']}")
        print(f"     Tags: {', '.join(info['tags'][:3])}")

    # Get persona by tag
    print("\nCloud-related personas:")
    cloud_personas = get_personas_by_tag("cloud")
    for pid in cloud_personas:
        print(f"  - {pid}")

    # Get detailed persona info
    print("\nDetailed info for 'webapp_expert':")
    info = get_persona_info("webapp_expert")
    print(f"  Name: {info['name']}")
    print(f"  Expertise ({len(info['expertise'])} items):")
    for exp in info["expertise"][:3]:
        print(f"    - {exp}")

    # Create persona using registry
    print("\nCreating persona via registry:")
    persona = create_persona("crypto_expert", "SSL-Analyzer")
    print(f"  Created: {persona.name}")


async def example_3_webapp_scanning():
    """Example 3: WebApp Expert - Web Application Scanning"""
    print("\n" + "=" * 60)
    print("Example 3: WebApp Expert - Web Application Scanning")
    print("=" * 60)

    from agents.personas import WebAppExpertPersona

    # Create WebApp Expert
    expert = WebAppExpertPersona("WebApp-Scanner")

    # Execute a web application scan task
    task = {
        "type": "webapp_scan",
        "context": {"target": "testphp.vulnweb.com", "scan_depth": "comprehensive", "test_sqli": True, "test_xss": True},
    }

    print(f"\nExecuting task: {task['type']}")
    print(f"Target: {task['context']['target']}")

    result = await expert.execute_task(task)
    print(f"Status: {result['status']}")
    print(f"Agent: {result['agent']}")


async def example_4_api_security_testing():
    """Example 4: API Security Expert - JWT and BOLA Testing"""
    print("\n" + "=" * 60)
    print("Example 4: API Security Expert - API Security Testing")
    print("=" * 60)

    from agents.personas import APISecurityExpertPersona

    # Create API Security Expert
    expert = APISecurityExpertPersona("API-Security-Tester")

    # Example: JWT Analysis
    jwt_task = {
        "type": "jwt_analysis",
        "context": {"jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "target": "api.example.com"},
    }

    print(f"\nExecuting task: {jwt_task['type']}")
    result = await expert.execute_task(jwt_task)
    print(f"Status: {result['status']}")

    # Example: API Security Scan
    scan_task = {
        "type": "api_security_scan",
        "context": {"target": "https://api.example.com/v1", "api_type": "rest", "test_auth": True, "test_bola": True},
    }

    print(f"\nExecuting task: {scan_task['type']}")
    result = await expert.execute_task(scan_task)
    print(f"Status: {result['status']}")


async def example_5_cloud_audit():
    """Example 5: Cloud Security Expert - AWS Audit"""
    print("\n" + "=" * 60)
    print("Example 5: Cloud Security Expert - Cloud Audit")
    print("=" * 60)

    from agents.personas import CloudSecurityExpertPersona

    # Create Cloud Security Expert
    expert = CloudSecurityExpertPersona("Cloud-Auditor")

    # AWS Audit Task
    task = {
        "type": "cloud_audit",
        "context": {
            "provider": "aws",
            "profile": "default",
            "regions": ["us-east-1", "eu-west-1"],
            "checks": ["iam", "s3", "ec2", "cloudtrail"],
        },
    }

    print(f"\nExecuting task: {task['type']}")
    print(f"Provider: {task['context']['provider']}")
    print(f"Regions: {', '.join(task['context']['regions'])}")

    result = await expert.execute_task(task)
    print(f"Status: {result['status']}")


async def example_6_ssl_analysis():
    """Example 6: Crypto Expert - SSL/TLS Analysis"""
    print("\n" + "=" * 60)
    print("Example 6: Crypto Expert - SSL/TLS Analysis")
    print("=" * 60)

    from agents.personas import CryptoExpertPersona

    # Create Crypto Expert
    expert = CryptoExpertPersona("SSL-Analyzer")

    # SSL Scan Task
    task = {
        "type": "ssl_scan",
        "context": {"target": "example.com", "port": 443, "check_vulnerabilities": True, "cipher_analysis": True},
    }

    print(f"\nExecuting task: {task['type']}")
    print(f"Target: {task['context']['target']}:{task['context']['port']}")

    result = await expert.execute_task(task)
    print(f"Status: {result['status']}")

    if result["status"] == "complete":
        print(f"SSL Grade: {result['analysis'].get('ssl_grade', 'Unknown')}")


async def example_7_forensics():
    """Example 7: Forensics Expert - Memory and Log Analysis"""
    print("\n" + "=" * 60)
    print("Example 7: Forensics Expert - Digital Forensics")
    print("=" * 60)

    from agents.personas import ForensicsExpertPersona

    # Create Forensics Expert
    expert = ForensicsExpertPersona("DFIR-Analyst")

    # Memory Analysis Task
    memory_task = {
        "type": "memory_analysis",
        "context": {"target": "WIN-WORKSTATION-01", "dump_path": "/evidence/memory.dmp", "profile": "Win10x64_19041"},
    }

    print(f"\nExecuting task: {memory_task['type']}")
    result = await expert.execute_task(memory_task)
    print(f"Status: {result['status']}")

    # Log Analysis Task
    log_task = {
        "type": "log_analysis",
        "context": {
            "log_path": "/var/log/auth.log",
            "log_type": "linux",
            "time_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-31T23:59:59Z"},
        },
    }

    print(f"\nExecuting task: {log_task['type']}")
    result = await expert.execute_task(log_task)
    print(f"Status: {result['status']}")


async def example_8_osint():
    """Example 8: Social Engineering Expert - OSINT"""
    print("\n" + "=" * 60)
    print("Example 8: Social Engineering Expert - OSINT")
    print("=" * 60)

    from agents.personas import SocialEngineeringExpertPersona

    # Create Social Engineering Expert
    expert = SocialEngineeringExpertPersona("OSINT-Researcher")

    # OSINT Gathering Task
    osint_task = {
        "type": "osint_gathering",
        "context": {"target": "example-corp.com", "scope": ["corporate", "technical", "social"]},
    }

    print(f"\nExecuting task: {osint_task['type']}")
    result = await expert.execute_task(osint_task)
    print(f"Status: {result['status']}")

    if result["status"] == "complete":
        print(f"Data points: {result['results'].get('data_points', 0)}")

    # Breach Check Task
    breach_task = {
        "type": "breach_check",
        "context": {"emails": ["admin@example-corp.com", "john.smith@example-corp.com"], "domain": "example-corp.com"},
    }

    print(f"\nExecuting task: {breach_task['type']}")
    result = await expert.execute_task(breach_task)
    print(f"Status: {result['status']}")
    if result["status"] == "complete":
        print(f"Compromised accounts: {len(result['results'].get('compromised', []))}")


async def example_9_multi_persona_collaboration():
    """Example 9: Multi-Persona Collaboration"""
    print("\n" + "=" * 60)
    print("Example 9: Multi-Persona Collaboration")
    print("=" * 60)

    from agents.personas import (
        APISecurityExpertPersona,
        CloudSecurityExpertPersona,
        WebAppExpertPersona,
    )

    target = "cloud-app.example.com"

    print(f"\nTarget: {target}")
    print("Running multi-persona security assessment...")

    # Create experts
    web_expert = WebAppExpertPersona("Web-Scanner")
    api_expert = APISecurityExpertPersona("API-Tester")
    cloud_expert = CloudSecurityExpertPersona("Cloud-Auditor")

    # Run parallel assessments
    tasks = [
        web_expert.execute_task({"type": "webapp_scan", "context": {"target": target, "scan_depth": "normal"}}),
        api_expert.execute_task(
            {"type": "api_security_scan", "context": {"target": f"https://{target}/api/v1", "api_type": "rest"}}
        ),
        cloud_expert.execute_task({"type": "cloud_audit", "context": {"provider": "aws", "target": target}}),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    print("\nResults:")
    for i, result in enumerate(results):
        persona_name = ["WebApp", "API", "Cloud"][i]
        if isinstance(result, Exception):
            print(f"  {persona_name}: Error - {result}")
        else:
            print(f"  {persona_name}: {result.get('status', 'unknown')}")


async def example_10_custom_analysis():
    """Example 10: Custom Analysis with Persona"""
    print("\n" + "=" * 60)
    print("Example 10: Custom Analysis with Persona")
    print("=" * 60)

    from agents.personas import WebAppExpertPersona

    expert = WebAppExpertPersona("Analyzer")

    # Sample findings
    findings = [
        {
            "type": "sqli",
            "category": "sql_injection",
            "severity": "critical",
            "url": "https://example.com/login",
            "parameter": "username",
        },
        {"type": "xss", "category": "xss", "severity": "high", "url": "https://example.com/search", "parameter": "q"},
        {"type": "csrf", "category": "csrf", "severity": "medium", "url": "https://example.com/settings"},
    ]

    print(f"\nAnalyzing {len(findings)} findings...")
    analysis = expert.analyze("example.com", findings)

    print("\nAnalysis Results:")
    print(f"  Total Findings: {analysis['total_findings']}")
    print(f"  Risk Level: {analysis['risk_level']}")
    print("  By Severity:")
    for sev, count in analysis["by_severity"].items():
        if count > 0:
            print(f"    - {sev}: {count}")

    print("\n  Attack Vectors:")
    for vector in analysis.get("attack_vectors", []):
        print(f"    - {vector}")

    print("\n  Recommendations:")
    for rec in analysis.get("recommendations", [])[:3]:
        print(f"    - {rec}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Zen-AI-Pentest Personas - Usage Examples")
    print("=" * 60)

    examples = [
        example_1_basic_usage,
        example_2_using_registry,
        example_3_webapp_scanning,
        example_4_api_security_testing,
        example_5_cloud_audit,
        example_6_ssl_analysis,
        example_7_forensics,
        example_8_osint,
        example_9_multi_persona_collaboration,
        example_10_custom_analysis,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

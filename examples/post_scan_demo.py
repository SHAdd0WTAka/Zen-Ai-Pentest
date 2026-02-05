#!/usr/bin/env python3
"""
Post-Scan Workflow Demo
Demonstrates the automated pentester workflow after initial scanning

This shows how a professional pentester would proceed after automated tools:
1. Manual verification of findings
2. False positive elimination
3. Exploitation attempts
4. Evidence collection
5. Loot documentation
6. Cleanup
7. Report preparation
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.post_scan_agent import PostScanAgent, run_post_scan_workflow


async def demo_post_scan_workflow():
    """Demonstrate the complete post-scan workflow"""

    print("\n" + "=" * 70)
    print("  ZEN AI PENTEST - Post-Scan Workflow Demo")
    print("  Professional Pentester Methodology Automation")
    print("=" * 70)
    print("""
This demo simulates what a professional penetration tester does AFTER
running automated scanning tools. Based on PTES (Penetration Testing 
Execution Standard) methodology.

Phases:
  1. Manual Verification      - Eliminate false positives
  2. Vulnerability Validation - Confirm exploitability
  3. Exploitation             - Attempt to exploit findings
  4. Post-Exploitation        - Privilege escalation, lateral movement
  5. Evidence Collection      - Screenshots, logs, proof
  6. Loot Documentation       - Credentials, sensitive data
  7. Cleanup                  - Remove backdoors, restore systems
  8. Report Preparation       - Prepare professional report
""")

    # Simulated scan findings (what automated tools would produce)
    simulated_findings = [
        {
            "id": "CVE-2021-44228",
            "title": "Log4j Remote Code Execution (Log4Shell)",
            "severity": "critical",
            "cvss_score": 10.0,
            "description": "Apache Log4j2 JNDI features do not protect against attacker-controlled "
            "LDAP and other JNDI related endpoints. Allows RCE.",
            "port": 8080,
            "service": "http",
        },
        {
            "id": "SQL_INJECTION_001",
            "title": "SQL Injection in Search Parameter",
            "severity": "high",
            "cvss_score": 8.6,
            "description": "User input in search field is directly concatenated into SQL query "
            "without parameterization.",
            "port": 80,
            "service": "http",
        },
        {
            "id": "DEFAULT_CREDS_001",
            "title": "Default Administrator Credentials",
            "severity": "high",
            "cvss_score": 8.1,
            "description": "Web application accepts default credentials admin/admin.",
            "port": 443,
            "service": "https",
        },
        {
            "id": "WEAK_CIPHER_001",
            "title": "Weak SSH Cipher Suites",
            "severity": "medium",
            "cvss_score": 5.3,
            "description": "SSH server supports deprecated ciphers (3DES, RC4).",
            "port": 22,
            "service": "ssh",
        },
        {
            "id": "INFO Disclosure",
            "title": "Server Version Disclosure",
            "severity": "low",
            "cvss_score": 2.3,
            "description": "Server header reveals exact version number.",
            "port": 80,
            "service": "http",
        },
        {
            "id": "FP_TEST_001",
            "title": "Potential False Positive Finding",
            "severity": "medium",
            "cvss_score": 5.0,
            "description": "Generic vulnerability signature matched, needs verification.",
            "port": None,
            "service": None,
        },
    ]

    target = "192.168.1.100"

    print(f"\n[Target] {target}")
    print(f"[Initial Findings] {len(simulated_findings)} findings from automated scan")
    print("\n" + "-" * 70)

    # Run the post-scan workflow
    results = await run_post_scan_workflow(target, simulated_findings)

    # Display results summary
    print("\n" + "=" * 70)
    print("  WORKFLOW COMPLETE - SUMMARY")
    print("=" * 70)

    print("\n[Verification Results]")
    verified = results.get("total_verified", 0)
    fp = results.get("total_false_positives", 0)
    print(f"  - Confirmed vulnerabilities: {verified}")
    print(f"  - False positives eliminated: {fp}")
    print(f"  - Reduction rate: {fp/(verified+fp)*100:.1f}%")

    print("\n[Exploitation Results]")
    exploited = results.get("total_exploited", 0)
    print(f"  - Successfully exploited: {exploited} systems")

    print("\n[Loot Collected]")
    loot = results.get("loot_summary", {})
    print(f"  - Credentials: {loot.get('credentials', 0)}")
    print(f"  - Screenshots: {loot.get('screenshots', 0)}")
    print(f"  - Sensitive files: {loot.get('sensitive_files', 0)}")

    print("\n[Evidence]")
    print(f"  - Evidence directory: {results.get('evidence_directory', 'N/A')}")

    print("\n[Report Ready]")
    report_data = results.get("report_data", {})
    exec_summary = report_data.get("executive_summary", {})
    print(f"  - Overall Risk: {exec_summary.get('overall_risk', 'N/A')}")
    print(f"  - Critical findings: {exec_summary.get('critical_count', 0)}")
    print(f"  - High findings: {exec_summary.get('high_count', 0)}")

    # Generate and display report preview
    agent = PostScanAgent()
    agent.report_data = report_data
    agent.evidence_dir = Path(results.get("evidence_directory", "evidence"))
    agent.loot.screenshots = [
        f"screenshot_{i}.png" for i in range(loot.get("screenshots", 0))
    ]
    agent.verified_findings = []  # Would be populated from results

    print("\n" + "=" * 70)
    print("  SAMPLE REPORT PREVIEW (Markdown)")
    print("=" * 70)

    report_preview = agent.get_report_template()
    # Show first 2000 characters
    print(report_preview[:2000])
    print("\n... [truncated for display] ...")
    print(
        f"\n[Full report saved to: {results.get('evidence_directory', 'evidence')}/report.md]"
    )

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70)
    print("""
Key Takeaways:
1. Automated scans find POTENTIAL vulnerabilities
2. Post-scan workflow ELIMINATES false positives
3. Professional pentesters VERIFY before reporting
4. Evidence collection is CRITICAL for reports
5. Cleanup is ESSENTIAL for authorized testing
6. Structured workflow ensures QUALITY deliverables

This automation follows PTES (Penetration Testing Execution Standard)
and industry best practices from professional penetration testers.
""")


async def demo_individual_phases():
    """Demonstrate individual phases of the workflow"""

    print("\n" + "=" * 70)
    print("  Individual Phase Demo")
    print("=" * 70)

    agent = PostScanAgent()

    # Sample finding
    test_finding = {
        "id": "TEST-001",
        "title": "Test SQL Injection",
        "severity": "high",
        "cvss_score": 8.1,
        "description": "SQL injection in login form",
        "port": 80,
        "service": "http",
    }

    print("\n[Phase 1: Verification]")
    print("  Purpose: Eliminate false positives")
    verification = await agent._verify_finding(agent._dict_to_finding(test_finding))
    print(f"  Result: {verification}")

    print("\n[Phase 2: Validation]")
    print("  Purpose: Confirm exploitability")
    validation = await agent._validate_vulnerability(
        agent._dict_to_finding(test_finding)
    )
    print(f"  Result: {validation}")

    print("\n[Phase 3: Exploitation]")
    print("  Purpose: Attempt safe exploitation")
    exploitation = await agent._attempt_exploitation(
        agent._dict_to_finding(test_finding)
    )
    print(f"  Result: {exploitation}")

    print("\n[Phases 4-7: Post-Exploitation, Evidence, Loot, Cleanup]")
    print("  These phases run automatically after successful exploitation")

    print("\n[Phase 8: Report Generation]")
    print("  Generates professional penetration testing report")
    print("  Includes: Executive Summary, Technical Findings, Remediation")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Post-Scan Workflow Demo - Professional Pentester Methodology"
    )
    parser.add_argument(
        "--phases", action="store_true", help="Show individual phase details"
    )

    args = parser.parse_args()

    if args.phases:
        asyncio.run(demo_individual_phases())
    else:
        asyncio.run(demo_post_scan_workflow())


if __name__ == "__main__":
    main()

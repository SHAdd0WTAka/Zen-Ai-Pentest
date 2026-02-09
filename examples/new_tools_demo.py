#!/usr/bin/env python3
"""
New Security Tools Demo - Zen AI Pentest
========================================

This demo showcases the 5 new security tool integrations:
1. OWASP ZAP - Web Application Security Scanner
2. TruffleHog - Secrets Detection in Code
3. ScoutSuite - Cloud Security Posture Assessment
4. Trivy - Container and Filesystem Vulnerability Scanner
5. Semgrep - Static Analysis for Code Security

Author: Zen-AI-Pentest Team
Version: 1.0.0
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.zap_integration import (
    ZAPScanner,
    zap_scan_url,
    zap_quick_scan,
    zap_spider_only,
)
from tools.trufflehog_integration import (
    TruffleHogScanner,
    trufflehog_scan_git,
    trufflehog_scan_path,
)
from tools.scout_integration import (
    ScoutSuiteScanner,
    CloudProvider,
    scoutsuite_scan_aws,
    scoutsuite_quick_scan,
)
from tools.trivy_integration import (
    TrivyScanner,
    TrivyScanTarget,
    trivy_scan_image,
    trivy_scan_filesystem,
)
from tools.semgrep_integration import (
    SemgrepScanner,
    semgrep_scan_code,
    semgrep_scan_owasp,
    semgrep_scan_secrets,
)


async def demo_zap():
    """Demo OWASP ZAP Integration"""
    print("\n" + "=" * 60)
    print("1. OWASP ZAP - Web Application Security Scanner")
    print("=" * 60)

    # Example 1: Basic ZAP scan
    print("\n--- Example: ZAP Scanner Class ---")
    scanner = ZAPScanner(
        target="http://testphp.vulnweb.com",
        api_url="http://localhost:8080",
        options={
            "spider": True,
            "active_scan": True,
            "ajax_spider": False,
            "scan_timeout": 600,
        },
    )
    print(f"ZAP Scanner initialized for: {scanner.target}")
    print(f"Options: spider={scanner.options['spider']}, "
          f"active_scan={scanner.options['active_scan']}")

    # Example 2: Quick scan using LangChain tool
    print("\n--- Example: ZAP Quick Scan Tool ---")
    try:
        result = zap_quick_scan("http://example.com")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Note: ZAP daemon not running ({e})")
        print("To run ZAP scan: Start ZAP daemon first")

    # Example 3: Spider only
    print("\n--- Example: ZAP Spider Only ---")
    try:
        result = zap_spider_only("http://example.com")
        print(result)
    except Exception as e:
        print(f"Note: ZAP daemon not running ({e})")


async def demo_trufflehog():
    """Demo TruffleHog Integration"""
    print("\n" + "=" * 60)
    print("2. TruffleHog - Secrets Detection in Code")
    print("=" * 60)

    # Example 1: Initialize scanner
    print("\n--- Example: TruffleHog Scanner Class ---")
    scanner = TruffleHogScanner(
        verified_only=True,
        max_depth=100,
        exclude_paths=["node_modules", "vendor", ".git"],
    )
    print(f"TruffleHog Scanner initialized")
    print(f"Verified only: {scanner.verified_only}")
    print(f"Max depth: {scanner.max_depth}")

    # Example 2: Scan local repository
    print("\n--- Example: Scan Local Repository ---")
    demo_repo = "."
    try:
        result = await scanner.scan_git(demo_repo)
        if result.success:
            print(f"Scan completed in {result.scan_time:.2f}s")
            print(f"Secrets found: {len(result.findings)}")
            for finding in result.findings[:3]:
                print(f"  - {finding.detector_name}: {finding.redacted}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: TruffleHog not installed ({e})")

    # Example 3: Filesystem scan
    print("\n--- Example: Filesystem Scan ---")
    try:
        result = await scanner.scan_filesystem(".")
        if result.success:
            print(f"Filesystem scan completed")
            print(f"Secrets found: {len(result.findings)}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: {e}")


async def demo_scoutsuite():
    """Demo ScoutSuite Integration"""
    print("\n" + "=" * 60)
    print("3. ScoutSuite - Cloud Security Posture Assessment")
    print("=" * 60)

    # Example 1: AWS Scanner
    print("\n--- Example: AWS Scanner Setup ---")
    try:
        scanner = ScoutSuiteScanner(
            provider=CloudProvider.AWS,
            regions=["us-east-1", "eu-west-1"],
            services=["iam", "s3", "ec2"],
            compliance=["cis", "pci-dss"],
            output_dir="./scout-reports",
        )
        print(f"ScoutSuite AWS Scanner initialized")
        print(f"Regions: {scanner.regions}")
        print(f"Services: {scanner.services}")
        print(f"Compliance: {scanner.compliance}")
    except Exception as e:
        print(f"Note: ScoutSuite not installed ({e})")

    # Example 2: Azure Scanner
    print("\n--- Example: Azure Scanner Setup ---")
    try:
        scanner = ScoutSuiteScanner(provider=CloudProvider.AZURE)
        print(f"ScoutSuite Azure Scanner initialized")
    except Exception as e:
        print(f"Note: ScoutSuite not installed ({e})")

    # Example 3: GCP Scanner
    print("\n--- Example: GCP Scanner Setup ---")
    try:
        scanner = ScoutSuiteScanner(
            provider=CloudProvider.GCP,
            thread_config=8,
        )
        print(f"ScoutSuite GCP Scanner initialized")
        print(f"Threads: {scanner.thread_config}")
    except Exception as e:
        print(f"Note: ScoutSuite not installed ({e})")


async def demo_trivy():
    """Demo Trivy Integration"""
    print("\n" + "=" * 60)
    print("4. Trivy - Container and Filesystem Vulnerability Scanner")
    print("=" * 60)

    # Example 1: Initialize scanner
    print("\n--- Example: Trivy Scanner Class ---")
    try:
        scanner = TrivyScanner(
            severity=["HIGH", "CRITICAL"],
            scanners=[TrivyScannerType.VULNERABILITY, TrivyScannerType.MISCONFIGURATION],
            cache_dir="/tmp/trivy-cache",
        )
        print(f"Trivy Scanner initialized")
        print(f"Severity filter: {scanner.severity}")
        print(f"Scanners: {[s.value for s in scanner.scanners]}")
    except Exception as e:
        print(f"Note: Trivy not installed ({e})")

    # Example 2: Scan container image
    print("\n--- Example: Scan Container Image ---")
    try:
        scanner = TrivyScanner(severity=["HIGH", "CRITICAL"])
        result = await scanner.scan_image("nginx:alpine")
        if result.success:
            print(f"Image scan completed in {result.scan_time:.2f}s")
            print(f"Vulnerabilities: {len(result.vulnerabilities)}")
            print(f"Misconfigurations: {len(result.misconfigurations)}")
            if result.os_info:
                print(f"OS: {result.os_info.get('Family')} {result.os_info.get('Name')}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: Trivy not installed ({e})")

    # Example 3: Filesystem scan
    print("\n--- Example: Filesystem Scan ---")
    try:
        scanner = TrivyScanner()
        result = await scanner.scan_filesystem(".")
        if result.success:
            print(f"Filesystem scan completed")
            print(f"Vulnerabilities: {len(result.vulnerabilities)}")
            print(f"Secrets: {len(result.secrets)}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: {e}")


async def demo_semgrep():
    """Demo Semgrep Integration"""
    print("\n" + "=" * 60)
    print("5. Semgrep - Static Analysis for Code Security")
    print("=" * 60)

    # Example 1: Initialize scanner
    print("\n--- Example: Semgrep Scanner Class ---")
    try:
        scanner = SemgrepScanner(
            config=["p/security-audit", "p/owasp-top-ten", "p/cwe-top-25"],
            exclude_patterns=["tests", "node_modules", "*.min.js"],
            num_jobs=4,
            timeout=300,
        )
        print(f"Semgrep Scanner initialized")
        print(f"Config: {scanner.config}")
        print(f"Jobs: {scanner.num_jobs}")
    except Exception as e:
        print(f"Note: Semgrep not installed ({e})")

    # Example 2: Scan with custom rules
    print("\n--- Example: Scan with OWASP Rules ---")
    try:
        scanner = SemgrepScanner(config=["p/owasp-top-ten"])
        result = await scanner.scan(".")
        if result.success:
            print(f"Scan completed in {result.scan_time:.2f}s")
            print(f"Findings: {len(result.findings)}")
            owasp_findings = [f for f in result.findings
                            if f.metadata.get("owasp")]
            print(f"OWASP-related findings: {len(owasp_findings)}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: {e}")

    # Example 3: Secrets detection
    print("\n--- Example: Secrets Detection ---")
    try:
        scanner = SemgrepScanner()
        scanner.add_secrets_rules()
        result = await scanner.scan(".")
        if result.success:
            print(f"Secrets scan completed")
            print(f"Potential secrets found: {len(result.findings)}")
        else:
            print(f"Scan failed: {result.error}")
    except Exception as e:
        print(f"Note: {e}")


async def demo_best_practices():
    """Demo best practices and usage patterns"""
    print("\n" + "=" * 60)
    print("Best Practices and Usage Patterns")
    print("=" * 60)

    print("""
1. OWASP ZAP Best Practices:
   - Always start ZAP daemon before scanning
   - Use spider-only mode first for reconnaissance
   - Configure proper scan policies for production
   - Review findings manually for false positives
   - Use API key for authenticated scans

2. TruffleHog Best Practices:
   - Use --verified-only in production for accuracy
   - Scan both git history and current files
   - Integrate with CI/CD for automated detection
   - Regularly rotate detected secrets
   - Use custom regex patterns for organization-specific secrets

3. ScoutSuite Best Practices:
   - Run with least-privilege credentials
   - Focus on specific services to reduce scan time
   - Review compliance frameworks relevant to your industry
   - Schedule regular scans for continuous monitoring
   - Use multi-threading for faster scans

4. Trivy Best Practices:
   - Keep vulnerability database updated
   - Use severity filters to focus on critical issues
   - Generate SBOMs for supply chain security
   - Scan both images and filesystems
   - Integrate into CI/CD pipelines

5. Semgrep Best Practices:
   - Start with security-audit and owasp-top-ten rules
   - Use --dry-run first to preview changes
   - Filter false positives with custom patterns
   - Focus on high-confidence findings initially
   - Customize rules for your codebase patterns
""")

    print("\n--- Example: Integrated Security Pipeline ---")
    print("""
# Example CI/CD Pipeline Integration:

# Step 1: Secrets Detection (TruffleHog)
$ trufflehog filesystem . --only-verified

# Step 2: Static Analysis (Semgrep)
$ semgrep --config=p/security-audit --config=p/owasp-top-ten --error

# Step 3: Container Scanning (Trivy)
$ trivy image --severity HIGH,CRITICAL myapp:latest

# Step 4: Cloud Security (ScoutSuite)
$ scout aws --services iam,s3,ec2

# Step 5: Web App Scanning (ZAP)
$ zap-baseline.py -t https://myapp.example.com
""")


async def main():
    """Main demo function"""
    print("=" * 60)
    print("Zen AI Pentest - New Security Tools Demo")
    print("=" * 60)
    print("""
This demo showcases 5 new security tool integrations:
1. OWASP ZAP - Web Application Security Scanner
2. TruffleHog - Secrets Detection in Code
3. ScoutSuite - Cloud Security Posture Assessment
4. Trivy - Container and Filesystem Vulnerability Scanner
5. Semgrep - Static Analysis for Code Security

Note: Some demos require the tools to be installed.
""")

    try:
        await demo_zap()
    except Exception as e:
        print(f"ZAP demo error: {e}")

    try:
        await demo_trufflehog()
    except Exception as e:
        print(f"TruffleHog demo error: {e}")

    try:
        await demo_scoutsuite()
    except Exception as e:
        print(f"ScoutSuite demo error: {e}")

    try:
        await demo_trivy()
    except Exception as e:
        print(f"Trivy demo error: {e}")

    try:
        await demo_semgrep()
    except Exception as e:
        print(f"Semgrep demo error: {e}")

    await demo_best_practices()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()

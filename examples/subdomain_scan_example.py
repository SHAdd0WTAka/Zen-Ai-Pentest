#!/usr/bin/env python3
"""
Subdomain Scan Example for target.com
Demonstrates the SubdomainScanner usage
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.subdomain_scanner import SubdomainScanner


async def scan_target_com():
    """
    Example: Scan target.com for subdomains
    """
    target = "target.com"
    
    print("=" * 70)
    print("  Zen AI Pentest - Subdomain Scanner Demo")
    print("  Target:", target)
    print("=" * 70)
    print()

    # Initialize scanner
    scanner = SubdomainScanner(max_workers=30, timeout=10)

    # Run comprehensive scan
    print(f"[*] Starting subdomain enumeration for {target}...")
    print("[*] Techniques: DNS, Wordlist, Certificate Transparency")
    print("[*] This may take a few moments...\n")

    results = await scanner.scan(
        domain=target,
        techniques=["dns", "wordlist", "crt"],
        check_http=True
    )

    # Display results
    print(f"\n[+] Discovery complete! Found {len(results)} subdomains\n")

    if results:
        # Live hosts first
        live_hosts = [(sub, r) for sub, r in results.items() if r.is_alive]
        dns_only = [(sub, r) for sub, r in results.items() if not r.is_alive]

        if live_hosts:
            print("=" * 70)
            print("LIVE SUBDOMAINS (HTTP/HTTPS Responsive)")
            print("=" * 70)
            for subdomain, result in sorted(live_hosts):
                print(f"\n  ▸ {subdomain}")
                print(f"    Status Code: {result.status_code}")
                print(f"    Server: {result.server_header or 'Unknown'}")
                if result.technologies:
                    print(f"    Technologies: {', '.join(result.technologies)}")

        if dns_only:
            print(f"\n{'=' * 70}")
            print("DNS-ONLY SUBDOMAINS")
            print("=" * 70)
            for subdomain, result in sorted(dns_only):
                print(f"  • {subdomain}")

        # Export examples
        print(f"\n{'=' * 70}")
        print("EXPORT EXAMPLES")
        print("=" * 70)
        
        json_output = scanner.export_results("json")
        print(f"\nJSON format ({len(json_output)} chars):")
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)

        print("\n\nTXT format sample:")
        txt_output = scanner.export_results("txt")
        print("\n".join(txt_output.split("\n")[:15]))

    else:
        print("[!] No subdomains discovered")
        print("    This could mean:")
        print("    - The domain has no publicly listed subdomains")
        print("    - Rate limiting from certificate transparency logs")
        print("    - Network connectivity issues")

    print(f"\n{'=' * 70}")
    print("Scan Complete")
    print("=" * 70)

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(scan_target_com())
        print(f"\n[*] Total subdomains found: {len(results)}")
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
OSINT Module Demo

Demonstrates Open Source Intelligence gathering capabilities:
- Email harvesting
- Domain reconnaissance
- Subdomain enumeration
- Technology detection
- Data breach checking

Usage:
    python osint_demo.py --domain example.com
    python osint_demo.py --email user@example.com
    python osint_demo.py --username johndoe
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.osint import OSINTModule


async def demo_email_harvesting(domain: str):
    """Demonstrate email harvesting"""
    print("\n" + "=" * 60)
    print(f"  OSINT Demo - Email Harvesting: {domain}")
    print("=" * 60 + "\n")

    async with OSINTModule() as osint:
        print("[1] Harvesting emails from multiple sources...")
        print("    Sources: Google, Bing, PGP Key Servers")
        print("    This may take 30-60 seconds...\n")

        results = await osint.harvest_emails(domain)

        if results:
            print(f"[✓] Found {len(results)} email addresses:\n")

            # Group by confidence
            by_confidence = {}
            for r in results:
                conf = r.confidence
                if conf not in by_confidence:
                    by_confidence[conf] = []
                by_confidence[conf].append(r)

            for conf in sorted(by_confidence.keys(), reverse=True):
                emails = by_confidence[conf]
                print(f"  Confidence {conf}/10:")
                for e in emails[:5]:  # Show top 5 per confidence
                    print(f"    - {e.value}")
                    if e.metadata.get("method"):
                        print(
                            f"      Source: {e.source} | Method: {e.metadata['method']}"
                        )
        else:
            print("[!] No emails found")

        return results


async def demo_domain_recon(domain: str):
    """Demonstrate domain reconnaissance"""
    print("\n" + "=" * 60)
    print(f"  OSINT Demo - Domain Reconnaissance: {domain}")
    print("=" * 60 + "\n")

    async with OSINTModule() as osint:
        print("[1] Gathering domain information...")
        print("    - WHOIS lookup")
        print("    - Subdomain enumeration")
        print("    - DNS record analysis")
        print("    - Technology detection\n")

        info = await osint.recon_domain(domain)

        print("[✓] Domain Information:\n")

        print(f"  Domain: {info.domain}")
        print(f"  Registrar: {info.registrar or 'N/A'}")
        print(f"  Created: {info.creation_date or 'N/A'}")
        print(f"  Expires: {info.expiration_date or 'N/A'}")

        if info.name_servers:
            print("\n  Name Servers:")
            for ns in info.name_servers:
                print(f"    - {ns}")

        if info.subdomains:
            print(f"\n  Subdomains Found ({len(info.subdomains)}):")
            for sub in info.subdomains[:10]:  # Show first 10
                print(f"    - {sub}")
            if len(info.subdomains) > 10:
                print(f"    ... and {len(info.subdomains) - 10} more")

        if info.ip_addresses:
            print("\n  IP Addresses:")
            for ip in info.ip_addresses:
                print(f"    - {ip}")

        if info.mx_records:
            print("\n  Mail Servers:")
            for mx in info.mx_records:
                print(f"    - {mx}")

        if info.technologies:
            print("\n  Detected Technologies:")
            for tech in info.technologies:
                print(f"    - {tech}")

        return info


async def demo_breach_check(email: str):
    """Demonstrate breach checking"""
    print("\n" + "=" * 60)
    print(f"  OSINT Demo - Data Breach Check: {email}")
    print("=" * 60 + "\n")

    async with OSINTModule() as osint:
        print("[1] Checking data breach databases...")
        print("    - Have I Been Pwned")
        print("    - Known breach collections")
        print("    - Dark web sources\n")

        profile = await osint.check_breach(email)

        print("[✓] Breach Analysis:\n")
        print(f"  Email: {profile.email}")
        print(f"  Valid Format: {'Yes' if profile.valid_format else 'No'}")
        print(f"  Breached: {'YES ⚠️' if profile.breached else 'No'}")

        if profile.breached:
            print("\n  ⚠️  WARNING: Email found in breaches!")
            print("\n  Breach Sources:")
            for source in profile.breach_sources:
                print(f"    - {source}")

        if profile.associated_domains:
            print("\n  Associated Domains:")
            for domain in profile.associated_domains:
                print(f"    - {domain}")

        return profile


async def demo_username_investigation(username: str):
    """Demonstrate username investigation"""
    print("\n" + "=" * 60)
    print(f"  OSINT Demo - Username Investigation: {username}")
    print("=" * 60 + "\n")

    async with OSINTModule() as osint:
        print("[1] Investigating username across platforms...")
        print("    - Twitter/X")
        print("    - GitHub")
        print("    - LinkedIn")
        print("    - Instagram")
        print("    - Facebook")
        print("    - Reddit\n")

        results = await osint.investigate_username(username)

        print("[✓] Platform Check Results:\n")

        found_count = 0
        for platform, data in results.items():
            exists = data.get("exists", False)
            status = "✓ Found" if exists else "✗ Not found"
            print(f"  {platform.capitalize():12} {status}")

            if exists:
                found_count += 1
                print(f"               URL: {data.get('url')}")

        print(f"\n[Summary] Found on {found_count}/{len(results)} platforms")

        return results


async def demo_full_recon(target: str):
    """Full reconnaissance demonstration"""
    print("\n" + "=" * 60)
    print(f"  OSINT Demo - Full Reconnaissance: {target}")
    print("=" * 60 + "\n")

    results = {
        "target": target,
        "timestamp": None,
        "emails": [],
        "domains": {},
        "breaches": [],
        "usernames": {},
    }

    async with OSINTModule() as osint:
        # Determine target type
        if "@" in target:
            # Email target
            print("[+] Detected email target\n")

            profile = await osint.check_breach(target)
            results["breaches"] = profile.breach_sources

            # Extract domain and do domain recon
            domain = target.split("@")[1]
            domain_info = await osint.recon_domain(domain)
            results["domains"][domain] = {
                "subdomains": domain_info.subdomains,
                "technologies": domain_info.technologies,
            }

        elif "." in target and " " not in target:
            # Domain target
            print("[+] Detected domain target\n")

            # Domain recon
            domain_info = await osint.recon_domain(target)
            results["domains"][target] = {
                "subdomains": domain_info.subdomains,
                "technologies": domain_info.technologies,
                "ip_addresses": domain_info.ip_addresses,
            }

            # Email harvesting
            emails = await osint.harvest_emails(target)
            results["emails"] = [e.value for e in emails]

        else:
            # Username target
            print("[+] Detected username target\n")

            username_results = await osint.investigate_username(target)
            results["usernames"] = username_results

        # Generate report
        report = osint.generate_report(target)

        print("\n" + "=" * 60)
        print("  RECONNAISSANCE REPORT")
        print("=" * 60)
        print(json.dumps(report, indent=2))

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Zen AI Pentest - OSINT Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --domain example.com
  %(prog)s --email admin@example.com
  %(prog)s --username johndoe
  %(prog)s --full example.com
        """,
    )

    parser.add_argument("--domain", help="Domain to investigate")
    parser.add_argument("--email", help="Email to check for breaches")
    parser.add_argument("--username", help="Username to investigate")
    parser.add_argument("--full", help="Full reconnaissance on target")

    args = parser.parse_args()

    if not any([args.domain, args.email, args.username, args.full]):
        parser.print_help()
        sys.exit(1)

    try:
        if args.domain:
            asyncio.run(demo_domain_recon(args.domain))
            asyncio.run(demo_email_harvesting(args.domain))

        elif args.email:
            asyncio.run(demo_breach_check(args.email))

        elif args.username:
            asyncio.run(demo_username_investigation(args.username))

        elif args.full:
            asyncio.run(demo_full_recon(args.full))

        print("\n" + "=" * 60)
        print("  Demo Complete!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

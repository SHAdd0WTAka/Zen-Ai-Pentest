#!/usr/bin/env python3
"""
Subdomain Enumeration Tool - CLI Interface
Unified interface for basic and advanced subdomain scanning
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from modules.subdomain_scanner import SubdomainScanner  # noqa: E402
from modules.subdomain_scanner_advanced import (  # noqa: E402
    AdvancedSubdomainScanner,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SubdomainEnum")


def print_banner():
    """Print tool banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    ███████╗███████╗███╗   ██╗    █████╗ ██╗                      ║
║    ██╔════╝██╔════╝████╗  ██║   ██╔══██╗██║                      ║
║    ███████╗█████╗  ██╔██╗ ██║   ███████║██║                      ║
║    ╚════██║██╔══╝  ██║╚██╗██║   ██╔══██║██║                      ║
║    ███████║███████╗██║ ╚████║██╗██║  ██║██║                      ║
║    ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝╚═╝                      ║
║                                                                  ║
║              Advanced Subdomain Enumeration                      ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_results(results, verbose: bool = False):
    """Print scan results in formatted table"""
    if not results:
        print("\n[!] No subdomains discovered")
        return

    live = [(sub, r) for sub, r in results.items() if r.is_alive]
    dns_only = [(sub, r) for sub, r in results.items() if not r.is_alive]

    print(f"\n{'='*80}")
    print(f" SCAN RESULTS - {len(results)} Total Subdomains")
    print(f"{'='*80}")

    # Live hosts section
    if live:
        print(f"\n✓ LIVE HOSTS ({len(live)}):")
        print("-" * 80)
        print(f"{'Subdomain':<45} {'Status':<8} {'Server':<18} {'Tech'}")
        print("-" * 80)

        for subdomain, result in sorted(live, key=lambda x: x[0]):
            status = f"{result.status_code}" if result.status_code else "???"
            server = (result.server_header or "Unknown")[:17]
            techs = (
                ", ".join(result.technologies[:2])
                if result.technologies
                else "-"
            )
            techs = techs[:20]
            print(f"{subdomain:<45} {status:<8} {server:<18} {techs}")

    # DNS-only section
    if dns_only:
        if verbose:
            print(f"\n○ DNS-ONLY ({len(dns_only)}):")
            print("-" * 80)
            for subdomain, result in sorted(dns_only, key=lambda x: x[0]):
                print(f"  • {subdomain}")
        else:
            print(f"\n○ DNS-only subdomains: {len(dns_only)} (use -v to list)")

    print(f"\n{'='*80}\n")


def print_technology_summary(results):
    """Print technology detection summary"""
    tech_count = {}
    server_count = {}
    status_count = {}

    for result in results.values():
        # Technologies
        for tech in result.technologies:
            tech_count[tech] = tech_count.get(tech, 0) + 1
        # Servers
        server = result.server_header or "Unknown"
        server_count[server] = server_count.get(server, 0) + 1
        # Status codes
        if result.status_code:
            status_count[result.status_code] = (
                status_count.get(result.status_code, 0) + 1
            )

    print("\n📊 Technology Summary:")
    print("-" * 40)

    if tech_count:
        print("\nDetected Technologies:")
        for tech, count in sorted(
            tech_count.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  • {tech}: {count}")

    if server_count:
        print("\nServer Headers:")
        for server, count in sorted(
            server_count.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"  • {server}: {count}")

    if status_count:
        print("\nStatus Codes:")
        for status, count in sorted(status_count.items()):
            print(f"  • HTTP {status}: {count}")


def load_wordlist(path: str) -> List[str]:
    """Load wordlist from file"""
    with open(path) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


async def run_scan(args) -> dict:
    """Execute subdomain scan based on arguments"""

    # Choose scanner type
    if args.advanced:
        logger.info("Using advanced scanner with extended techniques")
        scanner = AdvancedSubdomainScanner(
            max_workers=args.workers, timeout=args.timeout
        )

        if args.virustotal_key:
            scanner.set_virustotal_key(args.virustotal_key)

        techniques = (
            args.techniques.split(",")
            if args.techniques
            else ["basic", "permute", "dnsrecords"]
        )

        results = await scanner.scan_advanced(
            domain=args.domain,
            techniques=techniques,
            check_http=not args.no_http,
            permutation_depth=args.permutation_depth,
        )

        # Generate and optionally save report
        if args.report:
            report = scanner.generate_report()
            print("\n📋 Advanced Report:")
            print(json.dumps(report, indent=2))
    else:
        logger.info("Using standard scanner")
        scanner = SubdomainScanner(
            max_workers=args.workers, timeout=args.timeout
        )

        techniques = (
            args.techniques.split(",")
            if args.techniques
            else ["dns", "wordlist", "crt"]
        )

        wordlist = None
        if args.wordlist:
            wordlist = load_wordlist(args.wordlist)
            logger.info(f"Loaded {len(wordlist)} entries from wordlist")

        results = await scanner.scan(
            domain=args.domain,
            wordlist=wordlist,
            techniques=techniques,
            check_http=not args.no_http,
        )

    return results, scanner


async def main():
    parser = argparse.ArgumentParser(
        description="Advanced Subdomain Enumeration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python tools/subdomain_enum.py target.com

  # Advanced scan with all techniques
  python tools/subdomain_enum.py target.com --advanced

  # Custom wordlist
  python tools/subdomain_enum.py target.com -w wordlist.txt

  # Export results
  python tools/subdomain_enum.py target.com -o results.json

  # API integration
  python tools/subdomain_enum.py target.com --advanced --virustotal-key <key>

  # Quick DNS-only scan
  python tools/subdomain_enum.py target.com --no-http
        """,
    )

    # Target
    parser.add_argument("domain", help="Target domain to scan")

    # Scan modes
    parser.add_argument(
        "-a",
        "--advanced",
        action="store_true",
        help="Use advanced scanning techniques",
    )
    parser.add_argument(
        "-t",
        "--techniques",
        help="Comma-separated techniques (default: dns,wordlist,crt)",
    )

    # Wordlist
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file")
    parser.add_argument(
        "--generate-wordlist",
        action="store_true",
        help="Generate and save default wordlist",
    )

    # HTTP checking
    parser.add_argument(
        "--no-http",
        action="store_true",
        help="Skip HTTP/HTTPS checking (faster)",
    )

    # Performance
    parser.add_argument(
        "--workers",
        type=int,
        default=50,
        help="Concurrent workers (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )

    # Advanced options
    parser.add_argument(
        "--permutation-depth",
        type=int,
        default=1,
        help="Permutation depth for advanced scan (default: 1)",
    )
    parser.add_argument(
        "--virustotal-key", help="VirusTotal API key for enhanced enumeration"
    )

    # Output
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "txt", "csv"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed report (advanced mode)",
    )

    # Other
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress banner and minimize output",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Print banner
    if not args.quiet:
        print_banner()

    # Generate wordlist only
    if args.generate_wordlist:
        wordlist_path = args.wordlist or "subdomain_wordlist.txt"
        scanner = SubdomainScanner()
        with open(wordlist_path, "w") as f:
            f.write("\n".join(scanner.DEFAULT_WORDLIST))
        print(f"[+] Wordlist saved to: {wordlist_path}")
        return 0

    # Validate domain
    domain = args.domain.lower().strip()
    if domain.startswith(("http://", "https://")):
        from urllib.parse import urlparse

        domain = urlparse(domain).netloc
        args.domain = domain

    # Run scan
    try:
        results, scanner = await run_scan(args)
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return 1

    # Print results
    if not args.quiet:
        print_results(results, verbose=args.verbose)
        if args.verbose:
            print_technology_summary(results)

    # Export
    if args.output:
        try:
            output_data = scanner.export_results(format_type=args.format)
            with open(args.output, "w") as f:
                f.write(output_data)
            print(f"[+] Results exported to: {args.output}")
        except Exception as e:
            logger.error(f"Export failed: {e}")

    # Summary output for quiet mode
    if args.quiet:
        for subdomain in sorted(results.keys()):
            print(subdomain)

    return 0 if len(results) > 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

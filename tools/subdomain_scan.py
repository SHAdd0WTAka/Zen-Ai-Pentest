#!/usr/bin/env python3
"""
Subdomain Scanner CLI Tool
Quick subdomain enumeration for target.com
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from modules.subdomain_scanner import SubdomainScanner  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("SubdomainScan")


def print_banner():
    """Print scan banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          Zen AI Pentest - Subdomain Scanner               ║
║                    Target: target.com                     ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_results(results):
    """Pretty print scan results"""
    if not results:
        print("[!] No subdomains found")
        return

    # Header
    print(f"\n{'='*80}")
    print(f"SCAN RESULTS - {len(results)} Subdomains Discovered")
    print(f"{'='*80}\n")

    # Sort by status code (live first)
    sorted_results = sorted(
        results.items(),
        key=lambda x: (x[1].status_code or 9999, x[0])
    )

    # Live subdomains
    live = [(sub, r) for sub, r in sorted_results if r.is_alive]
    dead = [(sub, r) for sub, r in sorted_results if not r.is_alive]

    if live:
        print(f"\n[+] LIVE SUBDOMAINS ({len(live)}):")
        print("-" * 80)
        print(f"{'Subdomain':<40} {'Status':<8} {'Server':<15} {'Technologies'}")
        print("-" * 80)
        for subdomain, result in live:
            status = f"{result.status_code}" if result.status_code else "???"
            server = (result.server_header or "Unknown")[:14]
            techs = ", ".join(result.technologies[:2]) if result.technologies else "-"
            print(f"{subdomain:<40} {status:<8} {server:<15} {techs}")

    if dead:
        print(f"\n[*] DNS-only Subdomains ({len(dead)}):")
        print("-" * 80)
        for subdomain, result in dead:
            print(f"  • {subdomain}")

    print(f"\n{'='*80}")
    print(f"Scan Complete - {len(live)} live, {len(dead)} DNS-only")
    print(f"{'='*80}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="Subdomain Scanner for target.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/subdomain_scan.py target.com
  python tools/subdomain_scan.py target.com -o results.json
  python tools/subdomain_scan.py target.com --techniques dns,wordlist,crt
  python tools/subdomain_scan.py target.com -w custom_wordlist.txt
        """
    )

    parser.add_argument(
        "domain", nargs="?", default="target.com",
        help="Target domain (default: target.com)"
    )
    parser.add_argument("-o", "--output", help="Output file (JSON, TXT, or CSV)")
    parser.add_argument(
        "-f", "--format", choices=["json", "txt", "csv"],
        default="json", help="Output format"
    )
    parser.add_argument(
        "-t", "--techniques", default="dns,wordlist,crt",
        help="Enumeration techniques (comma-separated)"
    )
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file")
    parser.add_argument(
        "--no-http", action="store_true", help="Skip HTTP/HTTPS checking"
    )
    parser.add_argument(
        "--workers", type=int, default=50, help="Concurrent workers (default: 50)"
    )
    parser.add_argument(
        "--timeout", type=int, default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print_banner()

    # Load custom wordlist if provided
    wordlist = None
    if args.wordlist:
        try:
            with open(args.wordlist) as f:
                wordlist = [line.strip() for line in f if line.strip()]
            print(f"[*] Loaded {len(wordlist)} entries from wordlist")
        except Exception as e:
            print(f"[!] Failed to load wordlist: {e}")
            sys.exit(1)

    # Parse techniques
    techniques = [t.strip() for t in args.techniques.split(",")]

    print(f"[*] Target: {args.domain}")
    print(f"[*] Techniques: {', '.join(techniques)}")
    print(f"[*] HTTP Check: {'Disabled' if args.no_http else 'Enabled'}")
    print(f"[*] Workers: {args.workers}")
    print("[*] Starting scan...\n")

    # Run scan
    scanner = SubdomainScanner(max_workers=args.workers, timeout=args.timeout)
    results = await scanner.scan(
        domain=args.domain,
        wordlist=wordlist,
        techniques=techniques,
        check_http=not args.no_http
    )

    # Print results
    print_results(results)

    # Export if requested
    if args.output:
        try:
            output_data = scanner.export_results(format_type=args.format)
            with open(args.output, "w") as f:
                f.write(output_data)
            print(f"[+] Results exported to: {args.output}")
        except Exception as e:
            print(f"[!] Export failed: {e}")

    return len(results)


if __name__ == "__main__":
    try:
        count = asyncio.run(main())
        sys.exit(0 if count > 0 else 1)
    except KeyboardInterrupt:
        print("\n[!] Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

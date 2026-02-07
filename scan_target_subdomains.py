#!/usr/bin/env python3
"""
Quick Subdomain Scan for target.com
Simple wrapper for immediate use
"""

import asyncio
import sys
from datetime import datetime

from modules.subdomain_scanner import SubdomainScanner


async def main():
    target = "target.com"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           Subdomain Scanner - {target:<20}           ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print(f"[*] Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[*] Techniques: DNS + Wordlist + Certificate Transparency\n")
    
    scanner = SubdomainScanner(max_workers=50, timeout=10)
    
    try:
        results = await scanner.scan(
            domain=target,
            techniques=["dns", "wordlist", "crt"],
            check_http=True
        )
        
        print(f"\n[+] Scan complete! Found {len(results)} subdomains\n")
        
        if results:
            # Separate live and DNS-only
            live = [(sub, r) for sub, r in results.items() if r.is_alive]
            dns_only = [(sub, r) for sub, r in results.items() if not r.is_alive]
            
            # Live hosts
            if live:
                print(f"── Live Hosts ({len(live)}) ──")
                print(f"{'Subdomain':<45} {'Status':<8} {'Server'}")
                print("-" * 70)
                for subdomain, result in sorted(live):
                    status = f"{result.status_code}" if result.status_code else "???"
                    server = (result.server_header or "Unknown")[:20]
                    print(f"{subdomain:<45} {status:<8} {server}")
            
            # DNS only
            if dns_only:
                print(f"\n── DNS-only ({len(dns_only)}) ──")
                for subdomain, _ in sorted(dns_only):
                    print(f"  • {subdomain}")
            
            # Export to file
            output_file = f"subdomains_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_file, "w") as f:
                f.write(scanner.export_results("txt"))
            print(f"\n[+] Results saved to: {output_file}")
        else:
            print("[!] No subdomains discovered")
            
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

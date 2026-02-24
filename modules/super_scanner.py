"""
Super Scanner - Alle Tools kombiniert
Die ultimative All-in-One Reconnaissance-Lösung

Usage:
    python -m modules.super_scanner --target example.com
    python -m modules.super_scanner --target 192.168.1.0/24 --network
"""

import argparse
import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.amass_integration import AmassIntegration

# Tool imports
from tools.ffuf_integration_enhanced import FFuFIntegration
from tools.httpx_integration import HTTPXIntegration
from tools.nikto_integration import NiktoIntegration
from tools.subfinder_integration import SubfinderIntegration
from tools.wafw00f_integration import WAFW00FIntegration
from tools.whatweb_integration import WhatWebIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class SuperScanResult:
    """Complete super scan result"""

    target: str
    timestamp: str
    # All scan results
    port_scan: Dict[str, Any] = field(default_factory=dict)
    subdomains: Dict[str, Any] = field(default_factory=dict)
    technology: Dict[str, Any] = field(default_factory=dict)
    waf: Dict[str, Any] = field(default_factory=dict)
    directories: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: Dict[str, Any] = field(default_factory=dict)
    http_probe: Dict[str, Any] = field(default_factory=dict)
    # Summary
    summary: Dict[str, Any] = field(default_factory=dict)


class SuperScanner:
    """
    Super Scanner - Kombiniert alle verfügbaren Tools

    Führt aus:
    1. Subdomain Enumeration (Subfinder + Amass)
    2. Port Scanning (Nmap/Masscan)
    3. Technology Detection (WhatWeb)
    4. WAF Detection (WAFW00F)
    5. HTTP Probing (HTTPX)
    6. Directory Bruteforce (FFuF)
    7. Vulnerability Scanning (Nikto + Nuclei)
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize all tools
        self.ffuf = FFuFIntegration()
        self.whatweb = WhatWebIntegration()
        self.wafw00f = WAFW00FIntegration()
        self.subfinder = SubfinderIntegration()
        self.amass = AmassIntegration()
        self.httpx = HTTPXIntegration()
        self.nikto = NiktoIntegration()

    async def scan_domain(self, domain: str) -> SuperScanResult:
        """
        Complete domain scan with all tools

        Args:
            domain: Target domain (e.g., example.com)

        Returns:
            SuperScanResult with all findings
        """
        logger.info(f"🚀 Starting SUPER SCAN on {domain}")
        print(f"\n{'='*70}")
        print(f"🚀 SUPER SCANNER - {domain}")
        print(f"{'='*70}\n")

        result = SuperScanResult(
            target=domain, timestamp=datetime.now().isoformat()
        )

        # Phase 1: Subdomain Enumeration
        print("[1/7] 🔍 Subdomain Enumeration...")
        try:
            subfinder_result = await self.subfinder.enumerate(domain)
            amass_result = await self.amass.enumerate(domain, passive=True)

            # Combine results
            all_subdomains = list(
                set(subfinder_result.subdomains + amass_result.subdomains)
            )

            result.subdomains = {
                "success": True,
                "count": len(all_subdomains),
                "subdomains": all_subdomains[:100],  # Limit for report
                "sources": {
                    "subfinder": len(subfinder_result.subdomains),
                    "amass": len(amass_result.subdomains),
                },
            }
            print(f"      Found {len(all_subdomains)} subdomains")
        except Exception as e:
            logger.error(f"Subdomain enumeration failed: {e}")
            result.subdomains = {"success": False, "error": str(e)}

        # Phase 2: HTTP Probing on subdomains
        print("[2/7] 🌐 HTTP Probing...")
        try:
            targets = [domain] + result.subdomains.get("subdomains", [])[:20]
            httpx_result = await self.httpx.probe(targets)

            result.http_probe = {
                "success": True,
                "live_hosts": len(httpx_result.hosts),
                "hosts": [
                    {
                        "url": h.url,
                        "status_code": h.status_code,
                        "title": h.title,
                        "webserver": h.webserver,
                        "ip": h.ip,
                    }
                    for h in httpx_result.hosts
                ],
            }
            print(f"      Found {len(httpx_result.hosts)} live hosts")
        except Exception as e:
            logger.error(f"HTTP probing failed: {e}")
            result.http_probe = {"success": False, "error": str(e)}

        # Phase 3: Technology Detection on main domain
        print("[3/7] 🔧 Technology Detection...")
        try:
            whatweb_result = await self.whatweb.scan(f"http://{domain}")

            result.technology = {
                "success": True,
                "technologies": [
                    {
                        "name": t.name,
                        "version": t.version,
                        "category": t.category,
                    }
                    for t in whatweb_result.technologies[:20]
                ],
            }
            print(
                f"      Found {len(whatweb_result.technologies)} technologies"
            )
        except Exception as e:
            logger.error(f"Technology detection failed: {e}")
            result.technology = {"success": False, "error": str(e)}

        # Phase 4: WAF Detection
        print("[4/7] 🛡️  WAF Detection...")
        try:
            waf_result = await self.wafw00f.detect(f"http://{domain}")

            result.waf = {
                "success": True,
                "firewall_detected": waf_result.firewall_detected,
                "wafs": [
                    {"name": w.name, "confidence": w.confidence}
                    for w in waf_result.wafs
                ],
            }
            status = "Yes" if waf_result.firewall_detected else "No"
            print(f"      WAF detected: {status}")
        except Exception as e:
            logger.error(f"WAF detection failed: {e}")
            result.waf = {"success": False, "error": str(e)}

        # Phase 5: Port Scanning (quick)
        print("[5/7] 📡 Port Scanning...")
        try:
            import socket

            ip = socket.gethostbyname(domain)

            # Use subprocess for nmap
            cmd = ["nmap", "-F", "-sV", "--open", ip]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=120
            )

            # Parse output
            ports = []
            for line in stdout.decode().split("\n"):
                if "/tcp" in line and "open" in line:
                    parts = line.split()
                    port_num = int(parts[0].split("/")[0])
                    service = parts[2] if len(parts) > 2 else "unknown"
                    version = " ".join(parts[3:]) if len(parts) > 3 else ""
                    ports.append(
                        {
                            "port": port_num,
                            "service": service,
                            "version": version,
                        }
                    )

            result.port_scan = {"success": True, "ip": ip, "ports": ports}
            print(f"      Found {len(ports)} open ports")
        except Exception as e:
            logger.error(f"Port scanning failed: {e}")
            result.port_scan = {"success": False, "error": str(e)}

        # Phase 6: Directory Bruteforce
        print("[6/7] 📁 Directory Bruteforce...")
        try:
            ffuf_result = await self.ffuf.directory_bruteforce(
                f"http://{domain}/FUZZ",
                extensions=["php", "html", "txt", "js"],
                threads=20,
            )

            result.directories = {
                "success": True,
                "findings": [
                    {
                        "url": f.url,
                        "status_code": f.status_code,
                        "size": f.content_length,
                    }
                    for f in ffuf_result.findings[:50]
                ],
                "total_found": len(ffuf_result.findings),
            }
            print(f"      Found {len(ffuf_result.findings)} directories")
        except Exception as e:
            logger.error(f"Directory bruteforce failed: {e}")
            result.directories = {"success": False, "error": str(e)}

        # Phase 7: Vulnerability Scanning
        print("[7/7] 🐛 Vulnerability Scanning...")
        try:
            nikto_result = await self.nikto.scan(
                f"http://{domain}", max_time=300
            )

            result.vulnerabilities = {
                "success": True,
                "findings": [
                    {
                        "id": f.id,
                        "severity": f.severity,
                        "description": f.description,
                    }
                    for f in nikto_result.findings[:20]
                ],
                "total": len(nikto_result.findings),
            }
            print(f"      Found {len(nikto_result.findings)} issues")
        except Exception as e:
            logger.error(f"Vulnerability scanning failed: {e}")
            result.vulnerabilities = {"success": False, "error": str(e)}

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _generate_summary(self, result: SuperScanResult) -> Dict[str, Any]:
        """Generate scan summary"""
        # Calculate risk score
        risk_score = 0
        risk_factors = []

        # Subdomains
        sub_count = result.subdomains.get("count", 0)
        if sub_count > 50:
            risk_score += 10
            risk_factors.append("Large attack surface (many subdomains)")

        # WAF
        if not result.waf.get("firewall_detected"):
            risk_score += 20
            risk_factors.append("No WAF detected")

        # Open ports
        port_count = len(result.port_scan.get("ports", []))
        if port_count > 5:
            risk_score += 10
            risk_factors.append("Multiple open ports")

        # Directories
        dir_count = result.directories.get("total_found", 0)
        if dir_count > 10:
            risk_score += 15
            risk_factors.append("Many exposed directories")

        # Vulnerabilities
        vuln_count = result.vulnerabilities.get("total", 0)
        if vuln_count > 0:
            risk_score += min(vuln_count * 5, 30)
            risk_factors.append(f"{vuln_count} vulnerabilities found")

        # Determine risk level
        if risk_score >= 60:
            risk_level = "CRITICAL"
        elif risk_score >= 40:
            risk_level = "HIGH"
        elif risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "statistics": {
                "subdomains": result.subdomains.get("count", 0),
                "live_hosts": result.http_probe.get("live_hosts", 0),
                "technologies": len(result.technology.get("technologies", [])),
                "open_ports": len(result.port_scan.get("ports", [])),
                "directories": result.directories.get("total_found", 0),
                "vulnerabilities": result.vulnerabilities.get("total", 0),
            },
            "recommendations": self._generate_recommendations(result),
        }

    def _generate_recommendations(self, result: SuperScanResult) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if not result.waf.get("firewall_detected"):
            recommendations.append(
                "Implement a Web Application Firewall (WAF)"
            )

        if len(result.port_scan.get("ports", [])) > 3:
            recommendations.append("Close unnecessary ports and services")

        if result.directories.get("total_found", 0) > 5:
            recommendations.append("Restrict access to sensitive directories")

        if result.vulnerabilities.get("total", 0) > 0:
            recommendations.append(
                "Address identified vulnerabilities immediately"
            )

        # Check for outdated software
        for tech in result.technology.get("technologies", []):
            name = tech.get("name", "")
            version = tech.get("version", "")
            if name in ["Apache", "nginx", "PHP", "OpenSSH"] and version:
                recommendations.append(
                    f"Review {name} version {version} for known vulnerabilities"
                )

        return recommendations[:10]  # Limit recommendations

    def save_report(
        self, result: SuperScanResult, filename: Optional[str] = None
    ):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"super_scan_{result.target}_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2)

        logger.info(f"Report saved to {filepath}")
        return filepath

    def print_report(self, result: SuperScanResult):
        """Print formatted report"""
        print("\n" + "=" * 70)
        print("📊 SUPER SCAN REPORT")
        print("=" * 70)
        print(f"Target: {result.target}")
        print(f"Timestamp: {result.timestamp}")
        print()

        summary = result.summary
        print(f"🎯 RISK LEVEL: {summary.get('risk_level', 'UNKNOWN')}")
        print(f"📈 Risk Score: {summary.get('risk_score', 0)}/100")
        print()

        stats = summary.get("statistics", {})
        print("📋 STATISTICS")
        print("-" * 70)
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print()

        if summary.get("risk_factors"):
            print("⚠️  RISK FACTORS")
            print("-" * 70)
            for factor in summary["risk_factors"]:
                print(f"  • {factor}")
            print()

        if summary.get("recommendations"):
            print("💡 RECOMMENDATIONS")
            print("-" * 70)
            for rec in summary["recommendations"]:
                print(f"  • {rec}")

        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Super Scanner - All-in-One Reconnaissance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m modules.super_scanner --target example.com
  python -m modules.super_scanner --target example.com --output-dir ./reports
        """,
    )

    parser.add_argument("--target", "-t", required=True, help="Target domain")
    parser.add_argument(
        "--output-dir", "-o", default="reports", help="Output directory"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimal output"
    )

    args = parser.parse_args()

    # Safety check
    print("⚠️  SAFETY CHECK")
    print("=" * 70)
    print(f"Target: {args.target}")
    print("\nEnsure you have authorization to scan this target!")
    confirm = input("\nContinue? (yes/no): ")

    if confirm.lower() not in ["yes", "y", "ja", "j"]:
        print("Aborted.")
        return

    # Run scan
    scanner = SuperScanner(output_dir=args.output_dir)

    try:
        result = asyncio.run(scanner.scan_domain(args.target))

        # Save report
        report_path = scanner.save_report(result)

        # Print report
        if not args.quiet:
            scanner.print_report(result)
            print(f"\n💾 Full report: {report_path}")

    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise


if __name__ == "__main__":
    main()

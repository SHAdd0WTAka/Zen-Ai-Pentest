"""
OSINT Super Module - Alle OSINT Tools kombiniert
Social Media, Email, Domain, Network OSINT

Usage:
    python -m modules.osint_super --username johndoe
    python -m modules.osint_super --email test@example.com
    python -m modules.osint_super --domain example.com
"""

import argparse
import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tools.amass_integration import AmassIntegration
from tools.ignorant_integration import IgnorantIntegration
from tools.sherlock_integration import SherlockIntegration
from tools.subfinder_integration import SubfinderIntegration
from tools.whatweb_integration import WhatWebIntegration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class OSINTSuperResult:
    """Complete OSINT result"""

    target: str
    target_type: str  # username, email, domain
    timestamp: str
    social_media: Dict[str, Any] = field(default_factory=dict)
    email_check: Dict[str, Any] = field(default_factory=dict)
    subdomains: Dict[str, Any] = field(default_factory=dict)
    technologies: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)


class OSINTSuperModule:
    """
    OSINT Super Module - Kombiniert alle OSINT Tools

    Unterstützt:
    - Username OSINT (Sherlock)
    - Email OSINT (Ignorant)
    - Domain OSINT (Subfinder, Amass, WhatWeb)
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize tools
        self.sherlock = SherlockIntegration()
        self.ignorant = IgnorantIntegration()
        self.subfinder = SubfinderIntegration()
        self.amass = AmassIntegration()
        self.whatweb = WhatWebIntegration()

    async def investigate_username(self, username: str) -> OSINTSuperResult:
        """
        Investigate username across social media

        Args:
            username: Username to investigate

        Returns:
            OSINTSuperResult with findings
        """
        logger.info(f"🔍 Investigating username: {username}")
        print(f"\n{'='*70}")
        print(f"🔍 OSINT USERNAME INVESTIGATION: {username}")
        print(f"{'='*70}\n")

        result = OSINTSuperResult(
            target=username,
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )

        # Phase 1: Sherlock Social Media Search
        print("[1/1] 🔎 Searching 400+ social media platforms...")
        try:
            sherlock_result = await self.sherlock.search(username)

            result.social_media = {
                "success": sherlock_result.success,
                "username": sherlock_result.username,
                "found_accounts": sherlock_result.found_sites,
                "total_found": len(sherlock_result.found_sites),
                "platforms_checked": sherlock_result.total_sites,
            }
            print(f"      Found {len(sherlock_result.found_sites)} accounts")
        except Exception as e:
            logger.error(f"Sherlock search failed: {e}")
            result.social_media = {"success": False, "error": str(e)}

        # Generate summary
        result.summary = self._generate_username_summary(result)

        return result

    async def investigate_email(self, email: str) -> OSINTSuperResult:
        """
        Investigate email address

        Args:
            email: Email address to investigate

        Returns:
            OSINTSuperResult with findings
        """
        logger.info(f"📧 Investigating email: {email}")
        print(f"\n{'='*70}")
        print(f"📧 OSINT EMAIL INVESTIGATION: {email}")
        print(f"{'='*70}\n")

        result = OSINTSuperResult(
            target=email,
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )

        # Phase 1: Ignorant Email Check
        print("[1/2] 📮 Checking 120+ platforms for email...")
        try:
            ignorant_result = await self.ignorant.check_email(email)

            result.email_check = {
                "success": ignorant_result.success,
                "email": ignorant_result.email,
                "username": ignorant_result.username,
                "domain": ignorant_result.domain,
                "found_platforms": [
                    {"platform": p.platform, "url": p.url, "exists": p.exists}
                    for p in ignorant_result.found_platforms
                ],
                "total_found": len(ignorant_result.found_platforms),
                "platforms_checked": ignorant_result.total_checked,
            }
            print(
                f"      Found on {len(ignorant_result.found_platforms)} platforms"
            )
        except Exception as e:
            logger.error(f"Ignorant check failed: {e}")
            result.email_check = {"success": False, "error": str(e)}

        # Phase 2: Try username investigation if email parsed
        if result.email_check.get("username"):
            username = result.email_check["username"]
            print(
                f"[2/2] 🔎 Searching social media for username '{username}'..."
            )
            try:
                sherlock_result = await self.sherlock.search(username)
                result.social_media = {
                    "success": sherlock_result.success,
                    "username": sherlock_result.username,
                    "found_accounts": sherlock_result.found_sites,
                    "total_found": len(sherlock_result.found_sites),
                }
                print(
                    f"      Found {len(sherlock_result.found_sites)} accounts"
                )
            except Exception as e:
                logger.error(f"Social media search failed: {e}")
                result.social_media = {"success": False, "error": str(e)}

        # Generate summary
        result.summary = self._generate_email_summary(result)

        return result

    async def investigate_domain(self, domain: str) -> OSINTSuperResult:
        """
        Investigate domain

        Args:
            domain: Domain to investigate

        Returns:
            OSINTSuperResult with findings
        """
        logger.info(f"🌐 Investigating domain: {domain}")
        print(f"\n{'='*70}")
        print(f"🌐 OSINT DOMAIN INVESTIGATION: {domain}")
        print(f"{'='*70}\n")

        result = OSINTSuperResult(
            target=domain,
            target_type="domain",
            timestamp=datetime.now().isoformat(),
        )

        # Phase 1: Subdomain Enumeration
        print("[1/3] 🔍 Enumerating subdomains (Subfinder)...")
        try:
            subfinder_result = await self.subfinder.enumerate(domain)
            subdomains = subfinder_result.subdomains
            print(f"      Found {len(subdomains)} subdomains")
        except Exception as e:
            logger.error(f"Subfinder failed: {e}")
            subdomains = []

        # Phase 2: Amass Enumeration
        print("[2/3] 🔍 Deep subdomain enumeration (Amass)...")
        try:
            amass_result = await self.amass.enumerate(domain, passive=True)
            # Combine and deduplicate
            all_subdomains = list(set(subdomains + amass_result.subdomains))
            print(f"      Total unique subdomains: {len(all_subdomains)}")
        except Exception as e:
            logger.error(f"Amass failed: {e}")
            all_subdomains = subdomains

        result.subdomains = {
            "success": True,
            "domain": domain,
            "subdomains": all_subdomains[:100],  # Limit for report
            "total": len(all_subdomains),
        }

        # Phase 3: Technology Detection
        print("[3/3] 🔧 Detecting technologies...")
        try:
            target_url = f"http://{domain}"
            whatweb_result = await self.whatweb.scan(target_url)

            result.technologies = {
                "success": True,
                "technologies": [
                    {
                        "name": t.name,
                        "version": t.version,
                        "category": t.category,
                    }
                    for t in whatweb_result.technologies
                ],
            }
            print(
                f"      Found {len(whatweb_result.technologies)} technologies"
            )
        except Exception as e:
            logger.error(f"Technology detection failed: {e}")
            result.technologies = {"success": False, "error": str(e)}

        # Generate summary
        result.summary = self._generate_domain_summary(result)

        return result

    def _generate_username_summary(
        self, result: OSINTSuperResult
    ) -> Dict[str, Any]:
        """Generate summary for username investigation"""
        found = result.social_media.get("found_accounts", [])

        risk_level = "low"
        if len(found) > 20:
            risk_level = "high"
        elif len(found) > 5:
            risk_level = "medium"

        return {
            "target_type": "username",
            "target": result.target,
            "risk_level": risk_level,
            "accounts_found": len(found),
            "key_platforms": [a.get("site") for a in found[:5]],
            "recommendations": (
                [
                    "Review privacy settings on found platforms",
                    "Consider using different usernames across platforms",
                    "Remove or secure accounts on unused platforms",
                ]
                if found
                else []
            ),
        }

    def _generate_email_summary(
        self, result: OSINTSuperResult
    ) -> Dict[str, Any]:
        """Generate summary for email investigation"""
        email_found = result.email_check.get("total_found", 0)
        social_found = result.social_media.get("total_found", 0)

        risk_level = "low"
        if email_found > 10 or social_found > 10:
            risk_level = "high"
        elif email_found > 3 or social_found > 3:
            risk_level = "medium"

        return {
            "target_type": "email",
            "target": result.target,
            "risk_level": risk_level,
            "email_platforms": email_found,
            "social_accounts": social_found,
            "recommendations": (
                [
                    "Use unique passwords for each platform",
                    "Enable 2FA on all found accounts",
                    "Consider using different emails for different purposes",
                ]
                if email_found or social_found
                else []
            ),
        }

    def _generate_domain_summary(
        self, result: OSINTSuperResult
    ) -> Dict[str, Any]:
        """Generate summary for domain investigation"""
        subdomains = result.subdomains.get("total", 0)
        technologies = len(result.technologies.get("technologies", []))

        risk_level = "low"
        if subdomains > 100:
            risk_level = "high"
        elif subdomains > 20:
            risk_level = "medium"

        return {
            "target_type": "domain",
            "target": result.target,
            "risk_level": risk_level,
            "subdomains": subdomains,
            "technologies": technologies,
            "attack_surface": (
                "large"
                if subdomains > 50
                else "medium" if subdomains > 10 else "small"
            ),
            "recommendations": (
                [
                    "Implement subdomain monitoring",
                    "Review and secure exposed services",
                    "Keep software versions up to date",
                ]
                if subdomains > 10
                else []
            ),
        }

    def save_report(
        self, result: OSINTSuperResult, filename: Optional[str] = None
    ):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_target = result.target.replace("@", "_at_").replace(".", "_")
            filename = (
                f"osint_{result.target_type}_{safe_target}_{timestamp}.json"
            )

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2)

        logger.info(f"Report saved to {filepath}")
        return filepath

    def print_report(self, result: OSINTSuperResult):
        """Print formatted report"""
        print("\n" + "=" * 70)
        print("📊 OSINT INVESTIGATION REPORT")
        print("=" * 70)
        print(f"Target: {result.target}")
        print(f"Type: {result.target_type}")
        print(f"Timestamp: {result.timestamp}")
        print()

        summary = result.summary
        print(f"🎯 RISK LEVEL: {summary.get('risk_level', 'UNKNOWN').upper()}")
        print()

        # Print type-specific results
        if result.target_type == "username":
            print(
                f"👤 Social Media Accounts: {result.social_media.get('total_found', 0)}"
            )
            for account in result.social_media.get("found_accounts", [])[:10]:
                print(f"  ✓ {account.get('site')}: {account.get('url')}")

        elif result.target_type == "email":
            print(
                f"📧 Email Platforms: {result.email_check.get('total_found', 0)}"
            )
            print(
                f"👤 Social Accounts: {result.social_media.get('total_found', 0)}"
            )
            for platform in result.email_check.get("found_platforms", [])[:10]:
                print(f"  ✓ {platform.get('platform')}: {platform.get('url')}")

        elif result.target_type == "domain":
            print(f"🌐 Subdomains: {result.subdomains.get('total', 0)}")
            print(
                f"🔧 Technologies: {len(result.technologies.get('technologies', []))}"
            )
            for tech in result.technologies.get("technologies", [])[:10]:
                print(f"  • {tech.get('name')} {tech.get('version')}")

        print()
        if summary.get("recommendations"):
            print("💡 RECOMMENDATIONS")
            print("-" * 70)
            for rec in summary["recommendations"]:
                print(f"  • {rec}")

        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="OSINT Super Module - Username, Email & Domain Investigation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Username investigation
  python -m modules.osint_super --username johndoe

  # Email investigation
  python -m modules.osint_super --email user@example.com

  # Domain investigation
  python -m modules.osint_super --domain example.com
        """,
    )

    parser.add_argument("--username", "-u", help="Username to investigate")
    parser.add_argument("--email", "-e", help="Email address to investigate")
    parser.add_argument("--domain", "-d", help="Domain to investigate")
    parser.add_argument(
        "--output-dir", "-o", default="reports", help="Output directory"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimal output"
    )

    args = parser.parse_args()

    # Validate input
    if not any([args.username, args.email, args.domain]):
        parser.error("Please specify --username, --email, or --domain")

    # Initialize module
    osint = OSINTSuperModule(output_dir=args.output_dir)

    try:
        # Run investigation based on type
        if args.username:
            result = asyncio.run(osint.investigate_username(args.username))
        elif args.email:
            result = asyncio.run(osint.investigate_email(args.email))
        else:
            result = asyncio.run(osint.investigate_domain(args.domain))

        # Save report
        report_path = osint.save_report(result)

        # Print report
        if not args.quiet:
            osint.print_report(result)
            print(f"\n💾 Full report: {report_path}")

    except KeyboardInterrupt:
        print("\n\n[!] Investigation interrupted")
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        raise


if __name__ == "__main__":
    main()

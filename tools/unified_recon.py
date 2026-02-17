"""
Unified Reconnaissance Scanner
Kombiniert alle Tools für eine vollständige Enumeration

Usage:
    python unified_recon.py --target example.com
    python unified_recon.py --target example.com --full
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ffuf_integration_enhanced import FFuFIntegration
from whatweb_integration import WhatWebIntegration
from wafw00f_integration import WAFW00FIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ReconResult:
    """Complete reconnaissance result"""
    target: str
    timestamp: str
    technology_scan: Dict[str, Any] = field(default_factory=dict)
    waf_detection: Dict[str, Any] = field(default_factory=dict)
    directory_bruteforce: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)


class UnifiedReconScanner:
    """Unified reconnaissance scanner combining multiple tools"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize tool integrations
        self.whatweb = WhatWebIntegration(aggression=1)
        self.wafw00f = WAFW00FIntegration()
        self.ffuf = FFuFIntegration()
        
    async def run_full_scan(self, target: str) -> ReconResult:
        """Run complete reconnaissance scan"""
        logger.info(f"Starting unified reconnaissance on {target}")
        
        result = ReconResult(
            target=target,
            timestamp=datetime.now().isoformat()
        )
        
        # 1. Technology Detection
        logger.info("[1/3] Running technology detection...")
        try:
            tech_result = await self.whatweb.scan(target)
            result.technology_scan = {
                "success": tech_result.success,
                "technologies": [
                    {
                        "name": t.name,
                        "version": t.version,
                        "confidence": t.confidence,
                        "category": t.category
                    }
                    for t in tech_result.technologies
                ],
                "headers": tech_result.headers,
                "error": tech_result.error
            }
        except Exception as e:
            logger.error(f"Technology scan failed: {e}")
            result.technology_scan = {"success": False, "error": str(e)}
            
        # 2. WAF Detection
        logger.info("[2/3] Running WAF detection...")
        try:
            waf_result = await self.wafw00f.detect(target)
            result.waf_detection = {
                "success": waf_result.success,
                "firewall_detected": waf_result.firewall_detected,
                "wafs": [
                    {"name": w.name, "confidence": w.confidence}
                    for w in waf_result.wafs
                ],
                "error": waf_result.error
            }
        except Exception as e:
            logger.error(f"WAF detection failed: {e}")
            result.waf_detection = {"success": False, "error": str(e)}
            
        # 3. Directory Bruteforce (Quick - only common dirs)
        logger.info("[3/3] Running directory bruteforce...")
        try:
            # Use smaller wordlist for quick scan
            ffuf_result = await self.ffuf.directory_bruteforce(
                target=f"http://{target}/FUZZ",
                extensions=["php", "html", "txt"],
                threads=20
            )
            result.directory_bruteforce = {
                "success": ffuf_result.success,
                "findings": [
                    {
                        "url": f.url,
                        "status_code": f.status_code,
                        "content_length": f.content_length
                    }
                    for f in ffuf_result.findings
                ],
                "total_requests": ffuf_result.total_requests,
                "duration": ffuf_result.duration,
                "error": ffuf_result.error
            }
        except Exception as e:
            logger.error(f"Directory bruteforce failed: {e}")
            result.directory_bruteforce = {"success": False, "error": str(e)}
            
        # Generate summary
        result.summary = self._generate_summary(result)
        
        return result
        
    def _generate_summary(self, result: ReconResult) -> Dict[str, Any]:
        """Generate scan summary"""
        tech_count = len(result.technology_scan.get("technologies", []))
        waf_detected = result.waf_detection.get("firewall_detected", False)
        dir_count = len(result.directory_bruteforce.get("findings", []))
        
        # Risk assessment
        risk_level = "low"
        if waf_detected:
            risk_level = "medium"  # WAF present but we found it
        if dir_count > 10:
            risk_level = "high"  # Many exposed directories
            
        return {
            "technologies_detected": tech_count,
            "waf_detected": waf_detected,
            "directories_found": dir_count,
            "risk_level": risk_level,
            "recommendations": self._generate_recommendations(result)
        }
        
    def _generate_recommendations(self, result: ReconResult) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # WAF recommendations
        if not result.waf_detection.get("firewall_detected"):
            recommendations.append("Consider implementing a Web Application Firewall (WAF)")
            
        # Technology recommendations
        outdated_tech = ["Apache/2.4.7", "OpenSSH 6.6.1"]
        for tech in result.technology_scan.get("technologies", []):
            tech_str = f"{tech.get('name', '')} {tech.get('version', '')}".strip()
            for outdated in outdated_tech:
                if outdated in tech_str:
                    recommendations.append(f"Update outdated software: {tech_str}")
                    
        # Directory recommendations
        if len(result.directory_bruteforce.get("findings", [])) > 5:
            recommendations.append("Restrict access to sensitive directories")
            
        return recommendations
        
    def save_report(self, result: ReconResult, filename: Optional[str] = None):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recon_{result.target}_{timestamp}.json"
            
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(asdict(result), f, indent=2)
            
        logger.info(f"Report saved to {filepath}")
        return filepath
        
    def print_report(self, result: ReconResult):
        """Print formatted report to console"""
        print("\n" + "="*70)
        print("🎯 UNIFIED RECONNAISSANCE REPORT")
        print("="*70)
        print(f"Target: {result.target}")
        print(f"Timestamp: {result.timestamp}")
        print()
        
        # Technology Scan
        print("📊 TECHNOLOGY DETECTION")
        print("-"*70)
        tech_scan = result.technology_scan
        if tech_scan.get("success"):
            techs = tech_scan.get("technologies", [])
            print(f"Found {len(techs)} technologies:")
            for tech in techs:
                version = f" ({tech.get('version')})" if tech.get('version') else ""
                print(f"  • {tech['name']}{version} [{tech['confidence']}%]")
        else:
            print(f"Failed: {tech_scan.get('error', 'Unknown error')}")
        print()
        
        # WAF Detection
        print("🛡️  WAF DETECTION")
        print("-"*70)
        waf_scan = result.waf_detection
        if waf_scan.get("success"):
            if waf_scan.get("firewall_detected"):
                print("⚠️  Web Application Firewall detected:")
                for waf in waf_scan.get("wafs", []):
                    print(f"  • {waf['name']} ({waf['confidence']} confidence)")
            else:
                print("✅ No WAF detected")
        else:
            print(f"Failed: {waf_scan.get('error', 'Unknown error')}")
        print()
        
        # Directory Bruteforce
        print("📁 DIRECTORY BRUTEFORCE")
        print("-"*70)
        dir_scan = result.directory_bruteforce
        if dir_scan.get("success"):
            findings = dir_scan.get("findings", [])
            print(f"Found {len(findings)} accessible paths:")
            for finding in findings[:10]:  # Show top 10
                print(f"  [{finding['status_code']}] {finding['url']} ({finding['content_length']} bytes)")
            if len(findings) > 10:
                print(f"  ... and {len(findings) - 10} more")
            print(f"\nDuration: {dir_scan.get('duration', 0):.2f}s")
            print(f"Total requests: {dir_scan.get('total_requests', 0)}")
        else:
            print(f"Failed: {dir_scan.get('error', 'Unknown error')}")
        print()
        
        # Summary
        print("📝 SUMMARY & RECOMMENDATIONS")
        print("-"*70)
        summary = result.summary
        print(f"Risk Level: {summary.get('risk_level', 'unknown').upper()}")
        print(f"Technologies: {summary.get('technologies_detected', 0)}")
        print(f"Directories: {summary.get('directories_found', 0)}")
        print()
        print("Recommendations:")
        for rec in summary.get("recommendations", []):
            print(f"  • {rec}")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Unified Reconnaissance Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unified_recon.py --target example.com
  python unified_recon.py --target example.com --output-dir ./reports
        """
    )
    
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target domain or URL"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="reports",
        help="Output directory for reports (default: reports)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    # Safety check
    print("⚠️  SAFETY CHECK")
    print("="*70)
    print(f"Target: {args.target}")
    print("\nEnsure you have authorization to scan this target!")
    confirm = input("\nContinue? (yes/no): ")
    
    if confirm.lower() not in ["yes", "y", "ja", "j"]:
        print("Aborted.")
        return
    
    # Run scan
    scanner = UnifiedReconScanner(output_dir=args.output_dir)
    
    try:
        result = asyncio.run(scanner.run_full_scan(args.target))
        
        # Save report
        report_path = scanner.save_report(result)
        
        # Print report
        if not args.quiet:
            scanner.print_report(result)
            print(f"\n💾 Full report saved to: {report_path}")
            
    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted by user")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise


if __name__ == "__main__":
    main()

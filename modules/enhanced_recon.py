"""
Enhanced Reconnaissance Module
Integriert FFuF, WhatWeb, WAFW00F in das Zen-AI-Pentest Framework
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from core.orchestrator import ZenOrchestrator
from tools.ffuf_integration_enhanced import FFuFIntegration, directory_bruteforce_sync
from tools.whatweb_integration import WhatWebIntegration, scan_sync
from tools.wafw00f_integration import WAFW00FIntegration, detect_sync

logger = logging.getLogger(__name__)


class EnhancedReconModule:
    """
    Erweitertes Reconnaissance Modul
    Kombiniert Nmap, FFuF, WhatWeb und WAFW00F
    """
    
    def __init__(self, orchestrator: Optional[ZenOrchestrator] = None):
        self.orchestrator = orchestrator or ZenOrchestrator()
        
        # Initialize tool integrations
        self.ffuf = FFuFIntegration()
        self.whatweb = WhatWebIntegration(aggression=1)
        self.wafw00f = WAFW00FIntegration()
        
    def technology_detection(self, target: str) -> Dict[str, Any]:
        """
        Erkennt Technologien mit WhatWeb
        
        Args:
            target: Ziel-URL oder Domain
            
        Returns:
            Dictionary mit Technologie-Informationen
        """
        logger.info(f"[EnhancedRecon] Technology detection for {target}")
        
        result = scan_sync(target)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "technologies": []
            }
            
        return {
            "success": True,
            "url": result.url,
            "technologies": [
                {
                    "name": t.name,
                    "version": t.version,
                    "confidence": t.confidence,
                    "category": t.category
                }
                for t in result.technologies
            ],
            "headers": result.headers
        }
        
    def waf_detection(self, target: str) -> Dict[str, Any]:
        """
        Erkennt Web Application Firewalls
        
        Args:
            target: Ziel-URL oder Domain
            
        Returns:
            Dictionary mit WAF-Informationen
        """
        logger.info(f"[EnhancedRecon] WAF detection for {target}")
        
        result = detect_sync(target)
        
        return {
            "success": result.success,
            "url": result.url,
            "firewall_detected": result.firewall_detected,
            "wafs": [
                {"name": w.name, "confidence": w.confidence}
                for w in result.wafs
            ],
            "error": result.error
        }
        
    def directory_bruteforce(
        self,
        target: str,
        extensions: Optional[List[str]] = None,
        wordlist: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Directory Bruteforce mit FFuF
        
        Args:
            target: Ziel-URL mit /FUZZ
            extensions: Dateiendungen (z.B. ["php", "html"])
            wordlist: Pfad zur Wortliste
            
        Returns:
            Dictionary mit gefundenen Verzeichnissen
        """
        logger.info(f"[EnhancedRecon] Directory bruteforce for {target}")
        
        if not target.endswith("/FUZZ") and "/FUZZ" not in target:
            target = f"{target.rstrip('/')}/FUZZ"
            
        result = directory_bruteforce_sync(
            target,
            wordlist=wordlist,
            extensions=extensions
        )
        
        return {
            "success": result.success,
            "findings": [
                {
                    "url": f.url,
                    "status_code": f.status_code,
                    "content_length": f.content_length,
                    "content_words": f.content_words
                }
                for f in result.findings
            ],
            "total_requests": result.total_requests,
            "duration": result.duration,
            "error": result.error
        }
        
    def full_recon(self, target: str) -> Dict[str, Any]:
        """
        Komplette Reconnaissance
        Führt alle Scans aus
        
        Args:
            target: Ziel-Domain oder URL
            
        Returns:
            Dictionary mit allen Ergebnissen
        """
        logger.info(f"[EnhancedRecon] Full reconnaissance for {target}")
        
        # Ensure URL format
        if not target.startswith(("http://", "https://")):
            target_url = f"http://{target}"
        else:
            target_url = target
            target = target.replace("http://", "").replace("https://", "").split("/")[0]
            
        # Run all scans
        tech_result = self.technology_detection(target_url)
        waf_result = self.waf_detection(target_url)
        dir_result = self.directory_bruteforce(target_url)
        
        # Generate summary
        risk_level = "low"
        if waf_result.get("firewall_detected"):
            risk_level = "medium"
        if len(dir_result.get("findings", [])) > 5:
            risk_level = "high"
            
        # Generate recommendations
        recommendations = []
        if not waf_result.get("firewall_detected"):
            recommendations.append("Implement a Web Application Firewall (WAF)")
            
        for tech in tech_result.get("technologies", []):
            if tech.get("name") in ["Apache", "nginx", "PHP"]:
                version = tech.get("version", "")
                if version and version.startswith(("2.4.7", "1.18.0", "7.4")):
                    recommendations.append(f"Update outdated {tech['name']} ({version})")
                    
        if len(dir_result.get("findings", [])) > 5:
            recommendations.append("Restrict access to sensitive directories")
            
        return {
            "target": target,
            "timestamp": str(asyncio.get_event_loop().time()),
            "technology_scan": tech_result,
            "waf_detection": waf_result,
            "directory_scan": dir_result,
            "summary": {
                "risk_level": risk_level,
                "technologies_found": len(tech_result.get("technologies", [])),
                "waf_detected": waf_result.get("firewall_detected", False),
                "directories_found": len(dir_result.get("findings", [])),
                "recommendations": recommendations
            }
        }


# CLI Interface
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Enhanced Reconnaissance Module")
    parser.add_argument("--target", "-t", required=True, help="Target domain or URL")
    parser.add_argument("--mode", "-m", choices=["tech", "waf", "dir", "full"], default="full",
                       help="Scan mode (default: full)")
    parser.add_argument("--extensions", "-e", default="php,html,txt",
                       help="File extensions for directory scan (comma-separated)")
    parser.add_argument("--output", "-o", help="Output file for JSON report")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    # Initialize module
    recon = EnhancedReconModule()
    
    # Run scan based on mode
    if args.mode == "tech":
        result = recon.technology_detection(args.target)
    elif args.mode == "waf":
        result = recon.waf_detection(args.target)
    elif args.mode == "dir":
        extensions = args.extensions.split(",") if args.extensions else None
        result = recon.directory_bruteforce(args.target, extensions=extensions)
    else:  # full
        result = recon.full_recon(args.target)
        
    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        if not args.quiet:
            print(f"Report saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))

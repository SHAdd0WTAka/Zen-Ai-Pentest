"""
WAFW00F Integration - Web Application Firewall Detection
Erkennt WAFs (Cloudflare, AWS WAF, ModSecurity, etc.)
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WAFFinding:
    """Detected WAF"""

    name: str
    manufacturer: str = ""
    detected: bool = False
    confidence: str = "high"  # high, medium, low


@dataclass
class WAFW00FResult:
    """WAFW00F scan result"""

    success: bool
    url: str = ""
    wafs: List[WAFFinding] = field(default_factory=list)
    firewall_detected: bool = False
    error: Optional[str] = None
    raw_output: str = ""


class WAFW00FIntegration:
    """WAFW00F Web Application Firewall Detector"""

    async def detect(self, target: str) -> WAFW00FResult:
        """
        Detect WAF on target

        Args:
            target: Target URL or domain
        """
        # Validate target
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        cmd = ["wafw00f", "-a", "-o", "-", target]

        logger.info(f"Starting WAFW00F detection: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            if process.returncode != 0 and not output:
                logger.error(f"WAFW00F error: {error}")
                return WAFW00FResult(success=False, error=error)

            # Parse output
            wafs = []
            firewall_detected = False

            # Try JSON output first
            try:
                if output.startswith("["):
                    data = json.loads(output)
                    for item in data:
                        detected_wafs = item.get("firewall", "")
                        if detected_wafs and detected_wafs != "None":
                            firewall_detected = True
                            for waf_name in detected_wafs.split(","):
                                waf_name = waf_name.strip()
                                if waf_name:
                                    wafs.append(WAFFinding(name=waf_name, detected=True, confidence="high"))
            except json.JSONDecodeError:
                # Fallback: parse text output
                wafs, firewall_detected = self._parse_text_output(output)

            return WAFW00FResult(success=True, url=target, wafs=wafs, firewall_detected=firewall_detected, raw_output=output)

        except asyncio.TimeoutError:
            logger.error("WAFW00F detection timed out")
            return WAFW00FResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"WAFW00F error: {e}")
            return WAFW00FResult(success=False, error=str(e))

    def _parse_text_output(self, output: str) -> tuple:
        """Parse text output"""
        wafs = []
        firewall_detected = False

        # Pattern: "The site http://... is behind X WAF"
        waf_pattern = r"behind\s+(.+?)\s+WAF"
        matches = re.findall(waf_pattern, output, re.IGNORECASE)

        for match in matches:
            firewall_detected = True
            waf_names = match.split(" and ")
            for name in waf_names:
                wafs.append(WAFFinding(name=name.strip(), detected=True, confidence="high"))

        # Check for "No WAF detected"
        if "No WAF" in output or "not behind" in output.lower():
            firewall_detected = False

        return wafs, firewall_detected


# Sync wrapper
def detect_sync(target: str) -> WAFW00FResult:
    """Synchronous wrapper"""
    wafw00f = WAFW00FIntegration()
    return asyncio.run(wafw00f.detect(target))


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("Testing WAFW00F Integration...")
    print("=" * 60)

    result = detect_sync("http://scanme.nmap.org")

    print(f"Success: {result.success}")
    print(f"URL: {result.url}")
    print(f"Firewall Detected: {result.firewall_detected}")

    if result.wafs:
        print(f"\nDetected WAFs ({len(result.wafs)}):")
        for waf in result.wafs:
            print(f"  • {waf.name} ({waf.confidence} confidence)")
    else:
        print("\nNo WAF detected")

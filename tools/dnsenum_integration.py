"""
DNSenum Integration for Zen-AI-Pentest
DNS enumeration and zone transfer testing
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DNSEnumResult:
    """Result from DNS enumeration"""

    domain: str
    host_records: List[Dict[str, Any]]
    name_servers: List[str]
    mx_records: List[Dict[str, str]]
    zone_transfer_vulnerable: bool
    raw_output: str
    success: bool
    error_message: Optional[str] = None


class DNSenumScanner:
    """DNS enumeration scanner"""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.tool_path = self._find_dnsenum()

    def _find_dnsenum(self) -> Optional[str]:
        """Find dnsenum binary"""
        try:
            result = subprocess.run(["which", "dnsenum"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "dnsenum"

    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate scan parameters"""
        if "domain" not in params or not params["domain"]:
            return False, "Domain parameter is required"

        domain = params["domain"]
        if not isinstance(domain, str) or "." not in domain:
            return False, "Invalid domain format"

        return True, None

    def _build_command(self, domain: str, options: Dict[str, Any]) -> List[str]:
        """Build dnsenum command"""
        cmd = [self.tool_path, domain]

        # Add threads
        threads = options.get("threads", 10)
        cmd.extend(["-t", str(threads)])

        # Enable zone transfer check
        if options.get("check_zone_transfer", True):
            cmd.append("--enum")

        # Timeout
        timeout = options.get("timeout", self.timeout)
        cmd.extend(["--timeout", str(timeout)])

        # Verbose output
        cmd.append("-v")

        return cmd

    def _parse_output(self, output: str, domain: str) -> DNSEnumResult:
        """Parse dnsenum output"""
        host_records = []
        name_servers = []
        mx_records = []
        zone_transfer_vulnerable = False

        lines = output.split("\n")

        for line in lines:
            line = line.strip()

            # Check for zone transfer vulnerability
            if "Zone Transfer" in line and "successful" in line.lower():
                zone_transfer_vulnerable = True

            # Parse host records (A records)
            if line.startswith("Host:"):
                parts = line.split()
                if len(parts) >= 3:
                    host_records.append({"hostname": parts[1], "ip": parts[2] if len(parts) > 2 else None})

            # Parse name servers
            if "Name Server:" in line or line.startswith("NS:"):
                parts = line.split()
                for part in parts:
                    if "." in part and part != "Server:" and part != "NS:":
                        name_servers.append(part.rstrip("."))

            # Parse MX records
            if "MX" in line and "preference" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    mx_records.append(
                        {"server": parts[-1].rstrip("."), "preference": parts[-2] if parts[-2].isdigit() else "0"}
                    )

        # Remove duplicates
        name_servers = list(set(name_servers))

        return DNSEnumResult(
            domain=domain,
            host_records=host_records,
            name_servers=name_servers,
            mx_records=mx_records,
            zone_transfer_vulnerable=zone_transfer_vulnerable,
            raw_output=output,
            success=True,
        )

    async def execute(self, params: Dict[str, Any]) -> DNSEnumResult:
        """Execute DNS enumeration"""
        valid, error = self.validate_parameters(params)
        if not valid:
            return DNSEnumResult(
                domain=params.get("domain", ""),
                host_records=[],
                name_servers=[],
                mx_records=[],
                zone_transfer_vulnerable=False,
                raw_output="",
                success=False,
                error_message=error,
            )

        domain = params["domain"]
        options = params.get("options", {})

        cmd = self._build_command(domain, options)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            output = stdout.decode("utf-8", errors="ignore")

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.warning(f"DNSenum returned non-zero: {error_msg}")

            return self._parse_output(output, domain)

        except asyncio.TimeoutError:
            logger.error("DNSenum scan timed out")
            return DNSEnumResult(
                domain=domain,
                host_records=[],
                name_servers=[],
                mx_records=[],
                zone_transfer_vulnerable=False,
                raw_output="",
                success=False,
                error_message="Scan timed out",
            )
        except Exception as e:
            logger.error(f"DNSenum execution error: {e}")
            return DNSEnumResult(
                domain=domain,
                host_records=[],
                name_servers=[],
                mx_records=[],
                zone_transfer_vulnerable=False,
                raw_output="",
                success=False,
                error_message=str(e),
            )


# Import asyncio at module level
import asyncio


class DNSenumTool:
    """Tool wrapper for DNSenum integration"""

    def __init__(self):
        self.name = "dnsenum"
        self.description = "DNS enumeration and zone transfer testing"
        self.version = "1.0.0"

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema"""
        return {
            "domain": {"type": "string", "description": "Target domain", "required": True},
            "threads": {"type": "integer", "description": "Number of threads", "default": 10, "minimum": 1, "maximum": 50},
            "check_zone_transfer": {
                "type": "boolean",
                "description": "Check for zone transfer vulnerability",
                "default": True,
            },
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run DNSenum scan"""
        scanner = DNSenumScanner()
        result = await scanner.execute(params)

        return {
            "success": result.success,
            "domain": result.domain,
            "host_records": result.host_records,
            "name_servers": result.name_servers,
            "mx_records": result.mx_records,
            "zone_transfer_vulnerable": result.zone_transfer_vulnerable,
            "error": result.error_message,
        }


# Tool registration
TOOL_REGISTRY = {"dnsenum": DNSenumTool}


if __name__ == "__main__":
    # Test
    async def test():
        scanner = DNSenumScanner()
        result = await scanner.execute({"domain": "example.com", "options": {"threads": 5}})
        print(json.dumps(result.to_dict(), indent=2))

    asyncio.run(test())

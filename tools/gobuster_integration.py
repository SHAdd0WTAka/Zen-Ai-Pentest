"""
Gobuster Integration for Zen-AI-Pentest
Directory and file brute-forcing
"""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GobusterResult:
    """Result from Gobuster scan"""

    target: str
    found_paths: List[Dict[str, Any]]
    status_codes: Dict[int, int]
    total_requests: int
    duration: float
    success: bool
    error_message: Optional[str] = None


class GobusterScanner:
    """Gobuster directory/file brute-forcer"""

    def __init__(self, timeout: int = 300, wordlist: Optional[str] = None):
        self.timeout = timeout
        self.default_wordlist = wordlist or "/usr/share/wordlists/dirb/common.txt"
        self.tool_path = self._find_gobuster()

    def _find_gobuster(self) -> str:
        """Find gobuster binary"""
        try:
            result = subprocess.run(["which", "gobuster"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "gobuster"

    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate scan parameters"""
        if "target" not in params or not params["target"]:
            return False, "Target URL is required"

        target = params["target"]
        if not target.startswith(("http://", "https://")):
            return False, "Target must be a valid URL (http:// or https://)"

        return True, None

    def _build_command(self, target: str, options: Dict[str, Any]) -> List[str]:
        """Build gobuster command"""
        cmd = [self.tool_path, "dir", "-u", target]

        # Wordlist
        wordlist = options.get("wordlist", self.default_wordlist)
        cmd.extend(["-w", wordlist])

        # Threads
        threads = options.get("threads", 10)
        cmd.extend(["-t", str(threads)])

        # Extensions
        if "extensions" in options:
            cmd.extend(["-x", options["extensions"]])

        # Status codes to show
        cmd.extend(["-o", "/dev/stdout"])

        # Timeout
        timeout = options.get("timeout", self.timeout)
        cmd.extend(["--timeout", f"{timeout}s"])

        return cmd

    def _parse_output(self, output: str, target: str) -> GobusterResult:
        """Parse gobuster output"""
        found_paths = []
        status_codes = {}

        for line in output.split("\n"):
            line = line.strip()
            if not line or not line.startswith("/"):
                continue

            # Parse lines like: /admin (Status: 200) [Size: 1234]
            if "Status:" in line:
                parts = line.split()
                if len(parts) >= 3:
                    path = parts[0]
                    status_str = parts[2].rstrip(")")
                    try:
                        status = int(status_str)
                        found_paths.append({"path": path, "status": status, "url": f"{target.rstrip('/')}{path}"})
                        status_codes[status] = status_codes.get(status, 0) + 1
                    except ValueError:
                        pass

        return GobusterResult(
            target=target,
            found_paths=found_paths,
            status_codes=status_codes,
            total_requests=len(found_paths),
            duration=0.0,
            success=True,
        )

    async def execute(self, params: Dict[str, Any]) -> GobusterResult:
        """Execute Gobuster scan"""
        import time

        valid, error = self.validate_parameters(params)
        if not valid:
            return GobusterResult(
                target=params.get("target", ""),
                found_paths=[],
                status_codes={},
                total_requests=0,
                duration=0.0,
                success=False,
                error_message=error,
            )

        target = params["target"]
        options = params.get("options", {})

        cmd = self._build_command(target, options)

        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            duration = time.time() - start_time
            output = stdout.decode("utf-8", errors="ignore")

            result = self._parse_output(output, target)
            result.duration = duration

            return result

        except asyncio.TimeoutError:
            logger.error("Gobuster scan timed out")
            return GobusterResult(
                target=target,
                found_paths=[],
                status_codes={},
                total_requests=0,
                duration=time.time() - start_time,
                success=False,
                error_message="Scan timed out",
            )
        except Exception as e:
            logger.error(f"Gobuster execution error: {e}")
            return GobusterResult(
                target=target,
                found_paths=[],
                status_codes={},
                total_requests=0,
                duration=time.time() - start_time,
                success=False,
                error_message=str(e),
            )


class GobusterTool:
    """Tool wrapper for Gobuster integration"""

    def __init__(self):
        self.name = "gobuster"
        self.description = "Directory and file brute-forcing"
        self.version = "1.0.0"

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema"""
        return {
            "target": {"type": "string", "description": "Target URL (e.g., http://example.com)", "required": True},
            "wordlist": {
                "type": "string",
                "description": "Path to wordlist file",
                "default": "/usr/share/wordlists/dirb/common.txt",
            },
            "threads": {
                "type": "integer",
                "description": "Number of concurrent threads",
                "default": 10,
                "minimum": 1,
                "maximum": 50,
            },
            "extensions": {"type": "string", "description": "File extensions to search (e.g., php,txt,html)", "default": ""},
        }

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run Gobuster scan"""
        scanner = GobusterScanner()
        result = await scanner.execute(params)

        return {
            "success": result.success,
            "target": result.target,
            "found_paths": result.found_paths,
            "status_codes": result.status_codes,
            "total_requests": result.total_requests,
            "duration": result.duration,
            "error": result.error_message,
        }


# Tool registration
TOOL_REGISTRY = {"gobuster": GobusterTool}


if __name__ == "__main__":
    # Test
    async def test():
        scanner = GobusterScanner()
        result = await scanner.execute(
            {"target": "http://scanme.nmap.org", "options": {"threads": 5, "extensions": "php,txt"}}
        )
        logger.info(f"Found {len(result.found_paths)} paths")
        for path in result.found_paths[:5]:
            logger.info(f"  {path['path']} - Status: {path['status']}")

    asyncio.run(test())

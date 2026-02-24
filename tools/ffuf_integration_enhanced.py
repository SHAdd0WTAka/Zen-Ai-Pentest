"""
FFuF Integration - Fast Web Fuzzer
Erweiterte Integration für Zen-AI-Pentest

Supports:
- Directory bruteforcing
- Parameter fuzzing
- Virtual host discovery
- POST data fuzzing
- Filter & Matcher rules
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FFuFFinding:
    """Represents a FFuF finding"""

    url: str
    status_code: int
    content_length: int
    content_words: int
    content_lines: int
    redirect_location: str = ""
    result_type: str = "directory"  # directory, parameter, vhost


@dataclass
class FFuFResult:
    """FFuF scan result"""

    success: bool
    findings: List[FFuFFinding] = field(default_factory=list)
    command: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    total_requests: int = 0


class FFuFIntegration:
    """FFuF Web Fuzzer Integration"""

    def __init__(self, wordlist_dir: str = "/usr/share/wordlists"):
        self.wordlist_dir = Path(wordlist_dir)
        self.default_wordlists = {
            "directories": self.wordlist_dir / "dirb" / "common.txt",
            "big": self.wordlist_dir / "dirb" / "big.txt",
            "parameters": self.wordlist_dir / "dirb" / "common.txt",
        }

    async def directory_bruteforce(
        self,
        target: str,
        wordlist: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        threads: int = 40,
        timeout: int = 10,
    ) -> FFuFResult:
        """
        Directory bruteforcing with FFuF

        Args:
            target: Target URL (e.g., http://example.com/FUZZ)
            wordlist: Path to wordlist
            extensions: File extensions to test (e.g., ["php", "html", "js"])
            threads: Number of concurrent threads
            timeout: Request timeout in seconds
        """
        import time

        start_time = time.time()

        # Validate target
        if "FUZZ" not in target:
            target = f"{target.rstrip('/')}/FUZZ"

        wordlist_path = wordlist or str(self.default_wordlists["directories"])

        # Build command
        cmd = [
            "ffuf",
            "-u",
            target,
            "-w",
            wordlist_path,
            "-t",
            str(threads),
            "-timeout",
            str(timeout),
            "-json",
            "-mc",
            "200,201,204,301,302,307,401,403,405,500",  # Match codes
            "-fc",
            "404",  # Filter 404
        ]

        # Add extensions if specified
        if extensions:
            cmd.extend(
                ["-e", ",".join(f".{e.lstrip('.')}" for e in extensions)]
            )

        logger.info(f"Starting FFuF directory scan: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=300
            )

            findings = []
            total_requests = 0

            # Parse JSON output (one JSON object per line)
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)

                    # Skip config/error lines
                    if data.get("type") == "result":
                        finding = FFuFFinding(
                            url=data.get("url", ""),
                            status_code=data.get("status", 0),
                            content_length=data.get("length", 0),
                            content_words=data.get("words", 0),
                            content_lines=data.get("lines", 0),
                            redirect_location=data.get("redirectlocation", ""),
                            result_type="directory",
                        )
                        findings.append(finding)

                    elif data.get("type") == "summary":
                        total_requests = data.get("total", 0)

                except json.JSONDecodeError:
                    continue

            duration = time.time() - start_time

            return FFuFResult(
                success=True,
                findings=findings,
                command=" ".join(cmd),
                duration=duration,
                total_requests=total_requests,
            )

        except asyncio.TimeoutError:
            logger.error("FFuF scan timed out")
            return FFuFResult(
                success=False,
                error="Scan timeout (300s)",
                command=" ".join(cmd),
            )
        except Exception as e:
            logger.error(f"FFuF error: {e}")
            return FFuFResult(
                success=False, error=str(e), command=" ".join(cmd)
            )

    async def parameter_fuzzing(
        self,
        target: str,
        wordlist: Optional[str] = None,
        method: str = "GET",
        data: Optional[str] = None,
        threads: int = 20,
    ) -> FFuFResult:
        """
        Parameter fuzzing with FFuF

        Args:
            target: Target URL with FUZZ keyword (e.g., http://example.com/page?param=FUZZ)
            wordlist: Path to parameter wordlist
            method: HTTP method (GET, POST, etc.)
            data: POST data with FUZZ keyword
            threads: Number of threads
        """
        import time

        start_time = time.time()

        wordlist_path = wordlist or str(self.default_wordlists["parameters"])

        cmd = [
            "ffuf",
            "-u",
            target,
            "-w",
            wordlist_path,
            "-X",
            method,
            "-t",
            str(threads),
            "-json",
            "-mc",
            "200,201,204,301,302,307,401,403,500",
        ]

        if data:
            cmd.extend(["-d", data])

        logger.info(f"Starting FFuF parameter fuzzing: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=300
            )

            findings = []
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "result":
                        finding = FFuFFinding(
                            url=data.get("url", ""),
                            status_code=data.get("status", 0),
                            content_length=data.get("length", 0),
                            content_words=data.get("words", 0),
                            content_lines=data.get("lines", 0),
                            result_type="parameter",
                        )
                        findings.append(finding)
                except json.JSONDecodeError:
                    continue

            return FFuFResult(
                success=True,
                findings=findings,
                command=" ".join(cmd),
                duration=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"FFuF parameter fuzzing error: {e}")
            return FFuFResult(success=False, error=str(e))

    async def vhost_discovery(
        self, target: str, wordlist: Optional[str] = None, threads: int = 40
    ) -> FFuFResult:
        """
        Virtual host discovery

        Args:
            target: Target IP (e.g., http://10.0.0.1)
            wordlist: Path to vhost wordlist
            threads: Number of threads
        """
        import time

        start_time = time.time()

        wordlist_path = wordlist or str(self.default_wordlists["directories"])

        cmd = [
            "ffuf",
            "-u",
            target,
            "-H",
            "Host: FUZZ",
            "-w",
            wordlist_path,
            "-t",
            str(threads),
            "-json",
            "-mc",
            "200,301,302,403",
        ]

        logger.info(f"Starting FFuF vhost discovery: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=300
            )

            findings = []
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "result":
                        finding = FFuFFinding(
                            url=data.get("url", ""),
                            status_code=data.get("status", 0),
                            content_length=data.get("length", 0),
                            result_type="vhost",
                        )
                        findings.append(finding)
                except json.JSONDecodeError:
                    continue

            return FFuFResult(
                success=True,
                findings=findings,
                command=" ".join(cmd),
                duration=time.time() - start_time,
            )

        except Exception as e:
            logger.error(f"FFuF vhost discovery error: {e}")
            return FFuFResult(success=False, error=str(e))


# Sync wrapper for easier usage
def directory_bruteforce_sync(
    target: str,
    wordlist: Optional[str] = None,
    extensions: Optional[List[str]] = None,
) -> FFuFResult:
    """Synchronous wrapper for directory bruteforcing"""
    ffuf = FFuFIntegration()
    return asyncio.run(ffuf.directory_bruteforce(target, wordlist, extensions))


if __name__ == "__main__":
    # Test
    import logging

    logging.basicConfig(level=logging.INFO)

    print("Testing FFuF Integration...")
    print("=" * 60)

    # Test directory bruteforce
    result = directory_bruteforce_sync(
        "http://scanme.nmap.org/FUZZ", extensions=["php", "html"]
    )

    print(f"Success: {result.success}")
    print(f"Findings: {len(result.findings)}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Total Requests: {result.total_requests}")

    for finding in result.findings[:5]:
        print(
            f"  [{finding.status_code}] {finding.url} ({finding.content_length} bytes)"
        )

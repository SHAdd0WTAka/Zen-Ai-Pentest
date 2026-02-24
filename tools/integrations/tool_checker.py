"""
Tool Availability Checker

Checks which pentest tools are installed and available.
"""

import logging
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool availability status"""

    AVAILABLE = "available"
    MISSING = "missing"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class ToolAvailability:
    """Tool availability information"""

    name: str
    status: ToolStatus
    version: Optional[str] = None
    path: Optional[str] = None
    error_message: Optional[str] = None
    required: bool = True


class ToolChecker:
    """
    Checks availability of pentest tools

    Usage:
        checker = ToolChecker()
        results = checker.check_all()

        if results["nmap"].status == ToolStatus.AVAILABLE:
            print("Nmap is ready!")
    """

    # Required tools for full functionality
    REQUIRED_TOOLS = ["nmap", "sqlmap"]

    # Optional but recommended tools
    OPTIONAL_TOOLS = [
        "nuclei",
        "gobuster",
        "subfinder",
        "amass",
        "ffuf",
        "hydra",
        "nikto",
        "whatweb",
        "wafw00f",
    ]

    def __init__(self):
        self._cache: Dict[str, ToolAvailability] = {}

    def check_tool(self, tool_name: str) -> ToolAvailability:
        """Check if a specific tool is available"""

        # Check cache first
        if tool_name in self._cache:
            return self._cache[tool_name]

        # Find tool in PATH
        tool_path = shutil.which(tool_name)

        if not tool_path:
            availability = ToolAvailability(
                name=tool_name,
                status=ToolStatus.MISSING,
                error_message=f"{tool_name} not found in PATH",
                required=tool_name in self.REQUIRED_TOOLS,
            )
            self._cache[tool_name] = availability
            return availability

        # Try to get version
        try:
            version = self._get_version(tool_name)
            availability = ToolAvailability(
                name=tool_name,
                status=ToolStatus.AVAILABLE,
                version=version,
                path=tool_path,
                required=tool_name in self.REQUIRED_TOOLS,
            )
        except Exception as e:
            availability = ToolAvailability(
                name=tool_name,
                status=ToolStatus.ERROR,
                path=tool_path,
                error_message=str(e),
                required=tool_name in self.REQUIRED_TOOLS,
            )

        self._cache[tool_name] = availability
        return availability

    def check_all(self) -> Dict[str, ToolAvailability]:
        """Check all known tools"""
        all_tools = self.REQUIRED_TOOLS + self.OPTIONAL_TOOLS

        results = {}
        for tool in all_tools:
            results[tool] = self.check_tool(tool)

        return results

    def _get_version(self, tool_name: str) -> Optional[str]:
        """Get tool version"""
        version_flags = {
            "nmap": "-V",
            "sqlmap": "--version",
            "nuclei": "-version",
            "gobuster": "version",
            "subfinder": "-version",
            "amass": "-version",
            "ffuf": "-V",
            "hydra": "-V",
            "nikto": "-Version",
            "whatweb": "-v",
            "wafw00f": "--version",
        }

        flag = version_flags.get(tool_name, "--version")

        try:
            result = subprocess.run(
                [tool_name, flag], capture_output=True, text=True, timeout=5
            )

            # Parse version from output (tool-specific)
            output = result.stdout + result.stderr

            if tool_name == "nmap":
                # Nmap version 7.94
                for line in output.split("\n"):
                    if "Nmap version" in line:
                        return line.split()[2]

            elif tool_name == "sqlmap":
                # 1.7.10#stable
                for line in output.split("\n"):
                    if line and not line.startswith("["):
                        return line.strip()

            elif tool_name == "nuclei":
                # [INF] Current Version: v3.1.0
                for line in output.split("\n"):
                    if "Current Version" in line:
                        return line.split(":")[1].strip()

            else:
                # Generic: first non-empty line
                for line in output.split("\n"):
                    if line.strip():
                        return line.strip()[:50]  # Limit length

            return "unknown"

        except Exception as e:
            logger.warning(f"Could not get version for {tool_name}: {e}")
            return "unknown"

    def get_missing_required(self) -> List[str]:
        """Get list of missing required tools"""
        missing = []
        for tool in self.REQUIRED_TOOLS:
            result = self.check_tool(tool)
            if result.status != ToolStatus.AVAILABLE:
                missing.append(tool)
        return missing

    def get_missing_optional(self) -> List[str]:
        """Get list of missing optional tools"""
        missing = []
        for tool in self.OPTIONAL_TOOLS:
            result = self.check_tool(tool)
            if result.status != ToolStatus.AVAILABLE:
                missing.append(tool)
        return missing

    def is_ready(self) -> bool:
        """Check if all required tools are available"""
        return len(self.get_missing_required()) == 0

    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        results = self.check_all()

        required_available = sum(
            1
            for t in self.REQUIRED_TOOLS
            if results[t].status == ToolStatus.AVAILABLE
        )

        optional_available = sum(
            1
            for t in self.OPTIONAL_TOOLS
            if results[t].status == ToolStatus.AVAILABLE
        )

        return {
            "ready": self.is_ready(),
            "required": {
                "total": len(self.REQUIRED_TOOLS),
                "available": required_available,
                "missing": self.get_missing_required(),
            },
            "optional": {
                "total": len(self.OPTIONAL_TOOLS),
                "available": optional_available,
                "missing": self.get_missing_optional(),
            },
            "tools": {
                name: {
                    "status": result.status.value,
                    "version": result.version,
                    "path": result.path,
                    "required": result.required,
                }
                for name, result in results.items()
            },
        }


def check_tools_cli():
    """CLI tool to check tool availability"""

    print("🔍 Checking Pentest Tool Availability...\n")

    checker = ToolChecker()
    report = checker.get_status_report()

    # Print summary
    print("=" * 60)
    print(
        f"Required Tools: {report['required']['available']}/{report['required']['total']} ✅"
    )
    print(
        f"Optional Tools: {report['optional']['available']}/{report['optional']['total']} 📦"
    )
    print("=" * 60)
    print()

    # Print details
    for tool_name, info in report["tools"].items():
        status_icon = "✅" if info["status"] == "available" else "❌"
        required_indicator = "[REQ]" if info["required"] else "[OPT]"

        print(f"{status_icon} {tool_name:15} {required_indicator}")

        if info["version"]:
            print(f"   Version: {info['version']}")
        if info["path"]:
            print(f"   Path: {info['path']}")
        if info["status"] != "available":
            print(f"   Status: {info['status']}")

    print()

    # Print missing required
    if report["required"]["missing"]:
        print("⚠️  Missing Required Tools:")
        for tool in report["required"]["missing"]:
            print(f"   - {tool}")
        print("\nInstall with: ./install-tools.sh")

    # Exit code
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    exit(check_tools_cli())

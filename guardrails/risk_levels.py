"""
Risk Levels
===========

Defines and enforces risk levels for security testing operations.
Higher risk levels allow more aggressive testing but require more validation.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Set


class RiskLevel(IntEnum):
    """
    Risk levels for pentest operations.

    0 - SAFE: Reconnaissance only, no active testing
    1 - NORMAL: Standard scanning, no exploitation
    2 - ELEVATED: Aggressive scanning, light exploitation
    3 - AGGRESSIVE: Full exploitation, all techniques
    """

    SAFE = 0
    NORMAL = 1
    ELEVATED = 2
    AGGRESSIVE = 3


@dataclass
class ToolRiskProfile:
    """Risk profile for a security tool"""

    name: str
    min_risk_level: RiskLevel
    description: str
    dangerous_flags: List[str]
    requires_confirmation: bool = False


class RiskLevelManager:
    """
    Manages risk levels and tool permissions.

    Maps tools to minimum required risk levels and validates
    operations against current risk level.
    """

    # Default tool risk profiles
    TOOL_PROFILES: Dict[str, ToolRiskProfile] = {
        # SAFE tools (Risk Level 0)
        "whois": ToolRiskProfile(
            name="whois",
            min_risk_level=RiskLevel.SAFE,
            description="WHOIS lookup - passive reconnaissance",
            dangerous_flags=[],
        ),
        "dns": ToolRiskProfile(
            name="dns",
            min_risk_level=RiskLevel.SAFE,
            description="DNS enumeration - passive reconnaissance",
            dangerous_flags=[],
        ),
        "subdomain": ToolRiskProfile(
            name="subdomain",
            min_risk_level=RiskLevel.SAFE,
            description="Subdomain discovery - passive reconnaissance",
            dangerous_flags=[],
        ),
        # NORMAL tools (Risk Level 1)
        "nmap": ToolRiskProfile(
            name="nmap",
            min_risk_level=RiskLevel.NORMAL,
            description="Port scanning - active reconnaissance",
            dangerous_flags=["-T5", "--script", "--osscan-guess"],
        ),
        "web_enum": ToolRiskProfile(
            name="web_enum",
            min_risk_level=RiskLevel.NORMAL,
            description="Web enumeration - active reconnaissance",
            dangerous_flags=["--force", "--brute-force"],
        ),
        "directory": ToolRiskProfile(
            name="directory",
            min_risk_level=RiskLevel.NORMAL,
            description="Directory brute force - active reconnaissance",
            dangerous_flags=["--recursive", "--force"],
        ),
        "service": ToolRiskProfile(
            name="service",
            min_risk_level=RiskLevel.NORMAL,
            description="Service detection - active reconnaissance",
            dangerous_flags=[],
        ),
        "nuclei": ToolRiskProfile(
            name="nuclei",
            min_risk_level=RiskLevel.NORMAL,
            description="Vulnerability scanning - active testing",
            dangerous_flags=["-severity critical", "-tags dos"],
        ),
        # ELEVATED tools (Risk Level 2)
        "sqlmap": ToolRiskProfile(
            name="sqlmap",
            min_risk_level=RiskLevel.ELEVATED,
            description="SQL injection testing - exploitation",
            dangerous_flags=["--risk=3", "--level=5", "--os-shell"],
            requires_confirmation=True,
        ),
        "exploit": ToolRiskProfile(
            name="exploit",
            min_risk_level=RiskLevel.ELEVATED,
            description="Exploit attempt - active exploitation",
            dangerous_flags=["--payload", "--reverse-shell"],
            requires_confirmation=True,
        ),
        # AGGRESSIVE tools (Risk Level 3)
        "pivot": ToolRiskProfile(
            name="pivot",
            min_risk_level=RiskLevel.AGGRESSIVE,
            description="Network pivoting - post-exploitation",
            dangerous_flags=["--tunnel", "--port-forward"],
            requires_confirmation=True,
        ),
        "lateral": ToolRiskProfile(
            name="lateral",
            min_risk_level=RiskLevel.AGGRESSIVE,
            description="Lateral movement - post-exploitation",
            dangerous_flags=["--pass-the-hash", "--mimikatz"],
            requires_confirmation=True,
        ),
    }

    # Risk level descriptions
    RISK_DESCRIPTIONS: Dict[RiskLevel, str] = {
        RiskLevel.SAFE: "Safe reconnaissance only - no active testing",
        RiskLevel.NORMAL: "Standard security scanning - no exploitation",
        RiskLevel.ELEVATED: "Aggressive scanning with light exploitation",
        RiskLevel.AGGRESSIVE: "Full exploitation and post-exploitation",
    }

    def __init__(self, current_level: RiskLevel = RiskLevel.NORMAL):
        """
        Initialize risk level manager.

        Args:
            current_level: Current risk level for operations
        """
        self.current_level = current_level
        self.tool_profiles = self.TOOL_PROFILES.copy()
        self.approved_tools: Set[str] = set()  # Tools explicitly approved for this session

    def set_risk_level(self, level: RiskLevel):
        """Set current risk level"""
        self.current_level = level

    def get_risk_level(self) -> RiskLevel:
        """Get current risk level"""
        return self.current_level

    def can_run_tool(self, tool_name: str) -> bool:
        """
        Check if a tool can be run at current risk level.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool is allowed at current risk level
        """
        profile = self.tool_profiles.get(tool_name)
        if not profile:
            # Unknown tool - allow at NORMAL and above, require confirmation
            return self.current_level >= RiskLevel.NORMAL

        return self.current_level >= profile.min_risk_level

    def validate_tool(self, tool_name: str, flags: Optional[List[str]] = None) -> Dict:
        """
        Validate tool execution with flags.

        Args:
            tool_name: Name of the tool
            flags: Command flags being used

        Returns:
            Validation result dict with allowed status and warnings
        """
        flags = flags or []
        profile = self.tool_profiles.get(tool_name)

        result = {
            "allowed": False,
            "requires_confirmation": False,
            "warnings": [],
            "blocked_flags": [],
            "reason": None,
        }

        # Check if tool exists
        if not profile:
            if self.current_level < RiskLevel.NORMAL:
                result["reason"] = f"Unknown tool '{tool_name}' requires at least NORMAL risk level"
                return result
            result["warnings"].append(f"Unknown tool '{tool_name}' - proceed with caution")
            result["allowed"] = True
            return result

        # Check risk level
        if self.current_level < profile.min_risk_level:
            result["reason"] = (
                f"Tool '{tool_name}' requires {profile.min_risk_level.name} risk level, "
                f"but current level is {self.current_level.name}"
            )
            return result

        # Check for dangerous flags
        for flag in flags:
            for dangerous in profile.dangerous_flags:
                if dangerous in flag:
                    result["blocked_flags"].append(flag)
                    result["warnings"].append(f"Flag '{flag}' is potentially dangerous")

        # Check if confirmation required
        if profile.requires_confirmation and tool_name not in self.approved_tools:
            result["requires_confirmation"] = True
            result["warnings"].append(f"Tool '{tool_name}' requires explicit confirmation")

        result["allowed"] = len(result["blocked_flags"]) == 0
        return result

    def approve_tool(self, tool_name: str):
        """Explicitly approve a tool for this session"""
        self.approved_tools.add(tool_name)

    def get_allowed_tools(self) -> List[str]:
        """Get list of tools allowed at current risk level"""
        return [name for name, profile in self.tool_profiles.items() if self.current_level >= profile.min_risk_level]

    def get_blocked_tools(self) -> List[str]:
        """Get list of tools blocked at current risk level"""
        return [name for name, profile in self.tool_profiles.items() if self.current_level < profile.min_risk_level]

    def get_risk_description(self) -> str:
        """Get description of current risk level"""
        return self.RISK_DESCRIPTIONS.get(self.current_level, "Unknown risk level")

    def add_tool_profile(self, profile: ToolRiskProfile):
        """Add or update a tool profile"""
        self.tool_profiles[profile.name] = profile


# Convenience functions
_default_manager: Optional[RiskLevelManager] = None


def get_risk_manager() -> RiskLevelManager:
    """Get default risk level manager"""
    global _default_manager
    if _default_manager is None:
        _default_manager = RiskLevelManager()
    return _default_manager


def set_risk_level(level: RiskLevel):
    """Set global risk level"""
    get_risk_manager().set_risk_level(level)


def can_run_tool(tool_name: str) -> bool:
    """Check if tool can run at current risk level"""
    return get_risk_manager().can_run_tool(tool_name)


def validate_tool(tool_name: str, flags: Optional[List[str]] = None) -> Dict:
    """Validate tool with current risk level"""
    return get_risk_manager().validate_tool(tool_name, flags)

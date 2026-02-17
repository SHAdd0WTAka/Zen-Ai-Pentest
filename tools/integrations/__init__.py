"""
Pentest Tool Integrations

Wrappers and integrations for external security tools.
"""

from .tool_checker import ToolChecker, ToolAvailability

try:
    from .nmap_wrapper import NmapWrapper
    from .nuclei_wrapper import NucleiWrapper
    from .sqlmap_wrapper import SqlmapWrapper
except ImportError:
    # Wrappers not yet implemented
    NmapWrapper = None
    NucleiWrapper = None
    SqlmapWrapper = None

__all__ = [
    "ToolChecker",
    "ToolAvailability",
    "NmapWrapper",
    "NucleiWrapper",
    "SqlmapWrapper",
]

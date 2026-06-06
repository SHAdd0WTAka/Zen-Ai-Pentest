"""
Zen-AI-Pentest Tools Package

Alle Pentesting Tools Integrationen.
"""

import importlib
import logging
from typing import Any, Callable, Dict, List, Optional

# Configure module logger
logger = logging.getLogger(__name__)

# Type alias for tool functions
ToolFunction = Callable[..., Any]

# Tool Registry - wird dynamisch gefüllt
TOOL_REGISTRY: Dict[str, Optional[ToolFunction]] = {}


def _import_tool(module_name: str, function_names: List[str]) -> Dict[str, ToolFunction]:
    """Import tool functions from a module.

    Args:
        module_name: Name of the module to import from.
        function_names: List of function names to import.

    Returns:
        Dictionary of successfully imported functions.
    """
    imported: Dict[str, ToolFunction] = {}
    try:
        module = importlib.import_module(module_name, package=__name__)
        for func_name in function_names:
            func = getattr(module, func_name, None)
            if func and callable(func):
                imported[func_name] = func
            else:
                logger.debug("Function %s not found in %s", func_name, module_name)
    except ImportError as e:
        logger.debug("%s not available: %s", module_name, e)
    except Exception as e:
        logger.debug("Error importing %s: %s", module_name, e)
    return imported


# Tool import definitions: (module_name, [function_names])
_TOOL_IMPORTS: List[tuple] = [
    ("tools.nmap_integration", ["nmap_scan"]),
    ("tools.masscan_integration", ["masscan_quick_scan"]),
    ("tools.scapy_integration", ["scapy_arp_scan", "scapy_syn_scan"]),
    ("tools.tshark_integration", ["tshark_capture"]),
    ("tools.burpsuite_integration", ["burp_scan_url"]),
    ("tools.sqlmap_integration", ["sqlmap_scan"]),
    ("tools.gobuster_integration", ["gobuster_dir_scan"]),
    ("tools.metasploit_integration", ["metasploit_search"]),
    ("tools.hydra_integration", ["hydra_ssh_brute"]),
    ("tools.amass_integration", ["amass_enum"]),
    ("tools.bloodhound_integration", ["bloodhound_analyze_path"]),
    ("tools.crackmapexec_integration", ["cme_smb_check"]),
    ("tools.aircrack_integration", ["airodump_scan"]),
    ("tools.nikto_integration", ["nikto_scan"]),
    ("tools.nuclei_integration", ["nuclei_scan"]),
    ("tools.subfinder_integration", ["subfinder_scan"]),
    ("tools.ffuf_integration", ["ffuf_fuzz"]),
    ("tools.zap_integration", ["zap_scan"]),
    ("tools.wafw00f_integration", ["wafw00f_detect"]),
    ("tools.whatweb_integration", ["whatweb_scan"]),
    ("tools.responder_integration", ["responder_poison"]),
    ("tools.semgrep_integration", ["semgrep_scan"]),
    ("tools.trufflehog_integration", ["trufflehog_scan"]),
    ("tools.sherlock_integration", ["sherlock_osint"]),
    ("tools.ignorant_integration", ["ignorant_email"]),
    ("tools.scout_integration", ["scout_osint"]),
]

# Import all tools
for _module, _functions in _TOOL_IMPORTS:
    _imported = _import_tool(_module, _functions)
    for _name, _func in _imported.items():
        TOOL_REGISTRY[_name] = _func


# Mock tools für Testzwecke
def mock_scan(target: str, **kwargs: Any) -> Dict[str, Any]:
    """Mock scan for testing.

    Args:
        target: Target to scan.
        **kwargs: Additional arguments.

    Returns:
        Mock scan result.
    """
    return {"status": "success", "target": target, "mock": True}


# Füge Mock-Tools hinzu, wenn keine echten verfügbar sind
if not TOOL_REGISTRY:
    logger.warning("No real tools available, using mock tools")
    TOOL_REGISTRY["mock_scan"] = mock_scan

__all__ = ["TOOL_REGISTRY", "get_all_tools", "mock_scan", "get_tool", "list_available_tools"]


def get_all_tools() -> List[Any]:
    """Gibt alle verfügbaren Tools zurück.

    Returns:
        List of tool objects. Uses LangChain Tool objects if available,
        otherwise returns list of (name, function) tuples.
    """
    try:
        from langchain_core.tools import Tool

        tools: List[Tool] = []
        for name, func in TOOL_REGISTRY.items():
            if func:
                tools.append(Tool(name=name, func=func, description=func.__doc__ or ""))

        return tools
    except ImportError:
        # Fallback ohne LangChain
        logger.debug("LangChain not available, returning raw tool registry")
        return list(TOOL_REGISTRY.items())


def get_tool(name: str) -> Optional[ToolFunction]:
    """Get a specific tool by name.

    Args:
        name: Name of the tool to retrieve.

    Returns:
        The tool function if found, None otherwise.
    """
    return TOOL_REGISTRY.get(name)


def list_available_tools() -> List[str]:
    """List all available tool names.

    Returns:
        List of available tool names.
    """
    return sorted(name for name, func in TOOL_REGISTRY.items() if func is not None)

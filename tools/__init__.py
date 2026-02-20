"""
Zen-AI-Pentest Tools Package

Alle Pentesting Tools Integrationen.
"""

import logging

logger = logging.getLogger(__name__)

# Tool Registry - wird dynamisch gefüllt
TOOL_REGISTRY = {}

# Versuche alle Tools zu importieren
try:
    from .nmap_integration import nmap_scan

    TOOL_REGISTRY["nmap_scan"] = nmap_scan
except ImportError as e:
    logger.warning(f"nmap_integration not available: {e}")

try:
    from .masscan_integration import masscan_quick_scan

    TOOL_REGISTRY["masscan_quick_scan"] = masscan_quick_scan
except ImportError as e:
    logger.warning(f"masscan_integration not available: {e}")

try:
    from .scapy_integration import scapy_arp_scan, scapy_syn_scan

    TOOL_REGISTRY["scapy_syn_scan"] = scapy_syn_scan
    TOOL_REGISTRY["scapy_arp_scan"] = scapy_arp_scan
except ImportError as e:
    logger.warning(f"scapy_integration not available: {e}")

try:
    from .tshark_integration import tshark_capture

    TOOL_REGISTRY["tshark_capture"] = tshark_capture
except ImportError as e:
    logger.warning(f"tshark_integration not available: {e}")

try:
    from .burpsuite_integration import burp_scan_url

    TOOL_REGISTRY["burp_scan_url"] = burp_scan_url
except ImportError as e:
    logger.warning(f"burpsuite_integration not available: {e}")

try:
    from .sqlmap_integration import sqlmap_scan

    TOOL_REGISTRY["sqlmap_scan"] = sqlmap_scan
except ImportError as e:
    logger.warning(f"sqlmap_integration not available: {e}")

try:
    from .gobuster_integration import gobuster_dir_scan

    TOOL_REGISTRY["gobuster_dir_scan"] = gobuster_dir_scan
except ImportError as e:
    logger.warning(f"gobuster_integration not available: {e}")

try:
    from .metasploit_integration import metasploit_search

    TOOL_REGISTRY["metasploit_search"] = metasploit_search
except ImportError as e:
    logger.warning(f"metasploit_integration not available: {e}")

try:
    from .hydra_integration import hydra_ssh_brute

    TOOL_REGISTRY["hydra_ssh_brute"] = hydra_ssh_brute
except ImportError as e:
    logger.warning(f"hydra_integration not available: {e}")

try:
    from .amass_integration import amass_enum

    TOOL_REGISTRY["amass_enum"] = amass_enum
except ImportError as e:
    logger.warning(f"amass_integration not available: {e}")

try:
    from .bloodhound_integration import bloodhound_analyze_path

    TOOL_REGISTRY["bloodhound_analyze_path"] = bloodhound_analyze_path
except ImportError as e:
    logger.warning(f"bloodhound_integration not available: {e}")

try:
    from .crackmapexec_integration import cme_smb_check

    TOOL_REGISTRY["cme_smb_check"] = cme_smb_check
except ImportError as e:
    logger.warning(f"crackmapexec_integration not available: {e}")

try:
    from .aircrack_integration import airodump_scan

    TOOL_REGISTRY["airodump_scan"] = airodump_scan
except ImportError as e:
    logger.warning(f"aircrack_integration not available: {e}")


# Mock tools für Testzwecke
def mock_scan(target, **kwargs):
    """Mock scan for testing"""
    return {"status": "success", "target": target, "mock": True}


# Füge Mock-Tools hinzu, wenn keine echten verfügbar sind
if not TOOL_REGISTRY:
    logger.warning("No real tools available, using mock tools")
    TOOL_REGISTRY["mock_scan"] = mock_scan

__all__ = ["TOOL_REGISTRY", "get_all_tools"]


def get_all_tools():
    """Gibt alle verfügbaren Tools zurück"""
    try:
        from langchain_core.tools import Tool

        tools = []
        for name, func in TOOL_REGISTRY.items():
            if func:
                tools.append(Tool(name=name, func=func, description=func.__doc__))

        return tools
    except ImportError:
        # Fallback ohne LangChain
        return list(TOOL_REGISTRY.items())

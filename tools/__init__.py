"""
Zen-AI-Pentest Tools Package

Alle Pentesting Tools Integrationen.
"""

# Network Scanners
from .nmap_integration import NmapTool, nmap_scan
from .masscan_integration import MasscanScanner, masscan_quick_scan
from .scapy_integration import ScapyScanner, scapy_syn_scan, scapy_arp_scan
from .tshark_integration import TsharkAnalyzer, tshark_capture

# Web Security
from .burpsuite_integration import BurpSuiteAPI, burp_scan_url
from .sqlmap_integration import SQLMapScanner, sqlmap_scan
from .gobuster_integration import GobusterScanner, gobuster_dir_scan

# Exploitation
from .metasploit_integration import MetasploitManager, metasploit_search

# Brute Force
from .hydra_integration import HydraBruteForcer, hydra_ssh_brute

# Reconnaissance
from .amass_integration import AmassRecon, amass_enum
from .nuclei_integration import NucleiScanner  # Assuming exists

# Windows/AD
from .bloodhound_integration import BloodHoundAnalyzer, bloodhound_analyze_path
from .crackmapexec_integration import CrackMapExec, cme_smb_check
from .responder_integration import ResponderPoisoner

# Wireless
from .aircrack_integration import AircrackSuite, airodump_scan

__all__ = [
    # Network
    'NmapTool', 'nmap_scan',
    'MasscanScanner', 'masscan_quick_scan',
    'ScapyScanner', 'scapy_syn_scan', 'scapy_arp_scan',
    'TsharkAnalyzer', 'tshark_capture',
    
    # Web
    'BurpSuiteAPI', 'burp_scan_url',
    'SQLMapScanner', 'sqlmap_scan',
    'GobusterScanner', 'gobuster_dir_scan',
    
    # Exploitation
    'MetasploitManager', 'metasploit_search',
    
    # Brute Force
    'HydraBruteForcer', 'hydra_ssh_brute',
    
    # Recon
    'AmassRecon', 'amass_enum',
    
    # AD/Windows
    'BloodHoundAnalyzer', 'bloodhound_analyze_path',
    'CrackMapExec', 'cme_smb_check',
    'ResponderPoisoner',
    
    # Wireless
    'AircrackSuite', 'airodump_scan',
]

# Tool Registry für den Agent
TOOL_REGISTRY = {
    # Network
    'nmap_scan': nmap_scan,
    'masscan_quick_scan': masscan_quick_scan,
    'scapy_syn_scan': scapy_syn_scan,
    'scapy_arp_scan': scapy_arp_scan,
    'tshark_capture': tshark_capture,
    
    # Web
    'burp_scan_url': burp_scan_url,
    'sqlmap_scan': sqlmap_scan,
    'gobuster_dir_scan': gobuster_dir_scan,
    'gobuster_dns_scan': None,  # Import from module
    
    # Exploitation
    'metasploit_search': metasploit_search,
    
    # Brute Force
    'hydra_ssh_brute': hydra_ssh_brute,
    
    # Recon
    'amass_enum': amass_enum,
    
    # AD/Windows
    'bloodhound_analyze_path': bloodhound_analyze_path,
    'cme_smb_check': cme_smb_check,
    
    # Wireless
    'airodump_scan': airodump_scan,
}


def get_all_tools():
    """Gibt alle verfügbaren Tools zurück"""
    from langchain_core.tools import Tool
    
    tools = []
    for name, func in TOOL_REGISTRY.items():
        if func:
            tools.append(Tool(name=name, func=func, description=func.__doc__))
    
    return tools

"""
Penetration Testing Modules for Zen AI
"""

from .cve_database import CVEDatabase, CVEEntry, RansomwareEntry
from .exploit_assist import ExploitAssistModule
from .nuclei_integration import NucleiIntegration, NucleiTemplateManager
from .osint import DomainInfo, EmailProfile, OSINTModule, OSINTResult, check_email_breach, enumerate_subdomains, harvest_emails
from .protonvpn import ProtonVPNManager, VPNProtocol, VPNSecurityLevel, VPNServer, VPNStatus, quick_connect, secure_connect
from .recon import ReconModule
from .subdomain_scanner import SubdomainScanner, SubdomainResult, scan_subdomains
from .subdomain_scanner_advanced import AdvancedSubdomainScanner, scan_subdomains_advanced

# from .report_gen import ReportGenerator  # Module not available
from .sql_injection_db import DBType, SQLInjectionDatabase, SQLITechnique, SQLPayload
from .vuln_scanner import VulnScannerModule

__all__ = [
    "ReconModule",
    "SubdomainScanner",
    "SubdomainResult",
    "scan_subdomains",
    "AdvancedSubdomainScanner",
    "scan_subdomains_advanced",
    "VulnScannerModule",
    "ExploitAssistModule",
    # "ReportGenerator",  # Module not available
    "NucleiIntegration",
    "NucleiTemplateManager",
    "SQLInjectionDatabase",
    "SQLPayload",
    "SQLITechnique",
    "DBType",
    "CVEDatabase",
    "CVEEntry",
    "RansomwareEntry",
    "ProtonVPNManager",
    "VPNProtocol",
    "VPNSecurityLevel",
    "VPNStatus",
    "VPNServer",
    "quick_connect",
    "secure_connect",
    "OSINTModule",
    "DomainInfo",
    "EmailProfile",
    "OSINTResult",
    "harvest_emails",
    "enumerate_subdomains",
    "check_email_breach",
]

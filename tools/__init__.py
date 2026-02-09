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
    from .nmap_integration import (
        NmapScanner,
        nmap_scan,
        nmap_quick_scan,
        nmap_vuln_scan,
        ScanType,
        TimingTemplate,
    )

    TOOL_REGISTRY["nmap_scan"] = nmap_scan
    TOOL_REGISTRY["nmap_quick_scan"] = nmap_quick_scan
    TOOL_REGISTRY["nmap_vuln_scan"] = nmap_vuln_scan
except ImportError as e:
    logger.warning(f"nmap_integration not available: {e}")

try:
    from .masscan_integration import masscan_quick_scan

    TOOL_REGISTRY["masscan_quick_scan"] = masscan_quick_scan
except ImportError as e:
    logger.warning(f"masscan_integration not available: {e}")

try:
    from .scapy_integration import scapy_syn_scan, scapy_arp_scan

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

# New Security Tools - 2026 Q1

try:
    from .zap_integration import (
        ZAPScanner,
        ZAPAlert,
        ZAPScanResult,
        zap_scan_url,
        zap_quick_scan,
        zap_spider_only,
    )

    TOOL_REGISTRY["zap_scan_url"] = zap_scan_url
    TOOL_REGISTRY["zap_quick_scan"] = zap_quick_scan
    TOOL_REGISTRY["zap_spider_only"] = zap_spider_only
except ImportError as e:
    logger.warning(f"zap_integration not available: {e}")

try:
    from .trufflehog_integration import (
        TruffleHogScanner,
        TruffleHogFinding,
        TruffleHogResult,
        trufflehog_scan_git,
        trufflehog_scan_path,
        trufflehog_scan_local_repo,
    )

    TOOL_REGISTRY["trufflehog_scan_git"] = trufflehog_scan_git
    TOOL_REGISTRY["trufflehog_scan_path"] = trufflehog_scan_path
    TOOL_REGISTRY["trufflehog_scan_local_repo"] = trufflehog_scan_local_repo
except ImportError as e:
    logger.warning(f"trufflehog_integration not available: {e}")

try:
    from .scout_integration import (
        ScoutSuiteScanner,
        ScoutFinding,
        ScoutResult,
        CloudProvider,
        scoutsuite_scan_aws,
        scoutsuite_scan_azure,
        scoutsuite_scan_gcp,
        scoutsuite_quick_scan,
    )

    TOOL_REGISTRY["scoutsuite_scan_aws"] = scoutsuite_scan_aws
    TOOL_REGISTRY["scoutsuite_scan_azure"] = scoutsuite_scan_azure
    TOOL_REGISTRY["scoutsuite_scan_gcp"] = scoutsuite_scan_gcp
    TOOL_REGISTRY["scoutsuite_quick_scan"] = scoutsuite_quick_scan
except ImportError as e:
    logger.warning(f"scout_integration not available: {e}")

try:
    from .trivy_integration import (
        TrivyScanner,
        TrivyVulnerability,
        TrivyMisconfiguration,
        TrivySecret,
        TrivyResult,
        TrivyScanTarget,
        TrivyScannerType,
        trivy_scan_image,
        trivy_scan_filesystem,
        trivy_scan_dockerfile,
        trivy_generate_sbom,
    )

    TOOL_REGISTRY["trivy_scan_image"] = trivy_scan_image
    TOOL_REGISTRY["trivy_scan_filesystem"] = trivy_scan_filesystem
    TOOL_REGISTRY["trivy_scan_dockerfile"] = trivy_scan_dockerfile
    TOOL_REGISTRY["trivy_generate_sbom"] = trivy_generate_sbom
except ImportError as e:
    logger.warning(f"trivy_integration not available: {e}")

try:
    from .semgrep_integration import (
        SemgrepScanner,
        SemgrepFinding,
        SemgrepResult,
        SemgrepSeverity,
        SemgrepConfidence,
        semgrep_scan_code,
        semgrep_scan_owasp,
        semgrep_scan_secrets,
        semgrep_scan_ci,
    )

    TOOL_REGISTRY["semgrep_scan_code"] = semgrep_scan_code
    TOOL_REGISTRY["semgrep_scan_owasp"] = semgrep_scan_owasp
    TOOL_REGISTRY["semgrep_scan_secrets"] = semgrep_scan_secrets
    TOOL_REGISTRY["semgrep_scan_ci"] = semgrep_scan_ci
except ImportError as e:
    logger.warning(f"semgrep_integration not available: {e}")


# Mock tools für Testzwecke
def mock_scan(target, **kwargs):
    """Mock scan for testing"""
    return {"status": "success", "target": target, "mock": True}


# Füge Mock-Tools hinzu, wenn keine echten verfügbar sind
if not TOOL_REGISTRY:
    logger.warning("No real tools available, using mock tools")
    TOOL_REGISTRY["mock_scan"] = mock_scan

__all__ = [
    "TOOL_REGISTRY",
    "get_all_tools",
    "NmapScanner",
    "ScanType",
    "TimingTemplate",
    # ZAP Integration
    "ZAPScanner",
    "ZAPAlert",
    "ZAPScanResult",
    "zap_scan_url",
    "zap_quick_scan",
    "zap_spider_only",
    # TruffleHog Integration
    "TruffleHogScanner",
    "TruffleHogFinding",
    "TruffleHogResult",
    "trufflehog_scan_git",
    "trufflehog_scan_path",
    "trufflehog_scan_local_repo",
    # ScoutSuite Integration
    "ScoutSuiteScanner",
    "ScoutFinding",
    "ScoutResult",
    "CloudProvider",
    "scoutsuite_scan_aws",
    "scoutsuite_scan_azure",
    "scoutsuite_scan_gcp",
    "scoutsuite_quick_scan",
    # Trivy Integration
    "TrivyScanner",
    "TrivyVulnerability",
    "TrivyMisconfiguration",
    "TrivySecret",
    "TrivyResult",
    "TrivyScanTarget",
    "TrivyScannerType",
    "trivy_scan_image",
    "trivy_scan_filesystem",
    "trivy_scan_dockerfile",
    "trivy_generate_sbom",
    # Semgrep Integration
    "SemgrepScanner",
    "SemgrepFinding",
    "SemgrepResult",
    "SemgrepSeverity",
    "SemgrepConfidence",
    "semgrep_scan_code",
    "semgrep_scan_owasp",
    "semgrep_scan_secrets",
    "semgrep_scan_ci",
]


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

#!/usr/bin/env python3
"""
CVE Database Module
Comprehensive CVE database with ransomware and exploit information
Author: SHAdd0WTAka
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI")


@dataclass
class CVEEntry:
    """CVE Entry data class"""

    cve_id: str
    name: str
    cvss_score: float
    severity: str
    description: str
    affected_products: List[str]
    exploits: List[str]
    patches: List[str]
    mitigations: List[str]
    detection_methods: List[str]
    ransomware_used_by: List[str] = None
    ioc: Dict = None


@dataclass
class RansomwareEntry:
    """Ransomware entry"""

    name: str
    first_seen: str
    type: str
    description: str
    cves: List[str]
    file_extensions: List[str]
    ransom_note: str
    ioc: Dict
    mitigation: List[str]
    detection: List[str]
    decryptable: bool
    estimated_damage: int = 0


class CVEDatabase:
    """
    Comprehensive CVE and Ransomware Database
    """

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.db_path = "data/cve_db"
        self.ransomware_data = {}
        self.cve_data = {}
        self.exploit_chains = {}

        self._load_databases()

    def _load_databases(self):
        """Load all database files"""
        # Load ransomware database
        ransomware_file = os.path.join(self.db_path, "ransomware_cves.json")
        if os.path.exists(ransomware_file):
            try:
                with open(ransomware_file, "r") as f:
                    data = json.load(f)
                    self.ransomware_data = data.get("ransomware_campaigns", {})
                    self.cve_data = data.get("critical_historical_cves", {})
                    self.exploit_chains = data.get("common_exploit_chains", {})
                logger.info(
                    f"[CVE DB] Loaded {len(self.ransomware_data)} ransomware entries, {len(self.cve_data)} CVEs"
                )
            except Exception as e:
                logger.error(f"[CVE DB] Error loading database: {e}")

    def search_cve(self, cve_id: str) -> Optional[CVEEntry]:
        """Search for a specific CVE"""
        cve_id = cve_id.upper()

        if cve_id in self.cve_data:
            data = self.cve_data[cve_id]
            return CVEEntry(
                cve_id=cve_id,
                name=data.get("name", ""),
                cvss_score=data.get("cvss", 0.0),
                severity=data.get("severity", "Unknown"),
                description=data.get("description", ""),
                affected_products=data.get("affected_products", []),
                exploits=data.get("exploits", []),
                patches=[data.get("patch", "")] if data.get("patch") else [],
                mitigations=data.get("mitigation", []),
                detection_methods=data.get("detection", []),
                ransomware_used_by=data.get("ransomware_used_by", []),
            )
        return None

    def search_ransomware(self, name: str) -> Optional[RansomwareEntry]:
        """Search for ransomware by name"""
        name_lower = name.lower()

        for key, data in self.ransomware_data.items():
            if name_lower in key.lower() or name_lower in data.get("name", "").lower():
                return RansomwareEntry(
                    name=data.get("name", key),
                    first_seen=data.get("first_seen", ""),
                    type=data.get("type", ""),
                    description=data.get("description", ""),
                    cves=data.get("cves", []),
                    file_extensions=data.get("file_extensions", []),
                    ransom_note=data.get("ransom_note", ""),
                    ioc=data.get("ioc", {}),
                    mitigation=data.get("mitigation", []),
                    detection=data.get("detection", []),
                    decryptable=data.get("decryptable", False),
                    estimated_damage=data.get("estimated_damage_usd", 0),
                )
        return None

    def get_ransomware_by_cve(self, cve_id: str) -> List[str]:
        """Find ransomware that uses a specific CVE"""
        cve_id = cve_id.upper()
        results = []

        for key, data in self.ransomware_data.items():
            if cve_id in data.get("cves", []):
                results.append(data.get("name", key))

        return results

    def get_cves_by_severity(self, severity: str) -> List[CVEEntry]:
        """Get all CVEs by severity level"""
        results = []
        severity = severity.capitalize()

        for cve_id, data in self.cve_data.items():
            if data.get("severity") == severity:
                entry = self.search_cve(cve_id)
                if entry:
                    results.append(entry)

        return results

    def get_critical_cves(self) -> List[CVEEntry]:
        """Get all critical CVEs"""
        return self.get_cves_by_severity("Critical")

    def get_ransomware_iocs(self, ransomware_name: str) -> Dict:
        """Get IOCs for a specific ransomware"""
        entry = self.search_ransomware(ransomware_name)
        if entry:
            return entry.ioc
        return {}

    def check_system_for_ransomware(self, indicators: Dict) -> List[Dict]:
        """
        Check system indicators against ransomware IOCs
        indicators: dict with keys like 'files', 'registry', 'hashes', 'processes'
        """
        matches = []

        for key, data in self.ransomware_data.items():
            ransomware_name = data.get("name", key)
            ioc = data.get("ioc", {})

            match_score = 0
            match_details = []

            # Check file indicators
            if "files" in indicators and "files" in ioc:
                for file in indicators["files"]:
                    for ioc_file in ioc["files"]:
                        if (
                            file.lower() in ioc_file.lower()
                            or ioc_file.lower() in file.lower()
                        ):
                            match_score += 10
                            match_details.append(f"File match: {file}")

            # Check registry indicators
            if "registry" in indicators and "registry" in ioc:
                for reg in indicators["registry"]:
                    for ioc_reg in ioc["registry"]:
                        if reg.lower() in ioc_reg.lower():
                            match_score += 10
                            match_details.append(f"Registry match: {reg}")

            # Check hashes
            if "hashes" in indicators and "hashes" in ioc:
                for hash_val in indicators["hashes"]:
                    if hash_val.lower() in [h.lower() for h in ioc["hashes"]]:
                        match_score += 50  # Hash match is strong indicator
                        match_details.append(f"Hash match: {hash_val}")

            # Check processes
            if "processes" in indicators and "processes" in ioc:
                for proc in indicators["processes"]:
                    for ioc_proc in ioc["processes"]:
                        if proc.lower() in ioc_proc.lower():
                            match_score += 15
                            match_details.append(f"Process match: {proc}")

            if match_score >= 20:
                matches.append(
                    {
                        "ransomware": ransomware_name,
                        "confidence": min(match_score, 100),
                        "indicators": match_details,
                        "recommendation": "Isolate system immediately and initiate incident response",
                    }
                )

        return sorted(matches, key=lambda x: x["confidence"], reverse=True)

    async def analyze_vulnerability_for_ransomware_risk(self, cve_id: str) -> Dict:
        """Analyze if a CVE is commonly used by ransomware"""
        cve_id = cve_id.upper()
        entry = self.search_cve(cve_id)

        if not entry:
            return {"error": f"CVE {cve_id} not found"}

        ransomware_list = entry.ransomware_used_by or []
        risk_level = "High" if len(ransomware_list) > 0 else entry.severity

        analysis = {
            "cve_id": cve_id,
            "cvss_score": entry.cvss_score,
            "severity": entry.severity,
            "ransomware_associated": ransomware_list,
            "ransomware_risk": risk_level,
            "mitigation_priority": "Critical" if ransomware_list else entry.severity,
            "recommended_actions": entry.mitigations,
        }

        # Add LLM analysis if orchestrator available
        if self.orchestrator and ransomware_list:
            prompt = f"""
Analyze CVE {cve_id} which is used by ransomware: {', '.join(ransomware_list)}

Provide:
1. Why this CVE is attractive to ransomware operators
2. Historical context of attacks
3. Specific recommendations for ransomware prevention
4. Detection strategies beyond patching
"""
            llm_response = await self.orchestrator.process(prompt)
            analysis["ai_analysis"] = llm_response.content

        return analysis

    def get_exploit_chain(self, chain_name: str) -> Optional[Dict]:
        """Get a specific exploit chain"""
        for key, data in self.exploit_chains.items():
            if (
                chain_name.lower() in key.lower()
                or chain_name.lower() in data.get("name", "").lower()
            ):
                return data
        return None

    def list_all_ransomware(self) -> List[Dict]:
        """List all ransomware in database"""
        results = []
        for key, data in self.ransomware_data.items():
            results.append(
                {
                    "key": key,
                    "name": data.get("name", key),
                    "first_seen": data.get("first_seen", ""),
                    "type": data.get("type", ""),
                    "decryptable": data.get("decryptable", False),
                    "cves": data.get("cves", []),
                }
            )
        return results

    def list_all_cves(self) -> List[Dict]:
        """List all CVEs in database"""
        results = []
        for cve_id, data in self.cve_data.items():
            results.append(
                {
                    "cve_id": cve_id,
                    "name": data.get("name", ""),
                    "cvss": data.get("cvss", 0),
                    "severity": data.get("severity", "Unknown"),
                    "ransomware_used_by": data.get("ransomware_used_by", []),
                }
            )
        return sorted(results, key=lambda x: x["cvss"], reverse=True)

    def get_latest_threats(self, limit: int = 10) -> List[Dict]:
        """Get latest critical threats"""
        all_cves = self.list_all_cves()
        critical = [c for c in all_cves if c["severity"] == "Critical"]
        return critical[:limit]

    def generate_vulnerability_report(self, cve_list: List[str]) -> str:
        """Generate a report for a list of CVEs"""
        report_lines = [
            "# Vulnerability Analysis Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## CVE Details",
            "",
        ]

        for cve_id in cve_list:
            entry = self.search_cve(cve_id.upper())
            if entry:
                report_lines.extend(
                    [
                        f"### {entry.cve_id}: {entry.name}",
                        f"**Severity:** {entry.severity} (CVSS: {entry.cvss_score})",
                        f"**Description:** {entry.description}",
                        "",
                        "**Affected Products:**",
                        "",
                    ]
                )
                for product in entry.affected_products[:5]:
                    report_lines.append(f"- {product}")

                if entry.ransomware_used_by:
                    report_lines.extend(
                        ["", "⚠️ **Ransomware Alert:** This CVE is used by:", ""]
                    )
                    for rw in entry.ransomware_used_by:
                        report_lines.append(f"- {rw}")

                report_lines.extend(["", "**Mitigation:**", ""])
                for mit in entry.mitigations[:3]:
                    report_lines.append(f"- {mit}")

                report_lines.append("")
            else:
                report_lines.append(f"### {cve_id}: Not found in database\n")

        return "\n".join(report_lines)

    def get_mitigation_for_cve(self, cve_id: str) -> List[str]:
        """Get mitigation steps for a CVE"""
        entry = self.search_cve(cve_id.upper())
        if entry:
            return entry.mitigations
        return []

    def get_detection_for_ransomware(self, ransomware_name: str) -> List[str]:
        """Get detection methods for ransomware"""
        entry = self.search_ransomware(ransomware_name)
        if entry:
            return entry.detection
        return []

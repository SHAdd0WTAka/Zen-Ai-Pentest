#!/usr/bin/env python3
"""
CVE Database Module - Performance Optimized
Comprehensive CVE database with ransomware and exploit information

Optimizations:
- In-memory caching for frequently accessed CVEs
- Batch query support
- Generator-based iteration for large datasets
- LRU cache for search operations
- Async batch loading

Author: SHAdd0WTAka
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Generator, Set

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

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


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

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class CVEDatabase:
    """
    Comprehensive CVE and Ransomware Database with caching.
    """

    def __init__(self, orchestrator=None, cache_size: int = 1000, cache_ttl: int = 3600):
        self.orchestrator = orchestrator
        self.db_path = "data/cve_db"
        self.ransomware_data: Dict[str, Dict] = {}
        self.cve_data: Dict[str, Dict] = {}
        self.exploit_chains: Dict[str, Dict] = {}

        # In-memory cache with TTL
        self._cache: Dict[str, Dict] = {}
        self._cache_times: Dict[str, datetime] = {}
        self._cache_size = cache_size
        self._cache_ttl = cache_ttl
        self._cache_lock = asyncio.Lock()

        # Index for faster lookups
        self._severity_index: Dict[str, Set[str]] = {}
        self._ransomware_cve_index: Dict[str, Set[str]] = {}

        self._load_databases()
        self._build_indexes()

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
                    f"[CVE DB] Loaded {len(self.ransomware_data)} ransomware entries, "
                    f"{len(self.cve_data)} CVEs"
                )
            except Exception as e:
                logger.error(f"[CVE DB] Error loading database: {e}")

    def _build_indexes(self):
        """Build search indexes for faster lookups."""
        # Build severity index
        for cve_id, data in self.cve_data.items():
            severity = data.get("severity", "Unknown")
            if severity not in self._severity_index:
                self._severity_index[severity] = set()
            self._severity_index[severity].add(cve_id)

        # Build ransomware->CVE index
        for key, data in self.ransomware_data.items():
            for cve in data.get("cves", []):
                cve_upper = cve.upper()
                if cve_upper not in self._ransomware_cve_index:
                    self._ransomware_cve_index[cve_upper] = set()
                self._ransomware_cve_index[cve_upper].add(data.get("name", key))

    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get item from cache with TTL check."""
        async with self._cache_lock:
            if key in self._cache:
                cached_time = self._cache_times.get(key)
                if cached_time and (datetime.utcnow() - cached_time).seconds < self._cache_ttl:
                    return self._cache[key]
                else:
                    # Expired
                    del self._cache[key]
                    del self._cache_times[key]
            return None

    async def _add_to_cache(self, key: str, value: Dict):
        """Add item to cache with LRU eviction."""
        async with self._cache_lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._cache_size:
                oldest_key = min(self._cache_times.keys(), key=lambda k: self._cache_times[k])
                del self._cache[oldest_key]
                del self._cache_times[oldest_key]

            self._cache[key] = value
            self._cache_times[key] = datetime.utcnow()

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

    async def search_cve_cached(self, cve_id: str) -> Optional[CVEEntry]:
        """Search CVE with caching support."""
        cve_id = cve_id.upper()

        # Check cache
        cache_key = f"cve:{cve_id}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            return CVEEntry(**cached)

        # Search and cache
        result = self.search_cve(cve_id)
        if result:
            await self._add_to_cache(cache_key, result.to_dict())

        return result

    def search_cve_batch(self, cve_ids: List[str]) -> Dict[str, Optional[CVEEntry]]:
        """Batch search for multiple CVEs (more efficient than individual lookups)."""
        results = {}
        for cve_id in cve_ids:
            results[cve_id] = self.search_cve(cve_id)
        return results

    async def search_cve_batch_cached(self, cve_ids: List[str]) -> Dict[str, Optional[CVEEntry]]:
        """Batch search with caching."""
        results = {}
        to_fetch = []

        # Check cache first
        for cve_id in cve_ids:
            cve_upper = cve_id.upper()
            cache_key = f"cve:{cve_upper}"
            cached = await self._get_from_cache(cache_key)
            if cached:
                results[cve_id] = CVEEntry(**cached)
            else:
                to_fetch.append(cve_id)

        # Fetch missing
        if to_fetch:
            fetched = self.search_cve_batch(to_fetch)
            for cve_id, entry in fetched.items():
                results[cve_id] = entry
                if entry:
                    await self._add_to_cache(f"cve:{cve_id.upper()}", entry.to_dict())

        return results

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
        """Find ransomware that uses a specific CVE (uses index)"""
        cve_id = cve_id.upper()
        return list(self._ransomware_cve_index.get(cve_id, set()))

    def get_cves_by_severity(self, severity: str) -> List[CVEEntry]:
        """Get all CVEs by severity level (uses index)"""
        severity = severity.capitalize()
        cve_ids = self._severity_index.get(severity, set())

        results = []
        for cve_id in cve_ids:
            entry = self.search_cve(cve_id)
            if entry:
                results.append(entry)

        return results

    def get_cves_by_severity_generator(self, severity: str) -> Generator[CVEEntry, None, None]:
        """Generator for CVEs by severity (memory efficient for large datasets)."""
        severity = severity.capitalize()
        cve_ids = self._severity_index.get(severity, set())

        for cve_id in cve_ids:
            entry = self.search_cve(cve_id)
            if entry:
                yield entry

    def get_critical_cves(self, limit: int = None) -> List[CVEEntry]:
        """Get all critical CVEs with optional limit."""
        results = self.get_cves_by_severity("Critical")
        if limit:
            results = sorted(results, key=lambda x: x.cvss_score or 0, reverse=True)[:limit]
        return results

    def get_ransomware_iocs(self, ransomware_name: str) -> Dict:
        """Get IOCs for a specific ransomware"""
        entry = self.search_ransomware(ransomware_name)
        if entry:
            return entry.ioc
        return {}

    def check_system_for_ransomware(self, indicators: Dict) -> List[Dict]:
        """
        Check system indicators against ransomware IOCs.
        Optimized with early termination and scoring.
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
                    file_lower = file.lower()
                    for ioc_file in ioc["files"]:
                        if file_lower in ioc_file.lower() or ioc_file.lower() in file_lower:
                            match_score += 10
                            match_details.append(f"File match: {file}")
                            break  # One match per file is enough

            # Check registry indicators
            if "registry" in indicators and "registry" in ioc and match_score < 100:
                for reg in indicators["registry"]:
                    reg_lower = reg.lower()
                    for ioc_reg in ioc["registry"]:
                        if reg_lower in ioc_reg.lower():
                            match_score += 10
                            match_details.append(f"Registry match: {reg}")
                            break

            # Check hashes (strong indicator)
            if "hashes" in indicators and "hashes" in ioc:
                indicator_hashes = set(h.lower() for h in indicators["hashes"])
                ioc_hashes = set(h.lower() for h in ioc["hashes"])
                hash_matches = indicator_hashes & ioc_hashes
                if hash_matches:
                    match_score += 50 * len(hash_matches)
                    match_details.extend([f"Hash match: {h}" for h in hash_matches])

            # Check processes
            if "processes" in indicators and "processes" in ioc and match_score < 100:
                for proc in indicators["processes"]:
                    proc_lower = proc.lower()
                    for ioc_proc in ioc["processes"]:
                        if proc_lower in ioc_proc.lower():
                            match_score += 15
                            match_details.append(f"Process match: {proc}")
                            break

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
Analyze CVE {cve_id} which is used by ransomware: {", ".join(ransomware_list)}

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
        name_lower = chain_name.lower()
        for key, data in self.exploit_chains.items():
            if name_lower in key.lower() or name_lower in data.get("name", "").lower():
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

    def list_all_cves(self, limit: int = None) -> List[Dict]:
        """List all CVEs in database with optional limit"""
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

        results.sort(key=lambda x: x["cvss"], reverse=True)

        if limit:
            return results[:limit]
        return results

    def get_latest_threats(self, limit: int = 10) -> List[Dict]:
        """Get latest critical threats"""
        all_cves = self.list_all_cves(limit=limit * 2)
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
                    report_lines.extend(["", "⚠️ **Ransomware Alert:** This CVE is used by:", ""])
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

    async def clear_cache(self):
        """Clear the in-memory cache."""
        async with self._cache_lock:
            self._cache.clear()
            self._cache_times.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self._cache_size,
            "cache_ttl_seconds": self._cache_ttl,
        }


# Module-level cache for search results
_cve_search_cache: Dict[str, tuple] = {}
_cve_cache_max_size = 100


@lru_cache(maxsize=128)
def _cached_cve_lookup(cve_id: str) -> Optional[CVEEntry]:
    """Module-level LRU cache for CVE lookups."""
    db = CVEDatabase()
    return db.search_cve(cve_id)


def search_cve_cached(cve_id: str) -> Optional[CVEEntry]:
    """Search CVE with module-level caching."""
    return _cached_cve_lookup(cve_id.upper())


def clear_cve_cache():
    """Clear the module-level CVE cache."""
    _cached_cve_lookup.cache_clear()

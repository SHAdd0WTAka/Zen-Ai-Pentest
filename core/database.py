"""
Database Module - Wrapper for CVE and Ransomware Database Access
"""

import os
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cve_database import CVEDatabase, CVEEntry, RansomwareEntry

# Global database instance
_db_instance: Optional[CVEDatabase] = None


def _get_db() -> CVEDatabase:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = CVEDatabase()
    return _db_instance


def get_cve_db() -> List[Dict[str, Any]]:
    """Get CVE database as list of dictionaries"""
    db = _get_db()
    cves = []
    for cve_id, cve_data in db.cve_data.items():
        entry = {"cve_id": cve_id}
        if isinstance(cve_data, dict):
            entry.update(cve_data)
        cves.append(entry)
    return cves


def get_ransomware_db() -> List[Dict[str, Any]]:
    """Get Ransomware database as list of dictionaries"""
    db = _get_db()
    ransomware_list = []
    for name, data in db.ransomware_data.items():
        entry = {"name": name}
        if isinstance(data, dict):
            entry.update(data)
        ransomware_list.append(entry)
    return ransomware_list


def search_cve(query: str) -> List[Dict[str, Any]]:
    """Search CVE database by keyword"""
    db = get_cve_db()
    query = query.lower()
    results = []
    for cve in db:
        # Search in ID
        if query in str(cve.get("cve_id", "")).lower():
            results.append(cve)
            continue
        # Search in description
        if query in str(cve.get("description", "")).lower():
            results.append(cve)
            continue
        # Search in name
        if query in str(cve.get("name", "")).lower():
            results.append(cve)
    return results


def get_cve_by_year(year: int) -> List[Dict[str, Any]]:
    """Get CVEs from a specific year"""
    db = get_cve_db()
    year_str = str(year)
    results = []
    for cve in db:
        cve_id = str(cve.get("cve_id", ""))
        # CVE IDs are in format CVE-YYYY-NNNNN
        if f"CVE-{year_str}-" in cve_id:
            results.append(cve)
    return results


def get_cve_by_id(cve_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific CVE by ID"""
    db = _get_db()
    cve_data = db.cve_data.get(cve_id.upper())
    if cve_data:
        if isinstance(cve_data, dict):
            return {"cve_id": cve_id, **cve_data}
        return {"cve_id": cve_id, "data": cve_data}
    return None


def get_ransomware_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get ransomware info by name"""
    db = _get_db()
    ransomware_data = db.ransomware_data.get(name)
    if ransomware_data:
        if isinstance(ransomware_data, dict):
            return {"name": name, **ransomware_data}
        return {"name": name, "data": ransomware_data}
    return None


__all__ = [
    "get_cve_db",
    "get_ransomware_db",
    "search_cve",
    "get_cve_by_year",
    "get_cve_by_id",
    "get_ransomware_by_name",
    "CVEDatabase",
    "CVEEntry",
    "RansomwareEntry",
]

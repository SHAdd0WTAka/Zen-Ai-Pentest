"""
Unit Tests for CVE Database
"""

import pytest  # noqa: F401

from core.database import get_cve_db


def test_cve_db_loading():
    """Test CVE database loads correctly"""
    db = get_cve_db()

    assert isinstance(db, list)
    assert len(db) > 0


def test_cve_entry_structure():
    """Test CVE entry structure"""
    db = get_cve_db()

    for cve in db[:10]:  # Check first 10
        assert "cve_id" in cve or "id" in cve
        assert "description" in cve


def test_cve_search():
    """Test CVE search functionality"""
    from core.database import search_cve

    results = search_cve("sql injection")

    assert isinstance(results, list)
    # Should find SQL injection related CVEs


def test_cve_by_year():
    """Test CVE filtering by year"""
    from core.database import get_cve_by_year

    results = get_cve_by_year(2024)

    assert isinstance(results, list)
    # All results should be from 2024
    for cve in results:
        assert "2024" in str(cve.get("cve_id", ""))

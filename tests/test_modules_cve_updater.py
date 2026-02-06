"""Tests for CVE updater module"""
import pytest
import asyncio

import os
import tempfile
from datetime import datetime
from unittest.mock import patch, AsyncMock
from modules.cve_updater import CVEUpdater, NVDClient, CVEEntry


class TestCVEEntry:
    """Test CVEEntry dataclass"""

    def test_cve_entry_creation(self):
        """Test CVE entry creation"""
        cve = CVEEntry(
            id="CVE-2024-1234",
            published="2024-01-01T00:00:00.000",
            last_modified="2024-01-02T00:00:00.000",
            description="Test vulnerability",
            cvss_score=7.5,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            severity="high",
            references=["https://example.com/cve"],
            cpe_matches=["cpe:2.3:a:test:software:1.0:*:*:*:*:*:*:*"]
        )
        assert cve.id == "CVE-2024-1234"
        assert cve.cvss_score == 7.5
        assert cve.severity == "high"


class TestNVDClient:
    """Test NVD API Client"""

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """Test rate limiting"""
        client = NVDClient()
        start_time = asyncio.get_event_loop().time()
        
        async with client:
            await client._rate_limit()
            await client._rate_limit()
        
        elapsed = asyncio.get_event_loop().time() - start_time
        assert elapsed >= 6.0  # Should wait at least 6 seconds

    def test_parse_cves_empty(self):
        """Test parsing empty CVE response"""
        client = NVDClient()
        result = client._parse_cves({"vulnerabilities": []})
        assert len(result) == 0

    def test_parse_cves_with_data(self):
        """Test parsing CVE response with data"""
        client = NVDClient()
        mock_data = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1234",
                        "published": "2024-01-01T00:00:00.000",
                        "lastModified": "2024-01-02T00:00:00.000",
                        "descriptions": [{"lang": "en", "value": "Test CVE"}],
                        "metrics": {
                            "cvssMetricV31": [{
                                "cvssData": {
                                    "baseScore": 9.8,
                                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                                },
                                "baseSeverity": "CRITICAL"
                            }]
                        },
                        "references": [{"url": "https://example.com"}],
                        "configurations": [{
                            "nodes": [{
                                "cpeMatch": [{"criteria": "cpe:2.3:a:test:1.0"}]
                            }]
                        }]
                    }
                }
            ]
        }
        
        result = client._parse_cves(mock_data)
        assert len(result) == 1
        assert result[0].id == "CVE-2024-1234"
        assert result[0].cvss_score == 9.8
        assert result[0].severity == "critical"


class TestCVEUpdater:
    """Test CVE Updater"""

    @pytest.fixture
    def temp_updater(self):
        """Create temporary updater"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "cve_database.json")
            updater = CVEUpdater(db_path=db_path)
            yield updater

    @pytest.mark.asyncio
    async def test_initialize_db(self, temp_updater):
        """Test database initialization"""
        await temp_updater.initialize_db()
        assert os.path.exists(temp_updater.db_path)
        
        # Check metadata
        meta = await temp_updater._load_metadata()
        assert "last_update" in meta

    @pytest.mark.asyncio
    async def test_save_and_load_db(self, temp_updater):
        """Test saving and loading database"""
        test_data = {
            "CVE-2024-1234": {
                "id": "CVE-2024-1234",
                "cvss_score": 7.5
            }
        }
        
        await temp_updater._save_db(test_data)
        loaded = await temp_updater._load_db()
        
        assert loaded == test_data

    @pytest.mark.asyncio
    async def test_lookup_cve(self, temp_updater):
        """Test CVE lookup"""
        test_data = {
            "CVE-2024-1234": {
                "id": "CVE-2024-1234",
                "cvss_score": 7.5
            }
        }
        await temp_updater._save_db(test_data)
        
        result = await temp_updater.lookup_cve("CVE-2024-1234")
        assert result is not None
        assert result["cvss_score"] == 7.5
        
        # Non-existent CVE
        result = await temp_updater.lookup_cve("CVE-9999-9999")
        assert result is None

    def test_get_stats_empty(self, temp_updater):
        """Test stats for empty database"""
        stats = temp_updater.get_stats()
        assert stats["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, temp_updater):
        """Test stats with data"""
        test_data = {
            "CVE-2024-0001": {"id": "CVE-2024-0001", "severity": "high"},
            "CVE-2024-0002": {"id": "CVE-2024-0002", "severity": "critical"},
            "CVE-2024-0003": {"id": "CVE-2024-0003", "severity": "high"},
        }
        await temp_updater._save_db(test_data)
        await temp_updater._save_metadata({"last_update": datetime.utcnow().isoformat()})
        
        stats = temp_updater.get_stats()
        assert stats["status"] == "ready"
        assert stats["total_cves"] == 3
        assert stats["by_severity"]["high"] == 2
        assert stats["by_severity"]["critical"] == 1

    @pytest.mark.asyncio
    async def test_update_merges_data(self, temp_updater):
        """Test that update merges new data"""
        # Initial data
        initial_data = {
            "CVE-2024-0001": {
                "id": "CVE-2024-0001",
                "last_modified": "2024-01-01T00:00:00",
                "cvss_score": 5.0
            }
        }
        await temp_updater._save_db(initial_data)
        
        # Mock NVD client to return update
        mock_cves = [
            CVEEntry(
                id="CVE-2024-0001",
                published="2024-01-01T00:00:00",
                last_modified="2024-01-02T00:00:00",  # Changed
                description="Updated",
                cvss_score=7.0,  # Updated score
                cvss_vector="",
                severity="high",
                references=[],
                cpe_matches=[]
            ),
            CVEEntry(
                id="CVE-2024-0002",
                published="2024-01-01T00:00:00",
                last_modified="2024-01-01T00:00:00",
                description="New",
                cvss_score=9.0,
                cvss_vector="",
                severity="critical",
                references=[],
                cpe_matches=[]
            )
        ]
        
        with patch('modules.cve_updater.NVDClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_instance.fetch_cves = AsyncMock(return_value=mock_cves)
            mock_client.return_value = mock_instance
            
            result = await temp_updater.update()
            
            assert result["last_fetch_new"] == 1
            assert result["last_fetch_updated"] == 1
            assert result["total_cves"] == 2

    def test_get_info(self):
        """Test module info"""
        updater = CVEUpdater()
        info = updater.get_info()
        assert info["name"] == "cve_updater"
        assert "NVD" in info["source"]
        assert info["update_frequency"] == "daily"

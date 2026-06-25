"""Unit tests for api/core/scans.py"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from api.core.scans import ScanManager, scan_manager


class TestScanManager:
    """Test suite for ScanManager class"""

    def test_init(self):
        """Test ScanManager initialization"""
        manager = ScanManager()
        assert manager.scans == {}
        assert isinstance(manager.scans, dict)

    def test_get_scan_existing(self):
        """Test retrieving an existing scan"""
        manager = ScanManager()
        scan_data = {
            "id": "scan_0",
            "target": "example.com",
            "type": "nmap",
            "status": "pending",
        }
        manager.scans["scan_0"] = scan_data

        result = manager.get_scan("scan_0")

        assert result == scan_data

    def test_get_scan_nonexistent(self):
        """Test retrieving a non-existent scan returns None"""
        manager = ScanManager()

        result = manager.get_scan("nonexistent")

        assert result is None

    def test_get_scan_empty_manager(self):
        """Test get_scan on empty manager returns None"""
        manager = ScanManager()

        result = manager.get_scan("scan_0")

        assert result is None

    def test_list_scans_empty(self):
        """Test listing scans when no scans exist"""
        manager = ScanManager()

        result = manager.list_scans()

        assert result == []
        assert isinstance(result, list)

    def test_list_scans_single(self):
        """Test listing scans with single scan"""
        manager = ScanManager()
        scan_data = {
            "id": "scan_0",
            "target": "example.com",
            "type": "nmap",
            "status": "pending",
        }
        manager.scans["scan_0"] = scan_data

        result = manager.list_scans()

        assert len(result) == 1
        assert result[0] == scan_data

    def test_list_scans_multiple(self):
        """Test listing multiple scans"""
        manager = ScanManager()
        scan1 = {
            "id": "scan_0",
            "target": "example.com",
            "type": "nmap",
            "status": "pending",
        }
        scan2 = {
            "id": "scan_1",
            "target": "test.com",
            "type": "sqlmap",
            "status": "running",
        }
        manager.scans["scan_0"] = scan1
        manager.scans["scan_1"] = scan2

        result = manager.list_scans()

        assert len(result) == 2
        assert scan1 in result
        assert scan2 in result

    def test_list_scans_returns_copy(self):
        """Test that list_scans returns a copy of values"""
        manager = ScanManager()
        scan_data = {
            "id": "scan_0",
            "target": "example.com",
            "type": "nmap",
            "status": "pending",
        }
        manager.scans["scan_0"] = scan_data

        result = manager.list_scans()
        result.clear()  # Modify returned list

        # Original should be unchanged
        assert "scan_0" in manager.scans

    @patch("api.core.scans.datetime")
    def test_create_scan(self, mock_datetime):
        """Test creating a new scan"""
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2026-03-15T10:00:00"
        mock_datetime.now.return_value = mock_now

        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        assert scan_id == "scan_0"
        assert scan_id in manager.scans
        assert manager.scans[scan_id]["target"] == "example.com"
        assert manager.scans[scan_id]["type"] == "nmap"
        assert manager.scans[scan_id]["status"] == "pending"
        assert manager.scans[scan_id]["created_at"] == "2026-03-15T10:00:00"

    @patch("api.core.scans.datetime")
    def test_create_scan_multiple(self, mock_datetime):
        """Test creating multiple scans with auto-incrementing IDs"""
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2026-03-15T10:00:00"
        mock_datetime.now.return_value = mock_now

        manager = ScanManager()
        scan_id1 = manager.create_scan("example.com", "nmap")
        scan_id2 = manager.create_scan("test.com", "sqlmap")
        scan_id3 = manager.create_scan("demo.org", "nuclei")

        assert scan_id1 == "scan_0"
        assert scan_id2 == "scan_1"
        assert scan_id3 == "scan_2"
        assert len(manager.scans) == 3

    @patch("api.core.scans.datetime")
    def test_create_scan_with_special_characters_in_target(self, mock_datetime):
        """Test creating scan with special characters in target"""
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2026-03-15T10:00:00"
        mock_datetime.now.return_value = mock_now

        manager = ScanManager()
        target = "https://example.com:8080/path?query=value"
        scan_id = manager.create_scan(target, "custom")

        assert manager.scans[scan_id]["target"] == target

    def test_create_scan_different_types(self):
        """Test creating scans with different scan types"""
        manager = ScanManager()

        scan_types = ["nmap", "sqlmap", "nuclei", "gobuster", "ffuf", "custom"]
        for i, scan_type in enumerate(scan_types):
            scan_id = manager.create_scan(f"target{i}.com", scan_type)
            assert manager.scans[scan_id]["type"] == scan_type

    def test_scan_data_structure(self):
        """Test that created scan has correct data structure"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        scan = manager.scans[scan_id]
        assert "id" in scan
        assert "target" in scan
        assert "type" in scan
        assert "status" in scan
        assert "created_at" in scan

        # Verify types
        assert isinstance(scan["id"], str)
        assert isinstance(scan["target"], str)
        assert isinstance(scan["type"], str)
        assert isinstance(scan["status"], str)
        assert isinstance(scan["created_at"], str)


class TestGlobalScanManager:
    """Test suite for global scan_manager instance"""

    def test_global_instance_exists(self):
        """Test that global scan_manager instance exists"""
        assert scan_manager is not None
        assert isinstance(scan_manager, ScanManager)

    def test_global_instance_is_singleton(self):
        """Test that global instance is shared"""
        from api.core.scans import scan_manager as scan_manager_2

        assert scan_manager is scan_manager_2

    def test_global_instance_operations(self):
        """Test operations on global instance"""
        # Clear any existing scans
        scan_manager.scans.clear()

        scan_id = scan_manager.create_scan("global-test.com", "nmap")

        assert scan_manager.get_scan(scan_id) is not None
        assert len(scan_manager.list_scans()) >= 1


class TestScanStatusTracking:
    """Test suite for scan status tracking functionality"""

    def test_default_status_pending(self):
        """Test that new scans have pending status"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        scan = manager.get_scan(scan_id)
        assert scan["status"] == "pending"

    def test_status_can_be_updated(self):
        """Test that scan status can be manually updated"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        manager.scans[scan_id]["status"] = "running"

        scan = manager.get_scan(scan_id)
        assert scan["status"] == "running"

    def test_status_transitions(self):
        """Test various status transitions"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        statuses = [
            "pending",
            "running",
            "paused",
            "completed",
            "failed",
            "cancelled",
        ]
        for status in statuses:
            manager.scans[scan_id]["status"] = status
            assert manager.get_scan(scan_id)["status"] == status


class TestScanResultsHandling:
    """Test suite for scan results handling"""

    def test_add_results_to_scan(self):
        """Test adding results to a scan"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        manager.scans[scan_id]["results"] = {"ports": [80, 443]}

        scan = manager.get_scan(scan_id)
        assert "results" in scan
        assert scan["results"]["ports"] == [80, 443]

    def test_update_scan_results(self):
        """Test updating scan results"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        manager.scans[scan_id]["results"] = {"progress": 50}
        manager.scans[scan_id]["results"]["progress"] = 100

        scan = manager.get_scan(scan_id)
        assert scan["results"]["progress"] == 100

    def test_scan_with_empty_results(self):
        """Test scan with empty results"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        manager.scans[scan_id]["results"] = {}

        scan = manager.get_scan(scan_id)
        assert scan["results"] == {}

    def test_scan_with_complex_results(self):
        """Test scan with complex nested results"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        complex_results = {
            "findings": [
                {"severity": "high", "title": "SQL Injection"},
                {"severity": "medium", "title": "XSS"},
            ],
            "metadata": {
                "duration": 120.5,
                "tools_used": ["sqlmap", "nuclei"],
            },
        }
        manager.scans[scan_id]["results"] = complex_results

        scan = manager.get_scan(scan_id)
        assert scan["results"]["findings"][0]["severity"] == "high"
        assert len(scan["results"]["findings"]) == 2


class TestScanConfiguration:
    """Test suite for scan configuration"""

    def test_create_scan_with_custom_config(self):
        """Test creating scan and adding custom configuration"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        manager.scans[scan_id]["config"] = {
            "threads": 10,
            "timeout": 30,
            "verbose": True,
        }

        scan = manager.get_scan(scan_id)
        assert scan["config"]["threads"] == 10
        assert scan["config"]["timeout"] == 30
        assert scan["config"]["verbose"] is True

    def test_scan_config_immutability_after_creation(self):
        """Test that scan data can be modified after creation"""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")
        original_target = manager.scans[scan_id]["target"]

        manager.scans[scan_id]["target"] = "modified.com"

        scan = manager.get_scan(scan_id)
        assert scan["target"] == "modified.com"
        assert scan["target"] != original_target

    def test_scan_type_variations(self):
        """Test various scan type configurations"""
        manager = ScanManager()

        configs = [
            ("192.168.1.1", "nmap"),
            ("http://test.com", "sqlmap"),
            ("api.example.com", "nuclei"),
            ("", "custom"),  # Empty target
            ("sub.example.com", "subfinder"),
        ]

        for target, scan_type in configs:
            scan_id = manager.create_scan(target, scan_type)
            scan = manager.get_scan(scan_id)
            assert scan["target"] == target
            assert scan["type"] == scan_type


class TestErrorHandling:
    """Test suite for error handling scenarios"""

    def test_get_scan_with_invalid_type(self):
        """Test get_scan with invalid input types"""
        manager = ScanManager()

        # Should handle None and int gracefully
        assert manager.get_scan(None) is None
        assert manager.get_scan(123) is None

        # Unhashable types will raise TypeError (expected behavior)
        with pytest.raises(TypeError):
            manager.get_scan([])
        with pytest.raises(TypeError):
            manager.get_scan({})

    def test_create_scan_with_empty_strings(self):
        """Test creating scan with empty string parameters"""
        manager = ScanManager()

        scan_id = manager.create_scan("", "")

        scan = manager.get_scan(scan_id)
        assert scan["target"] == ""
        assert scan["type"] == ""

    def test_create_scan_with_unicode(self):
        """Test creating scan with unicode characters"""
        manager = ScanManager()

        scan_id = manager.create_scan("тест.рф", "сканирование")

        scan = manager.get_scan(scan_id)
        assert scan["target"] == "тест.рф"
        assert scan["type"] == "сканирование"

    def test_concurrent_scan_creation(self):
        """Test creating multiple scans rapidly"""
        manager = ScanManager()
        scan_ids = []

        for i in range(100):
            scan_id = manager.create_scan(f"target{i}.com", "nmap")
            scan_ids.append(scan_id)

        assert len(scan_ids) == 100
        assert len(set(scan_ids)) == 100  # All IDs should be unique
        assert all(f"scan_{i}" in manager.scans for i in range(100))

    def test_modify_scan_during_iteration(self):
        """Test modifying scans during iteration"""
        manager = ScanManager()

        for i in range(5):
            manager.create_scan(f"target{i}.com", "nmap")

        # Should be able to iterate without errors
        scans = manager.list_scans()
        for scan in scans:
            scan["modified"] = True

        # Verify modifications
        for scan in manager.list_scans():
            assert scan.get("modified") is True


class TestEdgeCases:
    """Test suite for edge cases"""

    def test_very_long_target(self):
        """Test scan with very long target string"""
        manager = ScanManager()
        long_target = "a" * 10000

        scan_id = manager.create_scan(long_target, "nmap")

        scan = manager.get_scan(scan_id)
        assert len(scan["target"]) == 10000

    def test_special_characters_in_scan_type(self):
        """Test scan with special characters in scan type"""
        manager = ScanManager()

        scan_type = "nmap -sV -O --script=vuln"
        scan_id = manager.create_scan("example.com", scan_type)

        scan = manager.get_scan(scan_id)
        assert scan["type"] == scan_type

    def test_datetime_isoformat_called(self):
        """Test that datetime.now().isoformat() is called during creation"""
        with patch("api.core.scans.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "mocked_timestamp"
            mock_datetime.now.return_value = mock_now

            manager = ScanManager()
            scan_id = manager.create_scan("example.com", "nmap")

            mock_datetime.now.assert_called_once()
            mock_now.isoformat.assert_called_once()
            assert manager.scans[scan_id]["created_at"] == "mocked_timestamp"

    def test_scan_id_format(self):
        """Test scan ID format"""
        manager = ScanManager()

        scan_id = manager.create_scan("example.com", "nmap")

        assert scan_id.startswith("scan_")
        assert scan_id.split("_")[1].isdigit()

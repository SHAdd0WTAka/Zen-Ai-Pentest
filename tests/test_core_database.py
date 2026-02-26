"""
Tests for core/database.py
Target: 90%+ Coverage
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


class MockCVEDatabase:
    """Mock CVE Database for testing"""

    def __init__(self):
        self.cve_data = {
            "CVE-2021-44228": {
                "description": "Log4j vulnerability",
                "cvss_score": 10.0,
                "name": "Log4Shell",
            },
            "CVE-2023-1234": {
                "description": "Test vulnerability 2023",
                "name": "Test CVE",
            },
            "CVE-2022-9999": "simple_string_entry",
        }
        self.ransomware_data = {
            "WannaCry": {"type": "encryptor", "first_seen": "2017-05-12"},
            "SimpleRansom": "ransomware_string",
        }


@pytest.fixture
def reset_db_instance():
    """Reset global database instance before each test"""
    # Need to patch the module before importing
    with patch.dict("sys.modules", {"modules.cve_database": MagicMock()}):
        import core.database as db_module

        db_module._db_instance = None
        yield db_module


class TestGetDB:
    """Test _get_db function"""

    @patch("core.database.CVEDatabase")
    def test_get_db_creates_instance(self, mock_cve_db_class):
        """Test _get_db creates new instance"""
        import core.database as db_module

        db_module._db_instance = None

        mock_instance = MagicMock()
        mock_cve_db_class.return_value = mock_instance

        result = db_module._get_db()

        mock_cve_db_class.assert_called_once()
        assert result == mock_instance

    @patch("core.database.CVEDatabase")
    def test_get_db_returns_existing(self, mock_cve_db_class):
        """Test _get_db returns existing instance"""
        import core.database as db_module

        existing = MagicMock()
        db_module._db_instance = existing

        result = db_module._get_db()

        mock_cve_db_class.assert_not_called()
        assert result == existing


class TestGetCVEDB:
    """Test get_cve_db function"""

    @patch("core.database._get_db")
    def test_get_cve_db_returns_list(self, mock_get_db):
        """Test get_cve_db returns list of CVEs"""
        from core.database import get_cve_db

        mock_db = MagicMock()
        mock_db.cve_data = {
            "CVE-2021-1234": {"description": "Test", "name": "Test CVE"}
        }
        mock_get_db.return_value = mock_db

        result = get_cve_db()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["cve_id"] == "CVE-2021-1234"

    @patch("core.database._get_db")
    def test_get_cve_db_handles_string_data(self, mock_get_db):
        """Test get_cve_db handles string CVE data"""
        from core.database import get_cve_db

        mock_db = MagicMock()
        mock_db.cve_data = {"CVE-2021-5678": "simple_string"}
        mock_get_db.return_value = mock_db

        result = get_cve_db()

        assert len(result) == 1
        assert result[0]["cve_id"] == "CVE-2021-5678"
        # Should not have 'simple_string' merged
        assert "simple_string" not in result[0]

    @patch("core.database._get_db")
    def test_get_cve_db_empty(self, mock_get_db):
        """Test get_cve_db with empty database"""
        from core.database import get_cve_db

        mock_db = MagicMock()
        mock_db.cve_data = {}
        mock_get_db.return_value = mock_db

        result = get_cve_db()

        assert result == []


class TestGetRansomwareDB:
    """Test get_ransomware_db function"""

    @patch("core.database._get_db")
    def test_get_ransomware_db_returns_list(self, mock_get_db):
        """Test get_ransomware_db returns list"""
        from core.database import get_ransomware_db

        mock_db = MagicMock()
        mock_db.ransomware_data = {"WannaCry": {"type": "encryptor"}}
        mock_get_db.return_value = mock_db

        result = get_ransomware_db()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "WannaCry"

    @patch("core.database._get_db")
    def test_get_ransomware_db_handles_string(self, mock_get_db):
        """Test get_ransomware_db handles string data"""
        from core.database import get_ransomware_db

        mock_db = MagicMock()
        mock_db.ransomware_data = {"SimpleRansom": "string_data"}
        mock_get_db.return_value = mock_db

        result = get_ransomware_db()

        assert len(result) == 1
        assert result[0]["name"] == "SimpleRansom"


class TestSearchCVE:
    """Test search_cve function"""

    @patch("core.database.get_cve_db")
    def test_search_by_cve_id(self, mock_get_cve_db):
        """Test search by CVE ID"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-44228", "description": "Log4j"},
            {"cve_id": "CVE-2022-1234", "description": "Other"},
        ]

        result = search_cve("2021-44228")

        assert len(result) == 1
        assert result[0]["cve_id"] == "CVE-2021-44228"

    @patch("core.database.get_cve_db")
    def test_search_by_description(self, mock_get_cve_db):
        """Test search by description"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-44228", "description": "Log4j vulnerability"},
            {"cve_id": "CVE-2022-1234", "description": "Other issue"},
        ]

        result = search_cve("log4j")

        assert len(result) == 1
        assert result[0]["cve_id"] == "CVE-2021-44228"

    @patch("core.database.get_cve_db")
    def test_search_by_name(self, mock_get_cve_db):
        """Test search by name"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-1", "name": "Log4Shell"},
            {"cve_id": "CVE-2021-2", "name": "Other"},
        ]

        result = search_cve("log4shell")

        assert len(result) == 1
        assert result[0]["name"] == "Log4Shell"

    @patch("core.database.get_cve_db")
    def test_search_case_insensitive(self, mock_get_cve_db):
        """Test search is case insensitive"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-1", "description": "UPPERCASE"}
        ]

        result = search_cve("uppercase")

        assert len(result) == 1

    @patch("core.database.get_cve_db")
    def test_search_no_results(self, mock_get_cve_db):
        """Test search with no matches"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-1", "description": "Something"}
        ]

        result = search_cve("nonexistent")

        assert result == []

    @patch("core.database.get_cve_db")
    def test_search_multiple_results(self, mock_get_cve_db):
        """Test search returning multiple results"""
        from core.database import search_cve

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-111", "description": "common term"},
            {"cve_id": "CVE-2021-222", "description": "common term"},
            {"cve_id": "CVE-2021-333", "description": "other"},
        ]

        result = search_cve("common")

        assert len(result) == 2


class TestGetCVEByYear:
    """Test get_cve_by_year function"""

    @patch("core.database.get_cve_db")
    def test_get_by_year_2021(self, mock_get_cve_db):
        """Test getting CVEs from 2021"""
        from core.database import get_cve_by_year

        mock_get_cve_db.return_value = [
            {"cve_id": "CVE-2021-44228"},
            {"cve_id": "CVE-2021-1234"},
            {"cve_id": "CVE-2022-5678"},
        ]

        result = get_cve_by_year(2021)

        assert len(result) == 2
        assert all("CVE-2021-" in cve["cve_id"] for cve in result)

    @patch("core.database.get_cve_db")
    def test_get_by_year_no_results(self, mock_get_cve_db):
        """Test getting CVEs from year with no entries"""
        from core.database import get_cve_by_year

        mock_get_cve_db.return_value = [{"cve_id": "CVE-2021-1234"}]

        result = get_cve_by_year(1999)

        assert result == []


class TestGetCVEByID:
    """Test get_cve_by_id function"""

    @patch("core.database._get_db")
    def test_get_cve_by_id_found(self, mock_get_db):
        """Test getting existing CVE"""
        from core.database import get_cve_by_id

        mock_db = MagicMock()
        mock_db.cve_data.get.return_value = {
            "description": "Test",
            "cvss_score": 9.8,
        }
        mock_get_db.return_value = mock_db

        result = get_cve_by_id("CVE-2021-1234")

        assert result is not None
        assert result["cve_id"] == "CVE-2021-1234"
        assert result["cvss_score"] == 9.8
        # Verify uppercase was used for lookup
        mock_db.cve_data.get.assert_called_with("CVE-2021-1234")

    @patch("core.database._get_db")
    def test_get_cve_by_id_not_found(self, mock_get_db):
        """Test getting non-existent CVE"""
        from core.database import get_cve_by_id

        mock_db = MagicMock()
        mock_db.cve_data.get.return_value = None
        mock_get_db.return_value = mock_db

        result = get_cve_by_id("CVE-9999-9999")

        assert result is None

    @patch("core.database._get_db")
    def test_get_cve_by_id_string_data(self, mock_get_db):
        """Test CVE with string data"""
        from core.database import get_cve_by_id

        mock_db = MagicMock()
        mock_db.cve_data.get.return_value = "string_data"
        mock_get_db.return_value = mock_db

        result = get_cve_by_id("CVE-2021-1")

        assert result["cve_id"] == "CVE-2021-1"
        assert result["data"] == "string_data"

    @patch("core.database._get_db")
    def test_get_cve_by_id_lowercase_input(self, mock_get_db):
        """Test CVE ID is uppercased"""
        from core.database import get_cve_by_id

        mock_db = MagicMock()
        mock_db.cve_data.get.return_value = None
        mock_get_db.return_value = mock_db

        get_cve_by_id("cve-2021-1234")

        mock_db.cve_data.get.assert_called_with("CVE-2021-1234")


class TestGetRansomwareByName:
    """Test get_ransomware_by_name function"""

    @patch("core.database._get_db")
    def test_get_ransomware_found(self, mock_get_db):
        """Test getting existing ransomware"""
        from core.database import get_ransomware_by_name

        mock_db = MagicMock()
        mock_db.ransomware_data.get.return_value = {
            "type": "encryptor",
            "first_seen": "2017-05-12",
        }
        mock_get_db.return_value = mock_db

        result = get_ransomware_by_name("WannaCry")

        assert result is not None
        assert result["name"] == "WannaCry"
        assert result["type"] == "encryptor"

    @patch("core.database._get_db")
    def test_get_ransomware_not_found(self, mock_get_db):
        """Test getting non-existent ransomware"""
        from core.database import get_ransomware_by_name

        mock_db = MagicMock()
        mock_db.ransomware_data.get.return_value = None
        mock_get_db.return_value = mock_db

        result = get_ransomware_by_name("UnknownRansom")

        assert result is None

    @patch("core.database._get_db")
    def test_get_ransomware_string_data(self, mock_get_db):
        """Test ransomware with string data"""
        from core.database import get_ransomware_by_name

        mock_db = MagicMock()
        mock_db.ransomware_data.get.return_value = "simple_string"
        mock_get_db.return_value = mock_db

        result = get_ransomware_by_name("SimpleRansom")

        assert result["name"] == "SimpleRansom"
        assert result["data"] == "simple_string"


class TestExports:
    """Test module exports"""

    def test_all_exports_defined(self):
        """Test __all__ is defined correctly"""
        from core import database

        expected = [
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

        assert database.__all__ == expected

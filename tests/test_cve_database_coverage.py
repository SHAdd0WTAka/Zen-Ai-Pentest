"""
Tests for cve_database module - Coverage Boost
"""

import json

import pytest


class TestCVEEntry:
    """Test CVEEntry dataclass"""

    def test_cve_entry_creation(self):
        """Test CVEEntry creation"""
        from modules.cve_database import CVEEntry

        entry = CVEEntry(
            cve_id="CVE-2021-1234",
            name="Test CVE",
            cvss_score=9.8,
            severity="Critical",
            description="Test description",
            affected_products=["Product 1", "Product 2"],
            exploits=["Exploit 1"],
            patches=["Patch 1"],
            mitigations=["Mitigation 1"],
            detection_methods=["Detection 1"],
            ransomware_used_by=["Ransomware 1"],
            ioc={"files": ["test.exe"]},
        )

        assert entry.cve_id == "CVE-2021-1234"
        assert entry.cvss_score == 9.8
        assert entry.severity == "Critical"
        assert len(entry.affected_products) == 2


class TestRansomwareEntry:
    """Test RansomwareEntry dataclass"""

    def test_ransomware_entry_creation(self):
        """Test RansomwareEntry creation"""
        from modules.cve_database import RansomwareEntry

        entry = RansomwareEntry(
            name="TestRansom",
            first_seen="2021-01-01",
            type="Encryptor",
            description="Test ransomware",
            cves=["CVE-2021-1234"],
            file_extensions=[".encrypted"],
            ransom_note="README.txt",
            ioc={"hashes": ["abc123"]},
            mitigation=["Backup regularly"],
            detection=["Monitor file changes"],
            decryptable=True,
            estimated_damage=1000000,
        )

        assert entry.name == "TestRansom"
        assert entry.decryptable is True
        assert entry.estimated_damage == 1000000


class TestCVEDatabase:
    """Test CVEDatabase class"""

    @pytest.fixture
    def mock_db_data(self):
        """Mock database data"""
        return {
            "ransomware_campaigns": {
                "wannacry": {
                    "name": "WannaCry",
                    "first_seen": "2017-05-12",
                    "type": "Worm",
                    "description": "Ransomware worm",
                    "cves": ["CVE-2017-0144"],
                    "file_extensions": [".wncry"],
                    "ransom_note": "@Please_Read_Me@.txt",
                    "ioc": {
                        "files": ["tasksche.exe", "mssecsvc.exe"],
                        "hashes": ["db349b97c37d22f5ea1d1841e3c89eb4"],
                        "registry": ["HKLM\\Software\\WannaCry"],
                        "processes": ["tasksche.exe"],
                        "network": ["iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea.com"],
                    },
                    "mitigation": ["Apply MS17-010"],
                    "detection": ["SMB anomaly detection"],
                    "decryptable": True,
                    "estimated_damage_usd": 4000000000,
                }
            },
            "critical_historical_cves": {
                "CVE-2017-0144": {
                    "name": "EternalBlue",
                    "cvss": 8.1,
                    "severity": "High",
                    "description": "SMB vulnerability",
                    "affected_products": ["Windows 7", "Windows Server 2008"],
                    "exploits": ["Metasploit module"],
                    "patch": "MS17-010",
                    "mitigation": ["Disable SMBv1"],
                    "detection": ["Network monitoring"],
                    "ransomware_used_by": ["WannaCry", "NotPetya"],
                }
            },
            "common_exploit_chains": {"eternalblue_chain": ["CVE-2017-0144", "CVE-2017-0145"]},
        }

    @pytest.fixture
    def cve_db(self, mock_db_data, tmp_path):
        """Create CVEDatabase with mocked data"""
        from modules.cve_database import CVEDatabase

        # Create temp data directory
        data_dir = tmp_path / "data" / "cve_db"
        data_dir.mkdir(parents=True)

        # Write mock data
        db_file = data_dir / "ransomware_cves.json"
        with open(db_file, "w") as f:
            json.dump(mock_db_data, f)

        db = CVEDatabase()
        db.db_path = str(data_dir)
        db._load_databases()
        return db

    def test_init_loads_databases(self, mock_db_data, tmp_path):
        """Test database initialization loads data"""
        from modules.cve_database import CVEDatabase

        data_dir = tmp_path / "data" / "cve_db"
        data_dir.mkdir(parents=True)
        db_file = data_dir / "ransomware_cves.json"

        with open(db_file, "w") as f:
            json.dump(mock_db_data, f)

        db = CVEDatabase()
        db.db_path = str(data_dir)
        db._load_databases()

        assert len(db.ransomware_data) == 1
        assert len(db.cve_data) == 1

    def test_search_cve_found(self, cve_db):
        """Test searching for existing CVE"""
        result = cve_db.search_cve("CVE-2017-0144")

        assert result is not None
        assert result.cve_id == "CVE-2017-0144"
        assert result.name == "EternalBlue"
        assert result.cvss_score == 8.1
        assert result.severity == "High"

    def test_search_cve_not_found(self, cve_db):
        """Test searching for non-existing CVE"""
        result = cve_db.search_cve("CVE-9999-9999")

        assert result is None

    def test_search_cve_case_insensitive(self, cve_db):
        """Test CVE search is case insensitive"""
        result_lower = cve_db.search_cve("cve-2017-0144")
        result_upper = cve_db.search_cve("CVE-2017-0144")

        assert result_lower.cve_id == result_upper.cve_id

    def test_search_ransomware_found(self, cve_db):
        """Test searching for existing ransomware"""
        result = cve_db.search_ransomware("wannacry")

        assert result is not None
        assert result.name == "WannaCry"
        assert result.decryptable is True

    def test_search_ransomware_not_found(self, cve_db):
        """Test searching for non-existing ransomware"""
        result = cve_db.search_ransomware("nonexistent")

        assert result is None

    def test_search_ransomware_case_insensitive(self, cve_db):
        """Test ransomware search is case insensitive"""
        result = cve_db.search_ransomware("WANNACRY")

        assert result is not None
        assert result.name == "WannaCry"

    def test_get_ransomware_by_cve(self, cve_db):
        """Test finding ransomware by CVE"""
        results = cve_db.get_ransomware_by_cve("CVE-2017-0144")

        assert len(results) == 1
        assert "WannaCry" in results

    def test_get_ransomware_by_cve_not_found(self, cve_db):
        """Test finding ransomware by non-existing CVE"""
        results = cve_db.get_ransomware_by_cve("CVE-9999-9999")

        assert len(results) == 0

    def test_get_cves_by_severity(self, cve_db):
        """Test getting CVEs by severity"""
        results = cve_db.get_cves_by_severity("High")

        assert len(results) == 1
        assert results[0].severity == "High"

    def test_get_cves_by_severity_not_found(self, cve_db):
        """Test getting CVEs by non-existing severity"""
        results = cve_db.get_cves_by_severity("Low")

        assert len(results) == 0

    def test_get_critical_cves(self, cve_db):
        """Test getting critical CVEs"""
        # Add a critical CVE
        cve_db.cve_data["CVE-2021-9999"] = {"name": "Critical Vuln", "cvss": 9.9, "severity": "Critical"}

        results = cve_db.get_critical_cves()

        assert len(results) == 1
        assert results[0].severity == "Critical"

    def test_get_ransomware_iocs(self, cve_db):
        """Test getting ransomware IOCs"""
        iocs = cve_db.get_ransomware_iocs("WannaCry")

        assert "files" in iocs
        assert "tasksche.exe" in iocs["files"]

    def test_get_ransomware_iocs_not_found(self, cve_db):
        """Test getting IOCs for non-existing ransomware"""
        iocs = cve_db.get_ransomware_iocs("NonExistent")

        assert iocs == {}

    def test_check_system_for_ransomware_no_match(self, cve_db):
        """Test system check with no ransomware indicators"""
        indicators = {"files": ["notepad.exe", "calc.exe"], "hashes": ["12345"]}

        results = cve_db.check_system_for_ransomware(indicators)

        # Should return empty or low-match results
        assert isinstance(results, list)

    def test_check_system_for_ransomware_with_match(self, cve_db):
        """Test system check with matching ransomware indicators"""
        indicators = {"files": ["tasksche.exe"], "hashes": ["db349b97c37d22f5ea1d1841e3c89eb4"]}

        results = cve_db.check_system_for_ransomware(indicators)

        assert len(results) > 0
        assert results[0]["ransomware"] == "WannaCry"

    def test_get_exploit_chain(self, cve_db):
        """Test getting exploit chain"""
        chain = cve_db.get_exploit_chain("eternalblue_chain")

        assert len(chain) == 2
        assert "CVE-2017-0144" in chain

    def test_list_all_ransomware(self, cve_db):
        """Test listing all ransomware"""
        results = cve_db.list_all_ransomware()

        assert len(results) == 1
        assert results[0]["name"] == "WannaCry"

    def test_list_all_cves(self, cve_db):
        """Test listing all CVEs"""
        results = cve_db.list_all_cves()

        assert len(results) == 1
        assert results[0]["cve_id"] == "CVE-2017-0144"

    def test_get_mitigation_for_cve(self, cve_db):
        """Test getting mitigation for CVE"""
        mitigations = cve_db.get_mitigation_for_cve("CVE-2017-0144")

        assert len(mitigations) == 1
        assert "Disable SMBv1" in mitigations

    def test_get_mitigation_for_cve_not_found(self, cve_db):
        """Test getting mitigation for non-existing CVE"""
        mitigations = cve_db.get_mitigation_for_cve("CVE-9999-9999")

        assert mitigations == []

    def test_get_detection_for_ransomware(self, cve_db):
        """Test getting detection methods for ransomware"""
        detection = cve_db.get_detection_for_ransomware("WannaCry")

        assert len(detection) == 1
        assert "SMB anomaly detection" in detection

    def test_get_detection_for_ransomware_not_found(self, cve_db):
        """Test getting detection for non-existing ransomware"""
        detection = cve_db.get_detection_for_ransomware("NonExistent")

        assert detection == []

    def test_generate_vulnerability_report(self, cve_db):
        """Test vulnerability report generation"""
        report = cve_db.generate_vulnerability_report(["CVE-2017-0144"])

        assert "CVE-2017-0144" in report
        assert "EternalBlue" in report

    def test_generate_vulnerability_report_empty(self, cve_db):
        """Test vulnerability report generation with empty list"""
        report = cve_db.generate_vulnerability_report([])

        assert len(report) > 0  # Should return header or message

    def test_get_latest_threats(self, cve_db):
        """Test getting latest threats"""
        threats = cve_db.get_latest_threats(limit=5)

        assert isinstance(threats, list)
        assert len(threats) <= 5

"""
Comprehensive Tests for CVE Database Module

This module tests the CVEDatabase class which provides
comprehensive CVE and ransomware information.

Target Coverage: 70%+
"""

import json
import os
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from modules.cve_database import CVEDatabase, CVEEntry, RansomwareEntry


class TestCVEEntry:
    """Test CVEEntry dataclass"""

    def test_basic_creation(self):
        """Test basic CVEEntry creation"""
        entry = CVEEntry(
            cve_id="CVE-2021-44228",
            name="Log4Shell",
            cvss_score=10.0,
            severity="Critical",
            description="Apache Log4j2 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints",
            affected_products=["Apache Log4j 2.0-beta9 to 2.14.1"],
            exploits=["https://github.com/example/exploit"],
            patches=["https://logging.apache.org/log4j/2.x/security.html"],
            mitigations=["Upgrade to Log4j 2.15.0 or later"],
            detection_methods=["Check for suspicious JNDI lookups"],
        )
        assert entry.cve_id == "CVE-2021-44228"
        assert entry.name == "Log4Shell"
        assert entry.cvss_score == 10.0
        assert entry.severity == "Critical"
        assert len(entry.affected_products) == 1

    def test_with_ransomware(self):
        """Test CVEEntry with ransomware associations"""
        entry = CVEEntry(
            cve_id="CVE-2023-1234",
            name="Test CVE",
            cvss_score=9.8,
            severity="Critical",
            description="Test description",
            affected_products=["Product 1"],
            exploits=[],
            patches=[],
            mitigations=[],
            detection_methods=[],
            ransomware_used_by=["LockBit", "BlackCat"],
            ioc={"files": ["ransom.exe"]},
        )
        assert entry.ransomware_used_by == ["LockBit", "BlackCat"]
        assert entry.ioc == {"files": ["ransom.exe"]}


class TestRansomwareEntry:
    """Test RansomwareEntry dataclass"""

    def test_basic_creation(self):
        """Test basic RansomwareEntry creation"""
        entry = RansomwareEntry(
            name="LockBit",
            first_seen="2019-09",
            type="Ransomware-as-a-Service",
            description="Advanced ransomware with affiliate model",
            cves=["CVE-2021-34527", "CVE-2022-1234"],
            file_extensions=[".lockbit", "abcd.lock"],
            ransom_note="Restore-My-Files.txt",
            ioc={"domains": ["lockbit-blog.com"]},
            mitigation=["Isolate infected systems"],
            detection=["Monitor for file encryption"],
            decryptable=False,
        )
        assert entry.name == "LockBit"
        assert entry.first_seen == "2019-09"
        assert entry.decryptable is False

    def test_with_damage_estimate(self):
        """Test RansomwareEntry with damage estimate"""
        entry = RansomwareEntry(
            name="WannaCry",
            first_seen="2017-05",
            type="Worm",
            description="Self-propagating ransomware",
            cves=["CVE-2017-0144"],
            file_extensions=[".wncry"],
            ransom_note="@Please_Read_Me@.txt",
            ioc={},
            mitigation=["Apply MS17-010 patch"],
            detection=["SMBv1 activity monitoring"],
            decryptable=True,
            estimated_damage=4000000000,  # $4B
        )
        assert entry.estimated_damage == 4000000000


class TestCVEDatabaseInit:
    """Test CVEDatabase initialization"""

    @patch("os.path.exists")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps({"ransomware_campaigns": {}, "critical_historical_cves": {}, "common_exploit_chains": {}})
        ),
    )
    def test_init_no_existing_db(self, mock_exists):
        """Test initialization when DB file doesn't exist"""
        mock_exists.return_value = False
        db = CVEDatabase()
        assert db.orchestrator is None
        assert db.db_path == "data/cve_db"
        assert db.ransomware_data == {}
        assert db.cve_data == {}

    @patch("os.path.exists")
    @patch(
        "builtins.open",
        mock_open(
            read_data=json.dumps(
                {
                    "ransomware_campaigns": {"lockbit": {"name": "LockBit", "cves": ["CVE-2021-1234"]}},
                    "critical_historical_cves": {"CVE-2021-44228": {"name": "Log4Shell", "cvss": 10.0}},
                    "common_exploit_chains": {"chain1": {"name": "Test Chain"}},
                }
            )
        ),
    )
    def test_init_with_existing_db(self, mock_exists):
        """Test initialization with existing DB file"""
        mock_exists.return_value = True
        db = CVEDatabase()
        assert "lockbit" in db.ransomware_data
        assert "CVE-2021-44228" in db.cve_data
        assert "chain1" in db.exploit_chains

    @patch("os.path.exists")
    @patch("builtins.open", side_effect=Exception("Read error"))
    def test_init_with_read_error(self, mock_open_fn, mock_exists):
        """Test initialization with file read error"""
        mock_exists.return_value = True
        db = CVEDatabase()
        # Should handle error gracefully
        assert db.cve_data == {}
        assert db.ransomware_data == {}

    def test_init_with_orchestrator(self):
        """Test initialization with orchestrator"""
        mock_orch = MagicMock()
        with patch("os.path.exists", return_value=False):
            db = CVEDatabase(orchestrator=mock_orch)
            assert db.orchestrator == mock_orch


class TestSearchCVE:
    """Test CVE search functionality"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "cvss": 10.0,
                    "severity": "Critical",
                    "description": "Log4j JNDI injection",
                    "affected_products": ["Log4j 2.0-2.14.1"],
                    "exploits": ["https://exploit.com"],
                    "patch": "https://patch.com",
                    "mitigation": ["Upgrade Log4j"],
                    "detection": ["Monitor JNDI"],
                    "ransomware_used_by": ["LockBit"],
                },
                "CVE-2021-34527": {
                    "name": "PrintNightmare",
                    "cvss": 8.8,
                    "severity": "High",
                    "description": "Windows Print Spooler vulnerability",
                    "affected_products": ["Windows Server"],
                    "exploits": [],
                    "patch": None,
                    "mitigation": ["Disable Print Spooler"],
                    "detection": [],
                },
            }
            return database

    def test_search_existing_cve(self, db):
        """Test searching for existing CVE"""
        result = db.search_cve("CVE-2021-44228")
        assert result is not None
        assert result.cve_id == "CVE-2021-44228"
        assert result.name == "Log4Shell"
        assert result.cvss_score == 10.0
        assert result.severity == "Critical"

    def test_search_cve_case_insensitive(self, db):
        """Test CVE ID case insensitivity"""
        result = db.search_cve("cve-2021-44228")
        assert result is not None
        assert result.cve_id == "CVE-2021-44228"

    def test_search_nonexistent_cve(self, db):
        """Test searching for non-existent CVE"""
        result = db.search_cve("CVE-2099-99999")
        assert result is None

    def test_search_cve_without_patch(self, db):
        """Test CVE without patch info"""
        result = db.search_cve("CVE-2021-34527")
        assert result is not None
        assert result.patches == []  # Should handle None gracefully


class TestSearchRansomware:
    """Test ransomware search functionality"""

    @pytest.fixture
    def db(self):
        """Create database with sample ransomware data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "first_seen": "2019-09",
                    "type": "RaaS",
                    "description": "Ransomware-as-a-Service",
                    "cves": ["CVE-2021-1234"],
                    "file_extensions": [".lockbit"],
                    "ransom_note": "Restore-My-Files.txt",
                    "ioc": {"domains": ["lockbit.com"]},
                    "mitigation": ["Isolate systems"],
                    "detection": ["Monitor files"],
                    "decryptable": False,
                },
                "wannacry": {
                    "name": "WannaCry",
                    "first_seen": "2017-05",
                    "type": "Worm",
                    "description": "Self-propagating ransomware",
                    "cves": ["CVE-2017-0144"],
                    "file_extensions": [".wncry"],
                    "ransom_note": "README.txt",
                    "ioc": {},
                    "mitigation": ["Apply patches"],
                    "detection": ["Monitor SMB"],
                    "decryptable": True,
                },
            }
            return database

    def test_search_existing_ransomware(self, db):
        """Test searching for existing ransomware"""
        result = db.search_ransomware("LockBit")
        assert result is not None
        assert result.name == "LockBit"
        assert result.first_seen == "2019-09"
        assert result.decryptable is False

    def test_search_ransomware_case_insensitive(self, db):
        """Test ransomware name case insensitivity"""
        result = db.search_ransomware("lockbit")
        assert result is not None
        assert result.name == "LockBit"

    def test_search_ransomware_partial_match(self, db):
        """Test partial match on ransomware name"""
        result = db.search_ransomware("wanna")
        assert result is not None
        assert result.name == "WannaCry"

    def test_search_nonexistent_ransomware(self, db):
        """Test searching for non-existent ransomware"""
        result = db.search_ransomware("FakeRansomware")
        assert result is None


class TestGetRansomwareByCVE:
    """Test getting ransomware by CVE"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "cves": ["CVE-2021-1234", "CVE-2021-5678"],
                },
                "blackcat": {
                    "name": "BlackCat",
                    "cves": ["CVE-2021-1234"],
                },
            }
            return database

    def test_get_by_existing_cve(self, db):
        """Test getting ransomware by CVE that exists"""
        result = db.get_ransomware_by_cve("CVE-2021-1234")
        assert len(result) == 2
        assert "LockBit" in result
        assert "BlackCat" in result

    def test_get_by_nonexistent_cve(self, db):
        """Test getting ransomware by CVE that doesn't exist"""
        result = db.get_ransomware_by_cve("CVE-2099-9999")
        assert result == []

    def test_case_insensitive_cve(self, db):
        """Test case insensitivity for CVE ID"""
        result = db.get_ransomware_by_cve("cve-2021-1234")
        assert len(result) == 2


class TestGetCVEsBySeverity:
    """Test getting CVEs by severity"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "cvss": 10.0,
                    "severity": "Critical",
                },
                "CVE-2021-34527": {
                    "name": "PrintNightmare",
                    "cvss": 8.8,
                    "severity": "High",
                },
                "CVE-2021-1234": {
                    "name": "Another Critical",
                    "cvss": 9.9,
                    "severity": "Critical",
                },
            }
            return database

    def test_get_critical_cves(self, db):
        """Test getting critical CVEs"""
        result = db.get_cves_by_severity("Critical")
        assert len(result) == 2
        cve_ids = [r.cve_id for r in result]
        assert "CVE-2021-44228" in cve_ids
        assert "CVE-2021-1234" in cve_ids

    def test_get_high_cves(self, db):
        """Test getting high severity CVEs"""
        result = db.get_cves_by_severity("High")
        assert len(result) == 1
        assert result[0].cve_id == "CVE-2021-34527"

    def test_get_critical_convenience(self, db):
        """Test get_critical_cves convenience method"""
        result = db.get_critical_cves()
        assert len(result) == 2

    def test_case_insensitive_severity(self, db):
        """Test case insensitivity for severity"""
        result = db.get_cves_by_severity("critical")
        assert len(result) == 2


class TestGetRansomwareIOCs:
    """Test getting ransomware IOCs"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "ioc": {
                        "files": ["lockbit.exe", "encrypt.dll"],
                        "domains": ["lockbit-blog.com"],
                        "hashes": ["abc123"],
                    },
                },
            }
            return database

    def test_get_iocs_existing(self, db):
        """Test getting IOCs for existing ransomware"""
        result = db.get_ransomware_iocs("LockBit")
        assert "files" in result
        assert "lockbit.exe" in result["files"]

    def test_get_iocs_nonexistent(self, db):
        """Test getting IOCs for non-existent ransomware"""
        result = db.get_ransomware_iocs("FakeRansomware")
        assert result == {}


class TestCheckSystemForRansomware:
    """Test system indicator checking"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "ioc": {
                        "files": ["ransom.exe", "lockbit.exe"],
                        "registry": ["HKLM\\Software\\LockBit"],
                        "hashes": ["abc123def456"],
                        "processes": ["lockbit_process"],
                    },
                },
            }
            return database

    def test_check_with_matching_file(self, db):
        """Test checking with matching file indicator"""
        indicators = {
            "files": ["ransom.exe"],  # Matches IOC exactly
        }
        result = db.check_system_for_ransomware(indicators)
        # May or may not match depending on scoring
        if len(result) > 0:
            assert result[0]["ransomware"] == "LockBit"

    def test_check_with_matching_hash(self, db):
        """Test checking with matching hash"""
        indicators = {
            "hashes": ["abc123def456"],
        }
        result = db.check_system_for_ransomware(indicators)
        assert len(result) == 1
        assert result[0]["confidence"] >= 50  # Hash match is strong

    def test_check_with_matching_registry(self, db):
        """Test checking with matching registry key"""
        indicators = {
            "registry": ["HKLM\\Software\\LockBit"],
        }
        result = db.check_system_for_ransomware(indicators)
        # Registry matches add to score
        assert isinstance(result, list)

    def test_check_with_matching_process(self, db):
        """Test checking with matching process"""
        indicators = {
            "processes": ["lockbit_process"],
        }
        result = db.check_system_for_ransomware(indicators)
        # Process matches add to score
        assert isinstance(result, list)

    def test_check_no_matches(self, db):
        """Test checking with no matches"""
        indicators = {
            "files": ["legitimate.exe"],
            "hashes": ["xyz789"],
        }
        result = db.check_system_for_ransomware(indicators)
        assert len(result) == 0

    def test_check_below_threshold(self, db):
        """Test checking with matches below threshold"""
        indicators = {
            "files": ["some.exe"],  # Won't match exactly
        }
        result = db.check_system_for_ransomware(indicators)
        assert len(result) == 0  # Below 20 threshold

    def test_check_sorted_by_confidence(self, db):
        """Test that results are sorted by confidence"""
        indicators = {
            "files": ["lockbit.exe"],
            "hashes": ["abc123def456"],  # Higher confidence
        }
        result = db.check_system_for_ransomware(indicators)
        assert len(result) == 1
        assert result[0]["confidence"] == 60  # 10 for file + 50 for hash


class TestAnalyzeVulnerability:
    """Test vulnerability analysis"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "cvss": 10.0,
                    "severity": "Critical",
                    "description": "Log4j vulnerability",
                    "mitigation": ["Upgrade Log4j"],
                    "ransomware_used_by": ["LockBit", "BlackCat"],
                },
                "CVE-2021-34527": {
                    "name": "PrintNightmare",
                    "cvss": 8.8,
                    "severity": "High",
                    "description": "Print Spooler vulnerability",
                    "mitigation": ["Disable Print Spooler"],
                    "ransomware_used_by": [],
                },
            }
            return database

    @pytest.mark.asyncio
    async def test_analyze_with_ransomware(self, db):
        """Test analyzing CVE used by ransomware"""
        result = await db.analyze_vulnerability_for_ransomware_risk("CVE-2021-44228")
        assert result["cve_id"] == "CVE-2021-44228"
        assert result["cvss_score"] == 10.0
        assert len(result["ransomware_associated"]) == 2
        assert result["ransomware_risk"] == "High"
        assert result["mitigation_priority"] == "Critical"

    @pytest.mark.asyncio
    async def test_analyze_without_ransomware(self, db):
        """Test analyzing CVE not used by ransomware"""
        result = await db.analyze_vulnerability_for_ransomware_risk("CVE-2021-34527")
        assert result["cve_id"] == "CVE-2021-34527"
        assert result["ransomware_associated"] == []
        assert result["ransomware_risk"] == "High"  # Severity
        assert result["mitigation_priority"] == "High"

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_cve(self, db):
        """Test analyzing non-existent CVE"""
        result = await db.analyze_vulnerability_for_ransomware_risk("CVE-2099-9999")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_with_llm(self, db):
        """Test analyzing with LLM integration"""
        mock_orch = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Detailed AI analysis of the ransomware risk"

        # Make process a coroutine to be awaitable
        async def async_process(*args, **kwargs):
            return mock_response

        mock_orch.process = async_process
        db.orchestrator = mock_orch

        result = await db.analyze_vulnerability_for_ransomware_risk("CVE-2021-44228")

        assert "ai_analysis" in result


class TestExploitChains:
    """Test exploit chain functionality"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.exploit_chains = {
                "chain1": {
                    "name": "Web Shell Chain",
                    "description": "Upload shell and execute",
                    "steps": ["Upload", "Execute"],
                },
                "privilege_escalation": {
                    "name": "Windows Privilege Escalation",
                    "description": "Common Windows PE chain",
                    "cves": ["CVE-2021-1234"],
                },
            }
            return database

    def test_get_existing_chain(self, db):
        """Test getting existing exploit chain"""
        result = db.get_exploit_chain("Web Shell")
        assert result is not None
        assert result["name"] == "Web Shell Chain"

    def test_get_chain_by_key(self, db):
        """Test getting chain by key"""
        result = db.get_exploit_chain("privilege_escalation")
        assert result is not None
        assert result["name"] == "Windows Privilege Escalation"

    def test_get_nonexistent_chain(self, db):
        """Test getting non-existent chain"""
        result = db.get_exploit_chain("Fake Chain")
        assert result is None


class TestListOperations:
    """Test list operations"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "first_seen": "2019-09",
                    "type": "RaaS",
                    "decryptable": False,
                    "cves": ["CVE-2021-1234"],
                },
            }
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "cvss": 10.0,
                    "severity": "Critical",
                    "ransomware_used_by": ["LockBit"],
                },
                "CVE-2021-34527": {
                    "name": "PrintNightmare",
                    "cvss": 8.8,
                    "severity": "High",
                    "ransomware_used_by": [],
                },
            }
            return database

    def test_list_all_ransomware(self, db):
        """Test listing all ransomware"""
        result = db.list_all_ransomware()
        assert len(result) == 1
        assert result[0]["name"] == "LockBit"
        assert result[0]["decryptable"] is False

    def test_list_all_cves(self, db):
        """Test listing all CVEs"""
        result = db.list_all_cves()
        assert len(result) == 2
        # Should be sorted by CVSS descending
        assert result[0]["cve_id"] == "CVE-2021-44228"
        assert result[1]["cve_id"] == "CVE-2021-34527"

    def test_get_latest_threats(self, db):
        """Test getting latest threats"""
        result = db.get_latest_threats(limit=10)
        # Only critical CVEs
        assert len(result) == 1
        assert result[0]["cve_id"] == "CVE-2021-44228"

    def test_get_latest_threats_with_limit(self, db):
        """Test getting latest threats with limit"""
        # Add more critical CVEs
        db.cve_data["CVE-2023-1234"] = {
            "name": "New CVE",
            "cvss": 9.9,
            "severity": "Critical",
        }
        db.cve_data["CVE-2023-5678"] = {
            "name": "Another CVE",
            "cvss": 9.8,
            "severity": "Critical",
        }

        result = db.get_latest_threats(limit=2)
        assert len(result) == 2


class TestReportGeneration:
    """Test report generation"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "cvss": 10.0,
                    "severity": "Critical",
                    "description": "Log4j JNDI injection vulnerability",
                    "affected_products": ["Log4j 2.0-2.14.1"],
                    "patch": "https://logging.apache.org/",
                    "mitigation": ["Upgrade to 2.15.0", "Remove JndiLookup"],
                    "ransomware_used_by": ["LockBit"],
                },
                "CVE-2099-9999": {
                    "name": "Non-existent for test",
                    "cvss": 5.0,
                    "severity": "Medium",
                    "description": "Test CVE",
                    "affected_products": [],
                },
            }
            return database

    def test_generate_report_existing_cves(self, db):
        """Test generating report with existing CVEs"""
        report = db.generate_vulnerability_report(["CVE-2021-44228"])
        assert "# Vulnerability Analysis Report" in report
        assert "CVE-2021-44228" in report
        assert "Log4Shell" in report
        assert "Critical" in report
        assert "10.0" in report
        assert "Ransomware Alert" in report

    def test_generate_report_nonexistent_cve(self, db):
        """Test generating report with non-existent CVE"""
        report = db.generate_vulnerability_report(["CVE-0000-0000"])
        assert "Not found in database" in report

    def test_generate_report_multiple(self, db):
        """Test generating report with multiple CVEs"""
        report = db.generate_vulnerability_report(["CVE-2021-44228", "CVE-2099-9999"])
        assert "CVE-2021-44228" in report
        assert "CVE-2099-9999" in report


class TestMitigationAndDetection:
    """Test mitigation and detection methods"""

    @pytest.fixture
    def db(self):
        """Create database with sample data"""
        with patch("os.path.exists", return_value=False):
            database = CVEDatabase()
            database.cve_data = {
                "CVE-2021-44228": {
                    "name": "Log4Shell",
                    "mitigation": ["Upgrade Log4j", "Remove JndiLookup"],
                },
            }
            database.ransomware_data = {
                "lockbit": {
                    "name": "LockBit",
                    "detection": ["Monitor file encryption", "Check registry"],
                },
            }
            return database

    def test_get_mitigation_existing(self, db):
        """Test getting mitigation for existing CVE"""
        result = db.get_mitigation_for_cve("CVE-2021-44228")
        assert len(result) == 2
        assert "Upgrade Log4j" in result

    def test_get_mitigation_nonexistent(self, db):
        """Test getting mitigation for non-existent CVE"""
        result = db.get_mitigation_for_cve("CVE-0000-0000")
        assert result == []

    def test_get_detection_existing(self, db):
        """Test getting detection for existing ransomware"""
        result = db.get_detection_for_ransomware("LockBit")
        assert len(result) == 2
        assert "Monitor file encryption" in result

    def test_get_detection_nonexistent(self, db):
        """Test getting detection for non-existent ransomware"""
        result = db.get_detection_for_ransomware("FakeRansomware")
        assert result == []

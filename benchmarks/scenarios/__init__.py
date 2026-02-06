"""
Zen-AI-Pentest Benchmark Scenarios

Pre-defined test scenarios for security testing benchmarks.
Each scenario represents a specific vulnerable application or challenge.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class ScenarioType(Enum):
    """Types of security test scenarios."""

    WEB_APP = "web_app"
    NETWORK = "network"
    CLOUD = "cloud"
    CONTAINER = "container"
    MOBILE = "mobile"
    API = "api"
    CTF = "ctf"


class DifficultyLevel(Enum):
    """Difficulty levels for scenarios."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class VulnerabilityProfile:
    """Expected vulnerabilities in a scenario."""

    vuln_type: str
    severity: str
    location: str
    cwe_id: Optional[str] = None
    exploit_available: bool = True
    verification_method: str = ""


@dataclass
class TestScenario:
    """Base class for test scenarios."""

    # Identification
    id: str
    name: str
    description: str
    scenario_type: ScenarioType
    difficulty: DifficultyLevel

    # Configuration
    target_url: Optional[str] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    credentials: Optional[Dict[str, str]] = None

    # Vulnerabilities
    expected_vulnerabilities: List[VulnerabilityProfile] = field(default_factory=list)
    known_false_positives: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    category: str = ""
    estimated_duration_minutes: int = 30
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

    # Setup
    setup_commands: List[str] = field(default_factory=list)
    teardown_commands: List[str] = field(default_factory=list)
    docker_compose_file: Optional[str] = None

    # Validation
    health_check_endpoint: Optional[str] = None
    success_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.scenario_type.value,
            "difficulty": self.difficulty.value,
            "target_url": self.target_url,
            "target_host": self.target_host,
            "target_port": self.target_port,
            "tags": self.tags,
            "category": self.category,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "expected_vulnerabilities_count": len(self.expected_vulnerabilities),
            "expected_vulnerabilities": [
                {
                    "type": v.vuln_type,
                    "severity": v.severity,
                    "location": v.location,
                    "cwe_id": v.cwe_id,
                    "exploit_available": v.exploit_available,
                }
                for v in self.expected_vulnerabilities
            ],
        }


# =============================================================================
# OWASP JUICE SHOP
# =============================================================================

OWASP_JUICE_SHOP = TestScenario(
    id="juice-shop",
    name="OWASP Juice Shop",
    description="Modern insecure web application for security training and benchmarks",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.MEDIUM,
    target_url="http://localhost:3000",
    target_port=3000,
    health_check_endpoint="http://localhost:3000/api/Products/",
    tags=["owasp", "web", "modern", "javascript", "angular"],
    category="Training Applications",
    estimated_duration_minutes=60,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="sql_injection",
            severity="critical",
            location="/rest/products/search",
            cwe_id="CWE-89",
            verification_method="sqlmap",
        ),
        VulnerabilityProfile(
            vuln_type="xss", severity="high", location="/api/Products/", cwe_id="CWE-79", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="authentication_bypass",
            severity="critical",
            location="/rest/user/login",
            cwe_id="CWE-287",
            verification_method="api_test",
        ),
        VulnerabilityProfile(
            vuln_type="insecure_deserialization",
            severity="critical",
            location="/api/Products/",
            cwe_id="CWE-502",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="sensitive_data_exposure",
            severity="high",
            location="/ftp/",
            cwe_id="CWE-200",
            verification_method="access_test",
        ),
        VulnerabilityProfile(
            vuln_type="access_control",
            severity="high",
            location="/rest/basket",
            cwe_id="CWE-639",
            verification_method="api_test",
        ),
        VulnerabilityProfile(
            vuln_type="xxe", severity="critical", location="/api/Products/", cwe_id="CWE-611", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="idor", severity="high", location="/rest/track-order", cwe_id="CWE-639", verification_method="api_test"
        ),
        VulnerabilityProfile(
            vuln_type="command_injection", severity="critical", location="/ftp/", cwe_id="CWE-78", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="unsafe_mass_assignment",
            severity="medium",
            location="/api/Users/",
            cwe_id="CWE-915",
            verification_method="api_test",
        ),
    ],
    docker_compose_file="""
version: '3'
services:
  juice-shop:
    image: bkimminich/juice-shop:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=ctf
""",
    setup_commands=["docker pull bkimminich/juice-shop:latest"],
)


# =============================================================================
# DVWA (Damn Vulnerable Web Application)
# =============================================================================

DVWA_SCENARIO = TestScenario(
    id="dvwa",
    name="DVWA",
    description="PHP/MySQL web application with deliberate vulnerabilities",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.EASY,
    target_url="http://localhost:8080",
    target_port=8080,
    credentials={"username": "admin", "password": "password"},
    health_check_endpoint="http://localhost:8080/login.php",
    tags=["dvwa", "php", "mysql", "classic", "training"],
    category="Training Applications",
    estimated_duration_minutes=45,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="sql_injection",
            severity="high",
            location="/vulnerabilities/sqli/",
            cwe_id="CWE-89",
            verification_method="sqlmap",
        ),
        VulnerabilityProfile(
            vuln_type="blind_sql_injection",
            severity="high",
            location="/vulnerabilities/sqli_blind/",
            cwe_id="CWE-89",
            verification_method="sqlmap",
        ),
        VulnerabilityProfile(
            vuln_type="command_injection",
            severity="high",
            location="/vulnerabilities/exec/",
            cwe_id="CWE-78",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="xss_reflected",
            severity="medium",
            location="/vulnerabilities/xss_r/",
            cwe_id="CWE-79",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="xss_stored",
            severity="medium",
            location="/vulnerabilities/xss_s/",
            cwe_id="CWE-79",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="csrf",
            severity="medium",
            location="/vulnerabilities/csrf/",
            cwe_id="CWE-352",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="file_inclusion",
            severity="high",
            location="/vulnerabilities/fi/",
            cwe_id="CWE-98",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="file_upload",
            severity="high",
            location="/vulnerabilities/upload/",
            cwe_id="CWE-434",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="insecure_captcha",
            severity="low",
            location="/vulnerabilities/captcha/",
            cwe_id="CWE-804",
            verification_method="api_test",
        ),
        VulnerabilityProfile(
            vuln_type="weak_session",
            severity="medium",
            location="/vulnerabilities/weak_id/",
            cwe_id="CWE-330",
            verification_method="analysis",
        ),
    ],
    docker_compose_file="""
version: '3'
services:
  dvwa:
    image: vulnerables/web-dvwa:latest
    ports:
      - "8080:80"
    environment:
      - MYSQL_PASS=dvwa
""",
    setup_commands=["docker pull vulnerables/web-dvwa:latest"],
)


# =============================================================================
# METASPLOITABLE 2
# =============================================================================

METASPLOITABLE2_SCENARIO = TestScenario(
    id="metasploitable2",
    name="Metasploitable 2",
    description="Intentionally vulnerable Ubuntu VM for penetration testing practice",
    scenario_type=ScenarioType.NETWORK,
    difficulty=DifficultyLevel.MEDIUM,
    target_host="192.168.56.101",
    credentials={"msfadmin": "msfadmin", "postgres": "postgres", "user": "user", "service": "service"},
    tags=["metasploitable", "network", "vm", "multi-service"],
    category="Vulnerable VMs",
    estimated_duration_minutes=90,
    resource_requirements={"vm_memory_mb": 512, "vm_disk_gb": 8, "network": "host-only"},
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="vsftpd_backdoor",
            severity="critical",
            location="port 21",
            cwe_id="CWE-78",
            verification_method="metasploit",
        ),
        VulnerabilityProfile(
            vuln_type="ssh_weak_credentials",
            severity="critical",
            location="port 22",
            cwe_id="CWE-798",
            verification_method="hydra",
        ),
        VulnerabilityProfile(
            vuln_type="telnet_plaintext",
            severity="high",
            location="port 23",
            cwe_id="CWE-319",
            verification_method="access_test",
        ),
        VulnerabilityProfile(
            vuln_type="smtp_user_enum",
            severity="medium",
            location="port 25",
            cwe_id="CWE-200",
            verification_method="smtp_user_enum",
        ),
        VulnerabilityProfile(
            vuln_type="distcc_command_execution",
            severity="critical",
            location="port 3632",
            cwe_id="CWE-78",
            verification_method="metasploit",
        ),
        VulnerabilityProfile(
            vuln_type="mysql_weak_auth",
            severity="critical",
            location="port 3306",
            cwe_id="CWE-798",
            verification_method="mysql_client",
        ),
        VulnerabilityProfile(
            vuln_type="postgresql_weak_auth",
            severity="critical",
            location="port 5432",
            cwe_id="CWE-798",
            verification_method="psql",
        ),
        VulnerabilityProfile(
            vuln_type="vnc_weak_auth",
            severity="critical",
            location="port 5900",
            cwe_id="CWE-798",
            verification_method="vnc_viewer",
        ),
        VulnerabilityProfile(
            vuln_type="nfs_exports", severity="high", location="port 2049", cwe_id="CWE-276", verification_method="showmount"
        ),
        VulnerabilityProfile(
            vuln_type="unreal_irc_backdoor",
            severity="critical",
            location="port 6667",
            cwe_id="CWE-78",
            verification_method="metasploit",
        ),
    ],
)


# =============================================================================
# METASPLOITABLE 3
# =============================================================================

METASPLOITABLE3_SCENARIO = TestScenario(
    id="metasploitable3",
    name="Metasploitable 3",
    description="Modern vulnerable VM with Windows and Linux versions",
    scenario_type=ScenarioType.NETWORK,
    difficulty=DifficultyLevel.HARD,
    target_host="192.168.56.102",
    credentials={"vagrant": "vagrant", "administrator": "vagrant"},
    tags=["metasploitable", "windows", "modern", "active-directory"],
    category="Vulnerable VMs",
    estimated_duration_minutes=120,
    resource_requirements={"vm_memory_mb": 2048, "vm_disk_gb": 20, "network": "host-only"},
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="elasticsearch_rce",
            severity="critical",
            location="port 9200",
            cwe_id="CWE-94",
            verification_method="metasploit",
        ),
        VulnerabilityProfile(
            vuln_type="apache_couchdb_rce",
            severity="critical",
            location="port 5984",
            cwe_id="CWE-78",
            verification_method="metasploit",
        ),
        VulnerabilityProfile(
            vuln_type="windows_smb_ms17_010",
            severity="critical",
            location="port 445",
            cwe_id="CWE-200",
            verification_method="metasploit",
        ),
        VulnerabilityProfile(
            vuln_type="jenkins_groovy_rce",
            severity="critical",
            location="port 8484",
            cwe_id="CWE-94",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="wordpress_plugin_rce",
            severity="high",
            location="port 8585",
            cwe_id="CWE-94",
            verification_method="wpscan",
        ),
        VulnerabilityProfile(
            vuln_type="phpmyadmin_auth_bypass",
            severity="high",
            location="port 8585/phpmyadmin",
            cwe_id="CWE-287",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="tomcat_manager_weak",
            severity="high",
            location="port 8282",
            cwe_id="CWE-798",
            verification_method="bruteforce",
        ),
        VulnerabilityProfile(
            vuln_type="solr_rce", severity="critical", location="port 8983", cwe_id="CWE-78", verification_method="metasploit"
        ),
    ],
)


# =============================================================================
# WEBGOAT
# =============================================================================

WEBGOAT_SCENARIO = TestScenario(
    id="webgoat",
    name="OWASP WebGoat",
    description="Deliberately insecure web application maintained by OWASP",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.EASY,
    target_url="http://localhost:8080/WebGoat",
    target_port=8080,
    credentials={"username": "guest", "password": "guest"},
    health_check_endpoint="http://localhost:8080/WebGoat/login",
    tags=["owasp", "java", "spring", "educational"],
    category="Training Applications",
    estimated_duration_minutes=120,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="sql_injection",
            severity="high",
            location="/SqlInjection/",
            cwe_id="CWE-89",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="sql_injection_advanced",
            severity="high",
            location="/SqlInjectionAdvanced/",
            cwe_id="CWE-89",
            verification_method="sqlmap",
        ),
        VulnerabilityProfile(
            vuln_type="xss", severity="medium", location="/CrossSiteScripting/", cwe_id="CWE-79", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="insecure_deserialization",
            severity="critical",
            location="/InsecureDeserialization/",
            cwe_id="CWE-502",
            verification_method="ysoserial",
        ),
        VulnerabilityProfile(
            vuln_type="vulnerable_components",
            severity="high",
            location="/VulnerableComponents/",
            cwe_id="CWE-1035",
            verification_method="dependency_check",
        ),
        VulnerabilityProfile(
            vuln_type="xxe", severity="critical", location="/XXE/", cwe_id="CWE-611", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="auth_bypass", severity="high", location="/AuthBypass/", cwe_id="CWE-287", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="csrf", severity="medium", location="/CSRF/", cwe_id="CWE-352", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="idor", severity="medium", location="/IDOR/", cwe_id="CWE-639", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="jwt_tokens", severity="high", location="/JWT/", cwe_id="CWE-345", verification_method="jwt_tool"
        ),
        VulnerabilityProfile(
            vuln_type="client_side_filtering",
            severity="low",
            location="/ClientSideFiltering/",
            cwe_id="CWE-200",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="html_tampering",
            severity="low",
            location="/HtmlTampering/",
            cwe_id="CWE-472",
            verification_method="manual",
        ),
    ],
    docker_compose_file="""
version: '3'
services:
  webgoat:
    image: webgoat/webgoat:latest
    ports:
      - "8080:8080"
      - "9090:9090"
    environment:
      - WEBGOAT_PORT=8080
      - WEBWOLF_PORT=9090
""",
)


# =============================================================================
# HACKTHEBOX CHALLENGES
# =============================================================================

HTB_STARTING_POINT_TIER1 = TestScenario(
    id="htb-starting-point-t1",
    name="HTB Starting Point Tier 1",
    description="HackTheBox beginner-friendly machines",
    scenario_type=ScenarioType.CTF,
    difficulty=DifficultyLevel.EASY,
    target_host="10.10.10.x",
    tags=["htb", "ctf", "beginner", "learning"],
    category="CTF Platforms",
    estimated_duration_minutes=60,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="anonymous_ftp",
            severity="medium",
            location="port 21",
            cwe_id="CWE-276",
            verification_method="ftp_client",
        ),
        VulnerabilityProfile(
            vuln_type="smb_null_session",
            severity="medium",
            location="port 445",
            cwe_id="CWE-287",
            verification_method="smbclient",
        ),
        VulnerabilityProfile(
            vuln_type="outdated_software",
            severity="high",
            location="various",
            cwe_id="CWE-1104",
            verification_method="vulnerability_scan",
        ),
        VulnerabilityProfile(
            vuln_type="default_credentials",
            severity="critical",
            location="web/services",
            cwe_id="CWE-798",
            verification_method="manual",
        ),
    ],
)

HTB_WEB_CHALLENGES = TestScenario(
    id="htb-web-challenges",
    name="HTB Web Challenges",
    description="HackTheBox web-focused challenges",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.MEDIUM,
    target_url="https://app.hackthebox.com/challenges",
    tags=["htb", "web", "ctf", "challenges"],
    category="CTF Platforms",
    estimated_duration_minutes=45,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="sqli", severity="high", location="webapp", cwe_id="CWE-89", verification_method="sqlmap"
        ),
        VulnerabilityProfile(
            vuln_type="ssti", severity="critical", location="template_engine", cwe_id="CWE-1336", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="lfi_rfi", severity="high", location="file_inclusion", cwe_id="CWE-98", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="type_juggling", severity="medium", location="php_auth", cwe_id="CWE-843", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="serialization",
            severity="critical",
            location="php/python/java",
            cwe_id="CWE-502",
            verification_method="manual",
        ),
    ],
)


# =============================================================================
# TRYHACKME ROOMS
# =============================================================================

THM_OWASP_TOP10 = TestScenario(
    id="thm-owasp-top10",
    name="TryHackMe OWASP Top 10",
    description="Room covering OWASP Top 10 vulnerabilities",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.EASY,
    target_url="https://tryhackme.com/room/owasptop10",
    tags=["thm", "owasp", "web", "educational"],
    category="Learning Platforms",
    estimated_duration_minutes=90,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="command_injection",
            severity="critical",
            location="ping_test",
            cwe_id="CWE-78",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="broken_authentication",
            severity="critical",
            location="login",
            cwe_id="CWE-287",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="sensitive_data_exposure",
            severity="high",
            location="db_files",
            cwe_id="CWE-200",
            verification_method="access_test",
        ),
        VulnerabilityProfile(
            vuln_type="xxe", severity="critical", location="xml_parser", cwe_id="CWE-611", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="broken_access_control",
            severity="high",
            location="admin_panel",
            cwe_id="CWE-639",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="xss", severity="medium", location="comment_form", cwe_id="CWE-79", verification_method="manual"
        ),
        VulnerabilityProfile(
            vuln_type="insecure_deserialization",
            severity="critical",
            location="cookie",
            cwe_id="CWE-502",
            verification_method="ysoserial",
        ),
        VulnerabilityProfile(
            vuln_type="known_vulnerabilities",
            severity="high",
            location="outdated_software",
            cwe_id="CWE-1035",
            verification_method="vulnerability_scan",
        ),
        VulnerabilityProfile(
            vuln_type="insufficient_logging",
            severity="medium",
            location="application",
            cwe_id="CWE-778",
            verification_method="analysis",
        ),
        VulnerabilityProfile(
            vuln_type="ssrf", severity="critical", location="url_fetcher", cwe_id="CWE-918", verification_method="manual"
        ),
    ],
)

THM_ROOTME = TestScenario(
    id="thm-rootme",
    name="TryHackMe RootMe",
    description="CTF challenge for beginners",
    scenario_type=ScenarioType.CTF,
    difficulty=DifficultyLevel.EASY,
    target_host="10.10.10.x",
    tags=["thm", "ctf", "beginner", "privilege-escalation"],
    category="Learning Platforms",
    estimated_duration_minutes=45,
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="hidden_directory", severity="info", location="web_root", verification_method="gobuster"
        ),
        VulnerabilityProfile(
            vuln_type="file_upload_bypass",
            severity="critical",
            location="upload",
            cwe_id="CWE-434",
            verification_method="manual",
        ),
        VulnerabilityProfile(
            vuln_type="suid_binary",
            severity="high",
            location="/usr/bin/python",
            cwe_id="CWE-250",
            verification_method="manual",
        ),
    ],
)


# =============================================================================
# SCENARIO REGISTRY
# =============================================================================

ALL_SCENARIOS: Dict[str, TestScenario] = {
    # Training Applications
    "juice-shop": OWASP_JUICE_SHOP,
    "dvwa": DVWA_SCENARIO,
    "webgoat": WEBGOAT_SCENARIO,
    # Vulnerable VMs
    "metasploitable2": METASPLOITABLE2_SCENARIO,
    "metasploitable3": METASPLOITABLE3_SCENARIO,
    # CTF Platforms
    "htb-starting-point": HTB_STARTING_POINT_TIER1,
    "htb-web-challenges": HTB_WEB_CHALLENGES,
    "thm-owasp-top10": THM_OWASP_TOP10,
    "thm-rootme": THM_ROOTME,
}


def get_scenario(scenario_id: str) -> Optional[TestScenario]:
    """Get a scenario by ID."""
    return ALL_SCENARIOS.get(scenario_id)


def get_scenarios_by_type(scenario_type: ScenarioType) -> List[TestScenario]:
    """Get all scenarios of a specific type."""
    return [s for s in ALL_SCENARIOS.values() if s.scenario_type == scenario_type]


def get_scenarios_by_difficulty(difficulty: DifficultyLevel) -> List[TestScenario]:
    """Get all scenarios of a specific difficulty."""
    return [s for s in ALL_SCENARIOS.values() if s.difficulty == difficulty]


def get_scenarios_by_tag(tag: str) -> List[TestScenario]:
    """Get all scenarios with a specific tag."""
    return [s for s in ALL_SCENARIOS.values() if tag in s.tags]


def list_all_scenarios() -> List[Dict[str, Any]]:
    """List all available scenarios with summary info."""
    return [s.to_dict() for s in ALL_SCENARIOS.values()]


def create_benchmark_suite(
    difficulty: Optional[DifficultyLevel] = None,
    scenario_type: Optional[ScenarioType] = None,
    tags: Optional[List[str]] = None,
    max_duration_minutes: Optional[int] = None,
) -> List[TestScenario]:
    """Create a benchmark suite based on filters."""
    scenarios = list(ALL_SCENARIOS.values())

    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty]

    if scenario_type:
        scenarios = [s for s in scenarios if s.scenario_type == scenario_type]

    if tags:
        scenarios = [s for s in scenarios if any(tag in s.tags for tag in tags)]

    if max_duration_minutes:
        scenarios = [s for s in scenarios if s.estimated_duration_minutes <= max_duration_minutes]

    return scenarios

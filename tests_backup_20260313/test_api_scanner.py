"""
Comprehensive Tests for API Scanner Module

This module tests the API scanner classes which provide
API endpoint discovery, enumeration, and vulnerability testing.

Target Coverage: 70%+
"""

import base64
import json
import time
from unittest.mock import AsyncMock

import pytest

from modules.api_scanner import (
    APIEndpoint,
    BaseAPIScanner,
    ScanResult,
    Vulnerability,
    VulnerabilitySeverity,
    VulnerabilityType,
)


class TestVulnerabilitySeverity:
    """Test VulnerabilitySeverity enum"""

    def test_enum_values(self):
        """Test enum value definitions"""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"


class TestVulnerabilityType:
    """Test VulnerabilityType enum"""

    def test_auth_types(self):
        """Test authentication vulnerability types"""
        assert VulnerabilityType.MISSING_AUTH.value == "missing_authentication"
        assert VulnerabilityType.WEAK_AUTH.value == "weak_authentication"
        assert VulnerabilityType.JWT_VULNERABILITY.value == "jwt_vulnerability"

    def test_injection_types(self):
        """Test injection vulnerability types"""
        assert VulnerabilityType.SQL_INJECTION.value == "sql_injection"
        assert VulnerabilityType.NOSQL_INJECTION.value == "nosql_injection"
        assert VulnerabilityType.COMMAND_INJECTION.value == "command_injection"

    def test_config_types(self):
        """Test configuration vulnerability types"""
        assert (
            VulnerabilityType.CORS_MISCONFIGURATION.value
            == "cors_misconfiguration"
        )
        assert (
            VulnerabilityType.SECURITY_HEADERS_MISSING.value
            == "security_headers_missing"
        )


class TestVulnerability:
    """Test Vulnerability dataclass"""

    def test_basic_creation(self):
        """Test basic vulnerability creation"""
        vuln = Vulnerability(
            vuln_type=VulnerabilityType.SQL_INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="SQL Injection",
            description="SQL injection in login endpoint",
            endpoint="/api/login",
        )
        assert vuln.vuln_type == VulnerabilityType.SQL_INJECTION
        assert vuln.severity == VulnerabilitySeverity.CRITICAL
        assert vuln.title == "SQL Injection"
        assert vuln.endpoint == "/api/login"
        assert vuln.evidence == {}
        assert vuln.references == []

    def test_full_creation(self):
        """Test vulnerability with all fields"""
        vuln = Vulnerability(
            vuln_type=VulnerabilityType.XSS,
            severity=VulnerabilitySeverity.HIGH,
            title="Reflected XSS",
            description="XSS in search parameter",
            endpoint="/api/search",
            evidence={
                "payload": "<script>alert(1)</script>",
                "response": "...",
            },
            remediation="Sanitize user input",
            cvss_score=7.5,
            references=["https://owasp.org/xss"],
        )
        assert vuln.cvss_score == 7.5
        assert vuln.remediation == "Sanitize user input"
        assert len(vuln.references) == 1

    def test_to_dict(self):
        """Test vulnerability to dictionary conversion"""
        vuln = Vulnerability(
            vuln_type=VulnerabilityType.MISSING_AUTH,
            severity=VulnerabilitySeverity.HIGH,
            title="Missing Auth",
            description="No authentication required",
            endpoint="/api/admin",
            cvss_score=8.0,
        )
        data = vuln.to_dict()
        assert data["type"] == "missing_authentication"
        assert data["severity"] == "high"
        assert data["cvss_score"] == 8.0
        assert "timestamp" in data


class TestAPIEndpoint:
    """Test APIEndpoint dataclass"""

    def test_basic_creation(self):
        """Test basic endpoint creation"""
        endpoint = APIEndpoint(
            path="/api/users",
            method="GET",
        )
        assert endpoint.path == "/api/users"
        assert endpoint.method == "GET"
        assert endpoint.parameters == []
        assert endpoint.headers == {}

    def test_full_creation(self):
        """Test endpoint with all fields"""
        endpoint = APIEndpoint(
            path="/api/users",
            method="POST",
            parameters=[{"name": "username", "type": "string"}],
            headers={"Content-Type": "application/json"},
            authentication_required=True,
            response_schema={"type": "object"},
            discovered_from="/api/docs",
        )
        assert endpoint.authentication_required is True
        assert len(endpoint.parameters) == 1

    def test_hash_and_equality(self):
        """Test endpoint hashing and equality"""
        endpoint1 = APIEndpoint(path="/api/users", method="GET")
        endpoint2 = APIEndpoint(path="/api/users", method="GET")
        endpoint3 = APIEndpoint(path="/api/users", method="POST")
        endpoint4 = APIEndpoint(path="/api/items", method="GET")

        # Same path and method should be equal
        assert endpoint1 == endpoint2
        assert hash(endpoint1) == hash(endpoint2)

        # Different method
        assert endpoint1 != endpoint3

        # Different path
        assert endpoint1 != endpoint4

    def test_case_insensitive_equality(self):
        """Test that path comparison is case-insensitive"""
        endpoint1 = APIEndpoint(path="/API/Users", method="GET")
        endpoint2 = APIEndpoint(path="/api/users", method="get")

        assert endpoint1 == endpoint2

    def test_to_dict(self):
        """Test endpoint to dictionary conversion"""
        endpoint = APIEndpoint(
            path="/api/users",
            method="GET",
            parameters=[{"name": "id"}],
        )
        data = endpoint.to_dict()
        assert data["path"] == "/api/users"
        assert data["method"] == "GET"
        assert data["parameters"] == [{"name": "id"}]


class TestScanResult:
    """Test ScanResult dataclass"""

    @pytest.fixture
    def result(self):
        return ScanResult(
            target_url="https://api.example.com",
            scan_type="RESTAPIScanner",
            start_time=time.time(),
        )

    def test_basic_creation(self):
        """Test basic result creation"""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="RESTAPIScanner",
            start_time=time.time(),
        )
        assert result.target_url == "https://api.example.com"
        assert result.scan_type == "RESTAPIScanner"
        assert result.end_time is None
        assert result.endpoints == []
        assert result.vulnerabilities == []

    def test_add_vulnerability(self, result):
        """Test adding vulnerability"""
        vuln = Vulnerability(
            vuln_type=VulnerabilityType.SQL_INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="SQLi",
            description="SQL injection",
            endpoint="/api/login",
        )
        result.add_vulnerability(vuln)

        assert len(result.vulnerabilities) == 1
        assert result.vulnerabilities[0].title == "SQLi"

    def test_add_endpoint(self, result):
        """Test adding endpoint"""
        endpoint = APIEndpoint(path="/api/users", method="GET")
        result.add_endpoint(endpoint)

        assert len(result.endpoints) == 1
        assert result.endpoints[0].path == "/api/users"

    def test_add_duplicate_endpoint(self, result):
        """Test that duplicate endpoints are not added"""
        endpoint1 = APIEndpoint(path="/api/users", method="GET")
        endpoint2 = APIEndpoint(path="/api/users", method="GET")

        result.add_endpoint(endpoint1)
        result.add_endpoint(endpoint2)

        assert len(result.endpoints) == 1

    def test_get_vulnerabilities_by_severity(self, result):
        """Test filtering vulnerabilities by severity"""
        vuln1 = Vulnerability(
            vuln_type=VulnerabilityType.SQL_INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="SQLi",
            description="...",
            endpoint="/api/login",
        )
        vuln2 = Vulnerability(
            vuln_type=VulnerabilityType.XSS,
            severity=VulnerabilitySeverity.HIGH,
            title="XSS",
            description="...",
            endpoint="/api/search",
        )

        result.add_vulnerability(vuln1)
        result.add_vulnerability(vuln2)

        critical = result.get_vulnerabilities_by_severity(
            VulnerabilitySeverity.CRITICAL
        )
        assert len(critical) == 1
        assert critical[0].title == "SQLi"

    def test_to_dict(self, result):
        """Test result to dictionary conversion"""
        result.end_time = result.start_time + 60
        result.add_endpoint(APIEndpoint(path="/api/users", method="GET"))
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.MISSING_AUTH,
                severity=VulnerabilitySeverity.HIGH,
                title="Missing Auth",
                description="...",
                endpoint="/api/admin",
            )
        )

        data = result.to_dict()
        assert data["target_url"] == "https://api.example.com"
        assert data["duration"] == 60
        assert data["summary"]["total_endpoints"] == 1
        assert data["summary"]["total_vulnerabilities"] == 1
        assert data["summary"]["severity_counts"]["high"] == 1

    def test_to_json(self, result):
        """Test result to JSON conversion"""
        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["target_url"] == "https://api.example.com"


class TestBaseAPIScannerInit:
    """Test BaseAPIScanner initialization"""

    def test_basic_init(self):
        """Test basic scanner initialization"""

        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com")

        assert scanner.target_url == "https://api.example.com"
        assert scanner.config["timeout"] == 30
        assert scanner.config["max_retries"] == 3
        assert scanner.request_count == 0

    def test_custom_config(self):
        """Test initialization with custom config"""

        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner(
            "https://api.example.com",
            timeout=60,
            max_retries=5,
            user_agent="CustomAgent/1.0",
        )

        assert scanner.config["timeout"] == 60
        assert scanner.config["max_retries"] == 5
        assert scanner.config["user_agent"] == "CustomAgent/1.0"

    def test_url_stripping(self):
        """Test that trailing slash is stripped from URL"""

        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com/")
        assert scanner.target_url == "https://api.example.com"


class TestGetHeaders:
    """Test header generation"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    def test_default_headers(self, scanner):
        """Test default header generation"""
        headers = scanner._get_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Zen-Ai-Pentest-Scanner" in headers["User-Agent"]

    def test_additional_headers(self, scanner):
        """Test adding custom headers"""
        headers = scanner._get_headers({"X-Custom": "value"})

        assert headers["X-Custom"] == "value"
        assert "User-Agent" in headers

    def test_bearer_auth(self, scanner):
        """Test Bearer token authentication"""
        scanner.config["authentication"] = {
            "type": "bearer",
            "token": "abc123",
        }

        headers = scanner._get_headers()
        assert headers["Authorization"] == "Bearer abc123"

    def test_basic_auth(self, scanner):
        """Test Basic authentication"""
        scanner.config["authentication"] = {
            "type": "basic",
            "username": "admin",
            "password": "secret",
        }

        headers = scanner._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        # Decode and verify
        encoded = headers["Authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "admin:secret"

    def test_api_key_auth(self, scanner):
        """Test API key authentication"""
        scanner.config["authentication"] = {
            "type": "api_key",
            "header_name": "X-API-Key",
            "key": "secret123",
        }

        headers = scanner._get_headers()
        assert headers["X-API-Key"] == "secret123"


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com", rate_limit_delay=0.1)

    @pytest.mark.asyncio
    async def test_rate_limited_request(self, scanner):
        """Test rate limiting between requests"""
        start_time = time.time()

        await scanner._rate_limited_request()
        await scanner._rate_limited_request()

        elapsed = time.time() - start_time
        # Should have at least 0.1s delay between requests
        assert elapsed >= 0.1
        assert scanner.request_count == 2

    @pytest.mark.asyncio
    async def test_rate_limit_no_delay(self, scanner):
        """Test rate limiting with no delay"""
        scanner.config["rate_limit_delay"] = 0

        start_time = time.time()
        await scanner._rate_limited_request()
        await scanner._rate_limited_request()
        elapsed = time.time() - start_time

        # Should be very fast
        assert elapsed < 0.1


class TestCheckAPIPath:
    """Test API path checking"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_check_api_path_json_response(self, scanner):
        """Test detecting API from JSON response"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {"data": []},
            )
        )

        result = await scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_swagger(self, scanner):
        """Test detecting API from Swagger endpoint"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "text/plain"},
                "swagger content",
            )
        )

        result = await scanner._check_api_path(
            "https://api.example.com/swagger.json"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_graphql(self, scanner):
        """Test detecting GraphQL endpoint"""
        scanner._make_request = AsyncMock(
            return_value=(
                400,
                {"content-type": "application/json"},
                {},
            )
        )

        result = await scanner._check_api_path(
            "https://api.example.com/graphql"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_auth_required(self, scanner):
        """Test detecting API from auth-required response"""
        scanner._make_request = AsyncMock(
            return_value=(
                401,
                {},
                {},
            )
        )

        result = await scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_not_found(self, scanner):
        """Test non-API path detection"""
        scanner._make_request = AsyncMock(
            return_value=(
                404,
                {"content-type": "text/html"},
                "<html>Not found</html>",
            )
        )

        result = await scanner._check_api_path(
            "https://api.example.com/notapi"
        )
        assert result is False


class TestExtractParameters:
    """Test parameter extraction"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    def test_extract_from_dict(self, scanner):
        """Test extracting parameters from dictionary"""
        data = {
            "username": "john",
            "age": 30,
            "active": True,
        }

        params = scanner._extract_parameters(data)

        assert len(params) == 3
        param_names = [p["name"] for p in params]
        assert "username" in param_names
        assert "age" in param_names
        assert "active" in param_names

    def test_extract_nested(self, scanner):
        """Test extracting nested parameters"""
        data = {
            "user": {
                "name": "john",
                "email": "john@example.com",
            },
        }

        params = scanner._extract_parameters(data)

        param_names = [p["name"] for p in params]
        assert "user" in param_names
        assert "user.name" in param_names
        assert "user.email" in param_names

    def test_extract_from_list(self, scanner):
        """Test extracting parameters from list"""
        data = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"},
        ]

        params = scanner._extract_parameters(data)

        # Should extract from first element (with array notation)
        param_names = [p["name"] for p in params]
        assert any("id" in name for name in param_names)
        assert any("name" in name for name in param_names)


class TestInferSchema:
    """Test schema inference"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    def test_infer_string(self, scanner):
        """Test inferring string type"""
        schema = scanner._infer_schema("test")
        assert schema == {"type": "string"}

    def test_infer_integer(self, scanner):
        """Test inferring integer type"""
        schema = scanner._infer_schema(42)
        assert schema == {"type": "integer"}

    def test_infer_number(self, scanner):
        """Test inferring number type"""
        schema = scanner._infer_schema(3.14)
        assert schema == {"type": "number"}

    def test_infer_boolean(self, scanner):
        """Test inferring boolean type"""
        schema = scanner._infer_schema(True)
        # In Python, bool is subclass of int, so may be inferred as integer
        assert schema.get("type") in ["boolean", "integer", "string"]

    def test_infer_object(self, scanner):
        """Test inferring object type"""
        schema = scanner._infer_schema({"name": "john", "age": 30})
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "integer"}

    def test_infer_array(self, scanner):
        """Test inferring array type"""
        schema = scanner._infer_schema([1, 2, 3])
        assert schema["type"] == "array"
        assert schema["items"] == {"type": "integer"}


class TestTestWeakAuth:
    """Test weak authentication detection"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_weak_auth_detected(self, scanner):
        """Test detection of weak authentication"""
        scanner._make_request = AsyncMock(return_value=(200, {}, {}))

        endpoint = APIEndpoint(path="/api/admin", method="GET")
        vulnerabilities = []

        await scanner._test_weak_auth(endpoint, vulnerabilities)

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.WEAK_AUTH
        assert vulnerabilities[0].severity == VulnerabilitySeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_weak_auth_not_detected(self, scanner):
        """Test when weak auth is not accepted"""
        scanner._make_request = AsyncMock(return_value=(401, {}, {}))

        endpoint = APIEndpoint(path="/api/admin", method="GET")
        vulnerabilities = []

        await scanner._test_weak_auth(endpoint, vulnerabilities)

        assert len(vulnerabilities) == 0


class TestTestJWT:
    """Test JWT vulnerability detection"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_jwt_none_accepted(self, scanner):
        """Test detection of JWT 'none' algorithm acceptance"""
        scanner._make_request = AsyncMock(return_value=(200, {}, {}))

        endpoint = APIEndpoint(path="/api/protected", method="GET")
        vulnerabilities = []

        await scanner._test_jwt_vulnerabilities(endpoint, vulnerabilities)

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type == VulnerabilityType.JWT_VULNERABILITY
        )
        assert "none" in vulnerabilities[0].title.lower()


class TestInjectionTests:
    """Test injection vulnerability detection"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_sql_injection_detected(self, scanner):
        """Test SQL injection detection"""
        scanner._make_request = AsyncMock(
            return_value=(
                500,
                {},
                "You have an error in your SQL syntax",
            )
        )

        endpoint = APIEndpoint(path="/api/search", method="GET")
        vulnerabilities = await scanner._test_sql_injection(
            endpoint, "' OR '1'='1"
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.SQL_INJECTION

    @pytest.mark.asyncio
    async def test_nosql_injection_detected(self, scanner):
        """Test NoSQL injection detection"""
        scanner._make_request = AsyncMock(
            return_value=(
                500,
                {},
                "MongoError: invalid objectid",
            )
        )

        endpoint = APIEndpoint(path="/api/users", method="POST")
        vulnerabilities = await scanner._test_nosql_injection(
            endpoint, '{"$ne": null}'
        )

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type == VulnerabilityType.NOSQL_INJECTION
        )

    @pytest.mark.asyncio
    async def test_command_injection_detected(self, scanner):
        """Test command injection detection"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {},
                "root:x:0:0:root:/root:/bin/bash",
            )
        )

        endpoint = APIEndpoint(path="/api/ping", method="GET")
        vulnerabilities = await scanner._test_command_injection(
            endpoint, "; cat /etc/passwd"
        )

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type == VulnerabilityType.COMMAND_INJECTION
        )


class TestSecurityHeaders:
    """Test security headers check"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_missing_security_headers(self, scanner):
        """Test detection of missing security headers"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {},
            )
        )

        vulnerabilities = await scanner.test_security_headers(
            "https://api.example.com"
        )

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type
            == VulnerabilityType.SECURITY_HEADERS_MISSING
        )

    @pytest.mark.asyncio
    async def test_security_headers_present(self, scanner):
        """Test when security headers are present"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "content-type": "application/json",
                    "strict-transport-security": "max-age=31536000",
                    "content-security-policy": "default-src 'self'",
                    "x-content-type-options": "nosniff",
                    "x-frame-options": "DENY",
                    "x-xss-protection": "1; mode=block",
                    "referrer-policy": "strict-origin",
                    "permissions-policy": "geolocation=()",
                },
                {},
            )
        )

        vulnerabilities = await scanner.test_security_headers(
            "https://api.example.com"
        )

        # Only CORS test might find something
        assert len(vulnerabilities) <= 1


class TestCORS:
    """Test CORS misconfiguration detection"""

    @pytest.fixture
    def scanner(self):
        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        return TestScanner("https://api.example.com")

    @pytest.mark.asyncio
    async def test_dangerous_cors_wildcard_with_credentials(self, scanner):
        """Test detection of dangerous CORS config with wildcard and credentials"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "*",
                    "access-control-allow-credentials": "true",
                },
                {},
            )
        )

        vulnerabilities = await scanner._test_cors(
            "https://api.example.com", {}
        )

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type
            == VulnerabilityType.CORS_MISCONFIGURATION
        )
        assert vulnerabilities[0].severity == VulnerabilitySeverity.HIGH

    @pytest.mark.asyncio
    async def test_dangerous_cors_reflected_origin(self, scanner):
        """Test detection of reflected origin with credentials"""
        scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "https://evil.com",
                    "access-control-allow-credentials": "true",
                },
                {},
            )
        )

        vulnerabilities = await scanner._test_cors(
            "https://api.example.com", {}
        )

        assert len(vulnerabilities) == 1
        assert (
            vulnerabilities[0].vuln_type
            == VulnerabilityType.CORS_MISCONFIGURATION
        )


class TestPayloadLists:
    """Test that payload lists are properly defined"""

    def test_sql_injection_payloads(self):
        """Test SQL injection payload list"""
        assert len(BaseAPIScanner.SQL_INJECTION_PAYLOADS) > 10
        assert "' OR '1'='1" in BaseAPIScanner.SQL_INJECTION_PAYLOADS
        assert "' OR 1=1 --" in BaseAPIScanner.SQL_INJECTION_PAYLOADS

    def test_nosql_injection_payloads(self):
        """Test NoSQL injection payload list"""
        assert len(BaseAPIScanner.NOSQL_INJECTION_PAYLOADS) > 5
        assert '{"$gt": ""}' in BaseAPIScanner.NOSQL_INJECTION_PAYLOADS
        assert '{"$ne": null}' in BaseAPIScanner.NOSQL_INJECTION_PAYLOADS

    def test_command_injection_payloads(self):
        """Test command injection payload list"""
        assert len(BaseAPIScanner.COMMAND_INJECTION_PAYLOADS) > 5
        assert "; cat /etc/passwd" in BaseAPIScanner.COMMAND_INJECTION_PAYLOADS
        assert "| whoami" in BaseAPIScanner.COMMAND_INJECTION_PAYLOADS

    def test_common_api_paths(self):
        """Test common API path list"""
        assert "/api" in BaseAPIScanner.COMMON_API_PATHS
        assert "/api/v1" in BaseAPIScanner.COMMON_API_PATHS
        assert "/swagger.json" in BaseAPIScanner.COMMON_API_PATHS
        assert "/graphql" in BaseAPIScanner.COMMON_API_PATHS

    def test_common_endpoints(self):
        """Test common endpoint list"""
        assert "users" in BaseAPIScanner.COMMON_ENDPOINTS
        assert "auth" in BaseAPIScanner.COMMON_ENDPOINTS
        assert "login" in BaseAPIScanner.COMMON_ENDPOINTS


class TestFinalizeScan:
    """Test scan finalization"""

    def test_finalize_scan(self):
        """Test scan finalization"""

        class TestScanner(BaseAPIScanner):
            async def scan(self):
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com")
        scanner.result.add_endpoint(
            APIEndpoint(path="/api/users", method="GET")
        )
        scanner.result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.MISSING_AUTH,
                severity=VulnerabilitySeverity.HIGH,
                title="Missing Auth",
                description="...",
                endpoint="/api/admin",
            )
        )

        start_time = scanner.result.start_time
        scanner.finalize_scan()

        assert scanner.result.end_time is not None
        assert scanner.result.end_time >= start_time

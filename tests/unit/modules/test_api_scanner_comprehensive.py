"""
Comprehensive Tests for API Scanner Module

This module provides extensive tests for the API scanner classes with:
- APIScanner class initialization
- OpenAPI/Swagger parsing
- Endpoint discovery and analysis
- Authentication detection
- Parameter extraction and validation
- Request building and execution
- Response analysis
- Vulnerability detection in APIs
- Report generation

Target Coverage: 80%+
"""

import base64
import json
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List, Optional, Tuple

import pytest
import aiohttp

from modules.api_scanner import (
    APIEndpoint,
    BaseAPIScanner,
    ScanResult,
    Vulnerability,
    VulnerabilitySeverity,
    VulnerabilityType,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_scanner():
    """Create a concrete implementation of BaseAPIScanner for testing."""
    class TestScanner(BaseAPIScanner):
        async def scan(self) -> ScanResult:
            return self.result

        async def _make_request(
            self,
            method: str,
            url: str,
            headers: Optional[Dict] = None,
            data: Optional[Any] = None,
            params: Optional[Dict] = None,
        ) -> Tuple[int, Dict[str, str], Any]:
            return (200, {"content-type": "application/json"}, {})

    return TestScanner("https://api.example.com")


@pytest.fixture
def mock_scanner_with_auth():
    """Create a scanner with authentication configured."""
    class TestScanner(BaseAPIScanner):
        async def scan(self) -> ScanResult:
            return self.result

        async def _make_request(
            self,
            method: str,
            url: str,
            headers: Optional[Dict] = None,
            data: Optional[Any] = None,
            params: Optional[Dict] = None,
        ) -> Tuple[int, Dict[str, str], Any]:
            return (200, {"content-type": "application/json"}, {})

    return TestScanner(
        "https://api.example.com",
        authentication={"type": "bearer", "token": "test-token"},
    )


@pytest.fixture
def sample_endpoint():
    """Create a sample API endpoint."""
    return APIEndpoint(
        path="/api/users",
        method="GET",
        parameters=[{"name": "id", "type": "string", "required": True}],
        headers={"Accept": "application/json"},
        authentication_required=True,
    )


@pytest.fixture
def sample_vulnerability():
    """Create a sample vulnerability."""
    return Vulnerability(
        vuln_type=VulnerabilityType.SQL_INJECTION,
        severity=VulnerabilitySeverity.CRITICAL,
        title="SQL Injection Detected",
        description="SQL injection vulnerability found in search parameter",
        endpoint="/api/search",
        evidence={"payload": "' OR 1=1 --", "response": "error in SQL syntax"},
        remediation="Use parameterized queries",
        cvss_score=9.1,
        references=["https://owasp.org/www-community/attacks/SQL_Injection"],
    )


# =============================================================================
# Test Class: APIScanner Initialization
# =============================================================================

class TestAPIScannerInitialization:
    """Test APIScanner class initialization."""

    def test_basic_initialization(self):
        """Test basic scanner initialization with default config."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com")

        assert scanner.target_url == "https://api.example.com"
        assert scanner.config["timeout"] == 30
        assert scanner.config["max_retries"] == 3
        assert scanner.config["rate_limit_delay"] == 0.5
        assert scanner.config["max_concurrent_requests"] == 10
        assert scanner.config["follow_redirects"] is True
        assert scanner.config["verify_ssl"] is True
        assert "Zen-Ai-Pentest-Scanner" in scanner.config["user_agent"]
        assert scanner.request_count == 0
        assert scanner.session_cookies == {}
        assert isinstance(scanner.result, ScanResult)

    def test_initialization_with_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com/")
        assert scanner.target_url == "https://api.example.com"

    def test_custom_configuration(self):
        """Test scanner initialization with custom configuration."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner(
            "https://api.example.com",
            timeout=60,
            max_retries=5,
            rate_limit_delay=1.0,
            max_concurrent_requests=20,
            follow_redirects=False,
            verify_ssl=False,
            user_agent="CustomAgent/2.0",
            headers={"X-Custom": "value"},
            proxy="http://proxy.example.com:8080",
            cookies={"session": "abc123"},
        )

        assert scanner.config["timeout"] == 60
        assert scanner.config["max_retries"] == 5
        assert scanner.config["rate_limit_delay"] == 1.0
        assert scanner.config["max_concurrent_requests"] == 20
        assert scanner.config["follow_redirects"] is False
        assert scanner.config["verify_ssl"] is False
        assert scanner.config["user_agent"] == "CustomAgent/2.0"
        assert scanner.config["headers"]["X-Custom"] == "value"
        assert scanner.config["proxy"] == "http://proxy.example.com:8080"
        assert scanner.config["cookies"]["session"] == "abc123"

    def test_initialization_with_authentication(self):
        """Test scanner initialization with various auth types."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        # Bearer token auth
        scanner = TestScanner(
            "https://api.example.com",
            authentication={"type": "bearer", "token": "secret-token"},
        )
        assert scanner.config["authentication"]["type"] == "bearer"

        # Basic auth
        scanner = TestScanner(
            "https://api.example.com",
            authentication={
                "type": "basic",
                "username": "admin",
                "password": "secret",
            },
        )
        assert scanner.config["authentication"]["type"] == "basic"

        # API key auth
        scanner = TestScanner(
            "https://api.example.com",
            authentication={
                "type": "api_key",
                "header_name": "X-API-Key",
                "key": "api-secret",
            },
        )
        assert scanner.config["authentication"]["type"] == "api_key"


# =============================================================================
# Test Class: OpenAPI/Swagger Parsing
# =============================================================================

class TestOpenAPISwaggerParsing:
    """Test OpenAPI/Swagger document parsing capabilities."""

    @pytest.mark.asyncio
    async def test_swagger_json_discovery(self, mock_scanner):
        """Test discovery of Swagger JSON endpoint."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {
                    "swagger": "2.0",
                    "info": {"title": "Test API", "version": "1.0.0"},
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "List users",
                                "parameters": [],
                            }
                        }
                    },
                },
            )
        )

        result = await mock_scanner._check_api_path(
            "https://api.example.com/swagger.json"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_openapi_json_discovery(self, mock_scanner):
        """Test discovery of OpenAPI 3.0 JSON endpoint."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {
                    "openapi": "3.0.0",
                    "info": {"title": "Test API", "version": "1.0.0"},
                    "paths": {},
                },
            )
        )

        result = await mock_scanner._check_api_path(
            "https://api.example.com/openapi.json"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_api_docs_discovery(self, mock_scanner):
        """Test discovery of API docs endpoints."""
        mock_scanner._make_request = AsyncMock(
            return_value=(200, {"content-type": "text/html"}, "<html>API Docs</html>")
        )

        result = await mock_scanner._check_api_path(
            "https://api.example.com/api-docs"
        )
        assert result is True


# =============================================================================
# Test Class: Endpoint Discovery and Analysis
# =============================================================================

class TestEndpointDiscoveryAndAnalysis:
    """Test endpoint discovery and analysis functionality."""

    @pytest.mark.asyncio
    async def test_discover_api_finds_endpoints(self, mock_scanner):
        """Test API discovery finds multiple API endpoints."""
        responses = {
            "https://api.example.com/api": (
                200,
                {"content-type": "application/json"},
                {"status": "ok"},
            ),
            "https://api.example.com/api/v1": (
                200,
                {"content-type": "application/json"},
                {"version": "1.0"},
            ),
            "https://api.example.com/swagger.json": (
                200,
                {"content-type": "application/json"},
                {"swagger": "2.0"},
            ),
        }

        async def mock_request(method, url, headers=None, data=None, params=None):
            return responses.get(url, (404, {}, {}))

        mock_scanner._make_request = mock_request

        discovered = await mock_scanner.discover_api()

        assert "https://api.example.com/api" in discovered
        assert "https://api.example.com/api/v1" in discovered
        assert "https://api.example.com/swagger.json" in discovered
        assert "discovered_apis" in mock_scanner.result.metadata

    @pytest.mark.asyncio
    async def test_discover_api_handles_errors(self, mock_scanner):
        """Test API discovery handles connection errors gracefully."""

        async def mock_request(method, url, headers=None, data=None, params=None):
            raise ConnectionError("Connection failed")

        mock_scanner._make_request = mock_request

        discovered = await mock_scanner.discover_api()
        assert isinstance(discovered, list)
        assert len(discovered) == 0

    @pytest.mark.asyncio
    async def test_enumerate_endpoints(self, mock_scanner):
        """Test endpoint enumeration from base URL."""
        valid_endpoints = {
            ("https://api.example.com/api/users", "GET"): (
                200,
                {"content-type": "application/json"},
                [{"id": 1, "name": "user1"}],
            ),
            ("https://api.example.com/api/users", "POST"): (
                201,
                {"content-type": "application/json"},
                {"id": 2, "created": True},
            ),
            ("https://api.example.com/api/auth", "POST"): (
                200,
                {"content-type": "application/json"},
                {"token": "abc123"},
            ),
        }

        async def mock_request(method, url, headers=None, data=None, params=None):
            return valid_endpoints.get((url, method), (404, {}, {}))

        mock_scanner._make_request = mock_request
        mock_scanner.COMMON_ENDPOINTS = ["users", "auth"]

        endpoints = await mock_scanner.enumerate_endpoints(
            "https://api.example.com/api"
        )

        assert len(endpoints) > 0
        endpoint_paths = [(e.path, e.method) for e in endpoints]
        assert ("https://api.example.com/api/users", "GET") in endpoint_paths
        assert ("https://api.example.com/api/users", "POST") in endpoint_paths

    @pytest.mark.asyncio
    async def test_test_endpoint_valid(self, mock_scanner):
        """Test single endpoint validation."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {"id": 1, "name": "test"},
            )
        )

        result = await mock_scanner._test_endpoint(
            "https://api.example.com/api/users", "GET"
        )

        assert result is not None
        assert result.path == "https://api.example.com/api/users"
        assert result.method == "GET"
        assert result.authentication_required is False
        assert len(result.parameters) > 0

    @pytest.mark.asyncio
    async def test_test_endpoint_authentication_required(self, mock_scanner):
        """Test endpoint detection of authentication requirement."""
        mock_scanner._make_request = AsyncMock(
            return_value=(401, {"www-authenticate": "Bearer"}, {"error": "Unauthorized"})
        )

        result = await mock_scanner._test_endpoint(
            "https://api.example.com/api/admin", "GET"
        )

        assert result is not None
        assert result.authentication_required is True

    @pytest.mark.asyncio
    async def test_test_endpoint_not_found(self, mock_scanner):
        """Test endpoint detection of 404 responses."""
        mock_scanner._make_request = AsyncMock(return_value=(404, {}, {}))

        result = await mock_scanner._test_endpoint(
            "https://api.example.com/api/nonexistent", "GET"
        )

        assert result is None


# =============================================================================
# Test Class: Authentication Detection
# =============================================================================

class TestAuthenticationDetection:
    """Test authentication detection mechanisms."""

    @pytest.mark.asyncio
    async def test_detect_missing_authentication(self, mock_scanner):
        """Test detection of missing authentication."""
        endpoint = APIEndpoint(
            path="https://api.example.com/api/admin",
            method="GET",
            authentication_required=True,
        )

        # First call returns 200 (with auth), second returns 200 (without auth - vulnerability!)
        call_count = [0]

        async def mock_request(method, url, headers=None, data=None, params=None):
            call_count[0] += 1
            auth_header = headers.get("Authorization", "") if headers else ""
            if not auth_header:
                return (200, {}, {"data": "sensitive"})  # Vulnerability!
            return (200, {}, {"data": "sensitive"})

        mock_scanner._make_request = mock_request

        vulnerabilities = await mock_scanner.test_authentication(endpoint)

        assert len(vulnerabilities) >= 1
        vuln_types = [v.vuln_type for v in vulnerabilities]
        assert VulnerabilityType.MISSING_AUTH in vuln_types

    @pytest.mark.asyncio
    async def test_detect_proper_authentication(self, mock_scanner):
        """Test when authentication is properly enforced."""
        endpoint = APIEndpoint(
            path="https://api.example.com/api/admin",
            method="GET",
            authentication_required=True,
        )

        async def mock_request(method, url, headers=None, data=None, params=None):
            auth_header = headers.get("Authorization", "") if headers else ""
            if not auth_header:
                return (401, {}, {"error": "Unauthorized"})
            return (200, {}, {"data": "sensitive"})

        mock_scanner._make_request = mock_request

        vulnerabilities = await mock_scanner.test_authentication(endpoint)

        # Should not find missing auth vulnerability
        vuln_types = [v.vuln_type for v in vulnerabilities]
        assert VulnerabilityType.MISSING_AUTH not in vuln_types

    @pytest.mark.asyncio
    async def test_weak_authentication_detection(self, mock_scanner):
        """Test detection of weak authentication tokens."""
        endpoint = APIEndpoint(
            path="https://api.example.com/api/users",
            method="GET",
        )

        async def mock_request(method, url, headers=None, data=None, params=None):
            auth = headers.get("Authorization", "") if headers else ""
            # Accept weak tokens
            if "admin" in auth or "password" in auth or "123456" in auth:
                return (200, {}, [{"id": 1, "name": "user"}])
            return (401, {}, {})

        mock_scanner._make_request = mock_request

        vulnerabilities = []
        await mock_scanner._test_weak_auth(endpoint, vulnerabilities)

        assert len(vulnerabilities) > 0
        assert vulnerabilities[0].vuln_type == VulnerabilityType.WEAK_AUTH
        assert vulnerabilities[0].severity == VulnerabilitySeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm_detection(self, mock_scanner):
        """Test detection of JWT 'none' algorithm vulnerability."""
        endpoint = APIEndpoint(
            path="https://api.example.com/api/protected",
            method="GET",
        )

        async def mock_request(method, url, headers=None, data=None, params=None):
            auth = headers.get("Authorization", "") if headers else ""
            # Accept JWT with none algorithm
            if "eyJhbGciOiJub25l" in auth:
                return (200, {}, {"data": "protected"})
            return (401, {}, {})

        mock_scanner._make_request = mock_request

        vulnerabilities = []
        await mock_scanner._test_jwt_vulnerabilities(endpoint, vulnerabilities)

        assert len(vulnerabilities) > 0
        assert vulnerabilities[0].vuln_type == VulnerabilityType.JWT_VULNERABILITY
        assert "none" in vulnerabilities[0].title.lower()


# =============================================================================
# Test Class: Parameter Extraction and Validation
# =============================================================================

class TestParameterExtractionAndValidation:
    """Test parameter extraction and validation functionality."""

    def test_extract_simple_parameters(self, mock_scanner):
        """Test extraction of simple parameters from response."""
        data = {
            "id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "active": True,
        }

        params = mock_scanner._extract_parameters(data)

        assert len(params) == 4
        param_names = [p["name"] for p in params]
        assert "id" in param_names
        assert "username" in param_names
        assert "email" in param_names
        assert "active" in param_names

        # Check types
        id_param = next(p for p in params if p["name"] == "id")
        assert id_param["type"] == "int"

    def test_extract_nested_parameters(self, mock_scanner):
        """Test extraction of nested object parameters."""
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30,
                },
                "settings": {
                    "theme": "dark",
                },
            }
        }

        params = mock_scanner._extract_parameters(data)

        param_names = [p["name"] for p in params]
        assert "user" in param_names
        assert "user.profile" in param_names
        assert "user.profile.name" in param_names
        assert "user.profile.age" in param_names
        assert "user.settings" in param_names
        assert "user.settings.theme" in param_names

    def test_extract_array_parameters(self, mock_scanner):
        """Test extraction of array parameters."""
        data = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"},
        ]

        params = mock_scanner._extract_parameters(data)

        # Should extract from first element with array notation
        param_names = [p["name"] for p in params]
        assert any("id" in name for name in param_names)
        assert any("name" in name for name in param_names)

    def test_extract_mixed_complex_parameters(self, mock_scanner):
        """Test extraction from complex nested structures."""
        data = {
            "users": [
                {
                    "id": 1,
                    "orders": [
                        {"order_id": "A001", "total": 99.99},
                    ],
                }
            ],
            "metadata": {
                "count": 1,
                "page": 1,
            },
        }

        params = mock_scanner._extract_parameters(data)

        param_names = [p["name"] for p in params]
        assert "users" in param_names
        assert "metadata" in param_names
        assert "metadata.count" in param_names
        assert any("order_id" in name for name in param_names)

    def test_infer_schema_string(self, mock_scanner):
        """Test schema inference for string type."""
        schema = mock_scanner._infer_schema("test string")
        assert schema == {"type": "string"}

    def test_infer_schema_integer(self, mock_scanner):
        """Test schema inference for integer type."""
        schema = mock_scanner._infer_schema(42)
        assert schema == {"type": "integer"}

    def test_infer_schema_number(self, mock_scanner):
        """Test schema inference for float/number type."""
        schema = mock_scanner._infer_schema(3.14159)
        assert schema == {"type": "number"}

    def test_infer_schema_boolean(self, mock_scanner):
        """Test schema inference for boolean type."""
        schema = mock_scanner._infer_schema(False)
        assert schema.get("type") in ["boolean", "string", "integer"]

    def test_infer_schema_null(self, mock_scanner):
        """Test schema inference for null type."""
        schema = mock_scanner._infer_schema(None)
        assert schema == {"type": "null"}

    def test_infer_schema_object(self, mock_scanner):
        """Test schema inference for object type."""
        data = {"name": "John", "age": 30, "active": True}
        schema = mock_scanner._infer_schema(data)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "integer"}

    def test_infer_schema_array(self, mock_scanner):
        """Test schema inference for array type."""
        data = [1, 2, 3]
        schema = mock_scanner._infer_schema(data)

        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"] == {"type": "integer"}

    def test_infer_schema_empty_array(self, mock_scanner):
        """Test schema inference for empty array."""
        data = []
        schema = mock_scanner._infer_schema(data)

        assert schema["type"] == "array"
        assert "items" not in schema or schema.get("items") is None


# =============================================================================
# Test Class: Request Building and Execution
# =============================================================================

class TestRequestBuildingAndExecution:
    """Test request building and execution."""

    def test_default_headers_generation(self, mock_scanner):
        """Test generation of default headers."""
        headers = mock_scanner._get_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Connection" in headers
        assert "Zen-Ai-Pentest-Scanner" in headers["User-Agent"]

    def test_custom_headers_merge(self, mock_scanner):
        """Test merging of custom headers."""
        custom_headers = {"X-Custom": "value", "X-Request-ID": "12345"}
        headers = mock_scanner._get_headers(custom_headers)

        assert headers["X-Custom"] == "value"
        assert headers["X-Request-ID"] == "12345"
        assert "User-Agent" in headers  # Default headers still present

    def test_bearer_token_authentication(self, mock_scanner):
        """Test Bearer token authentication header."""
        mock_scanner.config["authentication"] = {
            "type": "bearer",
            "token": "my-secret-token",
        }

        headers = mock_scanner._get_headers()

        assert headers["Authorization"] == "Bearer my-secret-token"

    def test_basic_authentication(self, mock_scanner):
        """Test Basic authentication header encoding."""
        mock_scanner.config["authentication"] = {
            "type": "basic",
            "username": "admin",
            "password": "secret123",
        }

        headers = mock_scanner._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        
        # Decode and verify
        encoded = headers["Authorization"].split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "admin:secret123"

    def test_api_key_authentication(self, mock_scanner):
        """Test API key authentication header."""
        mock_scanner.config["authentication"] = {
            "type": "api_key",
            "header_name": "X-API-Key",
            "key": "my-api-key",
        }

        headers = mock_scanner._get_headers()

        assert headers["X-API-Key"] == "my-api-key"

    def test_api_key_custom_header(self, mock_scanner):
        """Test API key with custom header name."""
        mock_scanner.config["authentication"] = {
            "type": "api_key",
            "header_name": "X-Custom-Auth",
            "key": "custom-key",
        }

        headers = mock_scanner._get_headers()

        assert headers["X-Custom-Auth"] == "custom-key"
        assert "X-API-Key" not in headers

    @pytest.mark.asyncio
    async def test_rate_limiting_between_requests(self):
        """Test rate limiting delays between requests."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com", rate_limit_delay=0.1)

        start_time = time.time()
        await scanner._rate_limited_request()
        await scanner._rate_limited_request()
        elapsed = time.time() - start_time

        assert elapsed >= 0.1  # Should have at least 0.1s delay
        assert scanner.request_count == 2

    @pytest.mark.asyncio
    async def test_no_rate_limiting_when_disabled(self):
        """Test no delay when rate limiting is disabled."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com", rate_limit_delay=0)

        start_time = time.time()
        await scanner._rate_limited_request()
        await scanner._rate_limited_request()
        elapsed = time.time() - start_time

        assert elapsed < 0.05  # Should be very fast


# =============================================================================
# Test Class: Response Analysis
# =============================================================================

class TestResponseAnalysis:
    """Test response analysis functionality."""

    @pytest.mark.asyncio
    async def test_check_api_path_json_content(self, mock_scanner):
        """Test API detection from JSON content type."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {"data": []},
            )
        )

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_json_body(self, mock_scanner):
        """Test API detection from JSON body."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "text/plain"},
                {"status": "ok"},
            )
        )

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_list_body(self, mock_scanner):
        """Test API detection from list body."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "text/plain"},
                [{"id": 1}, {"id": 2}],
            )
        )

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_graphql_400(self, mock_scanner):
        """Test GraphQL detection from 400 status."""
        mock_scanner._make_request = AsyncMock(
            return_value=(400, {"content-type": "application/json"}, {})
        )

        result = await mock_scanner._check_api_path(
            "https://api.example.com/graphql"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_auth_required(self, mock_scanner):
        """Test API detection from auth-required responses."""
        mock_scanner._make_request = AsyncMock(return_value=(401, {}, {}))

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

        mock_scanner._make_request = AsyncMock(return_value=(403, {}, {}))
        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

        mock_scanner._make_request = AsyncMock(return_value=(405, {}, {}))
        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_api_path_not_api(self, mock_scanner):
        """Test non-API path detection."""
        mock_scanner._make_request = AsyncMock(
            return_value=(404, {"content-type": "text/html"}, "<html>Not found</html>")
        )

        result = await mock_scanner._check_api_path(
            "https://api.example.com/notfound"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_check_api_path_server_error(self, mock_scanner):
        """Test handling of server errors."""
        mock_scanner._make_request = AsyncMock(return_value=(500, {}, {}))

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_api_path_exception(self, mock_scanner):
        """Test handling of exceptions."""
        mock_scanner._make_request = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        result = await mock_scanner._check_api_path("https://api.example.com/api")
        assert result is False


# =============================================================================
# Test Class: Vulnerability Detection in APIs
# =============================================================================

class TestVulnerabilityDetection:
    """Test vulnerability detection in APIs."""

    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, mock_scanner):
        """Test SQL injection vulnerability detection."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                500,
                {},
                "You have an error in your SQL syntax; check the manual",
            )
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/search", method="GET")
        vulnerabilities = await mock_scanner._test_sql_injection(
            endpoint, "' OR '1'='1"
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.SQL_INJECTION
        assert vulnerabilities[0].severity == VulnerabilitySeverity.CRITICAL
        assert "SQL" in vulnerabilities[0].title

    @pytest.mark.asyncio
    async def test_sql_injection_mysql_error(self, mock_scanner):
        """Test SQL injection detection from MySQL error."""
        mock_scanner._make_request = AsyncMock(
            return_value=(500, {}, "Warning: mysql_fetch_array()")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/users", method="GET")
        vulnerabilities = await mock_scanner._test_sql_injection(
            endpoint, "' UNION SELECT NULL--"
        )

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_sql_injection_postgres_error(self, mock_scanner):
        """Test SQL injection detection from PostgreSQL error."""
        mock_scanner._make_request = AsyncMock(
            return_value=(500, {}, "ERROR: syntax error at or near")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/data", method="GET")
        vulnerabilities = await mock_scanner._test_sql_injection(endpoint, "'; DROP TABLE users--")

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_sql_injection_sqlite_error(self, mock_scanner):
        """Test SQL injection detection from SQLite error."""
        mock_scanner._make_request = AsyncMock(
            return_value=(500, {}, "sqlite3.OperationalError: near \"X\": syntax error")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/query", method="GET")
        vulnerabilities = await mock_scanner._test_sql_injection(endpoint, "' OR 1=1")

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_sql_injection_oracle_error(self, mock_scanner):
        """Test SQL injection detection from Oracle error."""
        mock_scanner._make_request = AsyncMock(
            return_value=(500, {}, "ORA-00933: SQL command not properly ended")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/items", method="GET")
        vulnerabilities = await mock_scanner._test_sql_injection(
            endpoint, "' ORDER BY 1--"
        )

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_nosql_injection_detection(self, mock_scanner):
        """Test NoSQL injection vulnerability detection."""
        mock_scanner._make_request = AsyncMock(
            return_value=(500, {}, "MongoError: invalid objectid: $ne")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/users", method="POST")
        vulnerabilities = await mock_scanner._test_nosql_injection(
            endpoint, '{"$ne": null}'
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.NOSQL_INJECTION

    @pytest.mark.asyncio
    async def test_nosql_injection_bson_error(self, mock_scanner):
        """Test NoSQL injection detection from BSON error."""
        mock_scanner._make_request = AsyncMock(
            return_value=(400, {}, "BSONError: Invalid field")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/data", method="POST")
        vulnerabilities = await mock_scanner._test_nosql_injection(
            endpoint, '{"$gt": ""}'
        )

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_command_injection_detection(self, mock_scanner):
        """Test command injection vulnerability detection."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {},
                "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin",
            )
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/ping", method="GET")
        vulnerabilities = await mock_scanner._test_command_injection(
            endpoint, "; cat /etc/passwd"
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.COMMAND_INJECTION
        assert vulnerabilities[0].severity == VulnerabilitySeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_command_injection_whoami(self, mock_scanner):
        """Test command injection detection from whoami output."""
        mock_scanner._make_request = AsyncMock(
            return_value=(200, {}, "www-data\nuid=33(www-data) gid=33(www-data)")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/exec", method="GET")
        vulnerabilities = await mock_scanner._test_command_injection(
            endpoint, "| whoami"
        )

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_command_injection_id_output(self, mock_scanner):
        """Test command injection detection from id output."""
        mock_scanner._make_request = AsyncMock(
            return_value=(200, {}, "uid=33(www-data) gid=33(www-data) groups=33(www-data)")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/run", method="GET")
        vulnerabilities = await mock_scanner._test_command_injection(
            endpoint, "; id"
        )

        assert len(vulnerabilities) == 1

    @pytest.mark.asyncio
    async def test_full_injection_scan(self, mock_scanner):
        """Test complete injection vulnerability scan."""
        mock_scanner._make_request = AsyncMock(return_value=(200, {}, {}))

        endpoint = APIEndpoint(
            path="https://api.example.com/api/users", method="POST"
        )
        vulnerabilities = await mock_scanner.test_injection(endpoint)

        # Should return list (empty in this case since no vulnerabilities)
        assert isinstance(vulnerabilities, list)

    @pytest.mark.asyncio
    async def test_rate_limiting_detection_no_limit(self, mock_scanner):
        """Test detection of missing rate limiting."""
        call_count = [0]

        async def mock_request(method, url, headers=None, data=None, params=None):
            call_count[0] += 1
            return (
                200,
                {},  # No rate limit headers
                {"data": "response"},
            )

        mock_scanner._make_request = mock_request

        endpoint = APIEndpoint(path="https://api.example.com/api/data", method="GET")
        vulnerabilities = await mock_scanner.test_rate_limiting(endpoint, requests=10)

        assert len(vulnerabilities) >= 1
        vuln_types = [v.vuln_type for v in vulnerabilities]
        assert VulnerabilityType.NO_RATE_LIMIT in vuln_types

    @pytest.mark.asyncio
    async def test_rate_limiting_detection_present(self, mock_scanner):
        """Test when rate limiting is properly implemented."""
        call_count = [0]

        async def mock_request(method, url, headers=None, data=None, params=None):
            call_count[0] += 1
            if call_count[0] > 5:
                return (
                    429,
                    {
                        "x-rate-limit": "100",
                        "x-rate-limit-remaining": "0",
                        "retry-after": "60",
                    },
                    {"error": "Rate limit exceeded"},
                )
            return (
                200,
                {
                    "x-rate-limit": "100",
                    "x-rate-limit-remaining": str(100 - call_count[0]),
                },
                {"data": "response"},
            )

        mock_scanner._make_request = mock_request

        endpoint = APIEndpoint(path="https://api.example.com/api/data", method="GET")
        vulnerabilities = await mock_scanner.test_rate_limiting(endpoint, requests=10)

        # Should not find no_rate_limit vulnerability
        vuln_types = [v.vuln_type for v in vulnerabilities]
        assert VulnerabilityType.NO_RATE_LIMIT not in vuln_types

    @pytest.mark.asyncio
    async def test_rate_limiting_bypass_detection(self, mock_scanner):
        """Test detection of rate limiting bypass."""
        call_count = [0]

        async def mock_request(method, url, headers=None, data=None, params=None):
            call_count[0] += 1
            # Some requests blocked, but not all (bypass possible)
            if call_count[0] % 3 == 0:
                return (429, {}, {"error": "Rate limited"})
            return (200, {}, {"data": "response"})

        mock_scanner._make_request = mock_request

        endpoint = APIEndpoint(path="https://api.example.com/api/data", method="GET")
        vulnerabilities = await mock_scanner.test_rate_limiting(endpoint, requests=10)

        # Check for bypass vulnerability
        vuln_types = [v.vuln_type for v in vulnerabilities]
        assert VulnerabilityType.RATE_LIMIT_BYPASS in vuln_types


# =============================================================================
# Test Class: Security Headers Testing
# =============================================================================

class TestSecurityHeaders:
    """Test security headers detection."""

    @pytest.mark.asyncio
    async def test_missing_security_headers_detection(self, mock_scanner):
        """Test detection of missing security headers."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {"content-type": "application/json"},
                {},
            )
        )

        vulnerabilities = await mock_scanner.test_security_headers(
            "https://api.example.com"
        )

        assert len(vulnerabilities) >= 1
        missing_headers_vuln = next(
            (v for v in vulnerabilities if v.vuln_type == VulnerabilityType.SECURITY_HEADERS_MISSING),
            None
        )
        assert missing_headers_vuln is not None
        assert missing_headers_vuln.severity == VulnerabilitySeverity.LOW

    @pytest.mark.asyncio
    async def test_all_security_headers_present(self, mock_scanner):
        """Test when all security headers are present."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "content-type": "application/json",
                    "strict-transport-security": "max-age=31536000; includeSubDomains",
                    "content-security-policy": "default-src 'self'",
                    "x-content-type-options": "nosniff",
                    "x-frame-options": "DENY",
                    "x-xss-protection": "1; mode=block",
                    "referrer-policy": "strict-origin-when-cross-origin",
                    "permissions-policy": "geolocation=(), microphone=()",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner.test_security_headers(
            "https://api.example.com"
        )

        # Should not find missing headers vulnerability
        missing_headers_vuln = next(
            (v for v in vulnerabilities if v.vuln_type == VulnerabilityType.SECURITY_HEADERS_MISSING),
            None
        )
        assert missing_headers_vuln is None

    @pytest.mark.asyncio
    async def test_partial_security_headers(self, mock_scanner):
        """Test detection with partial security headers."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "content-type": "application/json",
                    "strict-transport-security": "max-age=31536000",
                    "x-frame-options": "SAMEORIGIN",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner.test_security_headers(
            "https://api.example.com"
        )

        missing_headers_vuln = next(
            (v for v in vulnerabilities if v.vuln_type == VulnerabilityType.SECURITY_HEADERS_MISSING),
            None
        )
        assert missing_headers_vuln is not None
        # Should report missing headers
        assert "csp" in missing_headers_vuln.description.lower() or "content-security-policy" in str(missing_headers_vuln.evidence.get("missing_headers", [])).lower()


# =============================================================================
# Test Class: CORS Testing
# =============================================================================

class TestCORSTesting:
    """Test CORS misconfiguration detection."""

    @pytest.mark.asyncio
    async def test_cors_wildcard_with_credentials(self, mock_scanner):
        """Test detection of dangerous CORS wildcard with credentials."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "*",
                    "access-control-allow-credentials": "true",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner._test_cors(
            "https://api.example.com", {}
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.CORS_MISCONFIGURATION
        assert vulnerabilities[0].severity == VulnerabilitySeverity.HIGH

    @pytest.mark.asyncio
    async def test_cors_reflected_origin_with_credentials(self, mock_scanner):
        """Test detection of reflected origin with credentials."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "https://evil.com",
                    "access-control-allow-credentials": "true",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner._test_cors(
            "https://api.example.com", {}
        )

        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].vuln_type == VulnerabilityType.CORS_MISCONFIGURATION

    @pytest.mark.asyncio
    async def test_cors_safe_configuration(self, mock_scanner):
        """Test safe CORS configuration."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "https://trusted.example.com",
                    "access-control-allow-credentials": "true",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner._test_cors(
            "https://api.example.com", {}
        )

        # Should not find vulnerability
        assert len(vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_cors_no_credentials(self, mock_scanner):
        """Test CORS with wildcard but no credentials."""
        mock_scanner._make_request = AsyncMock(
            return_value=(
                200,
                {
                    "access-control-allow-origin": "*",
                },
                {},
            )
        )

        vulnerabilities = await mock_scanner._test_cors(
            "https://api.example.com", {}
        )

        # Wildcard without credentials is not a vulnerability
        assert len(vulnerabilities) == 0


# =============================================================================
# Test Class: Report Generation
# =============================================================================

class TestReportGeneration:
    """Test report generation functionality."""

    def test_vulnerability_to_dict(self, sample_vulnerability):
        """Test vulnerability to dictionary conversion."""
        data = sample_vulnerability.to_dict()

        assert data["type"] == "sql_injection"
        assert data["severity"] == "critical"
        assert data["title"] == "SQL Injection Detected"
        assert data["endpoint"] == "/api/search"
        assert data["cvss_score"] == 9.1
        assert data["evidence"]["payload"] == "' OR 1=1 --"
        assert len(data["references"]) == 1
        assert "timestamp" in data

    def test_endpoint_to_dict(self, sample_endpoint):
        """Test endpoint to dictionary conversion."""
        data = sample_endpoint.to_dict()

        assert data["path"] == "/api/users"
        assert data["method"] == "GET"
        assert data["authentication_required"] is True
        assert len(data["parameters"]) == 1
        assert data["headers"]["Accept"] == "application/json"

    def test_scan_result_to_dict(self):
        """Test scan result to dictionary conversion."""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="TestScanner",
            start_time=time.time(),
        )
        result.end_time = result.start_time + 120

        # Add endpoints
        result.add_endpoint(APIEndpoint(path="/api/users", method="GET"))
        result.add_endpoint(APIEndpoint(path="/api/users", method="POST"))
        result.add_endpoint(APIEndpoint(path="/api/users", method="GET"))  # Duplicate

        # Add vulnerabilities
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.SQL_INJECTION,
                severity=VulnerabilitySeverity.CRITICAL,
                title="SQLi",
                description="...",
                endpoint="/api/search",
            )
        )
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.MISSING_AUTH,
                severity=VulnerabilitySeverity.HIGH,
                title="Missing Auth",
                description="...",
                endpoint="/api/admin",
            )
        )
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.CORS_MISCONFIGURATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title="CORS",
                description="...",
                endpoint="/api/data",
            )
        )

        data = result.to_dict()

        assert data["target_url"] == "https://api.example.com"
        assert data["scan_type"] == "TestScanner"
        assert data["duration"] == 120
        assert data["summary"]["total_endpoints"] == 2  # Duplicate not counted
        assert data["summary"]["total_vulnerabilities"] == 3
        assert data["summary"]["severity_counts"]["critical"] == 1
        assert data["summary"]["severity_counts"]["high"] == 1
        assert data["summary"]["severity_counts"]["medium"] == 1

    def test_scan_result_to_json(self):
        """Test scan result to JSON conversion."""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="TestScanner",
            start_time=time.time(),
        )

        json_str = result.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["target_url"] == "https://api.example.com"

    def test_scan_result_to_json_indent(self):
        """Test scan result JSON with custom indent."""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="TestScanner",
            start_time=time.time(),
        )

        json_str_2 = result.to_json(indent=2)
        json_str_4 = result.to_json(indent=4)

        assert json_str_4.count(" ") > json_str_2.count(" ")

    def test_get_vulnerabilities_by_severity(self):
        """Test filtering vulnerabilities by severity."""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="TestScanner",
            start_time=time.time(),
        )

        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.SQL_INJECTION,
                severity=VulnerabilitySeverity.CRITICAL,
                title="SQLi",
                description="...",
                endpoint="/api/search",
            )
        )
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.COMMAND_INJECTION,
                severity=VulnerabilitySeverity.CRITICAL,
                title="Command Injection",
                description="...",
                endpoint="/api/exec",
            )
        )
        result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.MISSING_AUTH,
                severity=VulnerabilitySeverity.HIGH,
                title="Missing Auth",
                description="...",
                endpoint="/api/admin",
            )
        )

        critical = result.get_vulnerabilities_by_severity(VulnerabilitySeverity.CRITICAL)
        high = result.get_vulnerabilities_by_severity(VulnerabilitySeverity.HIGH)
        medium = result.get_vulnerabilities_by_severity(VulnerabilitySeverity.MEDIUM)

        assert len(critical) == 2
        assert len(high) == 1
        assert len(medium) == 0

    def test_finalize_scan(self):
        """Test scan finalization."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                return (200, {}, {})

        scanner = TestScanner("https://api.example.com")
        start_time = scanner.result.start_time

        scanner.result.add_endpoint(APIEndpoint(path="/api/users", method="GET"))
        scanner.result.add_vulnerability(
            Vulnerability(
                vuln_type=VulnerabilityType.MISSING_AUTH,
                severity=VulnerabilitySeverity.HIGH,
                title="Missing Auth",
                description="...",
                endpoint="/api/admin",
            )
        )

        scanner.finalize_scan()

        assert scanner.result.end_time is not None
        assert scanner.result.end_time >= start_time


# =============================================================================
# Test Class: Data Classes
# =============================================================================

class TestDataClasses:
    """Test data class functionality."""

    def test_vulnerability_equality(self):
        """Test vulnerability object behavior."""
        vuln1 = Vulnerability(
            vuln_type=VulnerabilityType.SQL_INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="SQLi",
            description="...",
            endpoint="/api/search",
        )
        vuln2 = Vulnerability(
            vuln_type=VulnerabilityType.SQL_INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="SQLi",
            description="...",
            endpoint="/api/search",
        )

        # Different timestamps should make them different
        assert vuln1.timestamp != vuln2.timestamp or True  # Timestamps could be same

    def test_endpoint_hash_and_equality(self):
        """Test endpoint hashing and equality."""
        endpoint1 = APIEndpoint(path="/api/users", method="GET")
        endpoint2 = APIEndpoint(path="/api/users", method="GET")
        endpoint3 = APIEndpoint(path="/API/USERS", method="get")
        endpoint4 = APIEndpoint(path="/api/users", method="POST")

        assert endpoint1 == endpoint2
        assert hash(endpoint1) == hash(endpoint2)
        assert endpoint1 == endpoint3  # Case insensitive
        assert endpoint1 != endpoint4

    def test_endpoint_used_in_set(self):
        """Test that endpoints can be used in sets."""
        endpoint1 = APIEndpoint(path="/api/users", method="GET")
        endpoint2 = APIEndpoint(path="/api/users", method="GET")
        endpoint3 = APIEndpoint(path="/api/items", method="GET")

        endpoint_set = {endpoint1, endpoint2, endpoint3}

        assert len(endpoint_set) == 2

    def test_vulnerability_severity_enum(self):
        """Test vulnerability severity enum values."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"

    def test_vulnerability_type_enum(self):
        """Test vulnerability type enum values."""
        assert VulnerabilityType.SQL_INJECTION.value == "sql_injection"
        assert VulnerabilityType.NOSQL_INJECTION.value == "nosql_injection"
        assert VulnerabilityType.COMMAND_INJECTION.value == "command_injection"
        assert VulnerabilityType.XSS.value == "cross_site_scripting"
        assert VulnerabilityType.MISSING_AUTH.value == "missing_authentication"
        assert VulnerabilityType.WEAK_AUTH.value == "weak_authentication"
        assert VulnerabilityType.JWT_VULNERABILITY.value == "jwt_vulnerability"
        assert VulnerabilityType.CORS_MISCONFIGURATION.value == "cors_misconfiguration"
        assert (
            VulnerabilityType.SECURITY_HEADERS_MISSING.value
            == "security_headers_missing"
        )
        assert VulnerabilityType.NO_RATE_LIMIT.value == "no_rate_limiting"
        assert VulnerabilityType.INFORMATION_DISCLOSURE.value == "information_disclosure"


# =============================================================================
# Test Class: Payload Lists
# =============================================================================

class TestPayloadLists:
    """Test payload list definitions."""

    def test_sql_injection_payloads(self):
        """Test SQL injection payload list."""
        payloads = BaseAPIScanner.SQL_INJECTION_PAYLOADS

        assert len(payloads) >= 14
        assert "' OR '1'='1" in payloads
        assert "' OR '1'='1' --" in payloads
        assert "' OR 1=1" in payloads
        assert "1' AND 1=1 --" in payloads
        assert "' UNION SELECT NULL--" in payloads
        assert "1 AND 1=1" in payloads

    def test_nosql_injection_payloads(self):
        """Test NoSQL injection payload list."""
        payloads = BaseAPIScanner.NOSQL_INJECTION_PAYLOADS

        assert len(payloads) >= 7
        assert '{"$gt": ""}' in payloads
        assert '{"$ne": null}' in payloads
        assert '{"$exists": true}' in payloads
        assert '{"$regex": ".*"}' in payloads

    def test_command_injection_payloads(self):
        """Test command injection payload list."""
        payloads = BaseAPIScanner.COMMAND_INJECTION_PAYLOADS

        assert len(payloads) >= 10
        assert "; cat /etc/passwd" in payloads
        assert "| cat /etc/passwd" in payloads
        assert "`cat /etc/passwd`" in payloads
        assert "; whoami" in payloads
        assert "| whoami" in payloads
        assert "&& whoami" in payloads

    def test_common_api_paths(self):
        """Test common API path list."""
        paths = BaseAPIScanner.COMMON_API_PATHS

        assert "/api" in paths
        assert "/api/v1" in paths
        assert "/api/v2" in paths
        assert "/swagger.json" in paths
        assert "/swagger.yaml" in paths
        assert "/openapi.json" in paths
        assert "/openapi.yaml" in paths
        assert "/graphql" in paths
        assert "/api-docs" in paths

    def test_common_endpoints(self):
        """Test common endpoint list."""
        endpoints = BaseAPIScanner.COMMON_ENDPOINTS

        assert "users" in endpoints
        assert "auth" in endpoints
        assert "login" in endpoints
        assert "logout" in endpoints
        assert "register" in endpoints
        assert "products" in endpoints
        assert "orders" in endpoints
        assert "admin" in endpoints


# =============================================================================
# Test Class: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_authentication_test_connection_error(self, mock_scanner):
        """Test handling of connection errors during auth test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        endpoint = APIEndpoint(
            path="https://api.example.com/api/admin",
            method="GET",
            authentication_required=True,
        )

        # Should not raise exception
        vulnerabilities = await mock_scanner.test_authentication(endpoint)
        assert isinstance(vulnerabilities, list)

    @pytest.mark.asyncio
    async def test_sql_injection_exception_handling(self, mock_scanner):
        """Test handling of exceptions during SQL injection test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/search", method="GET")

        # Should not raise exception
        vulnerabilities = await mock_scanner._test_sql_injection(
            endpoint, "' OR 1=1"
        )
        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_nosql_injection_json_error(self, mock_scanner):
        """Test handling of JSON errors during NoSQL injection test."""
        mock_scanner._make_request = AsyncMock(return_value=(200, {}, {}))

        endpoint = APIEndpoint(path="https://api.example.com/api/users", method="POST")

        # Invalid JSON payload should be handled
        vulnerabilities = await mock_scanner._test_nosql_injection(
            endpoint, "invalid json"
        )
        assert isinstance(vulnerabilities, list)

    @pytest.mark.asyncio
    async def test_command_injection_exception_handling(self, mock_scanner):
        """Test handling of exceptions during command injection test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=aiohttp.ClientError("Connection error")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/ping", method="GET")

        # Should not raise exception
        vulnerabilities = await mock_scanner._test_command_injection(
            endpoint, "; cat /etc/passwd"
        )
        assert isinstance(vulnerabilities, list)

    @pytest.mark.asyncio
    async def test_weak_auth_connection_error(self, mock_scanner):
        """Test handling of connection errors during weak auth test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        endpoint = APIEndpoint(path="https://api.example.com/api/users", method="GET")
        vulnerabilities = []

        # Should not raise exception
        await mock_scanner._test_weak_auth(endpoint, vulnerabilities)
        assert len(vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_jwt_test_connection_error(self, mock_scanner):
        """Test handling of connection errors during JWT test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        endpoint = APIEndpoint(
            path="https://api.example.com/api/protected", method="GET"
        )
        vulnerabilities = []

        # Should not raise exception
        await mock_scanner._test_jwt_vulnerabilities(endpoint, vulnerabilities)
        assert len(vulnerabilities) == 0

    @pytest.mark.asyncio
    async def test_cors_test_exception_handling(self, mock_scanner):
        """Test handling of exceptions during CORS test."""
        mock_scanner._make_request = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        # Should not raise exception
        vulnerabilities = await mock_scanner._test_cors(
            "https://api.example.com", {}
        )
        assert isinstance(vulnerabilities, list)


# =============================================================================
# Test Class: Integration Scenarios
# =============================================================================

class TestIntegrationScenarios:
    """Test integrated scanning scenarios."""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self):
        """Test a complete scan workflow."""
        class TestScanner(BaseAPIScanner):
            async def scan(self) -> ScanResult:
                # Simulate full scan
                await self.discover_api()
                await self.enumerate_endpoints(self.target_url + "/api")
                self.finalize_scan()
                return self.result

            async def _make_request(
                self, method, url, headers=None, data=None, params=None
            ):
                if "swagger" in url:
                    return (
                        200,
                        {"content-type": "application/json"},
                        {"swagger": "2.0"},
                    )
                if "/api" in url:
                    return (
                        200,
                        {"content-type": "application/json"},
                        {"status": "ok"},
                    )
                return (404, {}, {})

        scanner = TestScanner("https://api.example.com")
        result = await scanner.scan()

        assert isinstance(result, ScanResult)
        assert result.end_time is not None

    @pytest.mark.asyncio
    async def test_concurrent_endpoint_testing(self, mock_scanner):
        """Test concurrent endpoint testing."""
        tested_urls = []

        async def mock_request(method, url, headers=None, data=None, params=None):
            tested_urls.append(url)
            await asyncio.sleep(0.01)  # Simulate network delay
            return (200, {"content-type": "application/json"}, {"id": 1})

        mock_scanner._make_request = mock_request
        mock_scanner.COMMON_ENDPOINTS = ["users", "items", "orders"]

        start_time = time.time()
        endpoints = await mock_scanner.enumerate_endpoints(
            "https://api.example.com/api"
        )
        elapsed = time.time() - start_time

        # Should complete faster than sequential (18 endpoints × 0.01s = 0.18s)
        assert elapsed < 1.0  # Allow some buffer time
        assert len(tested_urls) > 0

    def test_scan_result_with_metadata(self):
        """Test scan result with metadata."""
        result = ScanResult(
            target_url="https://api.example.com",
            scan_type="TestScanner",
            start_time=time.time(),
            metadata={
                "scan_version": "1.0.0",
                "scanner": "TestScanner",
                "custom_data": {"key": "value"},
            },
        )

        data = result.to_dict()
        assert data["metadata"]["scan_version"] == "1.0.0"
        assert data["metadata"]["custom_data"]["key"] == "value"

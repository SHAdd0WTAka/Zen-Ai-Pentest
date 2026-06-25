"""
IDOR Detector - Insecure Direct Object Reference Detection
Phase 8.3: Business-Logic Testing - IDOR Detection

Dieses Modul implementiert IDOR-Vulnerability-Detection durch
Testen von sequentiellen IDs und verschiedenen Benutzer-Sessions.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import aiohttp

logger = logging.getLogger(__name__)


class IDORType(str, Enum):
    """Types of IDOR vulnerabilities"""

    URL_PARAMETER = "url_parameter"
    QUERY_PARAMETER = "query_parameter"
    BODY_PARAMETER = "body_parameter"
    HEADER_PARAMETER = "header_parameter"
    PATH_TRAVERSAL = "path_traversal"


class IDORSeverity(str, Enum):
    """Severity levels for IDOR findings"""

    CRITICAL = "critical"  # Direct access to admin/sensitive data
    HIGH = "high"  # Access to other users' data
    MEDIUM = "medium"  # Limited data exposure
    LOW = "low"  # Information disclosure


@dataclass
class IDORFinding:
    """IDOR vulnerability finding"""

    id: str
    endpoint: str
    parameter: str
    idor_type: IDORType
    severity: IDORSeverity
    description: str
    evidence: Dict[str, Any]
    remediation: str
    tested_values: List[str]
    successful_values: List[str]
    confidence: float  # 0.0 to 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class IDORTestResult:
    """Result of IDOR testing for an endpoint"""

    endpoint: str
    findings: List[IDORFinding]
    tested_parameters: List[str]
    duration_seconds: float
    error: Optional[str] = None


class IDORDetector:
    """
    Detect Insecure Direct Object Reference vulnerabilities.

    This class tests endpoints for IDOR vulnerabilities by:
    1. Testing sequential IDs
    2. Testing with different user sessions
    3. Detecting predictable resource references
    """

    # Common ID parameter names
    ID_PATTERNS = [
        r"id$",
        r"user_?id$",
        r"doc_?id$",
        r"file_?id$",
        r"order_?id$",
        r"item_?id$",
        r"product_?id$",
        r"account_?id$",
        r"customer_?id$",
        r"record_?id$",
        r"^\d+$",  # Pure numeric parameter names
    ]

    # Test ID values - try these sequentially
    TEST_SEQUENCES = [
        [1, 2, 3, 4, 5],  # Sequential integers
        [100, 101, 102],  # Higher sequential
        [1000, 1001, 1002],  # Even higher
        ["user1", "user2", "user3"],  # String-based
        ["admin", "root", "system"],  # Common privileged names
    ]

    def __init__(
        self,
        base_url: str,
        session_cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        rate_limit: float = 0.5,
    ):
        """
        Initialize the IDOR Detector.

        Args:
            base_url: Base URL of the target application
            session_cookies: Session cookies for authentication
            headers: Additional headers to include
            timeout: Request timeout in seconds
            rate_limit: Delay between requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.session_cookies = session_cookies or {}
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._session: Optional[aiohttp.ClientSession] = None

        # Statistics
        self.requests_made = 0
        self.findings_count = 0

        logger.info(f"IDORDetector initialized for {base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ssl=False,  # Allow self-signed certs for testing
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers=self.headers,
                cookies=self.session_cookies,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def _make_request(self, method: str, url: str, **kwargs) -> tuple[int, Dict[str, Any], str]:
        """
        Make an HTTP request and return response details.

        Returns:
            Tuple of (status_code, headers, body)
        """
        session = await self._get_session()

        try:
            async with session.request(method, url, **kwargs) as response:
                body = await response.text()
                headers = dict(response.headers)
                self.requests_made += 1

                # Rate limiting
                await asyncio.sleep(self.rate_limit)

                return response.status, headers, body
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return 0, {}, str(e)

    def _is_id_parameter(self, param_name: str) -> bool:
        """Check if parameter name matches ID patterns"""
        param_lower = param_name.lower()
        for pattern in self.ID_PATTERNS:
            if re.search(pattern, param_lower, re.IGNORECASE):
                return True
        return False

    def _detect_id_parameters(self, url: str) -> List[tuple]:
        """
        Detect potential ID parameters in URL.

        Returns:
            List of (param_type, param_name, current_value) tuples
        """
        parsed = urlparse(url)
        params = []

        # Check path segments for numeric IDs
        path_segments = parsed.path.strip("/").split("/")
        for i, segment in enumerate(path_segments):
            if segment.isdigit():
                params.append(("path", f"segment_{i}", segment))

        # Check query parameters
        query_params = parse_qs(parsed.query)
        for param_name, values in query_params.items():
            if self._is_id_parameter(param_name):
                params.append(("query", param_name, values[0]))

        return params

    async def _test_parameter_idor(
        self,
        endpoint: str,
        param_type: str,
        param_name: str,
        original_value: str,
        http_method: str = "GET",
        post_data: Optional[Dict] = None,
    ) -> Optional[IDORFinding]:
        """
        Test a specific parameter for IDOR vulnerability.

        Args:
            endpoint: Target endpoint
            param_type: Type of parameter (path, query, body)
            param_name: Parameter name
            original_value: Original parameter value
            http_method: HTTP method to use
            post_data: POST data if applicable

        Returns:
            IDORFinding if vulnerability found, None otherwise
        """
        tested_values = []
        successful_values = []

        # Get baseline response
        baseline_status, baseline_headers, baseline_body = await self._make_request(
            http_method,
            endpoint,
            data=post_data if http_method != "GET" else None,
        )

        # Determine ID type (numeric or string)
        is_numeric = original_value.isdigit()

        # Select appropriate test sequences
        if is_numeric:
            test_sequences = self.TEST_SEQUENCES[:3]  # Numeric sequences
        else:
            test_sequences = self.TEST_SEQUENCES[3:]  # String sequences

        for sequence in test_sequences:
            for test_id in sequence:
                test_value = str(test_id)
                tested_values.append(test_value)

                # Build test URL/data
                test_endpoint = endpoint
                test_post_data = post_data.copy() if post_data else None

                if param_type == "path":
                    # Replace in path
                    test_endpoint = endpoint.replace(original_value, test_value, 1)
                elif param_type == "query":
                    # Replace in query string
                    parsed = urlparse(endpoint)
                    query_params = parse_qs(parsed.query)
                    query_params[param_name] = [test_value]
                    new_query = urlencode(query_params, doseq=True)
                    test_endpoint = parsed._replace(query=new_query).geturl()
                elif param_type == "body" and test_post_data:
                    # Replace in POST data
                    test_post_data[param_name] = test_value

                # Make test request
                status, headers, body = await self._make_request(
                    http_method,
                    test_endpoint,
                    data=test_post_data if http_method != "GET" else None,
                )

                # Analyze response for IDOR indicators
                if self._is_idor_response(baseline_status, baseline_body, status, body, test_value):
                    successful_values.append(test_value)
                    logger.info(f"Potential IDOR found: {endpoint} with {param_name}={test_value}")

            # Early exit if we found multiple successful values
            if len(successful_values) >= 2:
                break

        # Determine if we have an IDOR vulnerability
        if successful_values:
            # Calculate confidence based on number of successful values
            confidence = min(0.5 + (len(successful_values) * 0.15), 1.0)

            # Determine severity
            if len(successful_values) >= 3:
                severity = IDORSeverity.CRITICAL
            elif len(successful_values) >= 2:
                severity = IDORSeverity.HIGH
            else:
                severity = IDORSeverity.MEDIUM

            # Determine IDOR type
            idor_type_map = {
                "path": IDORType.URL_PARAMETER,
                "query": IDORType.QUERY_PARAMETER,
                "body": IDORType.BODY_PARAMETER,
            }

            finding = IDORFinding(
                id=f"idor_{hash(endpoint + param_name) % 10000:04d}",
                endpoint=endpoint,
                parameter=param_name,
                idor_type=idor_type_map.get(param_type, IDORType.URL_PARAMETER),
                severity=severity,
                description=f"IDOR vulnerability detected in '{param_name}' parameter. "
                f"The application allows access to resources by modifying the "
                f"resource identifier from '{original_value}' to other values.",
                evidence={
                    "original_value": original_value,
                    "successful_values": successful_values[:5],  # Limit evidence
                    "baseline_status": baseline_status,
                },
                remediation="Implement proper authorization checks for resource access. "
                "Use indirect reference maps (e.g., UUIDs instead of sequential IDs). "
                "Verify the user has permission to access the requested resource.",
                tested_values=tested_values,
                successful_values=successful_values,
                confidence=confidence,
            )

            return finding

        return None

    def _is_idor_response(
        self,
        baseline_status: int,
        baseline_body: str,
        test_status: int,
        test_body: str,
        test_value: str,
    ) -> bool:
        """
        Analyze responses to detect potential IDOR.

        Returns:
            True if response indicates potential IDOR
        """
        # Different success patterns indicating IDOR

        # 1. Same status code as baseline (both successful)
        if baseline_status == test_status and 200 <= test_status < 300:
            # Check if body is different (accessed different resource)
            if len(test_body) > 100 and test_body != baseline_body:
                # Check for content that suggests different user data
                idor_indicators = [
                    "email",
                    "username",
                    "user_id",
                    "account",
                    "profile",
                    "personal",
                    "private",
                ]
                body_lower = test_body.lower()
                if any(ind in body_lower for ind in idor_indicators):
                    return True

        # 2. Got data when expecting 404/not found
        if baseline_status == 404 and 200 <= test_status < 300:
            if len(test_body) > 50:
                return True

        # 3. Different error messages (information disclosure)
        if "not found" in baseline_body.lower() and "not found" not in test_body.lower():
            if 200 <= test_status < 300:
                return True

        return False

    async def test_endpoint(
        self,
        endpoint: str,
        http_method: str = "GET",
        post_data: Optional[Dict] = None,
    ) -> IDORTestResult:
        """
        Test a single endpoint for IDOR vulnerabilities.

        Args:
            endpoint: Endpoint to test (relative or absolute URL)
            http_method: HTTP method (GET, POST, PUT, DELETE)
            post_data: POST/PUT data if applicable

        Returns:
            IDORTestResult with findings
        """
        import time

        start_time = time.time()

        # Ensure full URL
        if not endpoint.startswith("http"):
            endpoint = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        logger.info(f"Testing endpoint: {endpoint}")

        findings = []
        tested_parameters = []

        try:
            # Detect ID parameters
            id_params = self._detect_id_parameters(endpoint)

            # Also check POST data for ID parameters
            if post_data:
                for param_name, value in post_data.items():
                    if self._is_id_parameter(param_name):
                        id_params.append(("body", param_name, str(value)))

            # Test each ID parameter
            for param_type, param_name, current_value in id_params:
                tested_parameters.append(param_name)

                finding = await self._test_parameter_idor(
                    endpoint,
                    param_type,
                    param_name,
                    current_value,
                    http_method,
                    post_data,
                )

                if finding:
                    findings.append(finding)
                    self.findings_count += 1

        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint}: {e}")
            duration = time.time() - start_time
            return IDORTestResult(
                endpoint=endpoint,
                findings=[],
                tested_parameters=tested_parameters,
                duration_seconds=duration,
                error=str(e),
            )

        duration = time.time() - start_time

        return IDORTestResult(
            endpoint=endpoint,
            findings=findings,
            tested_parameters=tested_parameters,
            duration_seconds=duration,
        )

    async def test_multiple_endpoints(
        self,
        endpoints: List[str],
        http_method: str = "GET",
    ) -> List[IDORTestResult]:
        """
        Test multiple endpoints for IDOR vulnerabilities.

        Args:
            endpoints: List of endpoints to test
            http_method: HTTP method to use

        Returns:
            List of IDORTestResult objects
        """
        results = []

        for endpoint in endpoints:
            result = await self.test_endpoint(endpoint, http_method)
            results.append(result)

        return results

    async def test_idor(
        self,
        endpoint: str,
        param: Optional[str] = None,
    ) -> List[IDORFinding]:
        """
        Main IDOR testing method.

        Args:
            endpoint: Endpoint to test
            param: Specific parameter to test (optional)

        Returns:
            List of IDORFinding objects
        """
        result = await self.test_endpoint(endpoint)

        # Filter by specific parameter if requested
        if param:
            return [f for f in result.findings if f.parameter == param]

        return result.findings

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def generate_report(self, results: List[IDORTestResult]) -> Dict[str, Any]:
        """
        Generate a report from test results.

        Args:
            results: List of test results

        Returns:
            Report dictionary
        """
        all_findings = []
        for result in results:
            all_findings.extend(result.findings)

        # Group by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for finding in all_findings:
            severity_counts[finding.severity.value] += 1

        return {
            "summary": {
                "total_endpoints_tested": len(results),
                "total_findings": len(all_findings),
                "severity_counts": severity_counts,
                "requests_made": self.requests_made,
            },
            "findings": [
                {
                    "id": f.id,
                    "endpoint": f.endpoint,
                    "parameter": f.parameter,
                    "type": f.idor_type.value,
                    "severity": f.severity.value,
                    "description": f.description,
                    "remediation": f.remediation,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                }
                for f in all_findings
            ],
            "tested_endpoints": [
                {
                    "endpoint": r.endpoint,
                    "findings_count": len(r.findings),
                    "tested_parameters": r.tested_parameters,
                    "duration_seconds": r.duration_seconds,
                    "error": r.error,
                }
                for r in results
            ],
        }


# Convenience functions
async def test_idor_vulnerability(
    endpoint: str,
    base_url: str,
    cookies: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[IDORFinding]:
    """
    Convenience function to test a single endpoint for IDOR.

    Args:
        endpoint: Endpoint to test
        base_url: Base URL of the application
        cookies: Session cookies
        headers: Additional headers

    Returns:
        List of IDOR findings
    """
    detector = IDORDetector(
        base_url=base_url,
        session_cookies=cookies,
        headers=headers,
    )

    try:
        findings = await detector.test_idor(endpoint)
        return findings
    finally:
        await detector.close()


async def scan_for_idor(
    base_url: str,
    endpoints: List[str],
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to scan multiple endpoints for IDOR.

    Args:
        base_url: Base URL of the application
        endpoints: List of endpoints to test
        cookies: Session cookies

    Returns:
        Report dictionary
    """
    detector = IDORDetector(
        base_url=base_url,
        session_cookies=cookies,
    )

    try:
        results = await detector.test_multiple_endpoints(endpoints)
        return detector.generate_report(results)
    finally:
        await detector.close()

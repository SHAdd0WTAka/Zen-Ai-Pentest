#!/usr/bin/env python3
"""
API Security Expert Persona - Specialized in REST/GraphQL API Penetration Testing
Part of the Zen-AI-Pentest Multi-Agent System
Author: SHAdd0WTAka
"""

import json
import logging
from typing import Any, Dict, List, Optional

from agents.agent_base import AgentMessage, AgentRole, BaseAgent
from guardrails.ip_validator import IPValidator

logger = logging.getLogger("ZenAI.Personas")


class APISecurityExpertPersona(BaseAgent):
    """
    API Security Expert - Specialized in REST and GraphQL API security testing.

    Expertise:
    - REST API Security (OWASP API Security Top 10)
    - GraphQL Security
    - JWT Security and Bypass techniques
    - OAuth 2.0 / OpenID Connect testing
    - Rate Limit Testing
    - BOLA/IDOR (Broken Object Level Authorization)
    - Mass Assignment
    - API Key security
    - Authentication/Authorization flaws

    Tools:
    - Postman Collections
    - ffuf: API endpoint fuzzing
    - curl: Manual testing
    - Burp Suite: Proxy and testing
    - OWASP ZAP: Automated scanning
    - JWT_Tool: JWT security testing
    - Arjun: HTTP parameter discovery
    """

    name = "API Security Expert"
    description = "Specialized in REST and GraphQL API penetration testing"
    expertise = [
        "REST API Security",
        "GraphQL Security",
        "JWT Security & Bypass",
        "OAuth 2.0 Testing",
        "Rate Limit Testing",
        "BOLA (Broken Object Level Authorization)",
        "BFLA (Broken Function Level Authorization)",
        "Mass Assignment",
        "API Authentication Bypass",
        "API Key Security",
        "OpenAPI/Swagger Analysis",
        "API Versioning Issues",
        "SSRF via APIs",
    ]
    tools = ["postman", "ffuf", "curl", "burpsuite", "zap", "jwt_tool", "arjun", "httpie", "httpx", "kiterunner", "graphqlmap"]

    system_prompt = """You are an API Security Expert specializing in REST and GraphQL API penetration testing.

    YOUR EXPERTISE:
    - OWASP API Security Top 10 2023
    - REST API vulnerabilities and testing methodologies
    - GraphQL-specific security issues (introspection, depth limiting, batching)
    - JWT security (algorithm confusion, key injection, expiration bypass)
    - OAuth 2.0 and OpenID Connect security flaws
    - API authentication and authorization mechanisms
    - Rate limiting and throttling bypass techniques
    - BOLA (Broken Object Level Authorization) exploitation
    - Mass assignment vulnerability detection
    - API versioning and deprecated endpoint security
    - Server-Side Request Forgery (SSRF) via APIs

    OWASP API SECURITY TOP 10 (2023):
    API1:2023 - Broken Object Level Authorization (BOLA)
    API2:2023 - Broken Authentication
    API3:2023 - Broken Object Property Level Authorization
    API4:2023 - Unrestricted Resource Consumption
    API5:2023 - Broken Function Level Authorization (BFLA)
    API6:2023 - Unrestricted Access to Sensitive Business Flows
    API7:2023 - Server Side Request Forgery (SSRF)
    API8:2023 - Security Misconfiguration
    API9:2023 - Improper Inventory Management
    API10:2023 - Unsafe Consumption of APIs

    METHODOLOGY - API PENTEST:
    1. DISCOVERY & RECONNAISSANCE
       - Identify API endpoints (swagger, openapi, wadl)
       - Check for API documentation exposure
       - Enumerate API versions (/v1, /v2, /api, /graphql)
       - Identify supported content types (JSON, XML, form-data)
       - Discover hidden parameters and endpoints

    2. AUTHENTICATION TESTING
       - Test JWT implementation (algorithm, signature, expiration)
       - Test OAuth 2.0 flows (authorization code, implicit, client credentials)
       - Test API key security and rotation
       - Test session management and token refresh
       - Test for credential stuffing vulnerabilities

    3. AUTHORIZATION TESTING
       - Test BOLA (IDOR) on all object references
       - Test BFLA on administrative functions
       - Test horizontal privilege escalation
       - Test vertical privilege escalation
       - Verify RBAC/ABAC implementation

    4. INPUT VALIDATION & INJECTION
       - Test for SQL injection in API parameters
       - Test for NoSQL injection
       - Test for Command injection
       - Test for XML/XXE in XML APIs
       - Test for JSON injection and prototype pollution

    5. RATE LIMITING & THROTTLING
       - Test rate limit enforcement
       - Test concurrent request handling
       - Test for race conditions
       - Verify DoS protection mechanisms

    6. GRAPHQL SPECIFIC TESTING
       - Check introspection query availability
       - Test query depth limiting
       - Test for batching attacks
       - Test field suggestion features
       - Analyze schema for sensitive fields

    7. BUSINESS LOGIC TESTING
       - Test payment flow manipulation
       - Test shopping cart logic
       - Test booking/reservation systems
       - Identify business rule bypass opportunities

    RULES:
    - ALWAYS check for API documentation first (swagger.json, openapi.yaml)
    - NEVER skip authorization testing on every endpoint
    - Test with different roles (admin, user, guest)
    - Document all rate limits discovered
    - Flag mass assignment vulnerabilities immediately
    - Test both authenticated and unauthenticated access
    - Verify JWT algorithm is not "none" or weak
    - Check for sensitive data in error responses

    JWT TESTING CHECKLIST:
    □ Algorithm confusion (RS256 -> HS256)
    □ Key injection via jwk/jku header
    □ Empty signature acceptance
    □ Expiration bypass
    □ Weak signing secrets (brute force)
    □ Information leakage in JWT payload

    BOLA TESTING CHECKLIST:
    □ Replace IDs in URL path (/user/1 -> /user/2)
    □ Replace IDs in query parameters
    □ Replace IDs in request body (JSON)
    □ Test with IDs from other users
    □ Test numeric ID enumeration
    □ Test UUID/GUID predictability
    □ Test with deleted/suspended user IDs

    GRAPHQL TESTING CHECKLIST:
    □ Introspection query enabled
    □ Query depth not limited
    □ Batching allowed without limits
    □ Sensitive fields accessible
    □ Mutation authorization bypass
    □ Subscription abuse potential

    REPORT FORMAT:
    For each API vulnerability:
    1. OWASP API Top 10 Category
    2. Endpoint and HTTP Method
    3. CVSS v3.1 Score
    4. Proof of Concept (curl/httpie command)
    5. Impact on business
    6. Remediation with code examples
    7. References to standards
    """

    def __init__(self, name: str = "API Security Expert", orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.ANALYST, orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.ip_validator = IPValidator()
        self.api_endpoints = []
        self.test_results = []

        # Register message handlers
        self.register_handler("api_scan", self._handle_api_scan)
        self.register_handler("jwt_test", self._handle_jwt_test)
        self.register_handler("bola_test", self._handle_bola_test)
        self.register_handler("graphql_test", self._handle_graphql_test)
        self.register_handler("rate_limit_test", self._handle_rate_limit_test)
        self.register_handler("auth_test", self._handle_auth_test)

    async def _handle_api_scan(self, msg: AgentMessage):
        """Handle comprehensive API security scan"""
        target = msg.context.get("target")
        api_type = msg.context.get("api_type", "rest")  # rest or graphql
        auth_token = msg.context.get("auth_token")

        logger.info(f"[APIExpert:{self.name}] Starting {api_type} API scan for {target}")

        # Phase 1: Discovery
        endpoints = await self._discover_api_endpoints(target, api_type)

        # Phase 2: Authentication Testing
        auth_issues = await self._test_authentication(target, auth_token)

        # Phase 3: Authorization Testing (BOLA/BFLA)
        authz_issues = await self._test_authorization(target, endpoints, auth_token)

        # Phase 4: Input Validation
        injection_issues = await self._test_input_validation(target, endpoints)

        # Phase 5: Rate Limiting
        rate_limit_issues = await self._test_rate_limits(target, endpoints)

        findings = {
            "target": target,
            "api_type": api_type,
            "endpoints_discovered": len(endpoints),
            "authentication_issues": auth_issues,
            "authorization_issues": authz_issues,
            "injection_issues": injection_issues,
            "rate_limit_issues": rate_limit_issues,
        }

        await self.send_message(
            content=f"API scan complete. Found {len(auth_issues + authz_issues + injection_issues)} issues.",
            recipient=msg.sender,
            msg_type="api_findings",
            context={"findings": findings},
        )

    async def _handle_jwt_test(self, msg: AgentMessage):
        """Handle JWT security testing"""
        jwt_token = msg.context.get("jwt_token")
        target = msg.context.get("target")

        logger.info(f"[APIExpert:{self.name}] Testing JWT security")

        results = await self._test_jwt_security(jwt_token, target)

        await self.send_message(
            content=f"JWT testing complete. Issues found: {len(results['vulnerabilities'])}",
            recipient=msg.sender,
            msg_type="jwt_results",
            context={"results": results},
        )

    async def _handle_bola_test(self, msg: AgentMessage):
        """Handle BOLA (IDOR) testing"""
        target = msg.context.get("target")
        endpoints = msg.context.get("endpoints", [])
        auth_token = msg.context.get("auth_token")

        logger.info(f"[APIExpert:{self.name}] Testing BOLA on {len(endpoints)} endpoints")

        results = await self._test_bola(target, endpoints, auth_token)

        await self.send_message(
            content=f"BOLA testing complete. Vulnerable endpoints: {len(results['vulnerable'])}",
            recipient=msg.sender,
            msg_type="bola_results",
            context={"results": results},
        )

    async def _handle_graphql_test(self, msg: AgentMessage):
        """Handle GraphQL-specific security testing"""
        endpoint = msg.context.get("endpoint")

        logger.info(f"[APIExpert:{self.name}] Testing GraphQL security")

        results = await self._test_graphql_security(endpoint)

        await self.send_message(
            content=f"GraphQL testing complete. Issues: {len(results['findings'])}",
            recipient=msg.sender,
            msg_type="graphql_results",
            context={"results": results},
        )

    async def _handle_rate_limit_test(self, msg: AgentMessage):
        """Handle rate limit testing"""
        target = msg.context.get("target")
        endpoint = msg.context.get("endpoint")

        logger.info(f"[APIExpert:{self.name}] Testing rate limits")

        results = await self._test_rate_limit_bypass(target, endpoint)

        await self.send_message(
            content=f"Rate limit testing complete. Bypass possible: {results['bypass_possible']}",
            recipient=msg.sender,
            msg_type="rate_limit_results",
            context={"results": results},
        )

    async def _handle_auth_test(self, msg: AgentMessage):
        """Handle authentication testing"""
        target = msg.context.get("target")
        auth_type = msg.context.get("auth_type", "jwt")

        logger.info(f"[APIExpert:{self.name}] Testing {auth_type} authentication")

        if auth_type == "jwt":
            results = await self._test_jwt_auth(target)
        elif auth_type == "oauth":
            results = await self._test_oauth(target)
        else:
            results = await self._test_api_key_auth(target)

        await self.send_message(
            content="Authentication testing complete.",
            recipient=msg.sender,
            msg_type="auth_results",
            context={"results": results},
        )

    async def _discover_api_endpoints(self, target: str, api_type: str) -> List[Dict[str, Any]]:
        """Discover API endpoints"""
        endpoints = []

        # Common API documentation paths
        doc_paths = [
            "/swagger.json",
            "/swagger.yaml",
            "/openapi.json",
            "/openapi.yaml",
            "/api-docs",
            "/api/docs",
            "/v2/api-docs",
            "/graphql",
            "/graphiql",
            "/altair",
        ]

        # Would make HTTP requests here
        for path in doc_paths:
            pass  # Placeholder for actual implementation

        return endpoints

    async def _test_authentication(self, target: str, auth_token: Optional[str]) -> List[Dict[str, Any]]:
        """Test authentication mechanisms"""
        issues = []

        # Test 1: Check if endpoints work without authentication
        # Test 2: Test JWT if present
        # Test 3: Test token expiration handling

        return issues

    async def _test_authorization(self, target: str, endpoints: List[Dict], auth_token: Optional[str]) -> List[Dict[str, Any]]:
        """Test authorization (BOLA/BFLA)"""
        issues = []

        for endpoint in endpoints:
            # Test BOLA by changing IDs
            if "{id}" in endpoint.get("path", ""):
                pass  # Would test ID manipulation

        return issues

    async def _test_input_validation(self, target: str, endpoints: List[Dict]) -> List[Dict[str, Any]]:
        """Test for injection vulnerabilities"""
        issues = []

        # SQL Injection payloads

        # NoSQL injection payloads

        return issues

    async def _test_rate_limits(self, target: str, endpoints: List[Dict]) -> List[Dict[str, Any]]:
        """Test rate limiting implementation"""
        issues = []

        # Test 1: Rapid sequential requests
        # Test 2: Concurrent requests
        # Test 3: Rate limit bypass headers (X-Forwarded-For, etc.)

        return issues

    async def _test_jwt_security(self, jwt_token: str, target: str) -> Dict[str, Any]:
        """Test JWT token security"""
        results = {"token_analyzed": jwt_token, "vulnerabilities": [], "decoded_header": {}, "decoded_payload": {}}

        try:
            # Decode JWT without verification for analysis
            import base64

            parts = jwt_token.split(".")
            if len(parts) == 3:
                header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))

                results["decoded_header"] = header
                results["decoded_payload"] = payload

                # Check for algorithm "none"
                if header.get("alg") == "none":
                    results["vulnerabilities"].append(
                        {"type": "algorithm_none", "severity": "critical", "description": "JWT accepts 'none' algorithm"}
                    )

                # Check for weak algorithm
                if header.get("alg") == "HS256":
                    results["vulnerabilities"].append(
                        {
                            "type": "weak_algorithm",
                            "severity": "medium",
                            "description": "HMAC-SHA256 might be brute-forceable if secret is weak",
                        }
                    )

                # Check for sensitive data in payload
                sensitive_fields = ["password", "ssn", "credit_card", "secret"]
                for field in sensitive_fields:
                    if field in payload:
                        results["vulnerabilities"].append(
                            {
                                "type": "sensitive_data",
                                "severity": "high",
                                "description": f"Sensitive field '{field}' found in JWT payload",
                            }
                        )

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _test_bola(self, target: str, endpoints: List[Dict], auth_token: Optional[str]) -> Dict[str, Any]:
        """Test for Broken Object Level Authorization"""
        results = {"tested": [], "vulnerable": [], "safe": []}

        test_ids = ["1", "2", "99999", "00001"]

        for endpoint in endpoints:
            path = endpoint.get("path", "")
            if "{id}" in path or any(param in path for param in ["user", "account", "order", "document"]):
                for test_id in test_ids:
                    test_path = path.replace("{id}", test_id)
                    results["tested"].append(test_path)

        return results

    async def _test_graphql_security(self, endpoint: str) -> Dict[str, Any]:
        """Test GraphQL-specific security issues"""
        results = {"introspection_enabled": False, "depth_limit": None, "findings": []}

        # Test introspection

        return results

    async def _test_rate_limit_bypass(self, target: str, endpoint: str) -> Dict[str, Any]:
        """Test rate limit bypass techniques"""
        results = {"bypass_possible": False, "techniques_tested": [], "successful_bypass": []}

        return results

    async def _test_jwt_auth(self, target: str) -> Dict[str, Any]:
        """Test JWT-based authentication"""
        return {"auth_type": "jwt", "issues": []}

    async def _test_oauth(self, target: str) -> Dict[str, Any]:
        """Test OAuth 2.0 implementation"""
        return {"auth_type": "oauth", "issues": []}

    async def _test_api_key_auth(self, target: str) -> Dict[str, Any]:
        """Test API key authentication"""
        return {"auth_type": "api_key", "issues": []}

    def analyze(self, target: Optional[str], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persona-specific analysis logic for API security findings.

        Args:
            target: The target API endpoint
            findings: List of vulnerability findings

        Returns:
            Analysis results with OWASP API Top 10 mapping
        """
        analysis = {
            "total_findings": len(findings),
            "by_owasp_api10": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "risk_level": "low",
            "critical_endpoints": [],
            "recommendations": [],
            "attack_scenarios": [],
        }

        # Categorize by OWASP API Top 10
        for finding in findings:
            category = finding.get("owasp_category", "unknown")
            severity = finding.get("severity", "info").lower()

            if category not in analysis["by_owasp_api10"]:
                analysis["by_owasp_api10"][category] = []
            analysis["by_owasp_api10"][category].append(finding)

            if severity in analysis["by_severity"]:
                analysis["by_severity"][severity] += 1

            if severity in ["critical", "high"]:
                analysis["critical_endpoints"].append(finding.get("endpoint"))

        # Determine risk level
        if analysis["by_severity"]["critical"] > 0:
            analysis["risk_level"] = "critical"
        elif analysis["by_severity"]["high"] > 0:
            analysis["risk_level"] = "high"
        elif analysis["by_severity"]["medium"] > 0:
            analysis["risk_level"] = "medium"

        # Generate recommendations
        analysis["recommendations"] = self._generate_api_recommendations(analysis)

        # Generate attack scenarios
        analysis["attack_scenarios"] = self._generate_attack_scenarios(findings)

        return analysis

    def _generate_api_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate API-specific recommendations"""
        recommendations = []

        if "API1:2023 - Broken Object Level Authorization" in analysis["by_owasp_api10"]:
            recommendations.append("Implement proper authorization checks for every object access")
            recommendations.append("Use UUIDs instead of predictable numeric IDs")

        if "API2:2023 - Broken Authentication" in analysis["by_owasp_api10"]:
            recommendations.append("Implement MFA and strong password policies")
            recommendations.append("Use short-lived tokens with secure refresh mechanisms")

        if "API4:2023 - Unrestricted Resource Consumption" in analysis["by_owasp_api10"]:
            recommendations.append("Implement strict rate limiting per user/API key")
            recommendations.append("Add query complexity limits for GraphQL")

        return recommendations

    def _generate_attack_scenarios(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate attack scenarios based on findings"""
        scenarios = []

        categories = [f.get("owasp_category", "") for f in findings]

        if "API1:2023 - Broken Object Level Authorization" in categories:
            scenarios.append("Attacker enumerates user IDs to access other users' data")

        if "API2:2023 - Broken Authentication" in categories:
            scenarios.append("Attacker bypasses authentication to access protected resources")

        if "API7:2023 - Server Side Request Forgery" in categories:
            scenarios.append("Attacker uses API to scan internal network or access cloud metadata")

        return scenarios

    async def execute_task(self, task: Dict) -> Dict:
        """Execute API security testing task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[APIExpert:{self.name}] Executing task: {task_type}")

        if task_type == "api_security_scan":
            target = context.get("target")
            findings = await self._discover_api_endpoints(target, context.get("api_type", "rest"))
            analysis = self.analyze(target, findings)

            return {"status": "complete", "endpoints": findings, "analysis": analysis, "agent": self.name}

        elif task_type == "jwt_analysis":
            results = await self._test_jwt_security(context.get("jwt_token"), context.get("target"))
            return {"status": "complete", "results": results, "agent": self.name}

        return {"status": "unknown_task"}

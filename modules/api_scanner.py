#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zen-Ai-Pentest API Scanner - Basis-Modul
========================================

Dieses Modul enthält die Basisklasse für API-Scanner mit:
- API Discovery
- Endpoint Enumeration
- Parameter Analysis
- Authentication Testing
- Rate Limit Testing

Author: Zen-Ai-Pentest Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("api_scanner")


class VulnerabilitySeverity(Enum):
    """Schweregrad von Schwachstellen"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Typen von API-Schwachstellen"""

    # Authentifizierung & Autorisierung
    MISSING_AUTH = "missing_authentication"
    WEAK_AUTH = "weak_authentication"
    BROKEN_ACCESS_CONTROL = "broken_access_control"
    JWT_VULNERABILITY = "jwt_vulnerability"

    # Injection
    SQL_INJECTION = "sql_injection"
    NOSQL_INJECTION = "nosql_injection"
    COMMAND_INJECTION = "command_injection"
    XSS = "cross_site_scripting"

    # Konfiguration
    INFORMATION_DISCLOSURE = "information_disclosure"
    CORS_MISCONFIGURATION = "cors_misconfiguration"
    SECURITY_HEADERS_MISSING = "security_headers_missing"

    # Rate Limiting
    NO_RATE_LIMIT = "no_rate_limiting"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"

    # Input Validation
    MASS_ASSIGNMENT = "mass_assignment"
    TYPE_CONFUSION = "type_confusion"

    # GraphQL spezifisch
    GRAPHQL_INTROSPECTION = "graphql_introspection_enabled"
    GRAPHQL_DEPTH_ATTACK = "graphql_depth_attack"
    GRAPHQL_BATCHING = "graphql_batching"


@dataclass
class Vulnerability:
    """Repräsentiert eine gefundene Schwachstelle"""

    vuln_type: VulnerabilityType
    severity: VulnerabilitySeverity
    title: str
    description: str
    endpoint: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation: str = ""
    cvss_score: Optional[float] = None
    references: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.vuln_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "endpoint": self.endpoint,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "cvss_score": self.cvss_score,
            "references": self.references,
            "timestamp": self.timestamp,
        }


@dataclass
class APIEndpoint:
    """Repräsentiert einen API-Endpunkt"""

    path: str
    method: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    authentication_required: bool = False
    response_schema: Optional[Dict] = None
    discovered_from: Optional[str] = None

    def __hash__(self):
        return hash((self.path.lower(), self.method.upper()))

    def __eq__(self, other):
        if isinstance(other, APIEndpoint):
            return (self.path.lower(), self.method.upper()) == (other.path.lower(), other.method.upper())
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "parameters": self.parameters,
            "headers": self.headers,
            "authentication_required": self.authentication_required,
            "response_schema": self.response_schema,
            "discovered_from": self.discovered_from,
        }


@dataclass
class ScanResult:
    """Ergebnis eines API-Scans"""

    target_url: str
    scan_type: str
    start_time: float
    end_time: Optional[float] = None
    endpoints: List[APIEndpoint] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_vulnerability(self, vuln: Vulnerability):
        self.vulnerabilities.append(vuln)

    def add_endpoint(self, endpoint: APIEndpoint):
        if endpoint not in self.endpoints:
            self.endpoints.append(endpoint)

    def get_vulnerabilities_by_severity(self, severity: VulnerabilitySeverity) -> List[Vulnerability]:
        return [v for v in self.vulnerabilities if v.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_url": self.target_url,
            "scan_type": self.scan_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.end_time else None,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "summary": {
                "total_endpoints": len(self.endpoints),
                "total_vulnerabilities": len(self.vulnerabilities),
                "severity_counts": {
                    "critical": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.CRITICAL)),
                    "high": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.HIGH)),
                    "medium": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.MEDIUM)),
                    "low": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.LOW)),
                    "info": len(self.get_vulnerabilities_by_severity(VulnerabilitySeverity.INFO)),
                },
            },
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class BaseAPIScanner(ABC):
    """
    Basisklasse für alle API-Scanner

    Implementiert gemeinsame Funktionalität für:
    - HTTP-Request-Handling
    - Rate Limiting
    - Authentifizierung
    - Schwachstellen-Tracking
    """

    # Häufige API-Pfade für Discovery
    COMMON_API_PATHS = [
        "/api",
        "/api/v1",
        "/api/v2",
        "/api/v3",
        "/rest",
        "/rest/v1",
        "/rest/v2",
        "/v1",
        "/v2",
        "/v3",
        "/swagger.json",
        "/swagger.yaml",
        "/api-docs",
        "/openapi.json",
        "/openapi.yaml",
        "/graphql",
        "/graphiql",
        "/.well-known/openapi.json",
        "/api/swagger-ui.html",
        "/api/docs",
        "/api/explorer",
    ]

    # Häufige Endpunkte für Enumeration
    COMMON_ENDPOINTS = [
        "users",
        "user",
        "accounts",
        "account",
        "auth",
        "login",
        "logout",
        "register",
        "products",
        "product",
        "items",
        "item",
        "orders",
        "order",
        "cart",
        "checkout",
        "posts",
        "post",
        "articles",
        "article",
        "comments",
        "comment",
        "search",
        "filter",
        "admin",
        "dashboard",
        "settings",
        "files",
        "upload",
        "download",
        "health",
        "status",
        "ping",
        "config",
        "configuration",
        "internal",
        "debug",
        "test",
    ]

    # Payloads für Injection-Tests
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "' OR 1=1",
        "' OR 1=1 --",
        "1' AND 1=1 --",
        "1' AND 1=2 --",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "1 AND 1=1",
        "1 AND 1=2",
        "1 OR 1=1",
        "1' OR '1'='1",
        "1' AND '1'='1",
        "1' AND '1'='2",
    ]

    NOSQL_INJECTION_PAYLOADS = [
        '{"$gt": ""}',
        '{"$ne": null}',
        '{"$exists": true}',
        '{"$regex": ".*"}',
        '{"$where": "this"}',
        '{"$gt": {}}',
        '{"$lt": {}}',
    ]

    COMMAND_INJECTION_PAYLOADS = [
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; whoami",
        "| whoami",
        "; id",
        "| id",
        "&& whoami",
        "|| whoami",
    ]

    def __init__(self, target_url: str, **kwargs):
        """
        Initialisiert den Scanner

        Args:
            target_url: Die Ziel-URL
            **kwargs: Zusätzliche Konfiguration
        """
        self.target_url = target_url.rstrip("/")
        self.parsed_url = urlparse(target_url)

        # Konfiguration
        self.config = {
            "timeout": kwargs.get("timeout", 30),
            "max_retries": kwargs.get("max_retries", 3),
            "rate_limit_delay": kwargs.get("rate_limit_delay", 0.5),
            "max_concurrent_requests": kwargs.get("max_concurrent_requests", 10),
            "follow_redirects": kwargs.get("follow_redirects", True),
            "verify_ssl": kwargs.get("verify_ssl", True),
            "user_agent": kwargs.get("user_agent", "Zen-Ai-Pentest-Scanner/1.0"),
            "headers": kwargs.get("headers", {}),
            "proxy": kwargs.get("proxy", None),
            "authentication": kwargs.get("authentication", None),
            "cookies": kwargs.get("cookies", {}),
        }

        # Session-Tracking
        self.session_cookies: Dict[str, str] = {}
        self.request_count = 0
        self.last_request_time = 0.0

        # Ergebnis
        self.result = ScanResult(target_url=target_url, scan_type=self.__class__.__name__, start_time=time.time())

        # HTTP Client (wird von Unterklassen implementiert)
        self.http_client = None

        logger.info(f"Scanner initialisiert für: {target_url}")

    def _get_headers(self, additional_headers: Optional[Dict] = None) -> Dict[str, str]:
        """Erstellt HTTP-Header für Requests"""
        headers = {
            "User-Agent": self.config["user_agent"],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        headers.update(self.config["headers"])

        if additional_headers:
            headers.update(additional_headers)

        # Füge Authentifizierung hinzu
        if self.config["authentication"]:
            auth = self.config["authentication"]
            if auth.get("type") == "bearer":
                headers["Authorization"] = f"Bearer {auth.get('token', '')}"
            elif auth.get("type") == "basic":
                import base64

                credentials = base64.b64encode(f"{auth.get('username', '')}:{auth.get('password', '')}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
            elif auth.get("type") == "api_key":
                header_name = auth.get("header_name", "X-API-Key")
                headers[header_name] = auth.get("key", "")

        return headers

    async def _rate_limited_request(self):
        """Implementiert Rate-Limiting zwischen Requests"""
        if self.config["rate_limit_delay"] > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config["rate_limit_delay"]:
                await asyncio.sleep(self.config["rate_limit_delay"] - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1

    @abstractmethod
    async def _make_request(
        self, method: str, url: str, headers: Optional[Dict] = None, data: Optional[Any] = None, params: Optional[Dict] = None
    ) -> Tuple[int, Dict[str, str], Any]:
        """
        Führt einen HTTP-Request durch

        Returns:
            Tuple von (status_code, headers, body)
        """
        pass

    async def discover_api(self) -> List[str]:
        """
        Entdeckt API-Endpunkte durch Enumeration häufiger Pfade

        Returns:
            Liste gefundener API-Basis-URLs
        """
        logger.info("Starte API Discovery...")
        discovered_apis = []

        tasks = []
        for path in self.COMMON_API_PATHS:
            url = urljoin(self.target_url, path)
            tasks.append(self._check_api_path(url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, result in zip([urljoin(self.target_url, p) for p in self.COMMON_API_PATHS], results):
            if isinstance(result, Exception):
                logger.debug(f"Fehler bei {url}: {result}")
                continue
            if result:
                discovered_apis.append(url)
                logger.info(f"API gefunden: {url}")

        # Speichere in Metadaten
        self.result.metadata["discovered_apis"] = discovered_apis

        return discovered_apis

    async def _check_api_path(self, url: str) -> bool:
        """Prüft ob ein Pfad eine API ist"""
        try:
            await self._rate_limited_request()
            status, headers, body = await self._make_request("GET", url)

            # API-Indikatoren
            content_type = headers.get("content-type", "").lower()

            # Prüfe auf API-typische Antworten
            if status == 200:
                if "application/json" in content_type:
                    return True
                if isinstance(body, (dict, list)):
                    return True

            # Swagger/OpenAPI Dokumentation
            if any(x in url.lower() for x in ["swagger", "openapi", "api-docs"]):
                if status == 200:
                    return True

            # GraphQL Endpunkte
            if "graphql" in url.lower():
                if status in [200, 400]:  # GraphQL gibt oft 400 bei fehlender Query
                    return True

            # Prüfe auf API-typische Fehlermeldungen
            if status in [401, 403, 405]:
                # Diese Statuscodes deuten oft auf geschützte APIs hin
                return True

            return False

        except Exception as e:
            logger.debug(f"Fehler beim Prüfen von {url}: {e}")
            return False

    async def enumerate_endpoints(self, base_url: str) -> List[APIEndpoint]:
        """
        Enumeriert API-Endpunkte

        Args:
            base_url: Die Basis-URL der API

        Returns:
            Liste gefundener Endpunkte
        """
        logger.info(f"Starte Endpoint Enumeration für: {base_url}")

        endpoints = []
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

        # Teste häufige Endpunkte
        tasks = []
        for endpoint in self.COMMON_ENDPOINTS:
            for method in methods:
                url = f"{base_url}/{endpoint}"
                tasks.append(self._test_endpoint(url, method))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                endpoints.append(result)
                self.result.add_endpoint(result)

        logger.info(f"{len(endpoints)} Endpunkte gefunden")
        return endpoints

    async def _test_endpoint(self, url: str, method: str) -> Optional[APIEndpoint]:
        """Testet einen einzelnen Endpunkt"""
        try:
            await self._rate_limited_request()
            status, headers, body = await self._make_request(method, url)

            # Gültige Endpunkte erkennen
            if status not in [404, 501, 502, 503]:
                # Extrahiere Parameter aus der Antwort
                params = self._extract_parameters(body)

                # Prüfe auf Authentifizierung
                auth_required = status in [401, 403]

                endpoint = APIEndpoint(
                    path=url,
                    method=method,
                    parameters=params,
                    headers=dict(headers),
                    authentication_required=auth_required,
                    response_schema=self._infer_schema(body) if body else None,
                )

                return endpoint

            return None

        except Exception as e:
            logger.debug(f"Fehler beim Testen von {method} {url}: {e}")
            return None

    def _extract_parameters(self, data: Any, prefix: str = "") -> List[Dict[str, Any]]:
        """Extrahiert Parameter aus einer API-Antwort"""
        params = []

        if isinstance(data, dict):
            for key, value in data.items():
                param_info = {
                    "name": f"{prefix}.{key}" if prefix else key,
                    "type": type(value).__name__,
                    "required": False,
                    "example": value if not isinstance(value, (dict, list)) else None,
                }
                params.append(param_info)

                # Rekursiv für verschachtelte Objekte
                if isinstance(value, (dict, list)):
                    params.extend(self._extract_parameters(value, param_info["name"]))

        elif isinstance(data, list) and data:
            # Nimm das erste Element als Beispiel
            params.extend(self._extract_parameters(data[0], f"{prefix}[]"))

        return params

    def _infer_schema(self, data: Any) -> Dict[str, Any]:
        """Leitet ein JSON Schema aus Beispieldaten ab"""
        if isinstance(data, dict):
            return {"type": "object", "properties": {k: self._infer_schema(v) for k, v in data.items()}}
        elif isinstance(data, list):
            if data:
                return {"type": "array", "items": self._infer_schema(data[0])}
            return {"type": "array"}
        elif isinstance(data, str):
            return {"type": "string"}
        elif isinstance(data, int):
            return {"type": "integer"}
        elif isinstance(data, float):
            return {"type": "number"}
        elif isinstance(data, bool):
            return {"type": "boolean"}
        else:
            return {"type": "null"}

    async def test_authentication(self, endpoint: APIEndpoint) -> List[Vulnerability]:
        """
        Testet Authentifizierungsmechanismen

        Args:
            endpoint: Der zu testende Endpunkt

        Returns:
            Liste gefundener Schwachstellen
        """
        logger.info(f"Teste Authentifizierung für: {endpoint.path}")
        vulnerabilities = []

        # Test 1: Zugriff ohne Authentifizierung
        if endpoint.authentication_required:
            try:
                await self._rate_limited_request()
                status, headers, body = await self._make_request(
                    endpoint.method, endpoint.path, headers={"Authorization": ""}  # Entferne Auth-Header
                )

                if status not in [401, 403]:
                    vuln = Vulnerability(
                        vuln_type=VulnerabilityType.MISSING_AUTH,
                        severity=VulnerabilitySeverity.HIGH,
                        title="Fehlende Authentifizierung",
                        description=f"Endpunkt {endpoint.path} ist ohne Authentifizierung zugänglich",
                        endpoint=endpoint.path,
                        evidence={"status_code": status, "response": str(body)[:500]},
                        remediation="Implementiere eine starke Authentifizierung für diesen Endpunkt",
                    )
                    vulnerabilities.append(vuln)
                    self.result.add_vulnerability(vuln)

            except Exception as e:
                logger.debug(f"Fehler beim Auth-Test: {e}")

        # Test 2: Schwache Authentifizierung
        await self._test_weak_auth(endpoint, vulnerabilities)

        # Test 3: JWT-Schwachstellen
        await self._test_jwt_vulnerabilities(endpoint, vulnerabilities)

        return vulnerabilities

    async def _test_weak_auth(self, endpoint: APIEndpoint, vulnerabilities: List[Vulnerability]):
        """Testet auf schwache Authentifizierungsmechanismen"""
        weak_tokens = ["admin", "password", "123456", "token", "secret", "test", "guest", "user", "api", "key"]

        for token in weak_tokens:
            try:
                await self._rate_limited_request()
                headers = {"Authorization": f"Bearer {token}"}
                status, _, body = await self._make_request(endpoint.method, endpoint.path, headers=headers)

                if status == 200:
                    vuln = Vulnerability(
                        vuln_type=VulnerabilityType.WEAK_AUTH,
                        severity=VulnerabilitySeverity.CRITICAL,
                        title="Schwache Authentifizierung",
                        description=f"API akzeptiert schwaches Token: {token}",
                        endpoint=endpoint.path,
                        evidence={"weak_token": token},
                        remediation="Verwende starke, zufällig generierte Tokens",
                    )
                    vulnerabilities.append(vuln)
                    self.result.add_vulnerability(vuln)
                    break

            except (ConnectionError, TimeoutError, aiohttp.ClientError):
                pass

    async def _test_jwt_vulnerabilities(self, endpoint: APIEndpoint, vulnerabilities: List[Vulnerability]):
        """Testet auf JWT-spezifische Schwachstellen"""
        # Teste für 'none' Algorithmus
        jwt_none = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QiLCJpYXQiOjE1MTYyMzkwMjJ9."

        try:
            await self._rate_limited_request()
            headers = {"Authorization": f"Bearer {jwt_none}"}
            status, _, body = await self._make_request(endpoint.method, endpoint.path, headers=headers)

            if status == 200:
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.JWT_VULNERABILITY,
                    severity=VulnerabilitySeverity.CRITICAL,
                    title="JWT 'none' Algorithmus akzeptiert",
                    description="API akzeptiert JWTs mit 'none' Algorithmus",
                    endpoint=endpoint.path,
                    evidence={"jwt": jwt_none},
                    remediation="Verbiete den 'none' Algorithmus in JWT-Validierung",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

        except (ConnectionError, TimeoutError, aiohttp.ClientError):
            pass

    async def test_rate_limiting(self, endpoint: APIEndpoint, requests: int = 50) -> List[Vulnerability]:
        """
        Testet Rate-Limiting

        Args:
            endpoint: Der zu testende Endpunkt
            requests: Anzahl der Requests für den Test

        Returns:
            Liste gefundener Schwachstellen
        """
        logger.info(f"Teste Rate-Limiting für: {endpoint.path}")
        vulnerabilities = []

        # Deaktiviere Rate-Limiting für den Test
        original_delay = self.config["rate_limit_delay"]
        self.config["rate_limit_delay"] = 0

        try:
            responses = []
            for i in range(requests):
                status, headers, body = await self._make_request(endpoint.method, endpoint.path)
                responses.append(
                    {
                        "status": status,
                        "retry_after": headers.get("retry-after"),
                        "rate_limit": headers.get("x-rate-limit"),
                        "rate_limit_remaining": headers.get("x-rate-limit-remaining"),
                    }
                )

            # Analysiere Antworten
            success_count = sum(1 for r in responses if r["status"] == 200)
            rate_limit_headers = any(r.get("rate_limit") for r in responses)
            blocked_count = sum(1 for r in responses if r["status"] == 429)

            # Kein Rate-Limiting erkannt
            if success_count == requests and not rate_limit_headers:
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.NO_RATE_LIMIT,
                    severity=VulnerabilitySeverity.MEDIUM,
                    title="Kein Rate-Limiting",
                    description=f"API hat kein Rate-Limiting für {endpoint.path}",
                    endpoint=endpoint.path,
                    evidence={
                        "requests_sent": requests,
                        "successful_requests": success_count,
                        "rate_limit_headers": rate_limit_headers,
                    },
                    remediation="Implementiere Rate-Limiting um Brute-Force und DoS zu verhindern",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

            # Rate-Limiting vorhanden aber umgangen
            elif blocked_count > 0 and blocked_count < requests * 0.5:
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.RATE_LIMIT_BYPASS,
                    severity=VulnerabilitySeverity.MEDIUM,
                    title="Rate-Limiting umgangen",
                    description="Rate-Limiting konnte teilweise umgangen werden",
                    endpoint=endpoint.path,
                    evidence={"blocked_requests": blocked_count, "successful_requests": success_count},
                    remediation="Stärkere Rate-Limiting-Implementierung erforderlich",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

        finally:
            self.config["rate_limit_delay"] = original_delay

        return vulnerabilities

    async def test_injection(self, endpoint: APIEndpoint) -> List[Vulnerability]:
        """
        Testet auf Injection-Schwachstellen

        Args:
            endpoint: Der zu testende Endpunkt

        Returns:
            Liste gefundener Schwachstellen
        """
        logger.info(f"Teste Injection für: {endpoint.path}")
        vulnerabilities = []

        # Teste SQL Injection
        for payload in self.SQL_INJECTION_PAYLOADS:
            vulns = await self._test_sql_injection(endpoint, payload)
            vulnerabilities.extend(vulns)

        # Teste NoSQL Injection
        for payload in self.NOSQL_INJECTION_PAYLOADS:
            vulns = await self._test_nosql_injection(endpoint, payload)
            vulnerabilities.extend(vulns)

        # Teste Command Injection
        for payload in self.COMMAND_INJECTION_PAYLOADS:
            vulns = await self._test_command_injection(endpoint, payload)
            vulnerabilities.extend(vulns)

        return vulnerabilities

    async def _test_sql_injection(self, endpoint: APIEndpoint, payload: str) -> List[Vulnerability]:
        """Testet auf SQL Injection"""
        vulnerabilities = []

        try:
            await self._rate_limited_request()

            # Teste als Query-Parameter
            params = {"test": payload}
            status, headers, body = await self._make_request("GET", endpoint.path, params=params)

            # SQL-Fehler-Indikatoren
            sql_errors = [
                "sql syntax",
                "mysql_fetch",
                "pg_query",
                "ora-",
                "sqlite_query",
                "sqlserver",
                "jdbc",
                "odbc",
                "syntax error",
                "unexpected",
                "warning: mysql",
            ]

            body_str = str(body).lower()
            if any(error in body_str for error in sql_errors):
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.SQL_INJECTION,
                    severity=VulnerabilitySeverity.CRITICAL,
                    title="SQL Injection",
                    description=f"SQL Injection in {endpoint.path} erkannt",
                    endpoint=endpoint.path,
                    evidence={"payload": payload, "error": body_str[:500]},
                    remediation="Verwende Prepared Statements und parametrisierte Queries",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

        except Exception as e:
            logger.debug(f"Fehler beim SQL Injection Test: {e}")

        return vulnerabilities

    async def _test_nosql_injection(self, endpoint: APIEndpoint, payload: str) -> List[Vulnerability]:
        """Testet auf NoSQL Injection"""
        vulnerabilities = []

        try:
            await self._rate_limited_request()

            # Teste als JSON-Body
            headers = {"Content-Type": "application/json"}
            data = json.loads(payload)

            status, _, body = await self._make_request("POST", endpoint.path, headers=headers, data=data)

            # NoSQL-Fehler-Indikatoren
            nosql_errors = ["mongodb", "bson", "mongoerror", "invalid objectid"]

            body_str = str(body).lower()
            if any(error in body_str for error in nosql_errors):
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.NOSQL_INJECTION,
                    severity=VulnerabilitySeverity.CRITICAL,
                    title="NoSQL Injection",
                    description=f"NoSQL Injection in {endpoint.path} erkannt",
                    endpoint=endpoint.path,
                    evidence={"payload": payload},
                    remediation="Validiere und sanitisiere alle Benutzereingaben",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"Fehler beim NoSQL Injection Test: {e}")

        return vulnerabilities

    async def _test_command_injection(self, endpoint: APIEndpoint, payload: str) -> List[Vulnerability]:
        """Testet auf Command Injection"""
        vulnerabilities = []

        try:
            await self._rate_limited_request()

            params = {"test": payload}
            status, _, body = await self._make_request("GET", endpoint.path, params=params)

            # Command Injection Indikatoren
            cmd_indicators = ["root:", "daemon:", "bin:", "sys:", "uid=", "gid=", "groups="]  # /etc/passwd Inhalt

            body_str = str(body)
            if any(indicator in body_str for indicator in cmd_indicators):
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.COMMAND_INJECTION,
                    severity=VulnerabilitySeverity.CRITICAL,
                    title="Command Injection",
                    description=f"Command Injection in {endpoint.path} erkannt",
                    endpoint=endpoint.path,
                    evidence={"payload": payload, "response": body_str[:500]},
                    remediation="Verwende keine Benutzereingaben in Systembefehlen",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

        except Exception as e:
            logger.debug(f"Fehler beim Command Injection Test: {e}")

        return vulnerabilities

    async def test_security_headers(self, url: str) -> List[Vulnerability]:
        """
        Testet auf fehlende Sicherheits-Header

        Args:
            url: Die zu testende URL

        Returns:
            Liste gefundener Schwachstellen
        """
        logger.info(f"Teste Sicherheits-Header für: {url}")
        vulnerabilities = []

        try:
            await self._rate_limited_request()
            status, headers, _ = await self._make_request("GET", url)

            headers_lower = {k.lower(): v for k, v in headers.items()}

            # Wichtige Sicherheits-Header
            security_headers = {
                "strict-transport-security": "HSTS fehlt",
                "content-security-policy": "CSP fehlt",
                "x-content-type-options": "X-Content-Type-Options fehlt",
                "x-frame-options": "X-Frame-Options fehlt",
                "x-xss-protection": "X-XSS-Protection fehlt",
                "referrer-policy": "Referrer-Policy fehlt",
                "permissions-policy": "Permissions-Policy fehlt",
            }

            missing_headers = []
            for header, description in security_headers.items():
                if header not in headers_lower:
                    missing_headers.append(header)

            if missing_headers:
                vuln = Vulnerability(
                    vuln_type=VulnerabilityType.SECURITY_HEADERS_MISSING,
                    severity=VulnerabilitySeverity.LOW,
                    title="Fehlende Sicherheits-Header",
                    description=f"Folgende Sicherheits-Header fehlen: {', '.join(missing_headers)}",
                    endpoint=url,
                    evidence={"missing_headers": missing_headers},
                    remediation="Implementiere alle empfohlenen Sicherheits-Header",
                )
                vulnerabilities.append(vuln)
                self.result.add_vulnerability(vuln)

            # CORS-Test
            await self._test_cors(url, headers_lower)

        except Exception as e:
            logger.debug(f"Fehler beim Header-Test: {e}")

        return vulnerabilities

    async def _test_cors(self, url: str, headers: Dict[str, str]) -> List[Vulnerability]:
        """Testet CORS-Konfiguration"""
        vulnerabilities = []

        try:
            # Teste mit gefälschtem Origin
            test_headers = {"Origin": "https://evil.com"}

            await self._rate_limited_request()
            status, response_headers, _ = await self._make_request("GET", url, headers=test_headers)

            response_headers_lower = {k.lower(): v for k, v in response_headers.items()}

            allow_origin = response_headers_lower.get("access-control-allow-origin", "")
            allow_credentials = response_headers_lower.get("access-control-allow-credentials", "")

            # Gefährliche CORS-Konfiguration
            if allow_origin == "https://evil.com" or allow_origin == "*":
                if allow_credentials.lower() == "true":
                    vuln = Vulnerability(
                        vuln_type=VulnerabilityType.CORS_MISCONFIGURATION,
                        severity=VulnerabilitySeverity.HIGH,
                        title="Gefährliche CORS-Konfiguration",
                        description="CORS erlaubt beliebige Origins mit Credentials",
                        endpoint=url,
                        evidence={
                            "access-control-allow-origin": allow_origin,
                            "access-control-allow-credentials": allow_credentials,
                        },
                        remediation="Beschränke Access-Control-Allow-Origin auf vertrauenswürdige Domains",
                    )
                    vulnerabilities.append(vuln)
                    self.result.add_vulnerability(vuln)

        except Exception as e:
            logger.debug(f"Fehler beim CORS-Test: {e}")

        return vulnerabilities

    @abstractmethod
    async def scan(self) -> ScanResult:
        """
        Führt den vollständigen Scan durch

        Returns:
            ScanResult mit allen Ergebnissen
        """
        pass

    def finalize_scan(self):
        """Finalisiert den Scan und setzt Endzeit"""
        self.result.end_time = time.time()
        logger.info(f"Scan abgeschlossen. Dauer: {self.result.end_time - self.result.start_time:.2f}s")
        logger.info(f"Gefundene Endpunkte: {len(self.result.endpoints)}")
        logger.info(f"Gefundene Schwachstellen: {len(self.result.vulnerabilities)}")


# Beispiel für die Verwendung
async def example_usage():
    """Beispiel für die Verwendung des BaseAPIScanner"""
    print("""
    === Zen-Ai-Pentest API Scanner ===

    Dies ist die Basisklasse für API-Scanner.

    Verwendung:

    1. REST API Scanner:
       from rest_scanner import RESTAPIScanner
       scanner = RESTAPIScanner("https://api.example.com")
       result = await scanner.scan()
       print(result.to_json())

    2. GraphQL Scanner:
       from graphql_scanner import GraphQLScanner
       scanner = GraphQLScanner("https://api.example.com/graphql")
       result = await scanner.scan()
       print(result.to_json())

    Die Scanner erkennen automatisch:
    - API-Endpunkte
    - Authentifizierungsprobleme
    - Injection-Schwachstellen
    - Rate-Limiting-Probleme
    - Fehlende Sicherheits-Header
    """)


if __name__ == "__main__":
    asyncio.run(example_usage())

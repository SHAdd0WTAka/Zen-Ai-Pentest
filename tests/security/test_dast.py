#!/usr/bin/env python3
"""
================================================================================
DAST (Dynamic Application Security Testing) Tests
================================================================================

⚠️  EDUCATIONAL / PROOF OF CONCEPT  ⚠️

Diese Datei enthält Proof-of-Concept Code für Sicherheitstests und dient
ausschließlich zu Bildungszwecken und autorisierten Penetrationstests.

================================================================================
LEGAL DISCLAIMER / RECHTLICHER HAFTUNGSAUSSCHLUSS
================================================================================

Diese Software ist für autorisierte Sicherheitstests und Bildungszwecke
gedacht. Die Verwendung dieser Tools gegen Systeme ohne ausdrückliche
schriftliche Erlaubnis des Eigentümers ist illegal.

Der Autor übernimmt keine Haftung für:
- Missbrauch dieser Software
- Schäden, die durch unsachgemäße Verwendung entstehen
- Illegale Aktivitäten, die mit dieser Software durchgeführt werden

Verwendung erfolgt auf eigene Gefahr und Verantwortung!

================================================================================
BESCHREIBUNG
================================================================================

Dynamische Sicherheitsanalyse für die Zen-AI-Pentest API.

Diese Tests prüfen:
- Authentifizierungssicherheit (Brute-Force, Session Fixation)
- Injection-Angriffe (SQL, NoSQL, Command, XSS)
- Zugriffskontrolle (IDOR, Privilege Escalation)
- Security Headers
- CSRF-Schutz
- Rate Limiting
- SSRF-Prävention
- Datei-Upload Sicherheit

================================================================================
SICHERHEITSHINWEIS FÜR ANTI-VIRUS SOFTWARE
================================================================================

Diese Datei enthält TEST-PAYLOADS für Sicherheitslücken, die von einigen
Anti-Virus Programmen als bösartig erkannt werden können. Dies ist ein
FALSE POSITIVE - die Payloads werden verwendet, um Sicherheitskontrollen
zu testen, nicht um Schaden anzurichten.

Wenn Ihr AV-Programm diese Datei blockiert:
1. Fügen Sie das Zen-AI-Pentest Verzeichnis zu Ausschlüssen hinzu
2. Oder verwenden Sie die Docker-Version des Frameworks

================================================================================
"""

import pytest
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = [
    pytest.mark.security,
    pytest.mark.dast,
    pytest.mark.asyncio
]

# Test-Konfiguration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:8000')


class TestAuthenticationSecurity:
    """DAST Tests für Authentifizierungssicherheit"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True) as client:
            yield client

    @pytest.mark.asyncio
    async def test_brute_force_protection(self, client):
        """DAST: Brute-Force-Schutz funktioniert"""
        login_attempts = []

        # Mehrere fehlgeschlagene Login-Versuche
        for i in range(20):
            response = await client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': f'wrongpassword{i}'
            })
            login_attempts.append(response.status_code)

        # Nach vielen Fehlversuchen sollte Rate-Limiting greifen
        assert 429 in login_attempts or 403 in login_attempts, \
            "Kein Brute-Force-Schutz erkannt"

    @pytest.mark.asyncio
    async def test_session_fixation_protection(self, client):
        """DAST: Session Fixation Schutz"""
        # Login
        response1 = await client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

        token1 = response1.json().get('access_token')

        # Erneuter Login
        response2 = await client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

        token2 = response2.json().get('access_token')

        # Tokens sollten unterschiedlich sein
        assert token1 != token2, "Session Fixation möglich - Token bleibt gleich"

    @pytest.mark.asyncio
    async def test_token_expiration(self, client):
        """DAST: Token läuft ab"""
        # Login
        login_response = await client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

        token = login_response.json()['access_token']

        # Warte auf Token-Ablauf (angenommen 15 Minuten)
        # In Tests verkürzen wir dies
        # time.sleep(900)  # 15 Minuten

        # Versuche Zugriff mit abgelaufenem Token
        # Dieser Test erfordert eine verkürzte Token-Lebensdauer im Test-Setup

    @pytest.mark.asyncio
    async def test_password_complexity_enforcement(self, client):
        """DAST: Passwort-Komplexität wird erzwungen"""
        # Versuche schwaches Passwort zu setzen
        response = await client.post('/api/v1/auth/register', json={
            'username': 'testuser',
            'password': '123',  # Zu schwach
            'email': 'test@example.com'
        })

        assert response.status_code == 400, \
            "Schwache Passwörter sollten abgelehnt werden"


class TestInjectionAttacks:
    """DAST Tests für Injection-Angriffe"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            login_response = await client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
            token = login_response.json()['access_token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, authenticated_client):
        """DAST: SQL Injection wird blockiert"""
        # Versuche SQL Injection in verschiedenen Parametern
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND 1=1 --",
        ]

        for payload in payloads:
            response = await authenticated_client.get(f'/api/v1/scans?id={payload}')

            # Sollte nicht 500 (Internal Server Error) sein
            assert response.status_code != 500, \
                f"SQL Injection möglich mit Payload: {payload}"

            # Sollte keine Datenbank-Fehler enthalten
            assert 'sql' not in response.text.lower() or \
                   'database' not in response.text.lower(), \
                f"Mögliche SQL Injection: {payload}"

    @pytest.mark.asyncio
    async def test_nosql_injection_protection(self, authenticated_client):
        """DAST: NoSQL Injection wird blockiert"""
        nosql_payloads = [
            {'$gt': ''},
            {'$ne': None},
            {'$regex': '.*'},
        ]

        for payload in nosql_payloads:
            response = await authenticated_client.post('/api/v1/scans', json={
                'target': 'example.com',
                'options': payload
            })

            assert response.status_code != 500, \
                f"NoSQL Injection möglich: {payload}"

    @pytest.mark.asyncio
    async def test_command_injection_protection(self, authenticated_client):
        """DAST: Command Injection wird blockiert"""
        payloads = [
            '; cat /etc/passwd',
            '| whoami',
            '$(id)',
            '`ls -la`',
        ]

        for payload in payloads:
            response = await authenticated_client.post('/api/v1/scans', json={
                'target': f'example.com{payload}',
                'scan_type': 'reconnaissance'
            })

            # Sollte keine System-Informationen preisgeben
            assert 'root:' not in response.text, \
                f"Command Injection möglich: {payload}"
            assert 'uid=' not in response.text, \
                f"Command Injection möglich: {payload}"

    @pytest.mark.asyncio
    async def test_xss_protection(self, authenticated_client):
        """DAST: XSS wird blockiert"""
        xss_payloads = [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert(1)',
            '<svg onload=alert(1)>',
        ]

        for payload in xss_payloads:
            response = await authenticated_client.post('/api/v1/scans', json={
                'target': 'example.com',
                'description': payload
            })

            # Response sollte XSS-Content nicht unescaped enthalten
            if response.status_code == 200:
                assert '<script>' not in response.text or \
                       '&lt;script&gt;' in response.text, \
                    f"XSS möglich: {payload}"


class TestAccessControl:
    """DAST Tests für Zugriffskontrolle"""

    @pytest.fixture
    async def admin_client(self):
        """Fixture für Admin-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            login_response = await client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
            token = login_response.json()['access_token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client

    @pytest.fixture
    async def user_client(self):
        """Fixture für normalen User-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            login_response = await client.post('/api/v1/auth/login', json={
                'username': 'user',
                'password': 'user123'
            })
            token = login_response.json()['access_token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, user_client):
        """DAST: Horizontale Privilegieneskalation wird verhindert"""
        # Versuche auf Daten eines anderen Users zuzugreifen
        response = await user_client.get('/api/v1/users/other-user-id/scans')

        assert response.status_code in [403, 404], \
            "Horizontale Privilegieneskalation möglich"

    @pytest.mark.asyncio
    async def test_vertical_privilege_escalation(self, user_client):
        """DAST: Vertikale Privilegieneskalation wird verhindert"""
        # Versuche Admin-Funktion als normaler User
        response = await user_client.post('/api/v1/admin/users', json={
            'username': 'newadmin',
            'role': 'admin'
        })

        assert response.status_code == 403, \
            "Vertikale Privilegieneskalation möglich"

    @pytest.mark.asyncio
    async def test_idor_protection(self, user_client):
        """DAST: IDOR (Insecure Direct Object Reference) Schutz"""
        # Versuche auf Ressourcen mit manipulierten IDs zuzugreifen
        response = await user_client.get('/api/v1/scans/999999')

        # Sollte 404 oder 403 sein, nicht 200
        assert response.status_code in [403, 404], \
            "IDOR möglich"


class TestSecurityHeaders:
    """DAST Tests für Security Headers"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """DAST: Security Headers werden gesendet"""
        response = await client.get('/api/v1/health')

        required_headers = [
            'x-content-type-options',
            'x-frame-options',
            'strict-transport-security',
            'content-security-policy',
        ]

        for header in required_headers:
            assert header in response.headers, \
                f"Fehlender Security Header: {header}"

    @pytest.mark.asyncio
    async def test_no_sensitive_headers(self, client):
        """DAST: Keine sensitiven Informationen in Headers"""
        response = await client.get('/api/v1/health')

        sensitive_headers = ['x-powered-by', 'server']

        for header in sensitive_headers:
            if header in response.headers:
                assert False, f"Sensitiver Header gefunden: {header}"

    @pytest.mark.asyncio
    async def test_hsts_header(self, client):
        """DAST: HSTS Header korrekt konfiguriert"""
        response = await client.get('/api/v1/health')

        if 'strict-transport-security' in response.headers:
            hsts = response.headers['strict-transport-security']
            assert 'max-age=' in hsts, "HSTS ohne max-age"
            assert int(hsts.split('max-age=')[1].split(';')[0]) >= 31536000, \
                "HSTS max-age zu niedrig"


class TestCSRFProtection:
    """DAST Tests für CSRF Schutz"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_csrf_token_required(self, client):
        """DAST: CSRF Token wird für State-Changing Requests verlangt"""
        # Versuche POST ohne CSRF Token
        response = await client.post('/api/v1/scans', json={
            'target': 'example.com',
            'scan_type': 'reconnaissance'
        })

        # Sollte 403 sein wenn CSRF Schutz aktiv
        # Oder 401 wenn Authentifizierung fehlt
        assert response.status_code in [401, 403, 422], \
            "CSRF Schutz möglicherweise deaktiviert"

    @pytest.mark.asyncio
    async def test_csrf_token_validation(self, client):
        """DAST: CSRF Token wird validiert"""
        # Login
        login_response = await client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

        token = login_response.json()['access_token']

        # Versuche POST mit falschem CSRF Token
        response = await client.post(
            '/api/v1/scans',
            json={'target': 'example.com'},
            headers={
                'Authorization': f'Bearer {token}',
                'X-CSRF-Token': 'invalid-token'
            }
        )

        assert response.status_code in [403, 422], \
            "CSRF Token wird nicht validiert"


class TestInformationDisclosure:
    """DAST Tests für Informationspreisgabe"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_no_stack_traces_in_production(self, client):
        """DAST: Keine Stack Traces in Production"""
        # Versuche einen Fehler zu provozieren
        response = await client.get('/api/v1/scans/invalid-id-format')

        # Sollte keine Stack Traces enthalten
        assert 'Traceback' not in response.text, \
            "Stack Traces werden preisgegeben"
        assert 'File "' not in response.text, \
            "Stack Traces werden preisgegeben"

    @pytest.mark.asyncio
    async def test_no_internal_paths(self, client):
        """DAST: Keine internen Pfade preisgeben"""
        response = await client.get('/api/v1/nonexistent')

        # Sollte keine internen Dateipfade enthalten
        assert '/home/' not in response.text, \
            "Interne Pfade werden preisgegeben"
        assert '/var/' not in response.text, \
            "Interne Pfade werden preisgegeben"

    @pytest.mark.asyncio
    async def test_error_messages_generic(self, client):
        """DAST: Fehlermeldungen sind generisch"""
        response = await client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrong'
        })

        # Sollte nicht verraten ob User existiert
        error_msg = response.json().get('detail', '').lower()
        assert 'user not found' not in error_msg or \
               'invalid credentials' in error_msg, \
            "Fehlermeldung gibt zu viel preis"


class TestRateLimiting:
    """DAST Tests für Rate Limiting"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, client):
        """DAST: Rate Limit Headers werden gesendet"""
        response = await client.get('/api/v1/health')

        rate_limit_headers = [
            'x-ratelimit-limit',
            'x-ratelimit-remaining',
            'x-ratelimit-reset',
        ]

        for header in rate_limit_headers:
            assert header in response.headers, \
                f"Rate Limit Header fehlt: {header}"

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, client):
        """DAST: Rate Limit wird durchgesetzt"""
        responses = []

        # Viele Requests schnell hintereinander
        for _ in range(100):
            response = await client.get('/api/v1/health')
            responses.append(response.status_code)

        # Einige sollten 429 sein
        assert 429 in responses, "Rate Limiting scheint nicht aktiv zu sein"


class TestSSRFPrevention:
    """DAST Tests für SSRF Prävention"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            login_response = await client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
            token = login_response.json()['access_token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client

    @pytest.mark.asyncio
    async def test_internal_ip_blocked(self, authenticated_client):
        """DAST: Interne IPs werden blockiert"""
        internal_targets = [
            'http://127.0.0.1/',
            'http://localhost/',
            'http://10.0.0.1/',
            'http://192.168.1.1/',
            'http://169.254.169.254/',  # AWS Metadata
        ]

        for target in internal_targets:
            response = await authenticated_client.post('/api/v1/scans', json={
                'target': target,
                'scan_type': 'reconnaissance'
            })

            assert response.status_code in [400, 403], \
                f"SSRF möglich mit: {target}"


class TestFileUploadSecurity:
    """DAST Tests für Datei-Upload Sicherheit"""

    @pytest.fixture
    async def authenticated_client(self):
        """Fixture für authentifizierten Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            login_response = await client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
            token = login_response.json()['access_token']
            client.headers['Authorization'] = f'Bearer {token}'
            yield client

    @pytest.mark.asyncio
    async def test_malicious_file_upload_blocked(self, authenticated_client):
        """DAST: Bösartige Datei-Uploads werden blockiert"""
        # EDUCATIONAL: Diese Payloads sind TEST-DATEN für Sicherheitstests
        # Sie werden verwendet, um zu prüfen, ob die API solche Uploads blockiert
        malicious_files = [
            ('test_shell.php', b'<?php /* TEST PAYLOAD - NOT FUNCTIONAL */ ?>'),
            ('test_shell.jsp', b'<% /* TEST PAYLOAD - NOT FUNCTIONAL */ %>'),
            ('test_shell.asp', b'<% /* TEST PAYLOAD - NOT FUNCTIONAL */ %>'),
        ]

        for filename, content in malicious_files:
            response = await authenticated_client.post(
                '/api/v1/uploads',
                files={'file': (filename, content, 'application/octet-stream')}
            )

            assert response.status_code in [400, 403], \
                f"Bösartiger Upload möglich: {filename}"


class TestAPIVersioning:
    """DAST Tests für API Versionierung"""

    @pytest.fixture
    async def client(self):
        """Fixture für HTTP-Client"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            yield client

    @pytest.mark.asyncio
    async def test_api_version_in_url(self, client):
        """DAST: API Version ist in URL"""
        response = await client.get('/api/v1/health')

        assert response.status_code == 200, \
            "API Versionierung nicht korrekt implementiert"


if __name__ == '__main__':
    print("=" * 80)
    print("DAST SECURITY TESTS - EDUCATIONAL USE ONLY")
    print("=" * 80)
    print("\nDiese Tests sind für autorisierte Sicherheitstests gedacht.")
    print("Die Verwendung ohne Erlaubnis ist illegal.\n")
    print("=" * 80)
    pytest.main([__file__, '-v'])

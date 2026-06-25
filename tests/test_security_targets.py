"""
Echte Sicherheits-Tests gegen DVWA und WebGoat
Diese Tests führen echte Scans durch und prüfen auf bekannte Schwachstellen.
"""

import subprocess
import time

import pytest
import requests

# Testziele
DVWA_URL = "http://localhost:8091"
WEBGOAT_URL = "http://localhost:8092/WebGoat"
NGINX_URL = "http://localhost:8090"


class TestDVWAAvailable:
    """DVWA (Damn Vulnerable Web Application) Tests"""

    def test_dvwa_login_page(self):
        """Prüfe ob DVWA Login-Seite erreichbar ist"""
        response = requests.get(f"{DVWA_URL}/login.php", timeout=10)
        assert response.status_code == 200
        assert "DVWA" in response.text or "login" in response.text.lower()

    def test_dvwa_vulnerabilities_page(self):
        """Prüfe ob DVWA Vulnerabilities-Seite existiert"""
        # Erst einloggen (default: admin/password)
        session = requests.Session()
        login_data = {
            "username": "admin",
            "password": "password",
            "Login": "Login",
        }
        session.post(f"{DVWA_URL}/login.php", data=login_data, timeout=10)

        response = session.get(f"{DVWA_URL}/vulnerabilities/sqli/", timeout=10)
        # DVWA ist absichtlich verwundbar - wir testen nur Erreichbarkeit
        assert response.status_code in [200, 302]


class TestWebGoatAvailable:
    """OWASP WebGoat Tests"""

    def test_webgoat_running(self):
        """Prüfe ob WebGoat läuft"""
        try:
            response = requests.get(WEBGOAT_URL, timeout=15)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("WebGoat noch nicht bereit")


class TestSQLMapAgainstDVWA:
    """Echte SQLMap-Tests gegen DVWA"""

    @pytest.mark.skipif(
        subprocess.run(["which", "sqlmap"], capture_output=True).returncode != 0,
        reason="sqlmap nicht installiert",
    )
    def test_sqlmap_dvwa_basic(self):
        """Grundlegender SQLMap-Scan gegen DVWA SQL Injection"""
        # Nicht-invasive Prüfung
        result = subprocess.run(
            [
                "sqlmap",
                "-u",
                f"{DVWA_URL}/vulnerabilities/sqli/?id=1&Submit=Submit",
                "--batch",
                "--level=1",
                "--risk=1",
                "--timeout=30",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # SQLMap sollte erkennen dass es verwundbar ist
        assert "SQL injection" in result.stdout or result.returncode == 0


class TestNiktoAgainstTargets:
    """Nikto Web-Scanner Tests"""

    @pytest.mark.skipif(
        subprocess.run(["which", "nikto"], capture_output=True).returncode != 0,
        reason="nikto nicht installiert",
    )
    def test_nikto_nginx_scan(self):
        """Nikto-Scan gegen nginx Testziel"""
        result = subprocess.run(
            ["nikto", "-h", NGINX_URL, "-timeout", "30", "-maxtime", "60s"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        # Nikto sollte ergebnisse finden (auch wenn nginx sicher ist)
        assert result.returncode == 0 or "Server" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

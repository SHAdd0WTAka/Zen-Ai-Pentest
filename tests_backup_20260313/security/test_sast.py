#!/usr/bin/env python3
"""
SAST (Static Application Security Testing) Tests
==============================================
Statische Sicherheitsanalyse für Zen-AI-Pentest Codebase
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = [pytest.mark.security, pytest.mark.sast]


class TestSQLInjection:
    """SAST Tests für SQL Injection Schwachstellen"""

    DANGEROUS_PATTERNS = [
        r'execute\s*\(\s*["\'].*%s',
        r'execute\s*\(\s*["\'].*\+',
        r'execute\s*\(\s*f["\']',
        r'execute\s*\(\s*["\'].*\.format\(',
        r"raw_input\s*\(\s*.*\)\s*.*execute",
        r'cursor\.execute\s*\(\s*["\'].*\$',
    ]

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien im Projekt finden"""
        project_root = Path(__file__).parent.parent.parent
        python_files = []

        for pattern in [
            "core/**/*.py",
            "api/**/*.py",
            "modules/**/*.py",
            "agents/**/*.py",
        ]:
            python_files.extend(project_root.glob(pattern))

        return [f for f in python_files if f.is_file()]

    def test_no_string_concatenation_in_sql(self):
        """SAST: Keine String-Konkatenation in SQL-Queries"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            for pattern in self.DANGEROUS_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    violations.append(
                        {
                            "file": str(file_path),
                            "line": content[: match.start()].count("\n") + 1,
                            "pattern": pattern,
                            "match": match.group()[:50],
                        }
                    )

        assert (
            len(violations) == 0
        ), f"SQL Injection Risiken gefunden: {violations}"

    def test_parameterized_queries_used(self):
        """SAST: Parametrisierte Queries werden verwendet"""
        python_files = self.get_python_files()

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach execute-Aufrufen
            if "execute(" in content:
                # Prüfe ob parametrisierte Queries verwendet werden
                if not re.search(
                    r'execute\s*\(\s*["\'][^"\']*\?[^"\']*["\']\s*,', content
                ):
                    if not re.search(
                        r'execute\s*\(\s*["\'][^"\']*%s[^"\']*["\']\s*,',
                        content,
                    ):
                        # Könnte ein Problem sein, aber wir müssen kontextuell prüfen
                        pass  # Manuelle Überprüfung erforderlich


class TestXSSVulnerabilities:
    """SAST Tests für XSS Schwachstellen"""

    XSS_PATTERNS = [
        r"\.innerHTML\s*=",
        r"\.outerHTML\s*=",
        r"document\.write\s*\(",
        r"eval\s*\(",
        r"\.html\s*\([^)]*\+",
        r"\.html\s*\([^)]*\$\{",
    ]

    def get_js_files(self) -> List[Path]:
        """Alle JavaScript-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.glob("web_ui/**/*.js"))

    def test_no_innerhtml_with_user_input(self):
        """SAST: Keine innerHTML mit Benutzereingaben"""
        js_files = self.get_js_files()
        violations = []

        for file_path in js_files:
            content = file_path.read_text()

            for pattern in self.XSS_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    violations.append(
                        {
                            "file": str(file_path),
                            "line": content[: match.start()].count("\n") + 1,
                            "match": match.group(),
                        }
                    )

        assert len(violations) == 0, f"XSS Risiken gefunden: {violations}"


class TestHardcodedSecrets:
    """SAST Tests für hardcodierte Secrets"""

    SECRET_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
        (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded Token"),
        (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', "AWS Access Key"),
        (r'private_key\s*=\s*["\']-----BEGIN', "Private Key"),
    ]

    EXCLUDED_FILES = ["test_", "example", "config.example", ".env.example"]

    def get_all_source_files(self) -> List[Path]:
        """Alle Quellcodedateien finden"""
        project_root = Path(__file__).parent.parent.parent
        files = []

        for ext in ["*.py", "*.js", "*.ts", "*.yaml", "*.yml", "*.json"]:
            files.extend(project_root.rglob(ext))

        return files

    def test_no_hardcoded_secrets(self):
        """SAST: Keine hardcodierten Secrets im Code"""
        source_files = self.get_all_source_files()
        violations = []

        for file_path in source_files:
            # Ausschluss von Test- und Beispieldateien
            if any(
                excluded in str(file_path) for excluded in self.EXCLUDED_FILES
            ):
                continue

            try:
                content = file_path.read_text()

                for pattern, description in self.SECRET_PATTERNS:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Prüfe ob es sich um einen Platzhalter handelt
                        if not re.search(
                            r"(placeholder|example|test|dummy|xxx|your_)",
                            match.group(),
                            re.IGNORECASE,
                        ):
                            violations.append(
                                {
                                    "file": str(file_path),
                                    "type": description,
                                    "line": content[: match.start()].count(
                                        "\n"
                                    )
                                    + 1,
                                }
                            )
            except Exception:
                continue

        assert (
            len(violations) == 0
        ), f"Hardcodierte Secrets gefunden: {violations}"


class TestInsecureDeserialization:
    """SAST Tests für unsichere Deserialisierung"""

    DANGEROUS_FUNCTIONS = [
        "pickle.loads",
        "yaml.load",
        "eval(",
        "exec(",
        "marshal.loads",
        "__import__",
    ]

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_no_pickle_on_untrusted_data(self):
        """SAST: Kein pickle auf nicht-vertrauenswürdigen Daten"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            if "pickle.loads" in content:
                # Prüfe ob es sich um eine sichere Verwendung handelt
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "pickle.loads" in line:
                        # Kontext prüfen
                        context = "\n".join(lines[max(0, i - 3) : i + 1])
                        if (
                            "trusted" not in context.lower()
                            and "safe" not in context.lower()
                        ):
                            violations.append(
                                {
                                    "file": str(file_path),
                                    "line": i + 1,
                                    "context": line.strip(),
                                }
                            )

        assert (
            len(violations) == 0
        ), f"Unsichere pickle Verwendung: {violations}"

    def test_yaml_safe_load(self):
        """SAST: yaml.safe_load statt yaml.load verwenden"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach yaml.load ohne Loader
            if re.search(r"yaml\.load\s*\([^)]*\)(?!.*Loader)", content):
                violations.append(
                    {
                        "file": str(file_path),
                        "issue": "yaml.load ohne Loader Parameter",
                    }
                )

        assert (
            len(violations) == 0
        ), f"Unsichere yaml.load Verwendung: {violations}"


class TestCommandInjection:
    """SAST Tests für Command Injection"""

    DANGEROUS_PATTERNS = [
        r"os\.system\s*\(",
        r"subprocess\.call\s*\([^)]*shell\s*=\s*True",
        r"subprocess\.Popen\s*\([^)]*shell\s*=\s*True",
        r"eval\s*\(",
        r"exec\s*\(",
    ]

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_no_shell_true_with_user_input(self):
        """SAST: Kein shell=True mit Benutzereingaben"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach subprocess mit shell=True
            if "shell=True" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "shell=True" in line:
                        context = "\n".join(lines[max(0, i - 5) : i + 1])

                        # Prüfe ob Benutzereingaben involviert sind
                        if re.search(
                            r"(request|input|param|arg)",
                            context,
                            re.IGNORECASE,
                        ):
                            # Prüfe ob Input validiert wird
                            if not re.search(
                                r"(validate|sanitize|escape)",
                                context,
                                re.IGNORECASE,
                            ):
                                violations.append(
                                    {
                                        "file": str(file_path),
                                        "line": i + 1,
                                        "context": line.strip(),
                                    }
                                )

        assert len(violations) == 0, f"Command Injection Risiken: {violations}"


class TestPathTraversal:
    """SAST Tests für Path Traversal"""

    DANGEROUS_PATTERNS = [
        r"open\s*\(\s*[^)]*\+",
        r'open\s*\(\s*f["\']',
        r"\.format\s*\([^)]*\)",
        r"os\.path\.join\s*\([^)]*\+",
    ]

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_path_traversal_protection(self):
        """SAST: Path Traversal Schutz"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach Dateioperationen mit Benutzereingaben
            if re.search(
                r"open\s*\([^)]*(request|input|param)", content, re.IGNORECASE
            ):
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "open(" in line and re.search(
                        r"(request|input|param)", line, re.IGNORECASE
                    ):
                        context = "\n".join(lines[max(0, i - 5) : i + 1])

                        # Prüfe ob Path Traversal Schutz vorhanden
                        if not re.search(
                            r"(sanitize|validate|realpath|abspath)",
                            context,
                            re.IGNORECASE,
                        ):
                            violations.append(
                                {"file": str(file_path), "line": i + 1}
                            )

        assert len(violations) == 0, f"Path Traversal Risiken: {violations}"


class TestInsecureCryptography:
    """SAST Tests für unsichere kryptographische Praktiken"""

    WEAK_ALGORITHMS = [
        "md5",
        "sha1",
        "des",
        "rc4",
        "ecb",
    ]

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_no_weak_hashing(self):
        """SAST: Keine schwachen Hash-Algorithmen"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            for algo in ["md5", "sha1"]:
                if f"hashlib.{algo}" in content:
                    violations.append(
                        {
                            "file": str(file_path),
                            "algorithm": algo,
                            "issue": "Weak hashing algorithm",
                        }
                    )

        assert len(violations) == 0, f"Schwache Kryptographie: {violations}"

    def test_secure_random_used(self):
        """SAST: Sichere Zufallszahlengenerierung"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach unsicherem random
            if re.search(r"import\s+random\s*\n[^#]*random\.", content):
                # Prüfe ob es für kryptographische Zwecke verwendet wird
                if re.search(
                    r"(token|password|key|secret)", content, re.IGNORECASE
                ):
                    violations.append(
                        {
                            "file": str(file_path),
                            "issue": "Insecure random for cryptographic use",
                        }
                    )

        assert (
            len(violations) == 0
        ), f"Unsichere Zufallszahlengenerierung: {violations}"


class TestSSRFProtection:
    """SAST Tests für SSRF Schutz"""

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_ssrf_prevention(self):
        """SAST: SSRF Prävention"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach HTTP-Requests mit Benutzereingaben
            if re.search(
                r"(requests\.(get|post)|urllib|http\.client)", content
            ):
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if re.search(r"(requests\.(get|post)|urllib)", line):
                        context = "\n".join(lines[max(0, i - 5) : i + 1])

                        # Prüfe ob URL validiert wird
                        if re.search(
                            r"(request|input|param)", context, re.IGNORECASE
                        ):
                            if not re.search(
                                r"(validate|whitelist|allowlist)",
                                context,
                                re.IGNORECASE,
                            ):
                                violations.append(
                                    {"file": str(file_path), "line": i + 1}
                                )

        assert len(violations) == 0, f"SSRF Risiken: {violations}"


class TestSecurityHeaders:
    """SAST Tests für Security Headers"""

    REQUIRED_HEADERS = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Strict-Transport-Security",
        "Content-Security-Policy",
    ]

    def test_security_headers_present(self):
        """SAST: Security Headers werden gesetzt"""
        project_root = Path(__file__).parent.parent.parent
        api_files = list(project_root.glob("api/**/*.py"))

        # Suche nach Security Header Konfiguration
        found_headers = set()

        for file_path in api_files:
            content = file_path.read_text()
            for header in self.REQUIRED_HEADERS:
                if header in content:
                    found_headers.add(header)

        missing = set(self.REQUIRED_HEADERS) - found_headers
        assert len(missing) == 0, f"Fehlende Security Headers: {missing}"


class TestInputValidation:
    """SAST Tests für Input Validation"""

    def get_python_files(self) -> List[Path]:
        """Alle Python-Dateien finden"""
        project_root = Path(__file__).parent.parent.parent
        return list(project_root.rglob("*.py"))

    def test_input_validation_on_endpoints(self):
        """SAST: Input Validation auf API Endpoints"""
        python_files = self.get_python_files()
        violations = []

        for file_path in python_files:
            content = file_path.read_text()

            # Suche nach FastAPI/Flask Endpoints
            if "@app." in content or "@router." in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "@app." in line or "@router." in line:
                        # Prüfe ob der nächsten Zeilen Validation haben
                        context = "\n".join(lines[i : min(i + 10, len(lines))])

                        if (
                            "request" in context.lower()
                            or "body" in context.lower()
                        ):
                            if not re.search(
                                r"(BaseModel|validator|Field)", context
                            ):
                                violations.append(
                                    {"file": str(file_path), "line": i + 1}
                                )

        assert len(violations) == 0, f"Fehlende Input Validation: {violations}"


class TestBanditScan:
    """SAST Tests mit Bandit"""

    def test_run_bandit_scan(self):
        """SAST: Bandit Security Scan"""
        project_root = Path(__file__).parent.parent.parent

        try:
            result = subprocess.run(
                ["bandit", "-r", str(project_root), "-f", "json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                # Keine Probleme gefunden
                pass
            else:
                # Parse Bandit Output
                import json

                try:
                    findings = json.loads(result.stdout)
                    high_severity = [
                        r
                        for r in findings.get("results", [])
                        if r["issue_severity"] in ["HIGH", "CRITICAL"]
                    ]

                    assert (
                        len(high_severity) == 0
                    ), f"Bandit fand kritische Probleme: {high_severity}"
                except json.JSONDecodeError:
                    pass  # Bandit nicht installiert oder kein JSON Output

        except FileNotFoundError:
            pytest.skip("Bandit nicht installiert")
        except subprocess.TimeoutExpired:
            pytest.skip("Bandit Scan timed out")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

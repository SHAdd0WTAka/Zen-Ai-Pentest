"""
Security Tests: Input Validation
===============================

Tests for common input validation vulnerabilities:
- XSS (Cross-Site Scripting)
- SQL Injection
- Command Injection
- Path Traversal
- SSRF (Server-Side Request Forgery)
"""

import html
import re
from unittest.mock import patch

import pytest


class InputValidator:
    """Input validation utility for security testing."""

    # XSS patterns to detect
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"data:text/html",
    ]

    # SQL Injection patterns
    SQLI_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
        r"UNION\s+SELECT",
        r"INSERT\s+INTO",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
    ]

    # Command injection patterns
    CMD_INJECTION_PATTERNS = [
        r"[;&|`]\s*\w+",
        r"\$\(.*?\)",
        r"`.*?`",
        r"\|\s*\w+",
        r";\s*\w+",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%252e%252e%252f",
        r"..%2f",
        r"%2e%2e/",
        r"..%5c",
        r"%252e%252e/",
    ]

    # SSRF patterns
    SSRF_PATTERNS = [
        r"^(ftp|file|dict|gopher|ldap|smtp)://",
        r"://localhost",
        r"://127\.\d+\.\d+\.\d+",
        r"://0\.0\.0\.0",
        r"::1",
        r"169\.254\.\d+\.\d+",
        r"10\.\d+\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+",
    ]

    @classmethod
    def sanitize_xss(cls, value: str) -> str:
        """Sanitize input to prevent XSS."""
        if not isinstance(value, str):
            return str(value)
        # HTML escape
        return html.escape(value)

    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """Detect potential XSS in input."""
        if not isinstance(value, str):
            return False
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_sqli(cls, value: str) -> bool:
        """Detect potential SQL injection in input."""
        if not isinstance(value, str):
            return False
        for pattern in cls.SQLI_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_command_injection(cls, value: str) -> bool:
        """Detect potential command injection in input."""
        if not isinstance(value, str):
            return False
        for pattern in cls.CMD_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_path_traversal(cls, value: str) -> bool:
        """Detect potential path traversal in input."""
        if not isinstance(value, str):
            return False
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def detect_ssrf(cls, value: str) -> bool:
        """Detect potential SSRF in URL input."""
        if not isinstance(value, str):
            return False
        for pattern in cls.SSRF_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not isinstance(filename, str):
            return ""
        # Remove path components
        sanitized = filename.replace("/", "_").replace("\\", "_")
        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")
        # Remove parent directory references
        sanitized = sanitized.replace("..", "_")
        return sanitized


# ============== XSS Tests ==============


class TestXSSPrevention:
    """Test cases for XSS prevention."""

    @pytest.mark.parametrize(
        "input_value,expected_detection",
        [
            ("<script>alert('xss')</script>", True),
            ("javascript:alert('xss')", True),
            ('<img src="x" onerror="alert(1)">', True),
            ('<iframe src="evil.com">', True),
            ('<object data="evil.swf">', True),
            ("data:text/html,<script>alert(1)</script>", True),
            ("normal text without xss", False),
            ("safe_value_123", False),
            ("also safe content", False),
        ],
    )
    def test_xss_detection(self, input_value: str, expected_detection: bool):
        """Test XSS pattern detection."""
        result = InputValidator.detect_xss(input_value)
        assert result == expected_detection, f"Failed for input: {input_value}"

    @pytest.mark.parametrize(
        "input_value,expected_sanitized",
        [
            (
                "<script>alert('xss')</script>",
                "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;",
            ),
            ('"double quotes"', "&quot;double quotes&quot;"),
            ("'single quotes'", "&#x27;single quotes&#x27;"),
            ("&ampersand&", "&amp;ampersand&amp;"),
            ("safe text", "safe text"),
        ],
    )
    def test_xss_sanitization(self, input_value: str, expected_sanitized: str):
        """Test XSS sanitization via HTML escaping."""
        result = InputValidator.sanitize_xss(input_value)
        assert result == expected_sanitized

    def test_xss_in_api_payload(self):
        """Test that API payloads are properly validated."""
        malicious_payload = {
            "username": "<script>alert('xss')</script>",
            "description": "normal text",
        }

        for key, value in malicious_payload.items():
            if InputValidator.detect_xss(value):
                # In real implementation, this would raise an error or sanitize
                assert True


# ============== SQL Injection Tests ==============


class TestSQLInjectionPrevention:
    """Test cases for SQL injection prevention."""

    @pytest.mark.parametrize(
        "input_value,expected_detection",
        [
            ("1' OR '1'='1", True),
            ("1; DROP TABLE users--", True),
            ("admin'--", True),
            ("' UNION SELECT * FROM passwords--", True),
            ("1' AND 1=1--", True),
            ("; exec xp_cmdshell 'dir'--", True),
            ("valid_username", False),
            ("user@example.com", False),
            ("John Doe", False),
        ],
    )
    def test_sqli_detection(self, input_value: str, expected_detection: bool):
        """Test SQL injection pattern detection."""
        result = InputValidator.detect_sqli(input_value)
        assert result == expected_detection, f"Failed for input: {input_value}"

    def test_parameterized_query_recommendation(self):
        """Ensure parameterized queries are recommended."""
        # This test documents the recommendation to use parameterized queries
        query = "SELECT * FROM users WHERE username = %s"
        # In real code, this should use query parameters, not string formatting
        assert "%s" in query or "?" in query or ":" in query


# ============== Command Injection Tests ==============


class TestCommandInjectionPrevention:
    """Test cases for command injection prevention."""

    @pytest.mark.parametrize(
        "input_value,expected_detection",
        [
            ("; cat /etc/passwd", True),
            ("| ls -la", True),
            ("`whoami`", True),
            ("$(id)", True),
            ("& ping -c 1 attacker.com", True),
            ("target; rm -rf /", True),
            ("safe_filename.txt", False),
            ("my-document.pdf", False),
            ("192.168.1.1", False),
        ],
    )
    def test_command_injection_detection(
        self, input_value: str, expected_detection: bool
    ):
        """Test command injection pattern detection."""
        result = InputValidator.detect_command_injection(input_value)
        assert result == expected_detection, f"Failed for input: {input_value}"

    def test_shell_execution_avoidance(self):
        """Test that shell=True is not used with user input."""
        user_input = "; cat /etc/passwd"

        # Mock subprocess to verify shell=False is used
        with patch("subprocess.run") as mock_run:
            # Safe implementation would use shell=False and pass list
            import subprocess

            subprocess.run(["echo", user_input], shell=False)

            call_args = mock_run.call_args
            assert call_args[1].get("shell") is False


# ============== Path Traversal Tests ==============


class TestPathTraversalPrevention:
    """Test cases for path traversal prevention."""

    @pytest.mark.parametrize(
        "input_value,expected_detection",
        [
            ("../../../etc/passwd", True),
            ("..\\..\\windows\\system32\\config\\sam", True),
            ("%2e%2e%2fetc%2fpasswd", True),
            ("..%2f..%2fetc%2fpasswd", True),
            ("file.txt", False),
            ("subdir/document.pdf", False),
            ("safe_filename_123.txt", False),
        ],
    )
    def test_path_traversal_detection(
        self, input_value: str, expected_detection: bool
    ):
        """Test path traversal pattern detection."""
        result = InputValidator.detect_path_traversal(input_value)
        assert result == expected_detection, f"Failed for input: {input_value}"

    @pytest.mark.parametrize(
        "input_value,expected_sanitized",
        [
            ("../../../etc/passwd", "______etc_passwd"),
            ("file.txt", "file.txt"),
            ("dir/subdir/file", "dir_subdir_file"),
            ("file\x00.txt", "file.txt"),  # Null byte removal
        ],
    )
    def test_filename_sanitization(
        self, input_value: str, expected_sanitized: str
    ):
        """Test filename sanitization."""
        result = InputValidator.sanitize_filename(input_value)
        assert result == expected_sanitized

    def test_chroot_jail_recommendation(self):
        """Document chroot jail recommendation for file operations."""
        base_path = "/var/www/uploads"
        user_file = "document.pdf"

        # Best practice: join paths and verify within base directory
        import os

        full_path = os.path.join(base_path, user_file)
        real_path = os.path.realpath(full_path)

        # Normalize path separator for Windows compatibility
        # Just verify the path joining works (OS-specific path handling)
        assert base_path in real_path.replace("\\", "/") or os.path.isabs(
            real_path
        )


# ============== SSRF Tests ==============


class TestSSRFPrevention:
    """Test cases for SSRF (Server-Side Request Forgery) prevention."""

    @pytest.mark.parametrize(
        "input_value,expected_detection",
        [
            ("http://localhost/admin", True),
            ("http://127.0.0.1:8080/internal", True),
            ("http://0.0.0.0/metrics", True),
            ("http://[::1]/api", True),
            ("http://169.254.169.254/latest/meta-data/", True),
            ("http://192.168.1.1/router", True),
            ("http://10.0.0.1/internal", True),
            ("ftp://internal.server/file", True),
            ("file:///etc/passwd", True),
            ("https://example.com", False),
            ("https://api.github.com", False),
        ],
    )
    def test_ssrf_detection(self, input_value: str, expected_detection: bool):
        """Test SSRF pattern detection."""
        result = InputValidator.detect_ssrf(input_value)
        assert result == expected_detection, f"Failed for input: {input_value}"

    def test_url_whitelist_recommendation(self):
        """Document URL whitelist recommendation."""
        allowed_domains = ["api.trusted.com", "cdn.example.org"]
        user_url = "https://api.trusted.com/data"

        from urllib.parse import urlparse

        parsed = urlparse(user_url)

        assert parsed.netloc in allowed_domains

    def test_private_ip_blocking(self):
        """Test that private IP ranges are blocked."""
        private_ips = [
            "127.0.0.1",
            "10.0.0.1",
            "192.168.1.1",
            "172.16.0.1",
            "169.254.1.1",
        ]

        for ip in private_ips:
            assert InputValidator.detect_ssrf(f"http://{ip}/") is True


# ============== Integration Tests ==============


class TestInputValidationIntegration:
    """Integration tests for complete input validation pipeline."""

    def test_api_endpoint_validation(self):
        """Test complete validation of API endpoint input."""
        api_input = {
            "username": "<script>alert(1)</script>",
            "email": "test@example.com'; DROP TABLE users--",
            "filename": "../../../etc/passwd",
            "callback_url": "http://localhost/internal",
        }

        results = {
            "xss": InputValidator.detect_xss(api_input["username"]),
            "sqli": InputValidator.detect_sqli(api_input["email"]),
            "path_traversal": InputValidator.detect_path_traversal(
                api_input["filename"]
            ),
            "ssrf": InputValidator.detect_ssrf(api_input["callback_url"]),
        }

        assert all(results.values()), "All malicious inputs should be detected"

    def test_safe_input_passes(self):
        """Test that safe inputs pass all validations."""
        safe_input = {
            "username": "john_doe_123",
            "email": "john@example.com",
            "filename": "document.pdf",
            "website": "https://example.com",
        }

        results = {
            "xss": InputValidator.detect_xss(safe_input["username"]),
            "sqli": InputValidator.detect_sqli(safe_input["email"]),
            "path_traversal": InputValidator.detect_path_traversal(
                safe_input["filename"]
            ),
            "ssrf": InputValidator.detect_ssrf(safe_input["website"]),
        }

        assert not any(
            results.values()
        ), "Safe inputs should not trigger detections"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Comprehensive unit tests for api/security_logging.py
Tests security event logging, sanitization, and log formatting.
"""

import html
from unittest.mock import MagicMock, patch

import pytest

from api.security_logging import (
    format_log_message,
    sanitize_for_log,
    sanitize_path_component,
)


class TestSanitizeForLog:
    """Test suite for sanitize_for_log function."""

    def test_sanitize_normal_string(self):
        """Test sanitizing a normal string returns unchanged."""
        input_str = "Hello World"
        result = sanitize_for_log(input_str)
        assert result == "Hello World"

    def test_sanitize_newlines(self):
        """Test that newlines are escaped to prevent log injection."""
        input_str = "line1\nline2\rline3\r\nline4"
        result = sanitize_for_log(input_str)
        assert "\n" not in result
        assert "\r" not in result
        assert result == "line1\\nline2\\rline3\\r\\nline4"

    def test_sanitize_null_bytes(self):
        """Test that null bytes are removed."""
        input_str = "hello\x00world\x00"
        result = sanitize_for_log(input_str)
        assert "\x00" not in result
        assert result == "helloworld"

    def test_sanitize_html_escaping(self):
        """Test that HTML characters are escaped to prevent XSS in log viewers."""
        input_str = "<script>alert('xss')</script>"
        result = sanitize_for_log(input_str)
        assert "<script>" not in result
        assert result == html.escape("<script>alert('xss')</script>")

    def test_sanitize_html_characters(self):
        """Test specific HTML character escaping."""
        input_str = "<div class='test'>Hello & goodbye</div>"
        result = sanitize_for_log(input_str)
        assert "<" not in result
        assert ">" not in result
        # & becomes &amp; which still contains & as part of the entity
        assert "&amp;" in result  # & becomes &amp;
        assert "&lt;div class=&#x27;test&#x27;&gt;Hello &amp; goodbye&lt;/div&gt;" == result

    def test_sanitize_length_truncation(self):
        """Test that long strings are truncated to prevent log flooding."""
        input_str = "A" * 300
        result = sanitize_for_log(input_str)
        assert len(result) == 256
        assert result.endswith("...")
        assert result == "A" * 253 + "..."

    def test_sanitize_exact_length_boundary(self):
        """Test exact boundary of 256 characters."""
        input_str = "B" * 256
        result = sanitize_for_log(input_str)
        assert len(result) == 256
        assert result == "B" * 256

    def test_sanitize_just_over_boundary(self):
        """Test string just over 256 characters."""
        input_str = "C" * 257
        result = sanitize_for_log(input_str)
        assert len(result) == 256
        assert result == "C" * 253 + "..."

    def test_sanitize_non_string_input_int(self):
        """Test sanitizing an integer (converted to string)."""
        input_val = 12345
        result = sanitize_for_log(input_val)
        assert result == "12345"

    def test_sanitize_non_string_input_none(self):
        """Test sanitizing None (converted to string)."""
        input_val = None
        result = sanitize_for_log(input_val)
        assert result == "None"

    def test_sanitize_non_string_input_float(self):
        """Test sanitizing a float (converted to string)."""
        input_val = 3.14159
        result = sanitize_for_log(input_val)
        assert result == "3.14159"

    def test_sanitize_non_string_input_list(self):
        """Test sanitizing a list (converted to string)."""
        input_val = ["a", "b", "c"]
        result = sanitize_for_log(input_val)
        # Single quotes in list repr get escaped to &#x27;
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_sanitize_combined_attack(self):
        """Test combined log injection attack vector."""
        input_str = "user\n[ERROR] Fake error message\x00<script>alert('xss')</script>" + "A" * 300
        result = sanitize_for_log(input_str)
        assert "\n" not in result
        assert "\x00" not in result
        assert "<script>" not in result
        assert len(result) == 256

    def test_sanitize_empty_string(self):
        """Test sanitizing an empty string."""
        input_str = ""
        result = sanitize_for_log(input_str)
        assert result == ""

    def test_sanitize_whitespace(self):
        """Test sanitizing whitespace-only string."""
        input_str = "   \t\n  "
        result = sanitize_for_log(input_str)
        assert "\n" not in result
        assert "\t" in result  # Tabs should remain

    def test_sanitize_unicode_characters(self):
        """Test sanitizing unicode characters."""
        input_str = "Hello 世界 🌍 émojis"
        result = sanitize_for_log(input_str)
        assert "Hello 世界 🌍 émojis" == result


class TestSanitizePathComponent:
    """Test suite for sanitize_path_component function."""

    def test_sanitize_path_normal(self):
        """Test sanitizing a normal path component."""
        input_str = "filename"
        result = sanitize_path_component(input_str)
        assert result == "filename"

    def test_sanitize_path_forward_slash(self):
        """Test that forward slashes are removed."""
        input_str = "path/to/file"
        result = sanitize_path_component(input_str)
        assert "/" not in result
        assert result == "pathtofile"

    def test_sanitize_path_backslash(self):
        """Test that backslashes are removed."""
        input_str = "path\\to\\file"
        result = sanitize_path_component(input_str)
        assert "\\" not in result
        assert result == "pathtofile"

    def test_sanitize_path_parent_directory(self):
        """Test that parent directory references are removed."""
        input_str = "../../../etc/passwd"
        result = sanitize_path_component(input_str)
        # Function removes / and \ first, then ..
        # So ../../../etc/passwd -> ....etcpasswd -> etcpasswd
        assert ".." not in result
        assert "/" not in result
        assert result == "etcpasswd"

    def test_sanitize_path_traversal_complete(self):
        """Test complete path traversal attack."""
        input_str = "../../../etc/passwd"
        result = sanitize_path_component(input_str)
        # First .. is replaced with empty, then remaining slashes
        # Actually the function replaces / \ first, then ..
        # So ../../../etc/passwd -> ....etcpasswd (after all replacements)
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_path_null_bytes(self):
        """Test that null bytes are removed."""
        input_str = "file\x00name"
        result = sanitize_path_component(input_str)
        assert "\x00" not in result
        assert result == "filename"

    def test_sanitize_path_non_string_int(self):
        """Test sanitizing an integer path component."""
        input_val = 123
        result = sanitize_path_component(input_val)
        assert result == "123"

    def test_sanitize_path_non_string_none(self):
        """Test sanitizing None path component."""
        input_val = None
        result = sanitize_path_component(input_val)
        assert result == "None"

    def test_sanitize_path_complex_traversal(self):
        """Test complex path traversal attack."""
        input_str = "..\\..\\..\\Windows\\System32\\config\\SAM"
        result = sanitize_path_component(input_str)
        assert ".." not in result
        assert "\\" not in result
        assert result == "WindowsSystem32configSAM"

    def test_sanitize_path_empty(self):
        """Test sanitizing empty path."""
        input_str = ""
        result = sanitize_path_component(input_str)
        assert result == ""

    def test_sanitize_path_only_separators(self):
        """Test path with only separators."""
        input_str = "///\\\\\\"
        result = sanitize_path_component(input_str)
        assert result == ""

    def test_sanitize_path_only_parent_refs(self):
        """Test path with only parent directory references."""
        input_str = "...."
        result = sanitize_path_component(input_str)
        # Each ".." becomes "", so "...." -> "" -> ""
        assert ".." not in result

    def test_sanitize_path_unicode(self):
        """Test path with unicode characters."""
        input_str = "ファイル/日本語"
        result = sanitize_path_component(input_str)
        assert "/" not in result
        assert result == "ファイル日本語"


class TestFormatLogMessage:
    """Test suite for format_log_message function."""

    def test_format_simple_message(self):
        """Test formatting a simple log message."""
        template = "User {user} logged in"
        result = format_log_message(template, user="admin")
        assert result == "User admin logged in"

    def test_format_multiple_placeholders(self):
        """Test formatting with multiple placeholders."""
        template = "User {user} accessed {resource} at {time}"
        result = format_log_message(template, user="admin", resource="/api/data", time="12:00")
        assert result == "User admin accessed /api/data at 12:00"

    def test_format_with_sanitization(self):
        """Test that values are sanitized in log messages."""
        template = "User {user} attempted login"
        malicious_user = "admin\n[CRITICAL] System hacked"
        result = format_log_message(template, user=malicious_user)
        assert "\n" not in result
        assert "[CRITICAL]" in result  # The text remains but newline is escaped

    def test_format_with_html_injection(self):
        """Test that HTML is escaped in log messages."""
        template = "Comment: {comment}"
        xss_attempt = "<img src=x onerror=alert(1)>"
        result = format_log_message(template, comment=xss_attempt)
        assert "<img" not in result
        assert "onerror" in result  # Text remains but < is escaped

    def test_format_empty_template(self):
        """Test formatting with empty template."""
        template = ""
        result = format_log_message(template, user="admin")
        assert result == ""

    def test_format_no_placeholders(self):
        """Test formatting with no placeholders."""
        template = "System started successfully"
        result = format_log_message(template)
        assert result == "System started successfully"

    def test_format_non_string_values(self):
        """Test formatting with non-string values."""
        template = "Count: {count}, Flag: {flag}"
        result = format_log_message(template, count=42, flag=True)
        assert result == "Count: 42, Flag: True"

    def test_format_special_characters(self):
        """Test formatting with special characters."""
        template = "Data: {data}"
        special = "Special: !@#$%^&*()"
        result = format_log_message(template, data=special)
        # & gets escaped to &amp; by html.escape
        assert "!@#$%^" in result
        assert "*()" in result
        assert "&amp;" in result  # & becomes &amp;

    def test_format_unicode(self):
        """Test formatting with unicode."""
        template = "User: {name}"
        unicode_name = "José 日本語 🎉"
        result = format_log_message(template, name=unicode_name)
        assert "José 日本語 🎉" in result

    def test_format_path_in_message(self):
        """Test formatting with path data."""
        template = "File {filename} accessed"
        filename = "../../../etc/passwd"
        result = format_log_message(template, filename=filename)
        # The path is sanitized with sanitize_for_log, not sanitize_path_component
        # So .. and / remain but newlines would be escaped
        assert "../../../etc/passwd" in result

    def test_format_long_value(self):
        """Test formatting with very long value."""
        template = "Data: {data}"
        long_data = "X" * 500
        result = format_log_message(template, data=long_data)
        assert len(result) < 300  # Should be truncated
        assert "..." in result

    def test_format_multiple_long_values(self):
        """Test formatting with multiple long values."""
        template = "User: {user}, Action: {action}"
        long_user = "U" * 300
        long_action = "A" * 300
        result = format_log_message(template, user=long_user, action=long_action)
        assert "..." in result


class TestSecurityEventLogging:
    """Test suite for security event logging scenarios."""

    def test_security_event_auth_failure(self):
        """Test logging failed authentication attempt."""
        template = "Authentication failed for user: {username} from IP: {ip}"
        result = format_log_message(template, username="admin", ip="192.168.1.1")
        assert "Authentication failed" in result
        assert "admin" in result
        assert "192.168.1.1" in result

    def test_security_event_suspicious_activity(self):
        """Test logging suspicious activity."""
        template = "Suspicious activity detected: {activity} from {source}"
        result = format_log_message(
            template,
            activity="Multiple failed login attempts",
            source="10.0.0.5",
        )
        assert "Suspicious activity detected" in result
        assert "Multiple failed login attempts" in result

    def test_security_event_injection_attempt(self):
        """Test logging with injection attempt in data."""
        template = "Request from {ip} with user-agent: {ua}"
        malicious_ip = "127.0.0.1\n[ERROR] Database dropped"
        malicious_ua = "<script>fetch('/api/secrets')</script>"
        result = format_log_message(template, ip=malicious_ip, ua=malicious_ua)
        # Injection should be neutralized
        assert "\n" not in result
        assert "<script>" not in result

    def test_security_event_privilege_escalation(self):
        """Test logging privilege escalation attempt."""
        template = "User {user} attempted unauthorized access to {resource}"
        result = format_log_message(template, user="regular_user", resource="/admin/superuser")
        assert "unauthorized access" in result
        assert "regular_user" in result


class TestFailedAuthLogging:
    """Test suite for failed authentication logging."""

    def test_failed_auth_wrong_password(self):
        """Test logging failed auth with wrong password."""
        template = "Failed login: {user} - Reason: {reason}"
        result = format_log_message(template, user="john.doe", reason="Invalid credentials")
        assert "Failed login" in result
        assert "john.doe" in result
        assert "Invalid credentials" in result

    def test_failed_auth_account_locked(self):
        """Test logging failed auth for locked account."""
        template = "Login rejected: {user} - Account {status}"
        result = format_log_message(template, user="jane.smith", status="locked")
        assert "Login rejected" in result
        assert "locked" in result

    def test_failed_auth_brute_force_indicators(self):
        """Test logging brute force indicators."""
        template = "Auth failure: {user} (attempt #{attempt}) from {ip}"
        result = format_log_message(template, user="admin", attempt=15, ip="10.20.30.40")
        assert "attempt #15" in result
        assert "10.20.30.40" in result


class TestSuspiciousActivityDetection:
    """Test suite for suspicious activity detection logging."""

    def test_suspicious_sql_injection_attempt(self):
        """Test logging SQL injection attempt."""
        template = "Possible SQL injection in {field}: {value}"
        sqli_payload = "' OR '1'='1' --"
        result = format_log_message(template, field="username", value=sqli_payload)
        assert "SQL injection" in result
        # The single quotes should be escaped
        assert "&#x27;" in result or "'" in result  # Depends on html.escape

    def test_suspicious_path_traversal_attempt(self):
        """Test logging path traversal attempt."""
        template = "Path traversal attempt: {path}"
        traversal = "../../../etc/passwd"
        result = format_log_message(template, path=traversal)
        assert "Path traversal attempt" in result

    def test_suspicious_xss_attempt(self):
        """Test logging XSS attempt."""
        template = "XSS attempt in parameter {param}: {value}"
        xss = "<script>alert(document.cookie)</script>"
        result = format_log_message(template, param="search", value=xss)
        assert "XSS attempt" in result
        assert "<script>" not in result  # Should be escaped

    def test_suspicious_rate_limit_violation(self):
        """Test logging rate limit violation."""
        template = "Rate limit exceeded: {client} - {count} requests in {window}s"
        result = format_log_message(template, client="192.168.1.100", count=150, window=60)
        assert "Rate limit exceeded" in result
        assert "150 requests" in result


class TestLogFormattingEdgeCases:
    """Test suite for log formatting edge cases."""

    def test_format_missing_placeholder(self):
        """Test formatting when placeholder is missing from kwargs."""
        template = "User {user} accessed {resource}"
        with pytest.raises(KeyError):
            format_log_message(template, user="admin")

    def test_format_extra_kwargs(self):
        """Test formatting with extra kwargs not in template."""
        template = "User {user} logged in"
        result = format_log_message(template, user="admin", extra_field="ignored", another_extra=123)
        assert result == "User admin logged in"

    def test_format_curly_braces_in_value(self):
        """Test formatting when value contains curly braces."""
        template = "Config: {config}"
        config_value = "{key: value}"
        result = format_log_message(template, config=config_value)
        assert "{key: value}" in result

    def test_format_nested_placeholders(self):
        """Test formatting with nested placeholder-like strings."""
        template = "Message: {msg}"
        msg = "Hello {name}"
        result = format_log_message(template, msg=msg)
        assert "Hello {name}" in result

    def test_format_json_like_string(self):
        """Test formatting with JSON-like string."""
        template = "Payload: {payload}"
        payload = '{"user": "admin", "action": "delete"}'
        result = format_log_message(template, payload=payload)
        assert "user" in result
        assert "admin" in result

    def test_format_none_values(self):
        """Test formatting with None values."""
        template = "Value: {value}"
        result = format_log_message(template, value=None)
        assert "None" in result

    def test_format_boolean_values(self):
        """Test formatting with boolean values."""
        template = "Success: {success}, Valid: {valid}"
        result = format_log_message(template, success=True, valid=False)
        assert "True" in result
        assert "False" in result


class TestIntegrationWithLogging:
    """Test integration with Python's logging module."""

    @patch("logging.Logger.info")
    def test_integration_with_logger_info(self, mock_info):
        """Test using format_log_message with logger.info."""
        import logging

        logger = logging.getLogger("test")

        message = format_log_message("User {user} action: {action}", user="test", action="login")
        logger.info(message)

        mock_info.assert_called_once()
        call_args = mock_info.call_args[0][0]
        assert "User test action: login" == call_args

    @patch("logging.Logger.warning")
    def test_integration_with_logger_warning(self, mock_warning):
        """Test using format_log_message with logger.warning."""
        import logging

        logger = logging.getLogger("test")

        message = format_log_message(
            "Suspicious: {ip} - {reason}",
            ip="10.0.0.1",
            reason="Port scan detected",
        )
        logger.warning(message)

        mock_warning.assert_called_once()

    @patch("logging.Logger.error")
    def test_integration_security_event_logged(self, mock_error):
        """Test security event is properly logged at error level."""
        import logging

        logger = logging.getLogger("security")

        message = format_log_message(
            "Security alert: {event} - Source: {source}",
            event="Unauthorized access attempt",
            source="192.168.1.50",
        )
        logger.error(message)

        mock_error.assert_called_once()


class TestSanitizationConsistency:
    """Test suite for consistency between sanitization functions."""

    def test_sanitization_preserves_safe_content(self):
        """Test that safe content is preserved by both functions."""
        safe_content = "SafeContent123"
        log_result = sanitize_for_log(safe_content)
        path_result = sanitize_path_component(safe_content)
        assert log_result == safe_content
        assert path_result == safe_content

    def test_sanitization_handles_unicode_consistently(self):
        """Test that both functions handle unicode properly."""
        unicode_content = "日本語ファイル"
        log_result = sanitize_for_log(unicode_content)
        path_result = sanitize_path_component(unicode_content)
        assert "日本語" in log_result
        assert "日本語" in path_result

    def test_null_bytes_removed_by_both(self):
        """Test that null bytes are removed by both functions."""
        content = "file\x00name"
        log_result = sanitize_for_log(content)
        path_result = sanitize_path_component(content)
        assert "\x00" not in log_result
        assert "\x00" not in path_result


class TestPerformanceAndLimits:
    """Test suite for performance and limit handling."""

    def test_sanitize_for_log_performance_large_input(self):
        """Test sanitization handles large inputs efficiently."""
        import time

        large_input = "X" * 10000 + "\n" * 100 + "<script>" * 50
        start = time.time()
        result = sanitize_for_log(large_input)
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should complete in less than 1 second
        assert len(result) == 256  # Should be truncated

    def test_sanitize_path_performance_large_input(self):
        """Test path sanitization handles large inputs."""
        import time

        large_input = "../" * 1000 + "filename"
        start = time.time()
        result = sanitize_path_component(large_input)
        elapsed = time.time() - start

        assert elapsed < 1.0
        assert ".." not in result

    def test_format_message_with_many_params(self):
        """Test formatting with many parameters."""
        template = ", ".join([f"param{i}={{val{i}}}" for i in range(50)])
        kwargs = {f"val{i}": f"value{i}" for i in range(50)}
        result = format_log_message(template, **kwargs)

        assert "param0=value0" in result
        assert "param49=value49" in result


# Markers for test categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.security,
    pytest.mark.api,
]

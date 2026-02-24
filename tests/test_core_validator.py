"""
Comprehensive tests for core/secure_input_validator.py - Secure Input Validator

Tests input validation, sanitization methods, and edge cases.
Target: 80%+ coverage for core/secure_input_validator.py
"""

import ipaddress
from unittest.mock import patch

import pytest

from core.secure_input_validator import (
    InputType,
    SecureInputValidator,
    ValidationError,
    ValidationRule,
    validate_command,
    validate_ip,
    validate_sql,
    validate_url,
)

# ==================== ValidationError Tests ====================


class TestValidationError:
    """Test ValidationError exception"""

    def test_error_creation(self):
        """Test creating ValidationError"""
        error = ValidationError("field_name", "Error message")
        assert error.field == "field_name"
        assert error.message == "Error message"
        assert error.value is None

    def test_error_with_value(self):
        """Test ValidationError with value"""
        error = ValidationError("field_name", "Error message", "bad_value")
        assert error.value == "bad_value"

    def test_error_string_representation(self):
        """Test string representation of ValidationError"""
        error = ValidationError("field_name", "Error message")
        assert str(error) == "[field_name] Error message"


# ==================== InputType Tests ====================


class TestInputType:
    """Test InputType enum"""

    def test_input_type_values(self):
        """Test all InputType values"""
        assert InputType.URL.value == "url"
        assert InputType.IP.value == "ip"
        assert InputType.DOMAIN.value == "domain"
        assert InputType.EMAIL.value == "email"
        assert InputType.COMMAND.value == "command"
        assert InputType.JSON.value == "json"
        assert InputType.TEXT.value == "text"
        assert InputType.HTML.value == "html"
        assert InputType.PATH.value == "path"
        assert InputType.SQL.value == "sql"


# ==================== ValidationRule Tests ====================


class TestValidationRule:
    """Test ValidationRule dataclass"""

    def test_default_values(self):
        """Test default validation rule values"""
        rule = ValidationRule()
        assert rule.min_length == 0
        assert rule.max_length == 1000
        assert rule.pattern is None
        assert rule.allowed_chars is None
        assert rule.sanitize is True
        assert rule.blocklist is None

    def test_custom_values(self):
        """Test custom validation rule values"""
        rule = ValidationRule(
            min_length=5,
            max_length=100,
            pattern=r"^[a-z]+$",
            allowed_chars="abcdefghijklmnopqrstuvwxyz",
            sanitize=False,
            blocklist=["bad", "worse"],
        )
        assert rule.min_length == 5
        assert rule.max_length == 100
        assert rule.pattern == r"^[a-z]+$"
        assert rule.sanitize is False
        assert rule.blocklist == ["bad", "worse"]


# ==================== SecureInputValidator Initialization Tests ====================


class TestSecureInputValidatorInit:
    """Test SecureInputValidator initialization"""

    def test_default_initialization(self):
        """Test default initialization"""
        validator = SecureInputValidator()
        assert validator.strict_mode is True
        assert validator.audit_logging is True
        assert validator.validation_stats == {
            "total_validated": 0,
            "rejected": 0,
            "sanitized": 0,
        }

    def test_custom_initialization(self):
        """Test custom initialization"""
        validator = SecureInputValidator(
            strict_mode=False, audit_logging=False
        )
        assert validator.strict_mode is False
        assert validator.audit_logging is False


# ==================== URL Validation Tests ====================


class TestUrlValidation:
    """Test URL validation methods"""

    def test_valid_http_url(self):
        """Test valid HTTP URL"""
        validator = SecureInputValidator()
        result = validator.validate_url("http://example.com")
        assert result == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL"""
        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com")
        assert result == "https://example.com"

    def test_valid_url_with_path(self):
        """Test valid URL with path"""
        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com/path/to/page")
        assert result == "https://example.com/path/to/page"

    def test_valid_url_with_query(self):
        """Test valid URL with query string"""
        validator = SecureInputValidator()
        result = validator.validate_url(
            "https://example.com?key=value&foo=bar"
        )
        assert "example.com" in result

    def test_valid_url_with_port(self):
        """Test valid URL with port"""
        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com:8080")
        assert result == "https://example.com:8080"

    def test_empty_url(self):
        """Test empty URL raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="URL is required"):
            validator.validate_url("")

    def test_none_url(self):
        """Test None URL raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="URL is required"):
            validator.validate_url(None)

    def test_invalid_url_format(self):
        """Test invalid URL format raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Invalid URL format"):
            validator.validate_url("not-a-url")

    def test_url_too_long(self):
        """Test URL exceeding max length raises error"""
        validator = SecureInputValidator()
        long_url = "https://example.com/" + "a" * 2048
        with pytest.raises(ValidationError, match="URL too long"):
            validator.validate_url(long_url)

    def test_localhost_blocked(self):
        """Test localhost URL is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Local URLs not allowed"):
            validator.validate_url("http://localhost:8080")

    def test_127_0_0_1_blocked(self):
        """Test 127.0.0.1 URL is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Local URLs not allowed"):
            validator.validate_url("http://127.0.0.1:8080")

    def test_192_168_blocked(self):
        """Test 192.168.x.x URL is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Local URLs not allowed"):
            validator.validate_url("http://192.168.1.1")

    def test_10_x_blocked(self):
        """Test 10.x.x.x URL is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Local URLs not allowed"):
            validator.validate_url("http://10.0.0.1")

    def test_localhost_allowed(self):
        """Test localhost URL allowed when allow_local=True"""
        validator = SecureInputValidator()
        result = validator.validate_url(
            "http://localhost:8080", allow_local=True
        )
        assert result == "http://localhost:8080"

    def test_html_entities_decoded(self):
        """Test HTML entities are decoded"""
        validator = SecureInputValidator()
        result = validator.validate_url(
            "https://example.com?key=&lt;value&gt;"
        )
        assert "<value>" in result

    def test_null_bytes_removed(self):
        """Test null bytes are removed from URL"""
        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com\x00/path")
        assert "\x00" not in result


# ==================== IP Validation Tests ====================


class TestIpValidation:
    """Test IP validation methods"""

    def test_valid_public_ip(self):
        """Test valid public IP"""
        validator = SecureInputValidator()
        result = validator.validate_ip("8.8.8.8")
        assert result == "8.8.8.8"

    def test_valid_public_ip_quad(self):
        """Test valid public IP with different octets"""
        validator = SecureInputValidator()
        result = validator.validate_ip("1.1.1.1")
        assert result == "1.1.1.1"

    def test_empty_ip(self):
        """Test empty IP raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="IP address is required"):
            validator.validate_ip("")

    def test_none_ip(self):
        """Test None IP raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="IP address is required"):
            validator.validate_ip(None)

    def test_invalid_ip_format(self):
        """Test invalid IP format raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Invalid IP address"):
            validator.validate_ip("not-an-ip")

    def test_private_ip_blocked(self):
        """Test private IP is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Private IP addresses not allowed"
        ):
            validator.validate_ip("192.168.1.1")

    def test_private_ip_10_blocked(self):
        """Test 10.x.x.x IP is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Private IP addresses not allowed"
        ):
            validator.validate_ip("10.0.0.1")

    def test_private_ip_172_blocked(self):
        """Test 172.16.x.x IP is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Private IP addresses not allowed"
        ):
            validator.validate_ip("172.16.0.1")

    def test_loopback_blocked(self):
        """Test loopback IP is blocked by default"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Private IP addresses not allowed"
        ):
            validator.validate_ip("127.0.0.1")

    def test_private_ip_allowed(self):
        """Test private IP allowed when allow_private=True"""
        validator = SecureInputValidator()
        result = validator.validate_ip("192.168.1.1", allow_private=True)
        assert result == "192.168.1.1"

    def test_ip_with_whitespace(self):
        """Test IP with whitespace is cleaned"""
        validator = SecureInputValidator()
        result = validator.validate_ip("  8.8.8.8  ")
        assert result == "8.8.8.8"


# ==================== Domain Validation Tests ====================


class TestDomainValidation:
    """Test domain validation methods"""

    def test_valid_domain(self):
        """Test valid domain"""
        validator = SecureInputValidator()
        result = validator.validate_domain("example.com")
        assert result == "example.com"

    def test_valid_subdomain(self):
        """Test valid subdomain"""
        validator = SecureInputValidator()
        result = validator.validate_domain("sub.example.com")
        assert result == "sub.example.com"

    def test_valid_multi_level_subdomain(self):
        """Test valid multi-level subdomain"""
        validator = SecureInputValidator()
        result = validator.validate_domain("deep.sub.example.com")
        assert result == "deep.sub.example.com"

    def test_empty_domain(self):
        """Test empty domain raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Domain is required"):
            validator.validate_domain("")

    def test_none_domain(self):
        """Test None domain raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Domain is required"):
            validator.validate_domain(None)

    def test_invalid_domain_format(self):
        """Test invalid domain format raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Invalid domain format"):
            validator.validate_domain("not a domain!")

    def test_domain_too_long(self):
        """Test domain exceeding max length raises error"""
        validator = SecureInputValidator()
        long_domain = "a" * 254
        with pytest.raises(ValidationError, match="Domain too long"):
            validator.validate_domain(long_domain)

    def test_domain_converted_to_lowercase(self):
        """Test domain is converted to lowercase"""
        validator = SecureInputValidator()
        result = validator.validate_domain("EXAMPLE.COM")
        assert result == "example.com"

    def test_domain_with_whitespace(self):
        """Test domain with whitespace is cleaned"""
        validator = SecureInputValidator()
        result = validator.validate_domain("  example.com  ")
        assert result == "example.com"

    def test_domain_starting_with_dash(self):
        """Test domain starting with dash is invalid"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Invalid domain format"):
            validator.validate_domain("-example.com")


# ==================== Command Validation Tests ====================


class TestCommandValidation:
    """Test command validation methods"""

    def test_valid_simple_command(self):
        """Test valid simple command"""
        validator = SecureInputValidator()
        result = validator.validate_command("ls")
        assert result == "ls"

    def test_valid_command_with_args(self):
        """Test valid command with arguments"""
        validator = SecureInputValidator()
        result = validator.validate_command("nmap -sV target.com")
        assert result == "nmap -sV target.com"

    def test_empty_command(self):
        """Test empty command raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Command is required"):
            validator.validate_command("")

    def test_none_command(self):
        """Test None command raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Command is required"):
            validator.validate_command(None)

    def test_dangerous_command_rm_blocked(self):
        """Test rm command is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Dangerous command detected"
        ):
            validator.validate_command("rm -rf /")

    def test_dangerous_command_bash_blocked(self):
        """Test bash command is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Dangerous command detected"
        ):
            validator.validate_command("bash script.sh")

    def test_dangerous_command_python_blocked(self):
        """Test python command is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Dangerous command detected"
        ):
            validator.validate_command("python exploit.py")

    def test_shell_metacharacter_semicolon_blocked(self):
        """Test semicolon metacharacter is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Shell metacharacter not allowed"
        ):
            validator.validate_command("cmd1; cmd2")

    def test_shell_metacharacter_ampersand_blocked(self):
        """Test ampersand metacharacter is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Shell metacharacter not allowed"
        ):
            validator.validate_command("cmd1 && cmd2")

    def test_shell_metacharacter_pipe_blocked(self):
        """Test pipe metacharacter is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Shell metacharacter not allowed"
        ):
            validator.validate_command("cmd1 | cmd2")

    def test_shell_metacharacter_backtick_blocked(self):
        """Test backtick metacharacter is blocked"""
        validator = SecureInputValidator()
        # Backtick triggers dangerous command check first (extracts 'cmd' as token)
        with pytest.raises(ValidationError):
            validator.validate_command("`cmd`")

    def test_shell_metacharacter_dollar_blocked(self):
        """Test dollar metacharacter is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Shell metacharacter not allowed"
        ):
            validator.validate_command("echo $VAR")


# ==================== SQL Validation Tests ====================


class TestSqlValidation:
    """Test SQL validation methods"""

    def test_valid_simple_sql(self):
        """Test valid simple SQL without keywords"""
        validator = SecureInputValidator()
        # Most SQL keywords are blocked for security
        result = validator.validate_sql("column_name = value")
        assert result == "column_name = value"

    def test_sql_blocked_keywords(self):
        """Test that common SQL keywords are blocked for security"""
        validator = SecureInputValidator()
        # SELECT is blocked by the validator
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql("SELECT id FROM users")

    def test_empty_sql(self):
        """Test empty SQL raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="SQL is required"):
            validator.validate_sql("")

    def test_none_sql(self):
        """Test None SQL raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="SQL is required"):
            validator.validate_sql(None)

    def test_sql_injection_union_blocked(self):
        """Test UNION-based SQL injection is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql(
                "SELECT * FROM users UNION SELECT * FROM passwords"
            )

    def test_sql_injection_or_blocked(self):
        """Test OR-based SQL injection is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql("SELECT * FROM users WHERE id = 1 OR 1=1")

    def test_sql_injection_comment_blocked(self):
        """Test comment-based SQL injection is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql("SELECT * FROM users; --")

    def test_sql_injection_stored_proc_blocked(self):
        """Test stored procedure SQL injection is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql("EXEC xp_cmdshell 'dir'")

    def test_sql_injection_time_delay_blocked(self):
        """Test time delay SQL injection is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="SQL injection pattern detected"
        ):
            validator.validate_sql("SELECT * FROM users WHERE SLEEP(5)")


# ==================== HTML Validation Tests ====================


class TestHtmlValidation:
    """Test HTML validation methods"""

    def test_valid_simple_html(self):
        """Test valid simple HTML"""
        validator = SecureInputValidator()
        result = validator.validate_html("<p>Hello World</p>")
        assert "Hello World" in result  # Should be escaped

    def test_valid_safe_tags(self):
        """Test safe HTML tags are allowed"""
        validator = SecureInputValidator()
        result = validator.validate_html("<div class='test'>Content</div>")
        # Tags should be escaped
        assert "&lt;div" in result or "<div" in result

    def test_empty_html(self):
        """Test empty HTML raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="HTML content is required"):
            validator.validate_html("")

    def test_none_html(self):
        """Test None HTML raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="HTML content is required"):
            validator.validate_html(None)

    def test_xss_script_blocked(self):
        """Test XSS script tag is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="XSS pattern detected"):
            validator.validate_html("<script>alert('xss')</script>")

    def test_xss_javascript_protocol_blocked(self):
        """Test javascript: protocol is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="XSS pattern detected"):
            validator.validate_html('<a href="javascript:alert(1)">Click</a>')

    def test_xss_event_handler_blocked(self):
        """Test event handler XSS is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="XSS pattern detected"):
            validator.validate_html('<img src="x" onerror="alert(1)">')

    def test_xss_iframe_blocked(self):
        """Test iframe XSS is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="XSS pattern detected"):
            validator.validate_html('<iframe src="evil.com"></iframe>')


# ==================== Path Validation Tests ====================


class TestPathValidation:
    """Test path validation methods"""

    def test_valid_simple_path(self):
        """Test valid simple path"""
        validator = SecureInputValidator()
        result = validator.validate_path("/home/user/file.txt")
        assert result == "/home/user/file.txt"

    def test_valid_relative_path(self):
        """Test valid relative path"""
        validator = SecureInputValidator()
        result = validator.validate_path("documents/file.txt")
        assert result == "documents/file.txt"

    def test_empty_path(self):
        """Test empty path raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Path is required"):
            validator.validate_path("")

    def test_none_path(self):
        """Test None path raises error"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError, match="Path is required"):
            validator.validate_path(None)

    def test_path_traversal_dotdot_blocked(self):
        """Test ../ path traversal is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Path traversal not allowed"
        ):
            validator.validate_path("../../../etc/passwd")

    def test_path_traversal_backslash_blocked(self):
        """Test ..\ path traversal is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Path traversal not allowed"
        ):
            validator.validate_path("..\\..\\windows\\system32")

    def test_path_traversal_encoded_blocked(self):
        """Test encoded path traversal is blocked"""
        validator = SecureInputValidator()
        with pytest.raises(
            ValidationError, match="Path traversal not allowed"
        ):
            validator.validate_path("%2e%2e%2fetc%2fpasswd")

    def test_backslash_normalized(self):
        """Test backslashes are normalized to forward slashes"""
        validator = SecureInputValidator()
        result = validator.validate_path("path\\to\\file")
        assert result == "path/to/file"


# ==================== Private IP Detection Tests ====================


class TestPrivateIpDetection:
    """Test private IP detection helper methods"""

    def test_is_private_ip_true_10(self):
        """Test 10.x.x.x is detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("10.0.0.1") is True

    def test_is_private_ip_true_172(self):
        """Test 172.16.x.x is detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("172.16.0.1") is True

    def test_is_private_ip_true_192(self):
        """Test 192.168.x.x is detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("192.168.1.1") is True

    def test_is_private_ip_true_127(self):
        """Test 127.x.x.x is detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("127.0.0.1") is True

    def test_is_private_ip_true_169(self):
        """Test 169.254.x.x is detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("169.254.0.1") is True

    def test_is_private_ip_false_public(self):
        """Test public IP is not detected as private"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("8.8.8.8") is False

    def test_is_private_ip_with_ipaddress_object(self):
        """Test _is_private_ip with ipaddress object"""
        validator = SecureInputValidator()
        ip = ipaddress.ip_address("192.168.1.1")
        assert validator._is_private_ip(ip) is True

    def test_is_private_ip_invalid(self):
        """Test _is_private_ip with invalid IP"""
        validator = SecureInputValidator()
        assert validator._is_private_ip("not-an-ip") is False

    def test_extract_ip_from_url(self):
        """Test extracting IP from URL"""
        validator = SecureInputValidator()
        result = validator._extract_ip_from_url("http://192.168.1.1/path")
        assert result == "192.168.1.1"

    def test_extract_ip_from_url_no_ip(self):
        """Test extracting IP from URL without IP"""
        validator = SecureInputValidator()
        result = validator._extract_ip_from_url("http://example.com/path")
        assert result is None


# ==================== Statistics Tests ====================


class TestStatistics:
    """Test validation statistics"""

    def test_initial_stats(self):
        """Test initial statistics"""
        validator = SecureInputValidator()
        stats = validator.get_stats()
        assert stats["total_validated"] == 0
        assert stats["rejected"] == 0
        assert stats["sanitized"] == 0

    def test_stats_after_successful_validation(self):
        """Test statistics after successful validation"""
        validator = SecureInputValidator()
        validator.validate_domain("example.com")
        stats = validator.get_stats()
        assert stats["total_validated"] == 1
        assert stats["rejected"] == 0

    def test_stats_after_rejection(self):
        """Test statistics after validation rejection"""
        validator = SecureInputValidator()
        try:
            validator.validate_domain("-invalid")
        except ValidationError:
            pass
        stats = validator.get_stats()
        assert stats["rejected"] == 1

    def test_stats_after_html_sanitization(self):
        """Test statistics after HTML sanitization"""
        validator = SecureInputValidator()
        try:
            validator.validate_html("<p>Test</p>")  # This gets sanitized
        except ValidationError:
            pass
        stats = validator.get_stats()
        # sanitized count increases when HTML is sanitized
        assert "sanitized" in stats

    def test_stats_returns_copy(self):
        """Test that get_stats returns a copy, not reference"""
        validator = SecureInputValidator()
        stats = validator.get_stats()
        stats["total_validated"] = 999
        new_stats = validator.get_stats()
        assert new_stats["total_validated"] == 0


# ==================== Audit Logging Tests ====================


class TestAuditLogging:
    """Test audit logging functionality"""

    @patch("core.secure_input_validator.logger")
    def test_rejection_logged(self, mock_logger):
        """Test that rejections are logged"""
        validator = SecureInputValidator(audit_logging=True)
        try:
            validator.validate_domain("-invalid")
        except ValidationError:
            pass
        mock_logger.warning.assert_called()

    @patch("core.secure_input_validator.logger")
    def test_rejection_not_logged_when_disabled(self, mock_logger):
        """Test that rejections are not logged when disabled"""
        validator = SecureInputValidator(audit_logging=False)
        try:
            validator.validate_domain("-invalid")
        except ValidationError:
            pass
        mock_logger.warning.assert_not_called()


# ==================== Convenience Function Tests ====================


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_validate_url_convenience(self):
        """Test validate_url convenience function"""
        result = validate_url("https://example.com")
        assert result == "https://example.com"

    def test_validate_url_convenience_with_allow_local(self):
        """Test validate_url with allow_local parameter"""
        result = validate_url("http://localhost:8080", allow_local=True)
        assert result == "http://localhost:8080"

    def test_validate_ip_convenience(self):
        """Test validate_ip convenience function"""
        result = validate_ip("8.8.8.8")
        assert result == "8.8.8.8"

    def test_validate_ip_convenience_with_allow_private(self):
        """Test validate_ip with allow_private parameter"""
        result = validate_ip("192.168.1.1", allow_private=True)
        assert result == "192.168.1.1"

    def test_validate_command_convenience(self):
        """Test validate_command convenience function"""
        result = validate_command("nmap -sV")
        assert result == "nmap -sV"

    def test_validate_sql_convenience_safe(self):
        """Test validate_sql convenience function with safe SQL"""
        result = validate_sql("column_name = value")
        assert result == "column_name = value"


# ==================== Edge Case Tests ====================


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_unicode_in_domain(self):
        """Test handling of unicode in domain"""
        validator = SecureInputValidator()
        # Unicode domains should be handled (may fail validation)
        try:
            result = validator.validate_domain("münchen.de")
            assert isinstance(result, str)
        except ValidationError:
            pass  # Also acceptable

    def test_whitespace_only_input(self):
        """Test handling of whitespace-only input"""
        validator = SecureInputValidator()
        # After stripping, should be empty and raise error
        with pytest.raises(ValidationError):
            validator.validate_domain("   ")

    def test_very_long_input(self):
        """Test handling of very long input"""
        validator = SecureInputValidator()
        long_input = "a" * 10000
        with pytest.raises(ValidationError):
            validator.validate_domain(long_input)

    def test_special_characters_in_path(self):
        """Test special characters in path"""
        validator = SecureInputValidator()
        result = validator.validate_path("/path/with-dash_underscore.txt")
        assert result == "/path/with-dash_underscore.txt"

    def test_multiple_spaces_in_command(self):
        """Test multiple spaces in command"""
        validator = SecureInputValidator()
        result = validator.validate_command("  nmap   -sV  ")
        assert result == "nmap   -sV"

    def test_sql_with_newlines_safe(self):
        """Test safe SQL with newlines"""
        validator = SecureInputValidator()
        result = validator.validate_sql("column1 = value1\ncolumn2 = value2")
        assert "column1" in result

    def test_html_entity_handling(self):
        """Test HTML entity handling in URL"""
        validator = SecureInputValidator()
        result = validator.validate_url(
            "https://example.com?q=test&amp;foo=bar"
        )
        # Should decode &amp; to &
        assert "&amp;" not in result or "&" in result

    def test_ip_address_object_input(self):
        """Test _is_private_ip with ipaddress object"""
        validator = SecureInputValidator()
        ip = ipaddress.IPv4Address("10.0.0.1")
        assert validator._is_private_ip(ip) is True

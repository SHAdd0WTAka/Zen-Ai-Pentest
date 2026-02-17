"""
Unit Tests for Secure Input Validator
"""

import pytest
from core.secure_input_validator import (
    SecureInputValidator,
    ValidationError,
    validate_url,
    validate_ip,
    validate_command,
    validate_sql
)


class TestSecureInputValidator:
    """Test SecureInputValidator"""

    def test_init(self):
        """Test validator initialization"""
        validator = SecureInputValidator()
        assert validator is not None
        assert validator.strict_mode is True

    def test_validate_url_valid(self):
        """Test valid URL validation"""
        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com")
        assert result == "https://example.com"

    def test_validate_url_block_localhost(self):
        """Test localhost blocking (SSRF prevention)"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_url("http://localhost/admin")

    def test_validate_url_block_private_ip(self):
        """Test private IP blocking (SSRF prevention)"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_url("http://192.168.1.1/admin")

    def test_validate_url_allow_local_with_flag(self):
        """Test allowing local URLs with flag"""
        validator = SecureInputValidator()
        result = validator.validate_url("http://localhost/api", allow_local=True)
        assert "localhost" in result

    def test_validate_ip_valid(self):
        """Test valid IP validation"""
        validator = SecureInputValidator()
        result = validator.validate_ip("8.8.8.8")
        assert result == "8.8.8.8"

    def test_validate_ip_block_private(self):
        """Test private IP blocking"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_ip("192.168.1.1")

    def test_validate_ip_allow_private_with_flag(self):
        """Test allowing private IPs with flag"""
        validator = SecureInputValidator()
        result = validator.validate_ip("192.168.1.1", allow_private=True)
        assert result == "192.168.1.1"

    def test_validate_command_valid(self):
        """Test valid command"""
        validator = SecureInputValidator()
        result = validator.validate_command("nmap -sV target.com")
        assert result == "nmap -sV target.com"

    def test_validate_command_block_dangerous(self):
        """Test blocking dangerous commands"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_command("rm -rf /")

    def test_validate_command_block_shell_meta(self):
        """Test blocking shell metacharacters"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_command("ls; cat /etc/passwd")

    def test_validate_sql_valid(self):
        """Test valid SQL"""
        validator = SecureInputValidator()
        result = validator.validate_sql("SELECT * FROM users WHERE id = 1")
        assert result == "SELECT * FROM users WHERE id = 1"

    def test_validate_sql_block_injection(self):
        """Test blocking SQL injection"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_sql("SELECT * FROM users; DROP TABLE users--")

    def test_validate_sql_block_union(self):
        """Test blocking UNION injection"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_sql("SELECT * FROM users UNION SELECT * FROM admin")

    def test_validate_path_valid(self):
        """Test valid path"""
        validator = SecureInputValidator()
        result = validator.validate_path("/home/user/file.txt")
        assert result == "/home/user/file.txt"

    def test_validate_path_block_traversal(self):
        """Test blocking path traversal"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_path("../../../etc/passwd")

    def test_validate_html_block_xss(self):
        """Test blocking XSS"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_html("<script>alert('XSS')</script>")

    def test_validate_domain_valid(self):
        """Test valid domain"""
        validator = SecureInputValidator()
        result = validator.validate_domain("example.com")
        assert result == "example.com"

    def test_validate_domain_invalid(self):
        """Test invalid domain"""
        validator = SecureInputValidator()
        with pytest.raises(ValidationError):
            validator.validate_domain("not a domain!")

    def test_stats_tracking(self):
        """Test statistics tracking"""
        validator = SecureInputValidator()

        # Valid validations
        validator.validate_url("https://example.com")
        validator.validate_ip("8.8.8.8")

        # Invalid validation
        try:
            validator.validate_url("http://localhost/test")
        except Exception:
            pass

        stats = validator.get_stats()
        assert stats['total_validated'] == 3
        assert stats['rejected'] == 1


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_validate_url_convenience(self):
        """Test validate_url convenience function"""
        result = validate_url("https://example.com")
        assert result == "https://example.com"

    def test_validate_ip_convenience(self):
        """Test validate_ip convenience function"""
        result = validate_ip("8.8.8.8")
        assert result == "8.8.8.8"

    def test_validate_command_convenience(self):
        """Test validate_command convenience function"""
        result = validate_command("nmap -sV target.com")
        assert result == "nmap -sV target.com"

    def test_validate_sql_convenience(self):
        """Test validate_sql convenience function"""
        result = validate_sql("SELECT * FROM users")
        assert result == "SELECT * FROM users"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

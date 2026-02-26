"""
Tests for core/input_validator.py
Target: 90%+ Coverage
"""
import pytest
from unittest.mock import patch, MagicMock
import subprocess


class TestValidationRule:
    """Test ValidationRule dataclass"""
    
    def test_validation_rule_creation(self):
        """Test ValidationRule kann erstellt werden"""
        from core.input_validator import ValidationRule
        import re
        
        rule = ValidationRule(
            pattern=re.compile(r"^[a-z]+$"),
            max_length=100,
            allow_empty=False,
            error_message="Invalid input"
        )
        
        assert rule.max_length == 100
        assert rule.allow_empty is False


class TestInputValidatorInit:
    """Test InputValidator initialization"""
    
    def test_init_creates_rules(self):
        """Test validator creates default rules"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        
        assert "domain" in validator.rules
        assert "ip" in validator.rules
        assert "email" in validator.rules
        assert "filename" in validator.rules
    
    def test_init_patterns(self):
        """Test validator has compiled patterns"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        
        assert validator.DOMAIN_PATTERN is not None
        assert validator.IP_PATTERN is not None
        assert validator.EMAIL_PATTERN is not None
        assert validator.FILENAME_PATTERN is not None
        assert validator.DANGEROUS_CHARS is not None
        assert validator.PATH_TRAVERSAL is not None


class TestValidateDomain:
    """Test validate_domain method"""
    
    def test_validate_valid_domain(self):
        """Test valid domain passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_domain("example.com")
        assert result == "example.com"
    
    def test_validate_domain_strips_whitespace(self):
        """Test domain whitespace is stripped"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_domain("  example.com  ")
        assert result == "example.com"
    
    def test_validate_domain_lowercase(self):
        """Test domain is lowercased"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_domain("EXAMPLE.COM")
        assert result == "example.com"
    
    def test_validate_empty_domain(self):
        """Test empty domain returns None"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_domain("") is None
        assert validator.validate_domain(None) is None
    
    def test_validate_domain_too_long(self):
        """Test too long domain is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        long_domain = "a" * 300 + ".com"
        assert validator.validate_domain(long_domain) is None
    
    def test_validate_domain_invalid_format(self):
        """Test invalid domain format is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_domain("not a domain!") is None
        assert validator.validate_domain("-invalid.com") is None
    
    def test_validate_domain_dangerous_chars(self):
        """Test domain with dangerous chars is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_domain("evil.com;rm -rf") is None


class TestValidateIp:
    """Test validate_ip method"""
    
    def test_validate_valid_ip(self):
        """Test valid IP passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_ip("192.168.1.1") == "192.168.1.1"
        assert validator.validate_ip("10.0.0.1") == "10.0.0.1"
        assert validator.validate_ip("255.255.255.255") == "255.255.255.255"
    
    def test_validate_ip_strips_whitespace(self):
        """Test IP whitespace is stripped"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_ip("  192.168.1.1  ")
        assert result == "192.168.1.1"
    
    def test_validate_empty_ip(self):
        """Test empty IP returns None"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_ip("") is None
        assert validator.validate_ip(None) is None
    
    def test_validate_invalid_ip(self):
        """Test invalid IP is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_ip("999.999.999.999") is None
        assert validator.validate_ip("not.an.ip.address") is None
        assert validator.validate_ip("192.168.1") is None


class TestValidateEmail:
    """Test validate_email method"""
    
    def test_validate_valid_email(self):
        """Test valid email passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_email("user@example.com") == "user@example.com"
        assert validator.validate_email("test.user+tag@domain.co.uk") == "test.user+tag@domain.co.uk"
    
    def test_validate_email_lowercase(self):
        """Test email is lowercased"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_email("USER@EXAMPLE.COM")
        assert result == "user@example.com"
    
    def test_validate_empty_email(self):
        """Test empty email returns None"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_email("") is None
        assert validator.validate_email(None) is None
    
    def test_validate_invalid_email(self):
        """Test invalid email is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_email("notanemail") is None
        assert validator.validate_email("@nodomain.com") is None
        assert validator.validate_email("spaces in@email.com") is None
    
    def test_validate_email_too_long(self):
        """Test too long email is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        long_email = "a" * 300 + "@test.com"
        assert validator.validate_email(long_email) is None


class TestValidateUrl:
    """Test validate_url method"""
    
    def test_validate_valid_http_url(self):
        """Test valid HTTP URL passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_url("http://example.com/path")
        assert result == "http://example.com/path"
    
    def test_validate_valid_https_url(self):
        """Test valid HTTPS URL passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_url("https://example.com")
        assert result == "https://example.com"
    
    def test_validate_url_with_port(self):
        """Test URL with port"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_url("http://example.com:8080")
        assert result == "http://example.com:8080"
    
    def test_validate_empty_url(self):
        """Test empty URL returns None"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_url("") is None
        assert validator.validate_url(None) is None
    
    def test_validate_invalid_scheme(self):
        """Test invalid URL scheme is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_url("ftp://example.com") is None
        assert validator.validate_url("javascript://alert(1)") is None
    
    def test_validate_url_no_hostname(self):
        """Test URL without hostname is rejected"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_url("http:///path") is None
    
    def test_validate_url_custom_schemes(self):
        """Test custom allowed schemes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.validate_url(
            "ftp://example.com",
            allowed_schemes=["ftp", "sftp"]
        )
        assert result == "ftp://example.com"


class TestValidateFilename:
    """Test validate_filename method"""
    
    def test_validate_valid_filename(self):
        """Test valid filename passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_filename("document.pdf") == "document.pdf"
        assert validator.validate_filename("file_name-123.txt") == "file_name-123.txt"
    
    def test_validate_filename_strips_path(self):
        """Test path is stripped from filename"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_filename("/path/to/file.txt") == "file.txt"
        assert validator.validate_filename("C:\\path\\file.txt") == "file.txt"
    
    def test_validate_empty_filename(self):
        """Test empty filename returns None"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.validate_filename("") is None
        assert validator.validate_filename(None) is None
    
    def test_validate_filename_path_traversal(self):
        """Test path traversal strips path, keeps filename"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        # Strips path, returns just filename
        assert validator.validate_filename("../../../etc/passwd") == "passwd"
        assert validator.validate_filename("..\\windows\\system32") == "system32"


class TestSanitizePath:
    """Test sanitize_path method"""
    
    def test_sanitize_normal_path(self):
        """Test normal path sanitization"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_path("/home/user/file.txt") == "/home/user/file.txt"
    
    def test_sanitize_empty_path(self):
        """Test empty path returns root"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_path("") == "/"
        assert validator.sanitize_path(None) == "/"
    
    def test_sanitize_removes_traversal(self):
        """Test path traversal components are removed"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        # ".." and "." are removed, path is simplified
        assert validator.sanitize_path("/home/../etc/passwd") == "/home/etc/passwd"
        assert validator.sanitize_path("/./file.txt") == "/file.txt"
    
    def test_sanitize_normalizes_slashes(self):
        """Test backslashes are normalized"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_path("\\home\\user") == "/home/user"


class TestSanitizeForShell:
    """Test sanitize_for_shell method"""
    
    def test_sanitize_normal_string(self):
        """Test normal string passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_for_shell("normal-string_123.txt") == "normal-string_123.txt"
    
    def test_sanitize_removes_metacharacters(self):
        """Test shell metacharacters are removed"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_for_shell("test; rm -rf") == "test rm -rf"
        assert validator.sanitize_for_shell("`whoami`") == "whoami"
        assert validator.sanitize_for_shell('$(echo hacked)') == "echo hacked"
        assert validator.sanitize_for_shell('"quotes"') == "quotes"
    
    def test_sanitize_empty_string(self):
        """Test empty string returns empty"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_for_shell("") == ""
        assert validator.sanitize_for_shell(None) == ""


class TestEscapeHtml:
    """Test escape_html method"""
    
    def test_escape_html_basic(self):
        """Test basic HTML escaping"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.escape_html("<script>") == "&lt;script&gt;"
        assert validator.escape_html('"quotes"') == "&quot;quotes&quot;"
        assert validator.escape_html("'single'") == "&#x27;single&#x27;"
    
    def test_escape_html_no_change(self):
        """Test normal text unchanged"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.escape_html("Hello World") == "Hello World"
    
    def test_escape_html_non_string(self):
        """Test non-string input is converted"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.escape_html(123) == "123"


class TestSanitizeLlmOutput:
    """Test sanitize_llm_output method"""
    
    def test_sanitize_normal_output(self):
        """Test normal output passes"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.sanitize_llm_output("Hello\nWorld\t!")
        assert "Hello" in result
        assert "World" in result
    
    def test_sanitize_removes_null_bytes(self):
        """Test null bytes are removed"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.sanitize_llm_output("hello\x00world")
        assert "\x00" not in result
    
    def test_sanitize_removes_control_chars(self):
        """Test control characters are removed"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.sanitize_llm_output("test\x01\x02\x03")
        # Only printable chars remain (plus \n and \t)
        assert all(ord(c) >= 32 or c in '\n\t' for c in result)
    
    def test_sanitize_escapes_html(self):
        """Test HTML is escaped"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        result = validator.sanitize_llm_output("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_empty_output(self):
        """Test empty output"""
        from core.input_validator import InputValidator
        
        validator = InputValidator()
        assert validator.sanitize_llm_output("") == ""
        assert validator.sanitize_llm_output(None) == ""


class TestSecureSubprocessRun:
    """Test SecureSubprocess.run method"""
    
    def test_run_empty_command_raises(self):
        """Test empty command raises ValueError"""
        from core.input_validator import SecureSubprocess
        
        with pytest.raises(ValueError):
            SecureSubprocess.run([])
    
    def test_run_with_dangerous_chars_raises(self):
        """Test dangerous chars raise ValueError"""
        from core.input_validator import SecureSubprocess
        
        with pytest.raises(ValueError):
            SecureSubprocess.run(["echo", "hello; rm -rf"])
        
        with pytest.raises(ValueError):
            SecureSubprocess.run(["echo", "`whoami`"])
    
    @patch('core.input_validator.subprocess.run')
    def test_run_successful(self, mock_run):
        """Test successful command execution"""
        from core.input_validator import SecureSubprocess
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = SecureSubprocess.run(["echo", "hello"])
        
        assert result.returncode == 0
        mock_run.assert_called_once()
        # Verify shell=False
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['shell'] is False
    
    @patch('core.input_validator.subprocess.run')
    def test_run_timeout(self, mock_run):
        """Test command timeout"""
        from core.input_validator import SecureSubprocess
        
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)
        
        with pytest.raises(subprocess.TimeoutExpired):
            SecureSubprocess.run(["sleep", "10"], timeout=300)
    
    @patch('core.input_validator.subprocess.run')
    def test_run_called_process_error(self, mock_run):
        """Test command failure"""
        from core.input_validator import SecureSubprocess
        
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        with pytest.raises(subprocess.CalledProcessError):
            SecureSubprocess.run(["false"], check=True)


class TestValidateNucleiArgs:
    """Test validate_nuclei_args method"""
    
    def test_validate_valid_args(self):
        """Test valid Nuclei args pass"""
        from core.input_validator import SecureSubprocess
        
        assert SecureSubprocess.validate_nuclei_args(["-u", "example.com"]) is True
        assert SecureSubprocess.validate_nuclei_args(["-list", "targets.txt"]) is True
    
    def test_validate_blocks_shell_flag(self):
        """Test -shell flag is blocked"""
        from core.input_validator import SecureSubprocess
        
        assert SecureSubprocess.validate_nuclei_args(["-shell", "whoami"]) is False
    
    def test_validate_blocks_exec_flag(self):
        """Test -exec flag is blocked"""
        from core.input_validator import SecureSubprocess
        
        assert SecureSubprocess.validate_nuclei_args(["-exec", "malicious"]) is False
    
    def test_validate_blocks_command_flag(self):
        """Test -command flag is blocked"""
        from core.input_validator import SecureSubprocess
        
        assert SecureSubprocess.validate_nuclei_args(["--command", "evil"]) is False
    
    def test_validate_blocks_long_form(self):
        """Test long form flags are blocked"""
        from core.input_validator import SecureSubprocess
        
        assert SecureSubprocess.validate_nuclei_args(["--shell"]) is False
        assert SecureSubprocess.validate_nuclei_args(["--exec"]) is False


class TestGetValidator:
    """Test get_validator function"""
    
    def test_get_validator_singleton(self):
        """Test get_validator returns singleton"""
        from core.input_validator import get_validator, InputValidator
        
        validator1 = get_validator()
        validator2 = get_validator()
        
        assert isinstance(validator1, InputValidator)
        assert validator1 is validator2

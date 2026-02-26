"""
Tests for utils/security.py
Target: 95%+ Coverage
"""
import pytest


class TestMaskSecret:
    """Test mask_secret function"""
    
    def test_mask_none(self):
        """Test masking None returns [EMPTY]"""
        from utils.security import mask_secret
        assert mask_secret(None) == "[EMPTY]"
    
    def test_mask_empty_string(self):
        """Test masking empty string returns [EMPTY]"""
        from utils.security import mask_secret
        assert mask_secret("") == "[EMPTY]"
    
    def test_mask_short_value(self):
        """Test masking short value"""
        from utils.security import mask_secret
        assert mask_secret("ab") == "***"
        assert mask_secret("abc") == "a***c"
    
    def test_mask_normal_value(self):
        """Test masking normal value"""
        from utils.security import mask_secret
        result = mask_secret("sk-abc123def456", visible_chars=3)
        assert result == "sk-***456"
    
    def test_mask_custom_visible(self):
        """Test masking with custom visible chars"""
        from utils.security import mask_secret
        result = mask_secret("mysecretkey", visible_chars=2)
        assert result == "my***ey"
    
    def test_mask_exact_double_visible(self):
        """Test value with exactly double visible chars uses short path"""
        from utils.security import mask_secret
        # 6 chars = 3 + 3 = double visible -> uses short value path
        # shows first and last char only
        assert mask_secret("abcdef", visible_chars=3) == "a***f"


class TestMaskApiKey:
    """Test mask_api_key function"""
    
    def test_mask_openai_key(self):
        """Test masking OpenAI-style key"""
        from utils.security import mask_api_key
        result = mask_api_key("sk-abc123def456ghi789")
        assert result == "sk-a***i789"
    
    def test_mask_github_token(self):
        """Test masking GitHub token"""
        from utils.security import mask_api_key
        result = mask_api_key("ghp_xxxxxxxxxxxxxxx")
        assert "***" in result
    
    def test_mask_api_key_empty(self):
        """Test masking empty API key"""
        from utils.security import mask_api_key
        assert mask_api_key(None) == "[EMPTY]"


class TestMaskToken:
    """Test mask_token function"""
    
    def test_mask_jwt_token(self):
        """Test masking JWT token"""
        from utils.security import mask_token
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ"
        result = mask_token(jwt)
        assert result.startswith("eyJhb")
        assert "***" in result
    
    def test_mask_short_token(self):
        """Test masking short token"""
        from utils.security import mask_token
        result = mask_token("short")
        assert "***" in result


class TestMaskPassword:
    """Test mask_password function"""
    
    def test_mask_password_normal(self):
        """Test masking password"""
        from utils.security import mask_password
        result = mask_password("mysecretpassword")
        assert result == "m***d"
    
    def test_mask_password_short(self):
        """Test masking short password"""
        from utils.security import mask_password
        assert mask_password("ab") == "***"


class TestContainsSensitiveData:
    """Test contains_sensitive_data function"""
    
    def test_contains_openai_key(self):
        """Test detection of OpenAI key pattern"""
        from utils.security import contains_sensitive_data
        text = "My API key is sk-abcdefghijklmnopqrstuvwxyz123456"
        assert contains_sensitive_data(text) is True
    
    def test_contains_github_token(self):
        """Test detection of GitHub token"""
        from utils.security import contains_sensitive_data
        text = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert contains_sensitive_data(text) is True
    
    def test_contains_password(self):
        """Test detection of password pattern"""
        from utils.security import contains_sensitive_data
        text = 'password = "secret123"'
        assert contains_sensitive_data(text) is True
    
    def test_contains_bearer_token(self):
        """Test detection of Bearer token"""
        from utils.security import contains_sensitive_data
        text = "Authorization: Bearer xyz123abc456"
        assert contains_sensitive_data(text) is True
    
    def test_no_sensitive_data(self):
        """Test text without sensitive data"""
        from utils.security import contains_sensitive_data
        text = "Hello world, this is a normal log message"
        assert contains_sensitive_data(text) is False
    
    def test_contains_api_key(self):
        """Test detection of api_key pattern"""
        from utils.security import contains_sensitive_data
        text = "api_key='secretvalue123'"
        assert contains_sensitive_data(text) is True


class TestSafeLogMessage:
    """Test safe_log_message function"""
    
    def test_safe_log_no_sensitive(self):
        """Test message without sensitive values"""
        from utils.security import safe_log_message
        message = "Normal log message"
        assert safe_log_message(message) == message
    
    def test_safe_log_with_sensitive(self):
        """Test masking sensitive values in message"""
        from utils.security import safe_log_message
        message = "API call with key sk-abc123secret"
        result = safe_log_message(message, ["sk-abc123secret"])
        assert "sk-abc123secret" not in result
        assert "***" in result
    
    def test_safe_log_empty_sensitive(self):
        """Test with empty sensitive list"""
        from utils.security import safe_log_message
        message = "Normal message"
        assert safe_log_message(message, []) == message
    
    def test_safe_log_short_sensitive(self):
        """Test short sensitive values are ignored"""
        from utils.security import safe_log_message
        message = "Key is abc"
        result = safe_log_message(message, ["abc"])
        # Short values (< 4 chars) are not replaced
        assert "abc" in result


class TestFormatSecret:
    """Test format_secret function"""
    
    def test_format_secret_normal(self):
        """Test formatting secret"""
        from utils.security import format_secret
        result = format_secret("OPENAI_API_KEY", "sk-abc123")
        assert result == "OPENAI_API_KEY=sk-***123"
    
    def test_format_secret_empty(self):
        """Test formatting empty secret"""
        from utils.security import format_secret
        result = format_secret("SECRET", None)
        assert result == "SECRET=[EMPTY]"


class TestSanitizeLogValue:
    """Test sanitize_log_value function"""
    
    def test_sanitize_normal_value(self):
        """Test normal value passes through"""
        from utils.security import sanitize_log_value
        value = "normal_id_123"
        assert sanitize_log_value(value) == value
    
    def test_sanitize_newline(self):
        """Test newline triggers sanitization"""
        from utils.security import sanitize_log_value
        value = "evil\nfake log"
        assert sanitize_log_value(value) == "[SANITIZED]"
    
    def test_sanitize_carriage_return(self):
        """Test carriage return triggers sanitization"""
        from utils.security import sanitize_log_value
        value = "evil\rfake"
        assert sanitize_log_value(value) == "[SANITIZED]"
    
    def test_sanitize_null_byte(self):
        """Test null byte triggers sanitization"""
        from utils.security import sanitize_log_value
        value = "evil\x00null"
        assert sanitize_log_value(value) == "[SANITIZED]"
    
    def test_sanitize_fake_log_level(self):
        """Test fake log level triggers sanitization"""
        from utils.security import sanitize_log_value
        value = "[INFO] Fake log entry"
        assert sanitize_log_value(value) == "[SANITIZED]"
    
    def test_sanitize_fake_timestamp(self):
        """Test fake timestamp triggers sanitization"""
        from utils.security import sanitize_log_value
        value = "2024-01-01 12:00:00 fake entry"
        assert sanitize_log_value(value) == "[SANITIZED]"
    
    def test_sanitize_empty(self):
        """Test empty value"""
        from utils.security import sanitize_log_value
        assert sanitize_log_value(None) == "[EMPTY]"
        assert sanitize_log_value("") == "[EMPTY]"
    
    def test_sanitize_truncation(self):
        """Test long value truncation"""
        from utils.security import sanitize_log_value
        value = "a" * 200
        result = sanitize_log_value(value, max_length=50)
        assert len(result) < 200
        assert "...[truncated]" in result
    
    def test_sanitize_non_string(self):
        """Test non-string input"""
        from utils.security import sanitize_log_value
        assert sanitize_log_value(12345) == "12345"


class TestSanitizeLogId:
    """Test sanitize_log_id function"""
    
    def test_sanitize_valid_id(self):
        """Test valid ID passes through"""
        from utils.security import sanitize_log_id
        assert sanitize_log_id("agent_123") == "agent_123"
        assert sanitize_log_id("task-456.test") == "task-456.test"
    
    def test_sanitize_invalid_chars(self):
        """Test invalid characters trigger sanitization"""
        from utils.security import sanitize_log_id
        assert sanitize_log_id("evil\nfake") == "[ID-SANITIZED]"
        assert sanitize_log_id("test<script>") == "[ID-SANITIZED]"
    
    def test_sanitize_empty(self):
        """Test empty identifier"""
        from utils.security import sanitize_log_id
        assert sanitize_log_id(None) == "[EMPTY]"
        assert sanitize_log_id("") == "[EMPTY]"
    
    def test_sanitize_integer(self):
        """Test integer input"""
        from utils.security import sanitize_log_id
        assert sanitize_log_id(12345) == "12345"
    
    def test_sanitize_long_id(self):
        """Test long ID truncation"""
        from utils.security import sanitize_log_id
        long_id = "a" * 100
        result = sanitize_log_id(long_id)
        assert "...[truncated]" in result
    
    def test_sanitize_custom_chars(self):
        """Test custom allowed characters"""
        from utils.security import sanitize_log_id
        result = sanitize_log_id("test@id", allow_chars="abcdefghijklmnopqrstuvwxyz@")
        assert result == "test@id"


class TestAliases:
    """Test module aliases"""
    
    def test_log_safe_alias(self):
        """Test log_safe is alias for sanitize_log_value"""
        from utils.security import log_safe, sanitize_log_value
        assert log_safe is sanitize_log_value
    
    def test_id_safe_alias(self):
        """Test id_safe is alias for sanitize_log_id"""
        from utils.security import id_safe, sanitize_log_id
        assert id_safe is sanitize_log_id


class TestEdgeCases:
    """Test edge cases"""
    
    def test_mask_very_long_secret(self):
        """Test masking very long secret"""
        from utils.security import mask_secret
        long_secret = "x" * 1000
        result = mask_secret(long_secret)
        assert "***" in result
        assert len(result) < len(long_secret)
    
    def test_mask_exactly_six_chars(self):
        """Test 6 char value (2x visible) uses short path"""
        from utils.security import mask_secret
        result = mask_secret("abcdef", visible_chars=3)
        # Exactly 6 chars = visible_chars * 2 -> uses short value path
        assert result == "a***f"
    
    def test_mask_seven_chars(self):
        """Test 7 char value (more than 2x visible)"""
        from utils.security import mask_secret
        result = mask_secret("abcdefg", visible_chars=3)
        assert result == "abc***efg"
    
    def test_contains_sensitive_case_insensitive(self):
        """Test case insensitive detection"""
        from utils.security import contains_sensitive_data
        assert contains_sensitive_data("PASSWORD = 'secret'") is True
        assert contains_sensitive_data("Bearer token123") is True

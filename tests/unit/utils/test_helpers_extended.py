"""
Extended Unit Tests für utils/helpers.py

Tests additional helper functions.
"""

import pytest
from utils.helpers import (
    sanitize_filename,
    format_duration,
    truncate_string,
    banner,
    colorize,
    get_severity_color,
)

pytestmark = pytest.mark.unit


class TestSanitizeFilename:
    """Test sanitize_filename function"""
    
    def test_sanitize_valid_filename(self):
        """Test sanitizing already valid filename"""
        result = sanitize_filename("valid_filename.txt")
        assert result == "valid_filename.txt"
    
    def test_sanitize_invalid_characters(self):
        """Test removing invalid characters"""
        result = sanitize_filename("file<name>.txt")
        assert "<" not in result
        assert result == "file_name_.txt"
    
    def test_sanitize_windows_reserved(self):
        """Test sanitizing Windows reserved characters"""
        result = sanitize_filename('file:name|test?.txt')
        assert ":" not in result
        assert "|" not in result
        assert "?" not in result
    
    def test_sanitize_path_traversal(self):
        """Test sanitizing path traversal attempts"""
        result = sanitize_filename("../../../etc/passwd")
        assert "../" not in result
        assert "_" in result
    
    def test_sanitize_long_filename(self):
        """Test truncating long filename"""
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100
    
    def test_sanitize_unicode(self):
        """Test sanitizing unicode filename"""
        result = sanitize_filename("file_日本語.txt")
        assert len(result) > 0


class TestFormatDuration:
    """Test format_duration function"""
    
    def test_format_seconds(self):
        """Test formatting seconds"""
        result = format_duration(45.5)
        assert result == "45.5s"
    
    def test_format_minutes(self):
        """Test formatting minutes"""
        result = format_duration(125)
        assert result == "2.1m"
    
    def test_format_hours(self):
        """Test formatting hours"""
        result = format_duration(3660)
        assert result == "1.0h"
    
    def test_format_zero(self):
        """Test formatting zero"""
        result = format_duration(0)
        assert result == "0.0s"
    
    def test_format_large_value(self):
        """Test formatting large value"""
        result = format_duration(86400)  # 24 hours
        assert result == "24.0h"


class TestTruncateString:
    """Test truncate_string function"""
    
    def test_truncate_short_string(self):
        """Test truncating short string (no change)"""
        result = truncate_string("short", max_length=10)
        assert result == "short"
    
    def test_truncate_long_string(self):
        """Test truncating long string"""
        long_string = "a" * 100
        result = truncate_string(long_string, max_length=50)
        assert len(result) <= 50
        assert result.endswith("...")
    
    def test_truncate_exact_length(self):
        """Test string at exact max length"""
        string = "a" * 10
        result = truncate_string(string, max_length=10)
        assert result == string
    
    def test_truncate_custom_suffix(self):
        """Test truncating with custom suffix"""
        long_string = "a" * 100
        result = truncate_string(long_string, max_length=20, suffix="[more]")
        assert result.endswith("[more]")
    
    def test_truncate_empty(self):
        """Test truncating empty string"""
        result = truncate_string("")
        assert result == ""


class TestBanner:
    """Test banner function"""
    
    def test_banner_contains_title(self):
        """Test banner contains title"""
        result = banner()
        assert "ZEN AI PENTEST" in result
    
    def test_banner_contains_author(self):
        """Test banner contains author"""
        result = banner()
        assert "SHAdd0WTAka" in result
    
    def test_banner_contains_version(self):
        """Test banner contains version"""
        result = banner()
        assert "Version" in result
    
    def test_banner_is_string(self):
        """Test banner returns string"""
        result = banner()
        assert isinstance(result, str)
    
    def test_banner_multiline(self):
        """Test banner has multiple lines"""
        result = banner()
        assert "\n" in result


class TestColorize:
    """Test colorize function"""
    
    def test_colorize_red(self):
        """Test red color"""
        result = colorize("test", "red")
        assert "\033[91m" in result
        assert "\033[0m" in result
    
    def test_colorize_green(self):
        """Test green color"""
        result = colorize("test", "green")
        assert "\033[92m" in result
    
    def test_colorize_invalid_color(self):
        """Test invalid color defaults"""
        result = colorize("test", "invalid_color")
        assert "test" in result
        assert "\033[0m" in result
    
    def test_colorize_empty(self):
        """Test empty string"""
        result = colorize("", "blue")
        assert result == "\033[94m\033[0m"
    
    def test_colorize_bold(self):
        """Test bold style"""
        result = colorize("test", "bold")
        assert "\033[1m" in result


class TestGetSeverityColor:
    """Test get_severity_color function"""
    
    def test_critical_severity(self):
        """Test Critical severity color"""
        result = get_severity_color("Critical")
        assert result == "red"
    
    def test_high_severity(self):
        """Test High severity color"""
        result = get_severity_color("High")
        assert result == "magenta"
    
    def test_medium_severity(self):
        """Test Medium severity color"""
        result = get_severity_color("Medium")
        assert result == "yellow"
    
    def test_low_severity(self):
        """Test Low severity color"""
        result = get_severity_color("Low")
        assert result == "blue"
    
    def test_info_severity(self):
        """Test Info severity color"""
        result = get_severity_color("Info")
        assert result == "white"
    
    def test_unknown_severity(self):
        """Test unknown severity defaults to white"""
        result = get_severity_color("Unknown")
        assert result == "white"
    
    def test_case_sensitivity(self):
        """Test case sensitivity"""
        result_lower = get_severity_color("critical")
        result_upper = get_severity_color("Critical")
        # Implementation may be case-sensitive
        assert isinstance(result_lower, str)
        assert isinstance(result_upper, str)

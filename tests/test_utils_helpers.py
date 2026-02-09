"""Tests for utils helpers"""

from utils.helpers import banner, colorize, get_severity_color


class TestHelpers:
    """Test helper functions"""

    def test_banner_output(self):
        """Test banner generation"""
        result = banner()
        assert isinstance(result, str)
        assert "Zen" in result or "ZEN" in result

    def test_colorize_red(self):
        """Test red colorize"""
        result = colorize("test", "red")
        assert "\033[91m" in result
        assert "\033[0m" in result

    def test_colorize_green(self):
        """Test green colorize"""
        result = colorize("test", "green")
        assert "\033[92m" in result
        assert "\033[0m" in result

    def test_colorize_yellow(self):
        """Test yellow colorize"""
        result = colorize("test", "yellow")
        assert "\033[93m" in result
        assert "\033[0m" in result

    def test_get_severity_color_critical(self):
        """Test severity color - critical"""
        result = get_severity_color("critical")
        assert result == "red"

    def test_get_severity_color_high(self):
        """Test severity color - high"""
        result = get_severity_color("high")
        assert result == "red"

    def test_get_severity_color_medium(self):
        """Test severity color - medium"""
        result = get_severity_color("medium")
        assert result == "yellow"

    def test_get_severity_color_low(self):
        """Test severity color - low"""
        result = get_severity_color("low")
        assert result == "green"

    def test_get_severity_color_info(self):
        """Test severity color - info"""
        result = get_severity_color("info")
        assert result == "blue"

    def test_get_severity_color_unknown(self):
        """Test severity color - unknown"""
        result = get_severity_color("unknown")
        assert result == "white"

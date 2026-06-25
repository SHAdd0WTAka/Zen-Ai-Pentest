"""
Tests for utils/stealth.py
Target: 100% Coverage
"""

import time
from unittest.mock import patch

import pytest


class TestStealthManagerInit:
    """Test StealthManager initialization"""

    def test_init_with_defaults(self):
        """Test StealthManager with default config"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        assert sm.config == {}
        assert sm.delay_min == 1
        assert sm.delay_max == 3
        assert sm.use_random_ua is True

    def test_init_with_custom_config(self):
        """Test StealthManager with custom config"""
        from utils.stealth import StealthManager

        config = {"delay_min": 2, "delay_max": 5, "random_user_agent": False}
        sm = StealthManager(config)
        assert sm.config == config
        assert sm.delay_min == 2
        assert sm.delay_max == 5
        assert sm.use_random_ua is False

    def test_init_with_empty_config(self):
        """Test StealthManager with empty config dict"""
        from utils.stealth import StealthManager

        sm = StealthManager({})
        assert sm.config == {}
        assert sm.delay_min == 1
        assert sm.delay_max == 3


class TestGetHeaders:
    """Test HTTP header generation"""

    def test_get_headers_returns_dict(self):
        """Test get_headers returns a dictionary"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        headers = sm.get_headers()
        assert isinstance(headers, dict)
        assert len(headers) > 0

    def test_get_headers_has_required_fields(self):
        """Test get_headers includes required fields"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        headers = sm.get_headers()

        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers
        assert "User-Agent" in headers
        assert "Referer" in headers
        assert "DNT" in headers

    def test_get_headers_without_random_ua(self):
        """Test get_headers without random user agent"""
        from utils.stealth import StealthManager

        sm = StealthManager({"random_user_agent": False})
        headers = sm.get_headers()

        # Should still have Referer but no User-Agent
        assert "Referer" in headers
        assert "User-Agent" not in headers

    def test_get_headers_with_custom_headers(self):
        """Test get_headers with custom headers"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        custom = {"X-Custom": "value", "Accept": "application/json"}
        headers = sm.get_headers(custom)

        assert headers["X-Custom"] == "value"
        assert headers["Accept"] == "application/json"


class TestGetRandomUserAgent:
    """Test user agent selection"""

    def test_get_random_user_agent_returns_string(self):
        """Test get_random_user_agent returns a string"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        ua = sm.get_random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 0

    def test_get_random_user_agent_from_list(self):
        """Test get_random_user_agent returns from known list"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        ua = sm.get_random_user_agent()
        assert ua in sm.USER_AGENTS

    def test_multiple_calls_different_ua(self):
        """Test multiple calls can return different user agents"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        uas = [sm.get_random_user_agent() for _ in range(10)]

        # At least 2 different UAs should appear (statistically likely)
        assert len(set(uas)) > 1


class TestDelay:
    """Test delay functions"""

    @patch("time.sleep")
    def test_delay_with_defaults(self, mock_sleep):
        """Test delay with default values"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        sm.delay()

        mock_sleep.assert_called_once()
        # Check delay is between 1 and 3
        call_arg = mock_sleep.call_args[0][0]
        assert 1 <= call_arg <= 3

    @patch("time.sleep")
    def test_delay_with_custom_values(self, mock_sleep):
        """Test delay with custom values"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        sm.delay(5, 10)

        call_arg = mock_sleep.call_args[0][0]
        assert 5 <= call_arg <= 10

    @patch("time.sleep")
    def test_delay_with_config_defaults(self, mock_sleep):
        """Test delay uses config defaults"""
        from utils.stealth import StealthManager

        sm = StealthManager({"delay_min": 0.5, "delay_max": 1.5})
        sm.delay()

        call_arg = mock_sleep.call_args[0][0]
        assert 0.5 <= call_arg <= 1.5

    @patch("time.sleep")
    def test_jitter_delay(self, mock_sleep):
        """Test jittered delay"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        sm.jitter_delay(2.0, 0.5)

        mock_sleep.assert_called_once()
        call_arg = mock_sleep.call_args[0][0]
        assert 1.5 <= call_arg <= 2.5

    @patch("time.sleep")
    def test_jitter_delay_negative_result(self, mock_sleep):
        """Test jittered delay doesn't sleep if result is negative"""
        from utils.stealth import StealthManager

        sm = StealthManager()

        # Mock random.uniform to return a value that makes delay negative
        with patch("random.uniform", return_value=-5.0):
            sm.jitter_delay(1.0, 2.0)

        # Should not sleep when delay is negative
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        sm.exponential_backoff(0, 1.0)

        mock_sleep.assert_called_once()
        call_arg = mock_sleep.call_args[0][0]
        assert 1.0 <= call_arg <= 2.0  # 1 * 2^0 + 0-1

    @patch("time.sleep")
    def test_exponential_backoff_attempt_2(self, mock_sleep):
        """Test exponential backoff with attempt=2"""
        from utils.stealth import StealthManager

        sm = StealthManager()
        sm.exponential_backoff(2, 1.0)

        call_arg = mock_sleep.call_args[0][0]
        assert 4.0 <= call_arg <= 5.0  # 1 * 2^2 + 0-1


class TestUserAgentsList:
    """Test User Agents constants"""

    def test_user_agents_list_exists(self):
        """Test USER_AGENTS list is defined"""
        from utils.stealth import StealthManager

        assert len(StealthManager.USER_AGENTS) == 5
        for ua in StealthManager.USER_AGENTS:
            assert "Mozilla" in ua

    def test_referers_list_exists(self):
        """Test REFERERS list is defined"""
        from utils.stealth import StealthManager

        assert len(StealthManager.REFERERS) == 5
        for ref in StealthManager.REFERERS:
            assert ref.startswith("https://")


class TestIntegration:
    """Integration tests"""

    def test_full_stealth_workflow(self):
        """Test complete stealth workflow"""
        from utils.stealth import StealthManager

        sm = StealthManager(
            {"delay_min": 0.1, "delay_max": 0.2, "random_user_agent": True}
        )

        # Get headers
        headers = sm.get_headers({"X-Test": "integration"})
        assert "User-Agent" in headers
        assert headers["X-Test"] == "integration"

        # Get random UA
        ua = sm.get_random_user_agent()
        assert ua in sm.USER_AGENTS

        # Test jitter delay doesn't crash
        with patch("time.sleep"):
            sm.jitter_delay(0.1, 0.05)

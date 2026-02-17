"""
Unit Tests für utils/stealth.py

Tests StealthManager without actual network calls.
"""

import pytest
from unittest.mock import patch
from utils.stealth import StealthManager

pytestmark = pytest.mark.unit


class TestStealthManagerInit:
    """Test StealthManager initialization"""

    def test_default_init(self):
        """Test default initialization"""
        sm = StealthManager()
        assert sm.delay_min == 1
        assert sm.delay_max == 3
        assert sm.use_random_ua is True

    def test_custom_config(self):
        """Test initialization with custom config"""
        config = {
            "delay_min": 2,
            "delay_max": 5,
            "random_user_agent": False
        }
        sm = StealthManager(config)
        assert sm.delay_min == 2
        assert sm.delay_max == 5
        assert sm.use_random_ua is False

    def test_partial_config(self):
        """Test initialization with partial config"""
        config = {"delay_min": 0.5}
        sm = StealthManager(config)
        assert sm.delay_min == 0.5
        assert sm.delay_max == 3  # default
        assert sm.use_random_ua is True  # default

    def test_empty_config(self):
        """Test initialization with empty config"""
        sm = StealthManager({})
        assert sm.delay_min == 1
        assert sm.delay_max == 3


class TestGetHeaders:
    """Test get_headers method"""

    def test_default_headers(self):
        """Test getting default headers"""
        sm = StealthManager()
        headers = sm.get_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Referer" in headers
        assert "Accept-Language" in headers

    def test_custom_headers(self):
        """Test merging custom headers"""
        sm = StealthManager()
        custom = {"X-Custom": "value", "Accept": "application/json"}
        headers = sm.get_headers(custom)

        assert headers["X-Custom"] == "value"
        assert headers["Accept"] == "application/json"

    def test_random_user_agent_disabled(self):
        """Test headers without random UA"""
        sm = StealthManager({"random_user_agent": False})
        headers = sm.get_headers()

        assert "User-Agent" not in headers

    def test_user_agent_from_list(self):
        """Test that UA comes from predefined list"""
        sm = StealthManager()
        headers = sm.get_headers()

        assert headers["User-Agent"] in sm.USER_AGENTS

    def test_referer_from_list(self):
        """Test that referer comes from predefined list"""
        sm = StealthManager()
        headers = sm.get_headers()

        assert headers["Referer"] in sm.REFERERS


class TestGetRandomUserAgent:
    """Test get_random_user_agent method"""

    def test_returns_string(self):
        """Test returns string"""
        sm = StealthManager()
        ua = sm.get_random_user_agent()
        assert isinstance(ua, str)

    def test_returns_from_list(self):
        """Test returns UA from predefined list"""
        sm = StealthManager()
        ua = sm.get_random_user_agent()
        assert ua in sm.USER_AGENTS

    def test_different_calls(self):
        """Test multiple calls return valid UAs"""
        sm = StealthManager()
        for _ in range(10):
            ua = sm.get_random_user_agent()
            assert ua in sm.USER_AGENTS


class TestDelay:
    """Test delay methods"""

    @patch('time.sleep')
    def test_default_delay(self, mock_sleep):
        """Test default delay behavior"""
        sm = StealthManager()
        sm.delay()

        mock_sleep.assert_called_once()
        # Check delay is within range
        call_args = mock_sleep.call_args[0][0]
        assert 1 <= call_args <= 3

    @patch('time.sleep')
    def test_custom_delay(self, mock_sleep):
        """Test custom delay parameters"""
        sm = StealthManager()
        sm.delay(min_seconds=5, max_seconds=10)

        call_args = mock_sleep.call_args[0][0]
        assert 5 <= call_args <= 10

    @patch('time.sleep')
    def test_config_delay(self, mock_sleep):
        """Test delay from config"""
        sm = StealthManager({"delay_min": 0.1, "delay_max": 0.5})
        sm.delay()

        call_args = mock_sleep.call_args[0][0]
        assert 0.1 <= call_args <= 0.5


class TestJitterDelay:
    """Test jitter_delay method"""

    @patch('time.sleep')
    def test_jitter_positive(self, mock_sleep):
        """Test jitter delay with positive result"""
        sm = StealthManager()

        # Patch random to return predictable value
        with patch('random.uniform', return_value=0.3):
            sm.jitter_delay(base_delay=1.0, jitter=0.5)

        mock_sleep.assert_called_once_with(1.3)

    @patch('time.sleep')
    def test_jitter_negative(self, mock_sleep):
        """Test jitter delay clamps to positive"""
        sm = StealthManager()

        with patch('random.uniform', return_value=-2.0):
            sm.jitter_delay(base_delay=1.0, jitter=0.5)

        # Should not sleep if delay <= 0
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_jitter_range(self, mock_sleep):
        """Test jitter stays within expected range"""
        sm = StealthManager()

        with patch('random.uniform', return_value=0.0):
            sm.jitter_delay(base_delay=2.0, jitter=0.5)

        mock_sleep.assert_called_once_with(2.0)


class TestExponentialBackoff:
    """Test exponential_backoff method"""

    @patch('time.sleep')
    def test_backoff_attempt_0(self, mock_sleep):
        """Test backoff for attempt 0"""
        sm = StealthManager()

        with patch('random.uniform', return_value=0.5):
            sm.exponential_backoff(attempt=0, base_delay=1.0)

        call_args = mock_sleep.call_args[0][0]
        assert call_args == 1.5  # 1 * 2^0 + 0.5

    @patch('time.sleep')
    def test_backoff_attempt_1(self, mock_sleep):
        """Test backoff for attempt 1"""
        sm = StealthManager()

        with patch('random.uniform', return_value=0.0):
            sm.exponential_backoff(attempt=1, base_delay=1.0)

        call_args = mock_sleep.call_args[0][0]
        assert call_args == 2.0  # 1 * 2^1 + 0

    @patch('time.sleep')
    def test_backoff_attempt_3(self, mock_sleep):
        """Test backoff for attempt 3"""
        sm = StealthManager()

        with patch('random.uniform', return_value=0.0):
            sm.exponential_backoff(attempt=3, base_delay=1.0)

        call_args = mock_sleep.call_args[0][0]
        assert call_args == 8.0  # 1 * 2^3 + 0

    @patch('time.sleep')
    def test_backoff_increases(self, mock_sleep):
        """Test that backoff increases with attempt"""
        sm = StealthManager()
        delays = []

        for attempt in range(5):
            with patch('random.uniform', return_value=0.0):
                sm.exponential_backoff(attempt=attempt, base_delay=1.0)

            call_args = mock_sleep.call_args[0][0]
            delays.append(call_args)
            mock_sleep.reset_mock()

        # Each delay should be >= previous
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i-1]


class TestPredefinedLists:
    """Test predefined lists are valid"""

    def test_user_agents_not_empty(self):
        """Test USER_AGENTS list is populated"""
        sm = StealthManager()
        assert len(sm.USER_AGENTS) > 0
        assert all(isinstance(ua, str) for ua in sm.USER_AGENTS)

    def test_referers_not_empty(self):
        """Test REFERERS list is populated"""
        sm = StealthManager()
        assert len(sm.REFERERS) > 0
        assert all(isinstance(ref, str) for ref in sm.REFERERS)

    def test_user_agents_contain_mozilla(self):
        """Test UAs contain Mozilla prefix"""
        sm = StealthManager()
        for ua in sm.USER_AGENTS:
            assert "Mozilla" in ua

    def test_referers_are_urls(self):
        """Test referers look like URLs"""
        sm = StealthManager()
        for ref in sm.REFERERS:
            assert ref.startswith("https://")

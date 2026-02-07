"""
Pytest configuration and shared fixtures
"""

import sys
from unittest.mock import MagicMock, Mock

# Mock external dependencies BEFORE any imports
# DNS module
_dns_mock = MagicMock()
_dns_mock.resolver = MagicMock()
_dns_mock.query = MagicMock()
_dns_mock.zone = MagicMock()
if 'dns' not in sys.modules:
    sys.modules['dns'] = _dns_mock
    sys.modules['dns.resolver'] = _dns_mock.resolver
    sys.modules['dns.query'] = _dns_mock.query
    sys.modules['dns.zone'] = _dns_mock.zone

# aiohttp mock
_aiohttp_mock = MagicMock()
_aiohttp_mock.ClientSession = MagicMock
_aiohttp_mock.ClientTimeout = MagicMock
if 'aiohttp' not in sys.modules:
    sys.modules['aiohttp'] = _aiohttp_mock

# requests mock
_requests_mock = MagicMock()
if 'requests' not in sys.modules:
    sys.modules['requests'] = _requests_mock

import pytest


@pytest.fixture
def mock_openai_client():
    client = Mock()
    client.chat.completions.create.return_value = Mock(choices=[Mock(message=Mock(content="Test response"))])
    return client


@pytest.fixture
def sample_cve_data():
    return {"id": "CVE-2023-1234", "severity": "HIGH", "cvss_score": 8.5, "description": "Test vulnerability"}

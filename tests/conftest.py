"""
Pytest configuration and shared fixtures
"""
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_openai_client():
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content='Test response'))]
    )
    return client

@pytest.fixture
def sample_cve_data():
    return {
        'id': 'CVE-2023-1234',
        'severity': 'HIGH',
        'cvss_score': 8.5,
        'description': 'Test vulnerability'
    }

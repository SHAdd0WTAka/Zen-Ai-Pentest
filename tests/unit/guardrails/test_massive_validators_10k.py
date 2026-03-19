import pytest

from guardrails.domain_validator import DomainValidator
from guardrails.ip_validator import IPValidator

PUBLIC_IP_CASES = [f"8.8.{i // 256}.{i % 256}" for i in range(5000)]
PRIVATE_IP_CASES = [f"10.{(i // 256) % 256}.{i % 256}.1" for i in range(5000)]

URL_CASES = [
    ("https://example.com", True),
    ("http://localhost", False),
    ("https://test.internal", False),
    ("file:///etc/passwd", False),
    ("scanme.nmap.org", True),
    ("192.168.1.1", False),
    ("https://sub.example.com:443/path", True),
    ("http://localhost.localdomain", False),
]


@pytest.mark.parametrize("ip", PUBLIC_IP_CASES)
def test_5000_public_ips_are_allowed(ip):
    validator = IPValidator()
    result = validator.validate_ip(ip)
    assert result.is_valid is True


@pytest.mark.parametrize("ip", PRIVATE_IP_CASES)
def test_5000_private_ips_are_blocked(ip):
    validator = IPValidator()
    result = validator.validate_ip(ip)
    assert result.is_valid is False
    assert result.blocked_ranges


@pytest.mark.parametrize("url,expected", URL_CASES)
def test_domain_validator_url_edge_matrix(url, expected):
    validator = DomainValidator()
    result = validator.validate_url(url)
    assert result.is_valid is expected


def test_domain_and_ip_exception_paths():
    d = DomainValidator()
    i = IPValidator()

    d.add_exception("localhost")
    i.add_exception("127.0.0.1")

    assert d.validate_domain("localhost").is_valid is True
    assert i.validate_ip("127.0.0.1").is_valid is True

    d.remove_exception("localhost")
    i.remove_exception("127.0.0.1")

    assert d.validate_domain("localhost").is_valid is False
    assert i.validate_ip("127.0.0.1").is_valid is False

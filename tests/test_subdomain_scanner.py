#!/usr/bin/env python3
"""
Tests for Subdomain Scanner Module
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from modules.subdomain_scanner import SubdomainScanner, SubdomainResult, scan_subdomains


class TestSubdomainResult:
    """Test SubdomainResult dataclass"""

    def test_basic_creation(self):
        result = SubdomainResult(subdomain="test.example.com")
        assert result.subdomain == "test.example.com"
        assert result.ip_addresses == []
        assert result.status_code is None
        assert result.is_alive is False

    def test_with_data(self):
        result = SubdomainResult(
            subdomain="test.example.com",
            ip_addresses=["192.168.1.1"],
            status_code=200,
            server_header="nginx",
            technologies=["nginx", "PHP"],
            is_alive=True
        )
        assert result.subdomain == "test.example.com"
        assert result.ip_addresses == ["192.168.1.1"]
        assert result.status_code == 200
        assert result.server_header == "nginx"
        assert result.technologies == ["nginx", "PHP"]
        assert result.is_alive is True


class TestSubdomainScanner:
    """Test SubdomainScanner class"""

    @pytest.fixture
    def scanner(self):
        return SubdomainScanner(max_workers=10, timeout=5)

    def test_init(self, scanner):
        assert scanner.max_workers == 10
        assert scanner.timeout == 5
        assert scanner.results == {}
        assert len(scanner.wordlist) > 0

    def test_filter_wildcards(self, scanner):
        test_subdomains = {
            "www.example.com",
            "admin.example.com",
            "test12345.example.com"
        }

        with patch('socket.gethostbyname') as mock_gethost:
            mock_gethost.side_effect = ["192.168.1.1", "192.168.1.2", "192.168.1.1"]
            result = scanner._filter_wildcards(test_subdomains, "example.com")
            assert "www.example.com" in result
            assert "admin.example.com" in result

    def test_detect_technologies(self, scanner):
        headers = {
            "Server": "nginx/1.18.0",
            "X-Powered-By": "PHP/7.4.0"
        }
        body = "<html><head></head><body>WordPress</body></html>"
        techs = scanner._detect_technologies(headers, body)

        assert "nginx" in techs
        assert "PHP" in techs
        assert "WordPress" in techs

    def test_export_results_json(self, scanner):
        scanner.results = {
            "test.example.com": SubdomainResult(
                subdomain="test.example.com",
                status_code=200,
                is_alive=True
            )
        }
        output = scanner.export_results("json")
        assert "test.example.com" in output
        assert '"is_alive": true' in output

    def test_export_results_txt(self, scanner):
        scanner.results = {
            "test.example.com": SubdomainResult(
                subdomain="test.example.com",
                status_code=200,
                is_alive=True
            )
        }
        output = scanner.export_results("txt")
        assert "test.example.com" in output

    def test_export_results_csv(self, scanner):
        scanner.results = {
            "test.example.com": SubdomainResult(
                subdomain="test.example.com",
                status_code=200,
                is_alive=True
            )
        }
        output = scanner.export_results("csv")
        assert "test.example.com" in output
        assert "subdomain,ip_addresses" in output

    def test_export_results_invalid_format(self, scanner):
        with pytest.raises(ValueError, match="Unsupported format"):
            scanner.export_results("xml")


class TestScanSubdomains:
    """Test scan_subdomains convenience function"""

    def test_scan_subdomains_basic(self):
        """Test the scan function exists and is callable"""
        # Just verify the function exists and has correct signature
        import inspect
        sig = inspect.signature(scan_subdomains)
        params = list(sig.parameters.keys())
        assert 'domain' in params
        assert 'check_http' in params
        assert 'max_workers' in params

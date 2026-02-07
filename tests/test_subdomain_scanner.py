#!/usr/bin/env python3
"""
Tests for Subdomain Scanner Module
"""

import pytest
import asyncio
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

    @pytest.mark.asyncio
    async def test_filter_wildcards(self, scanner):
        # Mock socket.gethostbyname to simulate wildcard behavior
        test_subdomains = {
            "www.example.com",
            "admin.example.com",
            "test12345.example.com"  # This looks like a wildcard
        }

        with patch('socket.gethostbyname') as mock_gethost:
            # First call returns real IP, subsequent calls return same IP (wildcard)
            mock_gethost.side_effect = ["192.168.1.1", "192.168.1.2", "192.168.1.1"]
            result = scanner._filter_wildcards(test_subdomains, "example.com")
            # test12345 should be filtered as wildcard
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

    @pytest.mark.asyncio
    async def test_scan_subdomains_basic(self):
        with patch.object(SubdomainScanner, 'scan', new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = {
                "www.example.com": SubdomainResult(subdomain="www.example.com")
            }
            results = await scan_subdomains("example.com", check_http=False)
            assert len(results) == 1
            mock_scan.assert_called_once()


class TestIntegration:
    """Integration tests (may require network)"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires network access")
    async def test_real_dns_lookup(self):
        """Test with real DNS lookup - skipped by default"""
        scanner = SubdomainScanner(max_workers=5, timeout=5)
        results = await scanner.scan(
            domain="example.com",
            techniques=["dns"],
            check_http=False
        )
        assert isinstance(results, dict)

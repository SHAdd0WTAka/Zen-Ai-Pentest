"""Tests for recon module"""

from unittest.mock import patch

import pytest  # noqa: F401

from modules.recon import ReconModule


class TestReconModule:
    """Test ReconModule functionality"""

    def test_init(self):
        """Test module initialization"""
        module = ReconModule()
        assert module.name == "recon"
        assert module.enabled is True

    def test_validate_target_valid(self):
        """Test valid target validation"""
        module = ReconModule()
        assert module.validate_target("192.168.1.1") is True
        assert module.validate_target("example.com") is True

    def test_validate_target_invalid(self):
        """Test invalid target validation"""
        module = ReconModule()
        assert module.validate_target("") is False
        assert module.validate_target(None) is False

    @patch("modules.recon.socket.gethostbyname")
    def test_resolve_dns_success(self, mock_gethost):
        """Test DNS resolution success"""
        mock_gethost.return_value = "93.184.216.34"
        module = ReconModule()
        result = module.resolve_dns("example.com")
        assert result == "93.184.216.34"

    @patch("modules.recon.socket.gethostbyname")
    def test_resolve_dns_failure(self, mock_gethost):
        """Test DNS resolution failure"""
        mock_gethost.side_effect = Exception("DNS Error")
        module = ReconModule()
        result = module.resolve_dns("invalid.invalid")
        assert result is None

    def test_run_basic_scan(self):
        """Test basic scan execution"""
        module = ReconModule()
        with patch.object(module, "scan_host") as mock_scan:
            mock_scan.return_value = {"open_ports": [80, 443]}
            result = module.run("192.168.1.1")
            assert "open_ports" in result

    def test_get_info(self):
        """Test module info"""
        module = ReconModule()
        info = module.get_info()
        assert "name" in info
        assert "version" in info
        assert "description" in info

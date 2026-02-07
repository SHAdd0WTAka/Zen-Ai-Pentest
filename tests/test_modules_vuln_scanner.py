"""Tests for vulnerability scanner module"""

import pytest  # noqa: F401
from unittest.mock import patch
from modules.vuln_scanner import VulnScannerModule


class TestVulnScannerModule:
    """Test VulnScannerModule functionality"""

    def test_init(self):
        """Test module initialization"""
        module = VulnScannerModule()
        assert module.name == "vuln_scanner"
        assert module.enabled is True

    def test_scan_port_open(self):
        """Test port scanning - open port"""
        module = VulnScannerModule()
        with patch("socket.socket") as mock_sock:
            mock_sock.return_value.connect_ex.return_value = 0
            result = module.scan_port("192.168.1.1", 80)
            assert result is True

    def test_scan_port_closed(self):
        """Test port scanning - closed port"""
        module = VulnScannerModule()
        with patch("socket.socket") as mock_sock:
            mock_sock.return_value.connect_ex.return_value = 1
            result = module.scan_port("192.168.1.1", 9999)
            assert result is False

    def test_scan_service_detection(self):
        """Test service detection"""
        module = VulnScannerModule()
        with patch.object(module, "detect_service") as mock_detect:
            mock_detect.return_value = {"name": "http", "version": "2.4.41"}
            result = module.detect_service("192.168.1.1", 80)
            assert result["name"] == "http"

    def test_cve_lookup(self):
        """Test CVE lookup"""
        module = VulnScannerModule()
        with patch.object(module, "lookup_cve") as mock_cve:
            mock_cve.return_value = [{"id": "CVE-2021-1234", "severity": "high"}]
            result = module.lookup_cve("apache", "2.4.41")
            assert len(result) > 0

    def test_get_info(self):
        """Test module info"""
        module = VulnScannerModule()
        info = module.get_info()
        assert "name" in info
        assert "description" in info

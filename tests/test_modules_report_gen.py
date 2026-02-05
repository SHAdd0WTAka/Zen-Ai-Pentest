"""Tests for report generator module"""
import pytest
from unittest.mock import Mock, patch, mock_open
from modules.report_gen import ReportGenerator


class TestReportGenerator:
    """Test ReportGenerator functionality"""

    def test_init(self):
        """Test report generator initialization"""
        gen = ReportGenerator()
        assert gen is not None
        assert gen.name == "report_gen"

    def test_generate_json_report(self):
        """Test JSON report generation"""
        gen = ReportGenerator()
        findings = [
            {"title": "Test", "severity": "high", "description": "Test finding"}
        ]
        with patch('builtins.open', mock_open()) as mock_file:
            result = gen.generate_json(findings, "test.json")
            mock_file.assert_called_once()

    def test_generate_markdown_report(self):
        """Test Markdown report generation"""
        gen = ReportGenerator()
        findings = [
            {"title": "Test", "severity": "high", "description": "Test finding"}
        ]
        with patch('builtins.open', mock_open()) as mock_file:
            result = gen.generate_markdown(findings, "test.md")
            mock_file.assert_called_once()

    def test_format_findings(self):
        """Test findings formatting"""
        gen = ReportGenerator()
        findings = [
            {"title": "Test", "severity": "high", "cvss": 8.5},
            {"title": "Test2", "severity": "low", "cvss": 2.0}
        ]
        result = gen.format_findings(findings)
        assert len(result) == 2

    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        gen = ReportGenerator()
        findings = [
            {"severity": "critical", "cvss": 9.5},
            {"severity": "high", "cvss": 7.5}
        ]
        score = gen.calculate_risk_score(findings)
        assert score > 0

    def test_get_info(self):
        """Test module info"""
        gen = ReportGenerator()
        info = gen.get_info()
        assert "name" in info

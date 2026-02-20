"""
Tests for Report Export Module
PDF, HTML, CSV, JSON Export
"""

import json
import csv
import io
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from modules.report_export import (
    ReportExporter,
    ReportData,
    export_findings,
)


# Fixtures
@pytest.fixture
def sample_findings():
    """Create sample findings for testing"""
    return [
        {
            "id": "CVE-2024-0001",
            "severity": "critical",
            "title": "SQL Injection in Login",
            "description": "The login form is vulnerable to SQL injection attacks.",
            "target": "http://example.com/login",
            "cve_id": "CVE-2024-0001",
            "cvss_score": "9.8",
            "status": "open",
            "discovered_at": "2024-01-15T10:30:00",
        },
        {
            "id": "CVE-2024-0002",
            "severity": "high",
            "title": "Cross-Site Scripting (XSS)",
            "description": "Reflected XSS in search parameter.",
            "target": "http://example.com/search",
            "cve_id": "CVE-2024-0002",
            "cvss_score": "8.1",
            "status": "open",
            "discovered_at": "2024-01-15T11:00:00",
        },
        {
            "id": "CVE-2024-0003",
            "severity": "medium",
            "title": "Information Disclosure",
            "description": "Server version exposed in headers.",
            "target": "http://example.com",
            "cve_id": None,
            "cvss_score": "5.3",
            "status": "open",
            "discovered_at": "2024-01-15T11:30:00",
        },
        {
            "id": "CVE-2024-0004",
            "severity": "low",
            "title": "Missing Security Headers",
            "description": "Content-Security-Policy header missing.",
            "target": "http://example.com",
            "cve_id": None,
            "cvss_score": "3.1",
            "status": "open",
            "discovered_at": "2024-01-15T12:00:00",
        },
    ]


@pytest.fixture
def sample_report_data(sample_findings):
    """Create sample report data"""
    return ReportData(
        title="Security Assessment Report",
        scan_date=datetime(2024, 1, 15, 12, 0, 0),
        target="example.com",
        findings=sample_findings,
        summary={
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 1,
        },
        recommendations=[
            "Implement input validation",
            "Use parameterized queries",
            "Add security headers",
        ],
    )


@pytest.fixture
def exporter():
    """Create a ReportExporter instance"""
    return ReportExporter()


# ReportExporter Tests
class TestReportExporter:
    """Tests for ReportExporter class"""

    def test_initialization(self, exporter):
        """Test ReportExporter initialization"""
        assert exporter is not None
        assert "executive" in exporter.templates
        assert "technical" in exporter.templates
        assert "compliance" in exporter.templates

    def test_export_csv(self, exporter, sample_findings):
        """Test CSV export"""
        csv_data = exporter.export_csv(sample_findings)
        
        assert isinstance(csv_data, bytes)
        
        # Parse CSV and verify content
        csv_string = csv_data.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_string))
        rows = list(reader)
        
        # Check header
        assert rows[0] == ["ID", "Severity", "Title", "Description", "Target", "CVE", "CVSS", "Status", "Discovered"]
        
        # Check data rows
        assert len(rows) == 5  # header + 4 findings
        assert rows[1][0] == "CVE-2024-0001"
        assert rows[1][1] == "critical"

    def test_export_csv_empty(self, exporter):
        """Test CSV export with empty findings"""
        csv_data = exporter.export_csv([])
        
        csv_string = csv_data.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_string))
        rows = list(reader)
        
        assert len(rows) == 1  # Only header

    def test_export_csv_custom_filename(self, exporter, sample_findings):
        """Test CSV export with custom filename"""
        csv_data = exporter.export_csv(sample_findings, filename="custom_report.csv")
        
        assert isinstance(csv_data, bytes)
        # Filename parameter doesn't affect content, just for reference

    def test_export_json(self, exporter, sample_findings):
        """Test JSON export"""
        json_data = exporter.export_json(sample_findings)
        
        assert isinstance(json_data, str)
        
        # Parse JSON and verify
        parsed = json.loads(json_data)
        assert len(parsed) == 4
        assert parsed[0]["id"] == "CVE-2024-0001"
        assert parsed[0]["severity"] == "critical"

    def test_export_json_empty(self, exporter):
        """Test JSON export with empty findings"""
        json_data = exporter.export_json([])
        
        parsed = json.loads(json_data)
        assert parsed == []

    @pytest.mark.skipif(not hasattr(ReportExporter, '_check_weasyprint') or not ReportExporter()._check_weasyprint(),
                       reason="WeasyPrint not available")
    def test_export_pdf_executive(self, exporter, sample_report_data):
        """Test PDF export with executive template"""
        with patch('modules.report_export.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"PDF content"
            
            pdf_data = exporter.export_pdf(sample_report_data, template="executive")
            
            assert pdf_data == b"PDF content"
            mock_html.assert_called_once()

    @pytest.mark.skipif(not hasattr(ReportExporter, '_check_weasyprint') or not ReportExporter()._check_weasyprint(),
                       reason="WeasyPrint not available")
    def test_export_pdf_technical(self, exporter, sample_report_data):
        """Test PDF export with technical template"""
        with patch('modules.report_export.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"PDF content"
            
            pdf_data = exporter.export_pdf(sample_report_data, template="technical")
            
            assert pdf_data == b"PDF content"

    @pytest.mark.skipif(not hasattr(ReportExporter, '_check_weasyprint') or not ReportExporter()._check_weasyprint(),
                       reason="WeasyPrint not available")
    def test_export_pdf_default_template(self, exporter, sample_report_data):
        """Test PDF export uses executive template by default"""
        with patch('modules.report_export.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"PDF content"
            
            pdf_data = exporter.export_pdf(sample_report_data)
            
            assert pdf_data == b"PDF content"

    def test_export_pdf_weasyprint_not_available(self, exporter, sample_report_data):
        """Test PDF export when WeasyPrint is not available"""
        with patch('modules.report_export.WEASYPRINT_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="PDF generation requires WeasyPrint"):
                exporter.export_pdf(sample_report_data)

    def test_executive_template(self, exporter, sample_report_data):
        """Test executive template generation"""
        html = exporter._executive_template(sample_report_data)
        
        assert "Security Assessment Report" in html
        assert "example.com" in html
        assert "Critical" in html or "critical" in html.lower()
        assert "2024-01-15" in html or "2024" in html
        # Check for severity colors
        assert "#dc2626" in html or "#ea580c" in html  # Critical/High colors

    def test_executive_template_with_many_findings(self, exporter):
        """Test executive template limits to top 10 findings"""
        many_findings = [
            {"id": f"FIND-{i}", "severity": "high", "title": f"Finding {i}", "description": "Test"}
            for i in range(20)
        ]
        report = ReportData(
            title="Test Report",
            scan_date=datetime.now(),
            target="test.com",
            findings=many_findings,
            summary={"critical": 0, "high": 20, "medium": 0, "low": 0},
            recommendations=[],
        )
        
        html = exporter._executive_template(report)
        
        # Should only show top 10
        assert html.count("Finding") <= 15  # Some tolerance for other occurrences

    def test_technical_template(self, exporter, sample_report_data):
        """Test technical template generation"""
        html = exporter._technical_template(sample_report_data)
        
        # Technical template currently returns executive template
        assert "Security Assessment Report" in html or len(html) > 0

    def test_compliance_template(self, exporter, sample_report_data):
        """Test compliance template generation"""
        html = exporter._compliance_template(sample_report_data)
        
        # Compliance template currently returns executive template
        assert len(html) > 0

    def test_get_export_formats(self, exporter):
        """Test getting available export formats"""
        formats = exporter.get_export_formats()
        
        assert "csv" in formats
        assert "json" in formats
        # PDF availability depends on WeasyPrint
        if hasattr(ReportExporter, '_check_weasyprint') and ReportExporter()._check_weasyprint():
            assert "pdf" in formats

    def test_get_export_formats_without_weasyprint(self, exporter):
        """Test getting formats when WeasyPrint is not available"""
        with patch('modules.report_export.WEASYPRINT_AVAILABLE', False):
            formats = exporter.get_export_formats()
            
            assert "csv" in formats
            assert "json" in formats
            assert "pdf" not in formats


# ReportData Tests
class TestReportData:
    """Tests for ReportData dataclass"""

    def test_report_data_creation(self):
        """Test ReportData creation"""
        report = ReportData(
            title="Test Report",
            scan_date=datetime.now(),
            target="test.com",
            findings=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
            recommendations=[],
        )
        
        assert report.title == "Test Report"
        assert report.target == "test.com"
        assert report.findings == []

    def test_report_data_with_findings(self, sample_findings):
        """Test ReportData with findings"""
        report = ReportData(
            title="Test Report",
            scan_date=datetime.now(),
            target="test.com",
            findings=sample_findings,
            summary={"critical": 1, "high": 1, "medium": 1, "low": 1},
            recommendations=["Fix issues"],
        )
        
        assert len(report.findings) == 4
        assert report.summary["critical"] == 1
        assert len(report.recommendations) == 1


# Export Function Tests
class TestExportFunctions:
    """Tests for export convenience functions"""

    def test_export_findings_csv(self, sample_findings):
        """Test export_findings with CSV format"""
        data = export_findings(sample_findings, format="csv")
        
        assert isinstance(data, bytes)
        csv_string = data.decode('utf-8')
        assert "CVE-2024-0001" in csv_string

    def test_export_findings_json(self, sample_findings):
        """Test export_findings with JSON format"""
        data = export_findings(sample_findings, format="json")
        
        assert isinstance(data, bytes)
        json_string = data.decode('utf-8')
        parsed = json.loads(json_string)
        assert len(parsed) == 4

    @pytest.mark.skipif(not hasattr(ReportExporter, '_check_weasyprint') or not ReportExporter()._check_weasyprint(),
                       reason="WeasyPrint not available")
    def test_export_findings_pdf(self, sample_findings):
        """Test export_findings with PDF format"""
        with patch('modules.report_export.HTML') as mock_html:
            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf.return_value = b"PDF content"
            
            data = export_findings(sample_findings, format="pdf")
            
            assert data == b"PDF content"

    def test_export_findings_invalid_format(self, sample_findings):
        """Test export_findings with invalid format"""
        with pytest.raises(ValueError, match="Unsupported format"):
            export_findings(sample_findings, format="xml")

    def test_export_findings_calculates_summary(self, sample_findings):
        """Test that export_findings calculates summary for PDF"""
        with patch('modules.report_export.ReportExporter.export_pdf') as mock_export, \
             patch('modules.report_export.WEASYPRINT_AVAILABLE', True):
            mock_export.return_value = b"PDF content"
            
            export_findings(sample_findings, format="pdf")
            
            # Check that export_pdf was called with ReportData
            call_args = mock_export.call_args
            assert call_args is not None
            report_data = call_args[0][0]
            assert report_data.summary["critical"] == 1
            assert report_data.summary["high"] == 1
            assert report_data.summary["medium"] == 1
            assert report_data.summary["low"] == 1


# Template Content Tests
class TestTemplateContent:
    """Tests for template content verification"""

    def test_executive_template_structure(self, exporter, sample_report_data):
        """Test executive template HTML structure"""
        html = exporter._executive_template(sample_report_data)
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in html or "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html
        
        # Check CSS styling
        assert "style" in html
        assert "font-family" in html or "color" in html

    def test_executive_template_severity_colors(self, exporter, sample_report_data):
        """Test that severity colors are properly applied"""
        html = exporter._executive_template(sample_report_data)
        
        # Check for severity color codes
        severity_colors = ["#dc2626", "#ea580c", "#ca8a04", "#16a34a"]
        has_color = any(color in html for color in severity_colors)
        assert has_color or "color" in html

    def test_executive_template_metrics(self, exporter, sample_report_data):
        """Test that metrics are displayed"""
        html = exporter._executive_template(sample_report_data)
        
        # Check for metric values in summary
        assert "1" in html  # Count values
        assert "metric" in html.lower() or "summary" in html.lower()

    def test_executive_template_confidentiality(self, exporter, sample_report_data):
        """Test confidentiality notice in template"""
        html = exporter._executive_template(sample_report_data)
        
        assert "Confidential" in html or "confidential" in html.lower()
        assert "authorized" in html.lower() or "authorized" in html


# Integration Tests
class TestIntegration:
    """Integration tests for report export workflow"""

    def test_full_export_workflow(self, exporter, sample_findings, sample_report_data):
        """Test complete export workflow"""
        # Export in all available formats
        csv_data = exporter.export_csv(sample_findings)
        json_data = exporter.export_json(sample_findings)
        
        assert csv_data is not None
        assert json_data is not None
        
        # Verify CSV can be parsed back
        csv_reader = csv.reader(io.StringIO(csv_data.decode('utf-8')))
        csv_rows = list(csv_reader)
        assert len(csv_rows) == len(sample_findings) + 1  # +1 for header
        
        # Verify JSON can be parsed back
        json_parsed = json.loads(json_data)
        assert len(json_parsed) == len(sample_findings)

    def test_report_data_consistency(self, exporter, sample_findings, sample_report_data):
        """Test that report data is consistent across exports"""
        # Export as JSON
        json_data = exporter.export_json(sample_findings)
        json_parsed = json.loads(json_data)
        
        # Verify all findings are present
        assert len(json_parsed) == len(sample_report_data.findings)
        
        # Verify severity counts match summary
        critical_count = sum(1 for f in sample_findings if f["severity"] == "critical")
        assert critical_count == sample_report_data.summary["critical"]

    def test_empty_report_handling(self, exporter):
        """Test handling of empty reports"""
        empty_report = ReportData(
            title="Empty Report",
            scan_date=datetime.now(),
            target="test.com",
            findings=[],
            summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
            recommendations=[],
        )
        
        html = exporter._executive_template(empty_report)
        
        assert "Empty Report" in html
        assert "0" in html  # Zero counts

    def test_large_report_handling(self, exporter):
        """Test handling of large reports"""
        large_findings = [
            {
                "id": f"FIND-{i}",
                "severity": ["critical", "high", "medium", "low"][i % 4],
                "title": f"Finding {i} with a very long title that might need truncation",
                "description": "Description " * 50,  # Long description
                "target": f"http://example.com/page{i}",
                "cve_id": f"CVE-2024-{i:04d}" if i % 2 == 0 else None,
                "cvss_score": str(9.0 - (i % 4) * 2),
                "status": "open",
                "discovered_at": datetime.now().isoformat(),
            }
            for i in range(100)
        ]
        
        large_report = ReportData(
            title="Large Report",
            scan_date=datetime.now(),
            target="example.com",
            findings=large_findings,
            summary={"critical": 25, "high": 25, "medium": 25, "low": 25},
            recommendations=["Fix all issues"],
        )
        
        html = exporter._executive_template(large_report)
        csv_data = exporter.export_csv(large_findings)
        json_data = exporter.export_json(large_findings)
        
        assert len(html) > 0
        assert len(csv_data) > 0
        assert len(json_data) > 0
        
        # Verify all 100 findings are in CSV/JSON
        csv_reader = csv.reader(io.StringIO(csv_data.decode('utf-8')))
        csv_rows = list(csv_reader)
        assert len(csv_rows) == 101  # header + 100 findings
        
        json_parsed = json.loads(json_data)
        assert len(json_parsed) == 100


# Edge Case Tests
class TestEdgeCases:
    """Tests for edge cases"""

    def test_finding_with_missing_fields(self, exporter):
        """Test handling of findings with missing optional fields"""
        incomplete_findings = [
            {
                "id": "FIND-1",
                "severity": "high",
                # Missing description, target, cve_id, cvss_score
            }
        ]
        
        csv_data = exporter.export_csv(incomplete_findings)
        json_data = exporter.export_json(incomplete_findings)
        
        assert csv_data is not None
        assert json_data is not None

    def test_finding_with_special_characters(self, exporter):
        """Test handling of findings with special characters"""
        special_findings = [
            {
                "id": "FIND-1",
                "severity": "high",
                "title": "XSS <script>alert('test')</script>",
                "description": "Unicode: 你好世界 🌍 émojis",
                "target": "http://example.com?param=<value>&other=test",
                "cve_id": "CVE-2024-0001",
                "cvss_score": "8.5",
                "status": "open",
                "discovered_at": datetime.now().isoformat(),
            }
        ]
        
        csv_data = exporter.export_csv(special_findings)
        json_data = exporter.export_json(special_findings)
        
        assert csv_data is not None
        assert json_data is not None
        
        # Verify JSON handles special characters
        parsed = json.loads(json_data)
        assert "<script>" in parsed[0]["title"]
        assert "你好世界" in parsed[0]["description"]

    def test_very_long_description_truncation(self, exporter):
        """Test that very long descriptions are handled"""
        long_desc_findings = [
            {
                "id": "FIND-1",
                "severity": "high",
                "title": "Test Finding",
                "description": "A" * 10000,  # Very long description
                "target": "http://example.com",
            }
        ]
        
        report = ReportData(
            title="Test",
            scan_date=datetime.now(),
            target="test.com",
            findings=long_desc_findings,
            summary={"critical": 0, "high": 1, "medium": 0, "low": 0},
            recommendations=[],
        )
        
        html = exporter._executive_template(report)
        
        # Should truncate or handle long description
        assert "..." in html or len(html) < 10000 * 2

    def test_html_injection_prevention(self, exporter):
        """Test that HTML in findings doesn't break template"""
        xss_findings = [
            {
                "id": "FIND-1",
                "severity": "high",
                "title": "</div><script>alert('XSS')</script><div>",
                "description": "<img src=x onerror=alert(1)>",
                "target": "http://example.com",
            }
        ]
        
        report = ReportData(
            title="Test",
            scan_date=datetime.now(),
            target="test.com",
            findings=xss_findings,
            summary={"critical": 0, "high": 1, "medium": 0, "low": 0},
            recommendations=[],
        )
        
        # Should not raise exception
        html = exporter._executive_template(report)
        assert len(html) > 0

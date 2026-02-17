"""
Tests for report_gen module - Coverage Boost
"""

import pytest
import json
import os
import csv
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, MagicMock, AsyncMock


class AsyncMock(Mock):
    """Async mock class for Python 3.7+ compatibility"""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class TestReportGenerator:
    """Test ReportGenerator class"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator with async support"""
        mock = MagicMock()
        future = asyncio.Future()
        future.set_result(MagicMock(content="Test executive summary"))
        mock.process = MagicMock(return_value=future)
        return mock

    @pytest.fixture
    def report_gen(self, mock_orchestrator):
        """Create ReportGenerator instance"""
        from modules.report_gen import ReportGenerator
        return ReportGenerator(mock_orchestrator)

    def test_init(self, report_gen, mock_orchestrator):
        """Test initialization"""
        assert report_gen.orchestrator == mock_orchestrator
        assert report_gen.findings == []
        assert report_gen.executive_summary == ""

    @pytest.mark.asyncio
    async def test_generate_executive_summary(self, report_gen, mock_orchestrator):
        """Test executive summary generation"""
        scan_results = {
            'target': 'example.com',
            'date': datetime.now().isoformat(),
            'vulnerability_summary': {
                'Critical': 2,
                'High': 5,
                'Medium': 10,
                'Low': 15,
                'Info': 20
            },
            'top_findings': [
                {'name': 'SQL Injection', 'severity': 'Critical'},
                {'name': 'XSS', 'severity': 'High'}
            ]
        }

        result = await report_gen.generate_executive_summary(scan_results)
        
        assert result == "Test executive summary"
        assert report_gen.executive_summary == "Test executive summary"
        mock_orchestrator.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_technical_report(self, report_gen):
        """Test technical report generation"""
        # Create mock vulnerabilities with proper iterable cve_ids
        vuln1 = Mock(
            name='SQL Injection',
            severity='Critical',
            description='Test description',
            evidence='Test evidence',
            remediation='Fix it',
            cve_ids=['CVE-2021-1234'],
            cvss_score=9.8
        )
        vuln2 = Mock(
            name='XSS',
            severity='High',
            description='XSS description',
            evidence='XSS evidence',
            remediation='Sanitize input',
            cve_ids=[],  # Empty list instead of None
            cvss_score=None
        )
        
        report_gen.executive_summary = "Test summary"
        
        result = await report_gen.generate_technical_report([vuln1, vuln2], 'example.com')
        
        assert 'Penetration Test Report' in result
        assert 'example.com' in result
        assert 'SQL Injection' in result
        assert 'XSS' in result
        assert 'Critical' in result
        assert 'High' in result
        assert 'Test summary' in result
        assert 'CVE-2021-1234' in result
        assert '9.8' in result

    def test_format_vulnerability(self, report_gen):
        """Test vulnerability formatting"""
        vuln = Mock(
            name='Test Vuln',
            severity='High',
            description='Test description',
            evidence='Test evidence',
            remediation='Fix it',
            cve_ids=['CVE-2021-1234', 'CVE-2021-5678'],
            cvss_score=8.5
        )
        
        lines = report_gen._format_vulnerability(vuln, 1)
        
        assert 'Test Vuln' in '\n'.join(lines)
        assert 'High' in '\n'.join(lines)
        assert 'Test description' in '\n'.join(lines)
        assert 'Test evidence' in '\n'.join(lines)
        assert 'Fix it' in '\n'.join(lines)
        assert 'CVE-2021-1234' in '\n'.join(lines)
        assert '8.5' in '\n'.join(lines)

    def test_format_vulnerability_no_optional(self, report_gen):
        """Test vulnerability formatting without optional fields"""
        vuln = Mock(
            name='Simple Vuln',
            severity='Low',
            description='Simple description',
            evidence='Simple evidence',
            remediation='Simple fix',
            cve_ids=[],  # Empty list
            cvss_score=None
        )
        
        lines = report_gen._format_vulnerability(vuln, 2)
        
        assert 'Simple Vuln' in '\n'.join(lines)
        assert 'Low' in '\n'.join(lines)

    @patch('builtins.open', mock_open())
    @patch('modules.report_gen.logger')
    def test_export_json(self, mock_logger, report_gen):
        """Test JSON export"""
        data = {
            'target': 'example.com',
            'findings': [{'name': 'Test', 'severity': 'High'}]
        }
        
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            result = report_gen.export_json(data, 'test_report.json')
        
        assert 'test_report.json' in result
        mock_logger.info.assert_called_once()

    @patch('builtins.open', mock_open())
    @patch('modules.report_gen.logger')
    def test_export_json_auto_filename(self, mock_logger, report_gen):
        """Test JSON export with auto-generated filename"""
        data = {'findings': []}
        
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            result = report_gen.export_json(data)
        
        assert 'report_20240101_120000.json' in result

    @patch('builtins.open', mock_open())
    @patch('csv.writer')
    @patch('modules.report_gen.logger')
    def test_export_csv(self, mock_logger, mock_csv_writer, report_gen):
        """Test CSV export"""
        vuln = Mock(
            name='Test Vuln',
            severity='High',
            description='Test description',
            evidence='Test evidence',
            remediation='Fix it',
            cve_ids=['CVE-2021-1234']
        )
        
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            result = report_gen.export_csv([vuln], 'test_vulns.csv')
        
        assert 'test_vulns.csv' in result
        mock_logger.info.assert_called_once()

    @patch('builtins.open', mock_open())
    @patch('csv.writer')
    @patch('modules.report_gen.logger')
    def test_export_csv_auto_filename(self, mock_logger, mock_csv_writer, report_gen):
        """Test CSV export with auto-generated filename"""
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            result = report_gen.export_csv([])
        
        assert 'vulnerabilities_20240101_120000.csv' in result

    @pytest.mark.asyncio
    async def test_generate_remediation_roadmap(self, report_gen, mock_orchestrator):
        """Test remediation roadmap generation"""
        vulns = [
            Mock(name='SQL Injection', severity='Critical'),
            Mock(name='XSS', severity='High'),
            Mock(name='Info Leak', severity='Low')
        ]
        
        result = await report_gen.generate_remediation_roadmap(vulns)
        
        assert result == "Test executive summary"
        mock_orchestrator.process.assert_called()

    @pytest.mark.asyncio
    async def test_generate_compliance_mapping(self, report_gen, mock_orchestrator):
        """Test compliance mapping generation"""
        class MockVuln:
            name = 'SQL Injection'
        
        vulns = [MockVuln(), MockVuln()]
        
        result = await report_gen.generate_compliance_mapping(vulns, 'NIST')
        
        assert result['framework'] == 'NIST'
        assert result['mapping'] == "Test executive summary"
        mock_orchestrator.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_compliance_mapping_default_framework(self, report_gen, mock_orchestrator):
        """Test compliance mapping with default framework"""
        class MockVuln:
            name = 'Test Vuln'
        
        vulns = [MockVuln()]
        
        result = await report_gen.generate_compliance_mapping(vulns)
        
        assert result['framework'] == 'NIST'

    @pytest.mark.asyncio
    async def test_generate_technical_report_empty_vulns(self, report_gen):
        """Test technical report with no vulnerabilities"""
        result = await report_gen.generate_technical_report([], 'example.com')
        
        assert 'Penetration Test Report' in result
        assert 'example.com' in result

    @pytest.mark.asyncio
    async def test_generate_technical_report_unknown_severity(self, report_gen):
        """Test technical report with unknown severity"""
        vuln = Mock(
            name='Unknown Vuln',
            severity='Unknown',
            description='Test',
            evidence='Test',
            remediation='Test',
            cve_ids=[],  # Empty list
            cvss_score=None
        )
        
        result = await report_gen.generate_technical_report([vuln], 'example.com')
        
        assert 'Unknown Vuln' in result

    @pytest.mark.asyncio
    async def test_generate_technical_report_no_executive_summary(self, report_gen):
        """Test technical report without executive summary"""
        result = await report_gen.generate_technical_report([], 'example.com')
        
        assert 'Executive Summary' in result
        assert 'not generated' in result

    @patch('modules.report_gen.logger')
    def test_export_json_with_dataclass(self, mock_logger, report_gen):
        """Test JSON export with dataclass object"""
        from dataclasses import dataclass
        
        @dataclass
        class TestData:
            name: str
            value: int
        
        data = {'obj': TestData('test', 42)}
        
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            with patch('builtins.open', mock_open()):
                result = report_gen.export_json(data, 'test.json')
        
        assert 'test.json' in result

    @patch('modules.report_gen.logger')
    def test_export_csv_with_cves(self, mock_logger, report_gen):
        """Test CSV export with multiple CVEs"""
        vuln = Mock(
            name='Test Vuln',
            severity='Critical',
            description='A' * 250,  # Test truncation
            evidence='B' * 250,
            remediation='C' * 250,
            cve_ids=['CVE-2021-1', 'CVE-2021-2', 'CVE-2021-3']
        )
        
        with patch('modules.report_gen.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            with patch('builtins.open', mock_open()):
                with patch('csv.writer') as mock_writer:
                    result = report_gen.export_csv([vuln])
        
        assert 'vulnerabilities_' in result

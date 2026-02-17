"""
Unit tests for Compliance Reporter

Tests compliance reporting for various standards:
- ISO 27001
- GDPR
- PCI DSS
"""

import pytest
from datetime import datetime, timedelta
import asyncio

# Import audit components
try:
    from audit import AuditLogger, ComplianceReporter
    from audit.config import AuditConfig, LogLevel, EventCategory
    from audit.compliance import ComplianceStandard
except ImportError:
    import sys
    sys.path.insert(0, "../../..")
    from audit import AuditLogger, ComplianceReporter
    from audit.config import AuditConfig, LogLevel, EventCategory
    from audit.compliance import ComplianceStandard


class TestComplianceReporter:
    """Test ComplianceReporter class"""
    
    @pytest.fixture
    async def reporter(self):
        """Create test reporter with sample data"""
        config = AuditConfig(async_logging=False, sign_logs=True)
        logger = AuditLogger(config)
        await logger.start()
        
        reporter = ComplianceReporter(logger)
        
        # Create sample audit data
        await logger.info(
            EventCategory.AUTHENTICATION,
            "user_login",
            "User logged in successfully",
            user_id="user1",
            ip_address="192.168.1.1"
        )
        
        await logger.info(
            EventCategory.AUTHORIZATION,
            "access_granted",
            "Access granted to resource",
            user_id="user1",
            resource_id="doc-123"
        )
        
        await logger.warning(
            EventCategory.SECURITY,
            "failed_login",
            "Failed login attempt",
            ip_address="10.0.0.1"
        )
        
        yield reporter
        await logger.stop()
    
    @pytest.mark.asyncio
    async def test_iso27001_report(self, reporter):
        """Test ISO 27001 compliance report"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        assert report["standard"] == "iso27001"
        assert "summary" in report
        assert "findings" in report
        assert "evidence_package" in report
        
        # Check summary
        assert report["summary"]["total_controls"] > 0
        assert "compliance_rate" in report["summary"]
        assert 0 <= report["summary"]["compliance_rate"] <= 100
    
    @pytest.mark.asyncio
    async def test_gdpr_report(self, reporter):
        """Test GDPR compliance report"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.GDPR,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        assert report["standard"] == "gdpr"
        assert report["summary"]["total_controls"] > 0
    
    @pytest.mark.asyncio
    async def test_pci_dss_report(self, reporter):
        """Test PCI DSS compliance report"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.PCI_DSS,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        assert report["standard"] == "pci_dss"
        assert report["summary"]["total_controls"] > 0
    
    @pytest.mark.asyncio
    async def test_report_with_findings(self, reporter):
        """Test report includes findings"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        # Should have findings for each control
        assert len(report["findings"]) > 0
        
        # Each finding should have required fields
        for finding in report["findings"]:
            assert "control_id" in finding
            assert "status" in finding
            assert finding["status"] in ["pass", "fail", "partial", "not_applicable"]
            assert "evidence_count" in finding
            assert "findings" in finding
            assert "recommendations" in finding
    
    @pytest.mark.asyncio
    async def test_evidence_package(self, reporter):
        """Test evidence package generation"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        evidence = report["evidence_package"]
        
        assert "log_summary" in evidence
        assert "integrity_verification" in evidence
        assert "sample_logs" in evidence
        assert "control_mapping" in evidence
        
        # Check log summary
        assert "total_events" in evidence["log_summary"]
        assert "by_category" in evidence["log_summary"]
        assert "by_level" in evidence["log_summary"]
    
    @pytest.mark.asyncio
    async def test_export_json(self, reporter):
        """Test JSON export"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        json_data = await reporter.export_report(report, "json")
        
        assert "iso27001" in json_data
        assert "summary" in json_data
        assert "findings" in json_data
    
    @pytest.mark.asyncio
    async def test_export_markdown(self, reporter):
        """Test Markdown export"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        md_data = await reporter.export_report(report, "markdown")
        
        assert "# Compliance Report" in md_data
        assert "ISO/IEC 27001" in md_data
        assert "## Summary" in md_data
        assert "## Findings" in md_data
        assert "|" in md_data  # Markdown table
    
    @pytest.mark.asyncio
    async def test_export_csv(self, reporter):
        """Test CSV export"""
        report = await reporter.generate_report(
            standard=ComplianceStandard.ISO27001,
            start_date=datetime.utcnow() - timedelta(days=30)
        )
        
        csv_data = await reporter.export_report(report, "csv")
        
        assert "control_id,status,evidence_count" in csv_data
        lines = csv_data.strip().split("\n")
        assert len(lines) > 1  # Header + data rows


class TestComplianceControls:
    """Test compliance control definitions"""
    
    def test_iso27001_controls_exist(self):
        """Test ISO 27001 controls are defined"""
        from audit.compliance import ComplianceReporter
        
        controls = ComplianceReporter.ISO27001_CONTROLS
        
        assert len(controls) > 0
        
        # Check required controls
        required = ["A.12.4.1", "A.12.4.2", "A.12.4.3"]
        for control_id in required:
            assert control_id in controls
    
    def test_gdpr_controls_exist(self):
        """Test GDPR controls are defined"""
        from audit.compliance import ComplianceReporter
        
        controls = ComplianceReporter.GDPR_CONTROLS
        
        assert len(controls) > 0
        assert "Art.32" in controls  # Security of processing
        assert "Art.33" in controls  # Breach notification
    
    def test_pci_dss_controls_exist(self):
        """Test PCI DSS controls are defined"""
        from audit.compliance import ComplianceReporter
        
        controls = ComplianceReporter.PCI_DSS_CONTROLS
        
        assert len(controls) > 0
        assert "Req.10.1" in controls
        assert "Req.10.2" in controls
    
    def test_control_structure(self):
        """Test control structure is valid"""
        from audit.compliance import ComplianceReporter, ComplianceControl
        
        for control in ComplianceReporter.ISO27001_CONTROLS.values():
            assert isinstance(control, ComplianceControl)
            assert control.control_id
            assert control.description
            assert control.requirement
            assert control.evidence_required
            assert control.verification_method


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
